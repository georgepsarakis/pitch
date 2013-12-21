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
*

### Optional
* [tabulate](https://pypi.python.org/pypi/tabulate)
* [simplejson](https://pypi.python.org/pypi/simplejson/)

## Future To-Dos

* Configuration file support.
* POST payload in requests.
* Redis support - specify keys instead of URLs. Redis can also contain the POST payload, instead of using files.
* Session support
