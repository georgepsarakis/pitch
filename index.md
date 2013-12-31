---
layout: default
title: pitch - URL fetching, comparison & benchmarking
---

## What is this?

`pitch` is a Python command-line tool & library that combines retrieving & comparing HTML content from pages and benchmarking.

## Features
* used both as a command-line tool or a library
* JSON output
* easily configurable with YAML
* receives POST/GET parameters from a JSON object stored either in a Redis key or a file or simply given in the configuration file in YAML format
* outputs retrieved HTML to a file or store in a Redis key
* compares retrieved HTML to stored content and provides a similarity ratio
* accepts multiple URLs and/or a/multiple file(s) containing URLs
* multithreading support with gevent for parallelizing requests thus introducing concurrency for benchmarks and faster HTML retrieval
* HTTP benchmarks with metrics such as average request time & size, failed/successful request count

You can see some configuration file samples for [benchmarking](https://github.com/georgepsarakis/pitch/blob/master/sample.benchmark.yml), [fetching](https://github.com/georgepsarakis/pitch/blob/master/sample.fetch.yml) & [content comparison](https://github.com/georgepsarakis/pitch/blob/master/sample.diff.yml).

## Dependencies

### Required
* [BeautifulSoup4](http://www.crummy.com/software/BeautifulSoup/bs4/doc/)
* [gevent](http://www.gevent.org/)
* [requests](http://docs.python-requests.org/en/latest/)
* [argparse](http://docs.python.org/2.7/library/argparse.html)
* [PyYAML](https://pypi.python.org/pypi/PyYAML)

### Optional
* [tabulate](https://pypi.python.org/pypi/tabulate)
* [simplejson](https://pypi.python.org/pypi/simplejson/)

## Usage

### Parameters

    -v, --verbose         Verbosity
    -P, --profile         Store & display profiling data for the requests.
    -E [ELEMENTS [ELEMENTS ...]], --elements [ELEMENTS [ELEMENTS ...]]
                          CSS selectors of elements in requested pages to be returned in output.
    -A AUTH, --auth AUTH  Basic Authentication username:password (e.g. -A 'george:superpass')
    -R, --raw             Output raw URL contents. Does not pass request content through BeautifulSoup
                          & disables -E/--elements feature. Default is off.
    -T THREADS, --threads THREADS
                          Number of parallel threads.
    -U [URL [URL ...]], --url [URL [URL ...]]
                          URL to process. You can enter multiple values.
    -F [URL_FILE [URL_FILE ...]], --url-file [URL_FILE [URL_FILE ...]]
                          Files with URLs to process. You can enter multiple values.
    -D DELAY, --delay DELAY
                          Delay between requests in msec.
    -X TIMEOUT, --timeout TIMEOUT
                          Request timeout in seconds.
    -B TIME, --time TIME  Duration of benchmark (in sec). Default is 60. 
                          Use combined with -p/--profile.
    -O {plain,json}, --output {plain,json}
                          Output format - benchmarking results & element content.
    -C CONFIG, --config CONFIG
                          Configuration file path. 
                          Some advanced options cannot be passed through the command line, 
                          it would be highly impractical. 
                          Commonly supported command-line parameters will override those given in the configuration file.  
                          See https://github.com/georgepsarakis/pitch#configuration-files for details.
    -M {GET,POST}, --method {GET,POST}
                          GET/POST method.

### Examples

#### Fetch a single page

    $ pitch -U example.com

> HTML will be processed by BeautifulSoup thus correcting/modifying the tree and output may differ from actual source. 

#### Fetch elements from multiple pages

    $ pitch -U example1.com example2.com/home example3.com --elements h1 h2 --output=json

The command will output a JSON object:

    {
      "http://example1.com" : {
        "h1" : ["Header for example1.com"],
        "h2" : ["Subheader #1", "Subheader #2"]
      },
      "http://example2.com/home" : {
        "h1" : ["example2 Header"],
        "h2" : ["example2 Home Page Subheader #1"]
      },
      "http://example3.com" : {
        "h1" : [ "Header #1"]
      }
    }

> Using `--threads` will parallelize the requests so that you may get faster results.

> You can also add `--delay=500` for a 500msec delay between successive requests in case you want to avoid overloading a host or being rate limited.

#### Benchmark

    $ pitch -U example.com dev.example.com --timeout=3.5 --time=30. --threads=20 --profile

On each run 20 requests will be made, divided randomly to the 2 given URLs.

Thus, concurrency is approximately 10. A single URL would result in 20 concurrent requests.

Parallel requests are performed with [gevent.pool](http://www.gevent.org/gevent.pool.html).

> Benchmark time is approximate and could be off by `timeout` seconds.

#### Configuration files

    $ pitch -C config.yml


Configuration files are composed with the following 1st level keys:

1. `headers`

    Dictionary of valid HTTP header field names and their corresponding values.
2. `settings`

    Dictionary of the command line parameters. If the same parameter is passed from the command-line it overrides the configuration file settings. 
3. `urls`

    A list of dictionaries where the `url` key is required and optionally the `data` key contains a dictionary with the POST/GET payload. Parameters values should not be URL-encoded.
  
    `--url` and `--url-file` parameter contents are added to those in the configuration file and not overridden.

## Future To-Dos

* Session support
* More profiler metrics
* Content diff/comparison feature enhancement
