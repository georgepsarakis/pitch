#!/usr/bin/python
try:
  from gevent import monkey
  monkey.patch_socket()
  import gevent
except ImportError:
  gevent = None
import os
import sys
import re
import requests
from time import time, sleep
from functools import partial
from itertools import imap
import argparse
try:
  import yaml
except ImportError:
  yaml = None
try:
  from tabulate import tabulate
except ImportError:
  tabulate = None
import signal
import random
try:
  from bs4 import BeautifulSoup as bs
except ImportError:
  bs = None
try:
  import simplejson as json
except ImportError:
  import json

arguments = {
  'profile'  : ( 'P', { 'help' : 'Store & display profiling data for the requests.', 'action' : 'store_true', 'default' : False } ),
  'time'     : ( 'B', { 'help' : 'Duration of benchmark (in sec). Default is 60. Use combined with -p/--profile.', 'type' : float, 'default': 60.}),
  'threads'  : ( 'T', { 'help' : 'Number of parallel threads.', 'default': 1, 'type': int}),
  'delay'    : ( 'D', { 'help' : 'Delay between requests in msec.', 'type': float, 'default': 0.}),
  'url'      : ( 'U', { 'help' : 'URL to process. You can enter multiple values.', 'nargs': '*'}),
  'url-file' : ( 'F', { 'help' : 'Files with URLs to process. You can enter multiple values.', 'nargs': '*', 'default': None}),
  'timeout'  : ( 'X', { 'help' : 'Request timeout in seconds.', 'type': float, 'default': 2.}),
  'elements' : ( 'E', { 'help': 'CSS selectors of elements in requested pages to be returned in STDOUT.', 'nargs': '*', 'default': None}),
  'method'   : ( 'M', { 'help': 'GET/POST method.', 'default': 'GET', 'choices': ['GET', 'POST']}),
  'auth'     : ( 'A', { 'help': "Basic Authentication username:password (e.g. -A 'george:superpass')", 'default': None}),
  'output'   : ( 'O', { 'help': 'Output format - benchmarking results & element content.', 'choices': ['plain','json'], 'default': 'plain'}),
  'verbose'  : ( 'v', { 'help': 'Verbosity', 'action': 'count', 'default': 0}),
  'config'   : ( 'C', { 'help': 'Configuration file. See https://github.com/georgepsarakis/pitch#configuration-files', }),
}

