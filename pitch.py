#!/usr/bin/python
from gevent import monkey
monkey.patch_socket()
import gevent
import os
import sys
import re
import requests
from time import time, sleep
from functools import partial
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

class Pitch(object):
  Pitcher   = None
  TERMINATE = False
  METRICS    = {
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
  ELEMENTS = {} 
  ERROR = 0
  WARN  = 1 
  INFO  = 2
  def __init__(self, parameters):
    self.URLS = []
    self.PARAMETERS = parameters
    self.__process_parameters()
    self.pitcher = partial(getattr(requests, self.PARAMETERS.method), timeout=self.PARAMETERS.timeout)
    self.STATS = {}
    if not self.PARAMETERS.url is None:
      self.URLS.extend(self.PARAMETERS.url)
    if not self.URLS:
      raise Exception('No URL supplied. Use --url or/and --url-file parameters.')
    for index, url in enumerate(self.URLS):
      if re.match(r'^http:', url) is None:
        self.URLS[index] = 'http://%s' % url
    if self.PARAMETERS.verbose > 0:
      header = [ "****  pitch v1.0 ****" ]
      header.append('Initializing with:')
      header.append('- URLs     : %d' % len(self.URLS))
      header.append('- Threads  : %d' % self.PARAMETERS.threads)
      header.append('- Timeout  : %d' % self.PARAMETERS.timeout)
      header.append('- Duration : %d' % self.PARAMETERS.time)
      header.append('- Elements : %s' % self.PARAMETERS.element)
      print "\n".join([ h.ljust(max(map(len, header))) for h in header ])

  def __process_parameters(self):
    self.PARAMETERS.method = self.PARAMETERS.method.lower()
    if not self.PARAMETERS.method in ['get','post']:
      self.PARAMETERS.method = 'get'
    if self.PARAMETERS.threads < 1:
      self.PARAMETERS.threads = 1
    if not self.PARAMETERS.url_file is None:
      for filename in self.PARAMETERS.url_file:     
        if os.path.exists(filename):
          with open(filename) as f:
            self.URLS.extend(f.readlines())
        else:
          self.log("File %s does not exist, ignored." % filename, self.WARN)

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
        for k in labels:
          if not k in stats:
            stats[k] = 0
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
    if not self.PARAMETERS.element is None:
      print printer(self.ELEMENTS)
               
  def fetcher(self, url):
    start = time()
    try:
      request = self.pitcher(url)
    except requests.ConnectionError:
      request = None
    request_time = time() - start
    return url, request, request_time
  
  def fetch_element(self, html):
    if not self.PARAMETERS.element is None:
      try:
        tree = bs(html, "lxml")
        elements = {}
        for selector in self.PARAMETERS.element:        
          elements[selector] = map(unicode, tree.select(selector))
        return elements
      except:
        return {}
   
  def incr(self, obj, key, value=1):
    try:
      obj[key] += value
    except KeyError:
      obj[key] = value
    return obj[key]
   
  def looper(self):
    start = time()
    profile = self.PARAMETERS.profile
    if not profile:
      duration = 0
    else:
      duration = self.PARAMETERS.time
    counter = 0
    request_factor = 1
    if self.PARAMETERS.threads > 1:
      request_factor = self.PARAMETERS.threads
    INTERVAL = 1.
    printed = time()
    while not self.TERMINATE and ( time() - start < duration or duration == 0):
      if self.PARAMETERS.verbose >= 1 and duration > 0 and time() - printed >= INTERVAL:
        printed = time()
        message = ">> %d REQUESTS (%d%%)" % (counter * request_factor, int(100*(time()-start)/duration))
        sys.stdout.write(message)
        sys.stdout.flush()
        sys.stdout.write('\b' * len(message))
      counter += 1
      results = []
      if self.PARAMETERS.threads > 1:
        urls = (random.choice(self.URLS) for n in xrange(self.PARAMETERS.threads))
        threads = [ gevent.spawn(self.fetcher, url) for url in urls ]
        timeout = duration - time() + start
        if timeout < self.PARAMETERS.timeout:
          timeout = self.PARAMETERS.timeout
        gevent.joinall(threads, timeout=timeout)
        results = [ _.value for _ in threads if _.successful ]
      else:
        results = [ self.fetcher(url) for url in self.URLS ]
      if not self.PARAMETERS.element is None:
        for url, request, request_time in results:
          self.ELEMENTS[url] = self.fetch_element(request.content) 
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
    
if __name__ == "__main__":
  import argparse
  optparser = argparse.ArgumentParser('pitch - URL Fetching & Benchmarking Tool')
  optparser.add_argument('-p', '--profile',  help='Store profiling data for the requests.', action='store_true', default=False)
  optparser.add_argument('-b', '--time',     help='Duration of benchmark (in sec). Default is 60. Use combined with -p/--profile.', type=float, default=60.)
  optparser.add_argument('-t', '--threads',  help='Number of parallel threads.', default=0, type=int)
  optparser.add_argument('-d', '--delay',    help='Delay between requests in msec.', type=float, default=0.)
  optparser.add_argument('-u', '--url',      help='URL to process. You can enter multiple values.', nargs='*')
  optparser.add_argument('-f', '--url-file', help='Files with URLs to process. You can enter multiple values.', nargs='*', default=None)
  optparser.add_argument('-X', '--timeout',  help='Request timeout in seconds.', type=float, default=2.)
  optparser.add_argument('-e', '--element',  help='CSS selectors of elements in requested pages to be returned in STDOUT in JSON format.', nargs='*', default=None)
  optparser.add_argument('-m', '--method',   help='GET/POST method.', default='GET')
  optparser.add_argument('-o', '--output',   help='Output format - benchmarking results & element content.', choices=['plain','json'], default='plain')
  optparser.add_argument('-v', '--verbose',  help='Verbosity', action='count', default=0)
  parameters = optparser.parse_args()
  P = Pitch(parameters)
  signal.signal(signal.SIGTERM, P.terminate)
  P.run()
