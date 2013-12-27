#!/usr/bin/python
try:
  from gevent import monkey
  monkey.patch_socket()
  import gevent
  from gevent.pool import Pool
except ImportError:
  gevent = None
  Pool = None
import os
import sys
import re
import requests
from difflib import SequenceMatcher
from time import time, sleep
from functools import partial
from itertools import imap
import argparse
try:
  import redis
except ImportError:
  redis = None
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
  'raw'      : ( 'R', { 'help': 'Output raw URL contents. Does not pass contents through BeautifulSoup & disables -E/--elements feature. Default is off.', 'action': 'store_true', 'default': False}),
  'config'   : ( 'C', { 'help': 'Configuration file. Some advanced options cannot be passed through the command line, it would be highly impractical. Commonly supported command-line parameters will override those given in the configuration file. See https://github.com/georgepsarakis/pitch#configuration-files for details.', }),
}

''' Custom Exceptions '''
class PitchInvalidSetting(Exception): pass
class PitchConfigurationRequired(Exception): pass

class Pitch(object):
  TERMINATE             = False
  PROGRESS_INTERVAL     = 1.
  PROGRESS_LAST_PRINTED = None
  CLI                   = True
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
  def __init__(self, **kwargs):
    self.URLS = []
    self.STATS = {}
    self.ELEMENTS = {} 
    self.DATA = {}
    self.HEADERS = {}
    self.SOURCES = {}
    self.OUTPUT = {}
    self.DIFFER = {}   
    self.REDIS = None
    self.CLI = not re.match(r'^pitch', os.path.basename(sys.argv[0])) is None
    self.differ = SequenceMatcher(None, "", "", False)
    self.WS = partial(re.compile(r'\s+').sub, ' ')
    self.PARAMETERS = Pitch.parameterizer(self.CLI, **kwargs)
    self.configure()
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
  def parameterizer(cli=True, **kwargs):   
    if cli:
      argv = sys.argv[1:]
      ''' display help when empty '''
      if len(argv) == 0:
        argv.append('-h')
    else:      
      argv = []
      for k, v in kwargs.iteritems():
        if isinstance(v, list):
          v = ' '.join(v)
        argv.append('--%s=%s' % (k, v))
    optparser = argparse.ArgumentParser('pitch - URL Fetching & Benchmarking Tool')
    for switch, parameters in arguments.iteritems():
      optparser.add_argument('-%s' % parameters[0], '--%s' % switch, **parameters[1])
    parameters = optparser.parse_args(argv)
    return parameters

  def configure(self):
    self.PARAMETERS.method = self.PARAMETERS.method.lower()
    if not self.PARAMETERS.method in ['get','post']:
      self.PARAMETERS.method = 'get'
    if self.PARAMETERS.delay > 0.:
      self.PARAMETERS.delay /= 1000.
    if self.PARAMETERS.threads < 1:
      self.PARAMETERS.threads = 1
    if tabulate is None:
      self.PARAMETERS.output = "json"
    if not self.PARAMETERS.profile and self.PARAMETERS.elements is None:
      self.PARAMETERS.elements = ['html']
    ''' BeautifulSoup not installed '''
    if bs is None:
      ''' A warning should be printed '''
      self.PARAMETERS.elements = None
      self.PARAMETERS.raw = True
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
      self.analyze_config_file(self.PARAMETERS.config)
    if not self.URLS:
      raise PitchInvalidSetting('No URL supplied. Use --url or/and --url-file parameters.')
    self.URLS = map(self.url_normalizer, self.URLS)
    if self.PARAMETERS.config is None:
      for url in self.URLS:
        if not url in self.OUTPUT:
          self.OUTPUT[url] = ("stdout", True)
  
  def analyze_config_file(self, config_file):
    if not os.path.exists(config_file):
      raise PitchInvalidSetting('Configuration file "%s" not found.' % config_file)
    try:
      with open(config_file, 'r') as f:
        configuration = yaml.load("\n".join(f.readlines()))
    except yaml.parser.ParserError:
      raise PitchInvalidSetting('Not valid YAML file "%s".' % config_file)
    redis_settings = {}
    if 'redis' in configuration:
      redis_settings.update(configuration['redis'])
    try:
      self.REDIS = redis.StrictRedis(**redis_settings)
      self.REDIS.ping()
    except redis.exceptions.ConnectionError:
      self.REDIS = None 
    if 'headers' in configuration:
      self.HEADERS.update(configuration['headers'])
    if 'settings' in configuration:
      for setting, value in configuration['settings'].iteritems():
        if not hasattr(self.PARAMETERS, setting):
          raise PitchInvalidSetting('Unknown setting "%s"' % setting)
      for setting, value in dict(configuration['settings'].items() + vars(self.PARAMETERS).items()).iteritems():
        setattr(self.PARAMETERS, setting, value)
    if 'urls' in configuration:
      for config in configuration['urls']:
        self.URLS.append(config['url'])
        if 'test' in config:
          test = config['test']
          self.DIFFER[config['url']] = { 
            'threshold': Pitch.getdefault(test, 'diff', 99.9)/100.,
            'hash'     : Pitch.getdefault(test, 'hash'),
            'url'      : Pitch.getdefault(test, 'url'),
            'file'     : Pitch.getdefault(test, 'file'),
            'redis'    : Pitch.getdefault(test, 'redis'),
            'ignore'   : Pitch.ternary(not bs is None, Pitch.getdefault(test, 'ignore')),
            }
        data = {}
        if 'data' in config:
          data = config['data']
        if 'redis-data' in config:
          data = self.data_get('url', 'redis', key=config['redis-data'])
        if 'file-data' in config:
          data = self.data_get('url', 'file', path=config['file-data'])
        self.DATA[config['url']] = data
        if 'output' in config:
          self.OUTPUT[config['url']] = ("stdout", config['output'])
        if 'redis-output' in config:
          self.OUTPUT[config['url']] = ("redis" , config['redis-output'])
        if 'file-output' in config:
          self.OUTPUT[config['url']] = ("file"  , config['file-output'])
  
  def identity(self, item):
    return item

  def data_get(self, action, source='redis', **kwargs):
    data = None
    if source == 'redis':
      key = kwargs['key']
      if self.REDIS is None:
        raise PitchConfigurationRequired
      try:
        data = self.REDIS.get(key)
      except:
        data = None
      if data is None:
        raise PitchInvalidSetting('Redis key missing or error: "%s"' % key)
    elif source == 'file':
      path = kwargs['path']
      if not os.path.exists(path):
        raise PitchConfigurationRequired('File not found "%s"' % path)
      try:
        with open(path, 'r') as f:
          data = "".join(f.readlines())
      except:
        raise PitchInvalidSetting('Unable to read file "%s"' % path)
    if action == 'url':
      try:
        data = json.loads(data)
      except ValueError:
        message = 'JSON data could not be decoded for ' 
        if source == "redis":
          message += 'Redis key "%s"' % key
        elif source == "file":
          message += 'file "%s"' % path          
        raise PitchInvalidSetting(message) 
    return data

  def similarity(self, a, b, threshold=1.):
    self.differ.set_seqs(self.WS(a), self.WS(b))
    rqr = self.differ.real_quick_ratio()
    if rqr >= threshold:
      return True, rqr
    else:
      qr = self.differ.quick_ratio()
      if qr >= threshold:
        return True, qr
      r = self.differ.ratio()
      return r >= threshold, r

  def save_content(self, url):
    if url in self.OUTPUT and url in self.ELEMENTS:
      media, target = self.OUTPUT[url]
      self.output(self.ELEMENTS[url], target, media)

  def output(self, content, target, media='redis'):    
    try:
      content = json.dumps(content)
    except ValueError:
      pass
    if media == "redis":
      if self.REDIS is None:
        raise PitchConfigurationRequired
      return self.REDIS.set(target, content)
    elif media == "stdout":
      sys.stdout.write(content)
      sys.stdout.flush()
    elif media == "file":
      if not os.path.exists(os.path.dirname(target)):
        try:
          os.makedirs(os.path.dirname(target))
        except OSError:
          ''' print a warning ? '''
      with open(target, 'w') as f:
        f.write(content)
      return True
    return None
             
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
    if self.PARAMETERS.profile:
      self.profiler()    
   
  def formatter(self, metric, item):
    if isinstance(item, int):
      return "%d%s" % (item, self.METRICS[metric]['unit'])
    elif isinstance(item, float):
      return "%8.3f%s" % (item, self.METRICS[metric]['unit'])
   
  def result_table(self, stats, metrics):
    display = [ [ self.METRICS[metric]['label'], self.formatter(metric, stats[metric]) ] for metric in metrics ]
    return Pitch.ternary(self.PARAMETERS.output == "json", dict(display), display)

  def profiler(self):
    if self.PARAMETERS.output == "json":
      dumper = partial(json.dumps, indent=2, separators=(',', ':'))
    else: 
      dumper = self.identity
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
          output.append([['URL', url.encode('utf-8')]] + table)
        elif self.PARAMETERS.output == "json":
          output.append({ url: table })
      if self.PARAMETERS.output == "plain":
        output = tabulate(output, tablefmt="grid")
      print printer(output)
               
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
  
  def fetch_element(self, request):  
    url, r, _ = request
    html = r.content
    elements = {}
    if self.PARAMETERS.raw:
      return url, {"html" : html}
    if not self.PARAMETERS.elements is None:
      tree = bs(html, "lxml")
      for selector in self.PARAMETERS.elements:        
        elements[selector] = map(unicode, tree.select(selector))
    return url, elements
   
  def incr(self, obj, key, value=1):
    try:
      obj[key] += value
    except KeyError:
      obj[key] = value
    return obj[key]
  
  def progress(self, counter):
    if self.PROGRESS_LAST_PRINTED is None:
      self.PROGRESS_LAST_PRINTED = time()
    if self.PARAMETERS.verbose >= 1 and self.PARAMETERS.time > 0:
      if time() - self.PROGRESS_LAST_PRINTED >= self.PROGRESS_INTERVAL:
        self.PROGRESS_LAST_PRINTED = time()
        message = ">> %d REQUESTS (%d%%)" % (counter * self.PARAMETERS.threads, int(100*(time()-self.LOOP_START)/self.PARAMETERS.time))
        sys.stdout.write(message)
        sys.stdout.flush()
        sys.stdout.write('\b' * len(message))
    counter += 1
    return counter
  
  def stats(self, results):
    for url, request, request_time in results:
      try:
        self.STATS[url]
      except KeyError:
        self.STATS[url] = {'min': 10**3, 'max': 0,}
      stats = self.STATS[url]
      stats['min'] = min(stats['min'], request_time)
      stats['max'] = max(stats['max'], request_time)
      try:
        self.incr(stats, 'size', int(request.headers['content-length']))
      except KeyError:
        pass
      self.incr(stats, 'time', request_time)
      self.incr(stats, 'total')                            
      status = Pitch.ternary(not request is None and request.status_code < 400, 'ok', 'error')
      self.incr(stats, status)
  
  @staticmethod
  def ternary(test, if_true, if_false=None):
    if test:
      return if_true
    else:
      return if_false
   
  @staticmethod
  def getdefault(obj, key, default=None):
    try:
      return obj[key]
    except KeyError:    
      return default
    except IndexError:
      return default

  def retriever(self, urls, timeout, multithreaded):
    results = []
    if multithreaded:
      timeout = duration - time() + self.LOOP_START
      if timeout < self.PARAMETERS.timeout:
        timeout = self.PARAMETERS.timeout
      with gevent.Timeout(timeout, False):
        results = self.THREAD_POOL.imap(self.fetcher, urls)
    else:
      results = filter(None, map(self.fetcher, self.URLS))
    return results
   
  def looper(self):
    counter = 0
    self.LOOP_START = time()
    profile = self.PARAMETERS.profile
    multithreaded = self.PARAMETERS.threads > 1 and not Pool is None
    if multithreaded:
      self.THREAD_POOL = Pool(self.PARAMETERS.threads)
    duration = Pitch.ternary(profile, self.PARAMETERS.time, 0)
    urls = self.URLS
    while not self.TERMINATE:
      counter = self.progress(counter)
      if profile:
        urls = (random.choice(self.URLS) for n in xrange(len(self.URLS)))
      timeout = duration - time() + self.LOOP_START
      results = self.retriever(urls, Pitch.ternary(timeout > self.PARAMETERS.timeout, self.PARAMETERS.timeout, timeout), multithreaded)
      if not self.PARAMETERS.elements is None:
        self.ELEMENTS.update(dict(map(self.fetch_element, results)))
      if profile:
        self.stats(results)
      if not profile or time() - start >= duration: 
        break
    map(self.save_content, self.ELEMENTS.keys())
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
  P = Pitch()
  signal.signal(signal.SIGTERM, P.terminate)
  P.run()  

if __name__ == "__main__":
  main()