class Pitch(object):
  TERMINATE             = False
  PROGRESS_INTERVAL     = 1.
  PROGRESS_LAST_PRINTED = None
  METRICS = {
    'ok'       : { 
      'label' : 'Successful',
      'unit'  : '',
      },
    'error'    : { 
      'label' : 'Failed',
      'unit'  : '',
      },
    'total'    : {
      'label' : 'Total',
      'unit'  : '',
      },
    'time'     : {
      'label' : 'Time',
      'unit'  : 'sec',
      },
    'max'      : {
      'label' : 'Maximum Time',
      'unit'  : 'sec',
      },
    'min'      : {
      'label' : 'Minimum Time',
      'unit'  : 'sec',
      },
    'avg'      : {
      'label' : 'Average Time',
      'unit'  : 'sec',
      },
    'size'     : {
      'label' : 'Total Size',
      'unit'  : 'KB',
      },
    'avg-size' : {
      'label' : 'Average Size',
      'unit'  : 'KB',
      }
  }     
  ERROR = 0
  WARN  = 1 
  INFO  = 2
  def __init__(self, parameters=None, **kwargs):
    self.URLS = []
    self.STATS = {}
    self.ELEMENTS = {} 
    self.DATA = {}
    self.HEADERS = {}
    if parameters is None:
      parameters = Pitch.parameterizer(**kwargs)
    self.PARAMETERS = parameters
    self.__process_parameters()
    if not self.PARAMETERS.auth is None:
      R = requests.Session()
      R.auth = tuple(self.PARAMETERS.auth.split(':'))
    else:
      R = requests
    self.pitcher = partial(getattr(R, self.PARAMETERS.method), timeout=self.PARAMETERS.timeout, headers=self.HEADERS, verify=False)
    if self.PARAMETERS.verbose > 0:
      header = [ "****  pitch v1.0 ****" ]
      header.append('Initializing with:')
      header.append('- URLs     : %d' % len(self.URLS))
      header.append('- Threads  : %d' % self.PARAMETERS.threads)
      header.append('- Timeout  : %d' % self.PARAMETERS.timeout)
      header.append('- Duration : %d' % self.PARAMETERS.time)
      header.append('- Elements : %s' % self.PARAMETERS.elements)
      print "\n".join([ h.ljust(max(map(len, header))) for h in header ])
  
  @staticmethod
  def parameterizer(**kwargs):   
    if kwargs:
      ''' temporary copy of sys.argv '''
      sys_argv = sys.argv[:]
      sys.argv = []
      for k, v in kwargs:
        if isinstance(v, list):
          v = ' '.join(v)
        sys.argv.append('--%s=%s' % (k, v))
    else:
      ''' display help when empty '''
      if len(sys.argv) <= 1:
        sys.argv.append('-h')
    optparser = argparse.ArgumentParser('pitch - URL Fetching & Benchmarking Tool')
    for switch, parameters in arguments.iteritems():
      optparser.add_argument('-%s' % parameters[0], '--%s' % switch, **parameters[1])
    parameters = optparser.parse_args()
    if kwargs:
      ''' restore original command line parameters '''
      sys.argv = sys_argv[:]
    return parameters

  def __process_parameters(self):
    self.PARAMETERS.method = self.PARAMETERS.method.lower()
    if not self.PARAMETERS.method in ['get','post']:
      self.PARAMETERS.method = 'get'
    if self.PARAMETERS.delay > 0.:
      self.PARAMETERS.delay /= 1000.
    if self.PARAMETERS.threads < 1:
      self.PARAMETERS.threads = 1
    if not self.PARAMETERS.profile and self.PARAMETERS.elements is None:
      self.PARAMETERS.elements = ['html']
    if not self.PARAMETERS.url is None:
      self.URLS.extend(self.PARAMETERS.url)
    if not self.PARAMETERS.url_file is None:
      for filename in self.PARAMETERS.url_file:     
        if os.path.exists(filename):
          with open(filename) as f:
            self.URLS.extend(f.readlines())
        else:
          self.log("File %s does not exist, ignored." % filename, self.WARN)
    if not self.PARAMETERS.config is None:
      if not os.path.exists(self.PARAMETERS.config):
        raise Exception('Configuration file "%s" not found.' % self.PARAMETERS.config)
      try:
        with open(self.PARAMETERS.config, 'r') as f:
          configuration = yaml.load("\n".join(f.readlines()))
      except yaml.parser.ParserError:
        raise Exception('Not valid YAML file.')
      if 'headers' in configuration:
        self.HEADERS.update(configuration['headers'])
      if 'settings' in configuration:
        for setting, value in configuration['settings'].iteritems():
          if not hasattr(self.PARAMETERS, setting):
            raise Exception('Unknown setting "%s"' % setting)
        for setting, value in dict(configuration['settings'].items() + vars(self.PARAMETERS).items()).iteritems():
          setattr(self.PARAMETERS, setting, value)
      if 'urls' in configuration:
        for config in configuration['urls']:
          self.URLS.append(config['url'])
          self.DATA[config['url']] = config['data']
    if not self.URLS:
      raise Exception('No URL supplied. Use --url or/and --url-file parameters.')
    self.URLS = map(self.url_normalizer, self.URLS)
         
  def url_normalizer(self, url):
    url = url.strip()
    if re.match(r'^http:', url) is None:      
      url = 'http://%s' % url
    return url
 
  def delayer(self):
    if self.PARAMETERS.delay > 0:
      sleep(self.PARAMETERS.delay)

  def run(self):
    try:
      self.looper()
    except KeyboardInterrupt:
      pass
    self.results()    
   
  def formatter(self, metric, item):
    if isinstance(item, int):
      return "%d%s" % (item, self.METRICS[metric]['unit'])
    elif isinstance(item, float):
      return "%8.3f%s" % (item, self.METRICS[metric]['unit'])
   
  def result_table(self, stats, metrics):
    display = [ [ self.METRICS[metric]['label'], self.formatter(metric, stats[metric]) ] for metric in metrics ]
    if self.PARAMETERS.output == "plain":
      return tabulate(display, tablefmt="grid")
    elif self.PARAMETERS.output == "json":
      return dict(display)

  def results(self):
    if self.PARAMETERS.output == "json":
      printer = partial(json.dumps, indent=2, separators=(',', ':'))
    else: 
      printer = "\n".join
    if self.PARAMETERS.profile:
      labels = self.METRICS.keys()
      output = []
      for url, stats in self.STATS.iteritems():
        stats = dict([(k,0) for k in labels] + stats.items())
        stats['avg'] = stats['total']/stats['time']
        stats['avg-size'] = stats['size']/stats['ok']/1024.
        stats['size'] /= 1024.       
        time_metrics = [ 'max', 'min', 'avg', 'time', ]
        state_metrics = [ 'ok', 'error', 'total', ]
        size_metrics = [ 'size', 'avg-size' ]
        table = self.result_table(stats, state_metrics + time_metrics + size_metrics)
        if self.PARAMETERS.output == "plain":
          output.append('|--- ' + url.encode('utf-8') + ' ---|')
          output.append(table)
        elif self.PARAMETERS.output == "json":
          output.append({ url : table })
      print printer(output)
    if not self.PARAMETERS.elements is None:
      if self.PARAMETERS.output == "json":
        elements = self.ELEMENTS
      elif self.PARAMETERS.output == "plain":
        elements = [ "\n".join(self.ELEMENTS[url][selector]) for url, selectors in self.ELEMENTS.iteritems() for selector in selectors ]       
      print printer(elements)
               
  def fetcher(self, url):
    start = time()
    try:
      try:
        if self.PARAMETERS.method == "get":
          params['params'] = self.DATA[url]
        elif self.PARAMETERS.method == "post":
          params['data'] = self.DATA[url]        
      except KeyError:      
        params = {}
      request = self.pitcher(url, **params)
    except requests.ConnectionError:
      request = None
    request_time = time() - start
    self.delayer()
    return url, request, request_time
  
  def fetch_element(self, html):
    if not self.PARAMETERS.elements is None:
      tree = bs(html, "lxml")
      elements = {}
      for selector in self.PARAMETERS.elements:        
        elements[selector] = map(unicode, tree.select(selector))
      return elements
    return {}
   
  def incr(self, obj, key, value=1):
    try:
      obj[key] += value
    except KeyError:
      obj[key] = value
    return obj[key]
  
  def progress(self, counter, start):
    if self.PROGRESS_LAST_PRINTED is None:
      self.PROGRESS_LAST_PRINTED = time()
    if self.PARAMETERS.verbose >= 1 and self.PARAMETERS.time > 0:
      if time() - self.PROGRESS_LAST_PRINTED >= self.PROGRESS_INTERVAL:
        self.PROGRESS_LAST_PRINTED = time()
        message = ">> %d REQUESTS (%d%%)" % (counter * self.PARAMETERS.threads, int(100*(time()-start)/self.PARAMETERS.time))
        sys.stdout.write(message)
        sys.stdout.flush()
        sys.stdout.write('\b' * len(message))
    counter += 1
    return counter
   
  def looper(self):
    counter = 0
    start = time()
    profile = self.PARAMETERS.profile
    if not profile:
      duration = 0
    else:
      duration = self.PARAMETERS.time
    while not self.TERMINATE and ( time() - start < duration or duration == 0):
      counter = self.progress(counter, start)
      results = []
      if self.PARAMETERS.threads > 1:
        if profile:
          urls = (random.choice(self.URLS) for n in xrange(self.PARAMETERS.threads))
        else:
          urls = self.URLS
        threads = [ gevent.spawn(self.fetcher, url) for url in urls ]
        timeout = duration - time() + start
        if timeout < self.PARAMETERS.timeout:
          timeout = self.PARAMETERS.timeout
        gevent.joinall(threads, timeout=timeout)
        results = (_.value for _ in threads if not _ is None and  _.successful)
      else:
        results = filter(None, map(self.fetcher, self.URLS))
      if not self.PARAMETERS.elements is None:
        self.ELEMENTS.update(dict(zip([ r[0] for r in results ], map(self.fetch_element, [ r[1].content for r in results ]))))
      if profile:
        for url, request, request_time in results:
          try:
            self.STATS[url]
          except KeyError:
            self.STATS[url] = {
              'min' : 10**6,
              'max' : 0,
            }
          stats = self.STATS[url]
          stats['min'] = min(stats['min'], request_time)
          stats['max'] = max(stats['max'], request_time)
          try:
            self.incr(stats, 'size', int(request.headers['content-length']))
          except KeyError:
            pass
          self.incr(stats, 'time', request_time)
          self.incr(stats, 'total')                            
          if not request is None and request.status_code < 400:
            self.incr(stats, 'ok')
          else:
            self.incr(stats, 'error')              
      if duration == 0: 
        break
    sys.stdout.flush()
  
  def terminate(self, signum, frame):
    self.TERMINATE = True

  def log(self, message, level=2):
    if level == self.ERROR:
      print "ERROR: %s" % message
    elif level == self.WARN:
      print "WARNING: %s" % message
    elif level == self.INFO:
      print "INFO: %s" % message

''' wrapper function for entry point '''
def main():
  P = Pitch(Pitch.parameterizer())
  signal.signal(signal.SIGTERM, P.terminate)
  P.run()  

if __name__ == "__main__":
  main()
