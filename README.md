pitch
=====

## Features
* used both as a command-line tool or a library
* accepts multiple URLs and/or a/multiple file(s) containing URLs
* performs HTTP benchmarks by leveraging gevent for making parallel requests and get metrics such as average request time & size, failed & successful request count

## Dependencies

### Required
* [BeautifulSoup4](http://www.crummy.com/software/BeautifulSoup/bs4/doc/)
* [gevent](http://www.gevent.org/)
* [requests](http://docs.python-requests.org/en/latest/)

### Optional
* [tabulate](https://pypi.python.org/pypi/tabulate)
* [simplejson](https://pypi.python.org/pypi/simplejson/)

## Usage

### Parameters

```
  -P, --profile         Store & display profiling data for the requests.
  -E [ELEMENTS [ELEMENTS ...]], --elements [ELEMENTS [ELEMENTS ...]]
                        CSS selectors of elements in requested pages to be
                        returned in STDOUT.
  -v, --verbose         Verbosity
  -A AUTH, --auth AUTH  Basic Authentication username:password (e.g. -A
                        'george:superpass')
  -T THREADS, --threads THREADS
                        Number of parallel threads.
  -U [URL [URL ...]], --url [URL [URL ...]]
                        URL to process. You can enter multiple values.
  -F [URL_FILE [URL_FILE ...]], --url-file [URL_FILE [URL_FILE ...]]
                        Files with URLs to process. You can enter multiple
                        values.
  -D DELAY, --delay DELAY
                        Delay between requests in msec.
  -X TIMEOUT, --timeout TIMEOUT
                        Request timeout in seconds.
  -B TIME, --time TIME  Duration of benchmark (in sec). Default is 60. Use
                        combined with -p/--profile.
  -O {plain,json}, --output {plain,json}
                        Output format - benchmarking results & element
                        content.
  -M {GET,POST}, --method {GET,POST}
                        GET/POST method.
```

### Examples

#### Fetch URL contents 

```
$ pitch -U example.com
```

> HTML will be processed by BeautifulSoup thus correcting/modifying the tree and output may differ from actual source. 
> Perhaps a `--raw` option should be added to display actual content in the future.

## Future To-Dos

* Configuration file support.
* POST payload in requests.
* Redis support - specify keys instead of URLs. Redis can also contain the POST payload, instead of using files.
* Session support
