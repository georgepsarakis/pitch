# pitch

[![Build Status](https://travis-ci.org/georgepsarakis/pitch.svg?branch=master)](https://travis-ci.org/georgepsarakis/pitch)

HTTP handling is very common in daily development and operations tasks alike. 
Writing small scripts using the Python library [requests](http://docs.python-requests.org/en/latest/) 
is already very easy, however a more structured and formalised way of composing a sequence of HTTP operations
would increase reusability, brevity, expandability and clarity.

## Installation

```bash
$ git clone https://github.com/georgepsarakis/pitch.git
$ pip install .
```

> `pitch` can be used from the command-line as well as a library.

## Examples

### GitHub Public API

The following scheme file will:

- Fetch the details of the first 10 users
- Fetch the repositories for users with id in the range [2,4]

```yaml
# Single process
processes: 1
# Single-threaded
threads: 1
# Execute only once per thread
repeat: 1
# Stop execution immediately if an
# unexpected HTTP status code is returned.
# By default error codes are defined
# as greater-equal to 400.
failfast: yes
base_url: https://api.github.com
plugins:
    - plugin: request_delay
      seconds: 1.0
requests:
    headers:
        User-Agent: pitch-json-api-client-test
variables: {}
steps:
    -
		# The relative URL
        url: /users
		# HTTP method (always GET by default)
        method: get
		# Conditionals are specified using the `when` keyword.
		# Any valid Jinja expression is allowed.
        # The following example evaluates to true.
        when: >
          {{ 2 > 1 }}
        # Any non-reserved keywords will be passed directly to
		# `requests.Request` objects as parameters.
        # Here we specify GET parameters with `params`.
        params:
            per_page: 10
        # The list of request/response plugins
        # that should be executed.
        # If not specified the scheme-level default plugins
        # list will be used.
        plugins:
            - plugin: post_register
              user_list: response.as_json
    # Fetch the list of repositories for each user
	# if the user id is in the range [2,4]
	-
        url: >
            /users/{{ item.login }}/repos
        # This iterable has been added to the context 
        # by the post_register plugin in the previous step.
        with_items: user_list
        # Conditionals are dynamically evaluated at each loop cycle.
        when: item.id >= 2 and item.id <=4

```

## Concepts

### Scheme Files

Instructions files containing a list of `steps` which will dynamically generate
a series of HTTP requests.

### Step

A `step` will be translated dynamically to one or more HTTP requests. 

The step definition also may include:

- Conditional
- Loops
- Request parameters
- List of Request/Response Plugins and their parameters

### Phases

A single step may generate multiple HTTP requests.
Each sub-step execution is divided in two phases: `request` and `response` phase.

## Main Features

### Session

Each scheme execution runs using the same
[requests.Session](http://docs.python-requests.org/en/latest/user/advanced/#session-objects).
This means that each request is not necessarily isolated but can be part of
a common browser HTTP flow.

### Control Flow

To avoid reinventing the wheel, `pitch` borrows certain concepts from
Ansible's
[Loops](http://docs.ansible.com/ansible/playbooks_loops.html) & 
[Conditionals](http://docs.ansible.com/ansible/playbooks_conditionals.html)
in order to enable more advanced logic & processing, while maintaining
simplicity.

### Templating

As already discussed in [Concepts](#concepts), `pitch` reads instructions from
`scheme` files. `Jinja2` template expressions can be widely used to allow
dynamic context during execution.

### Plugins

Additional functionality or pre/post-processing operations on
`Request`/`Response` objects with the use of plugins. Apart from the core
plugins, custom plugins can be written and loaded separately. See the
[Plugin Development Reference]
(#developing-plugins).

## Scheme File Reference

| Parameter | Definition | Type | Description |
| --------- |----------- | ---- | ----------- |
|`processes`|<ul><li>scheme</li></ul>|int|The total number of processes to spawn. Each process will initialize separate threads.|
|`threads`|<ul><li>scheme</li></ul>|int|Total number of threads for simultaneous scheme executions. Each thread will execute all scheme steps in a separate context and session.|
|`repeat`|<ul><li>scheme</li></ul>|int|Scheme execution repetition count for each thread.|
|`failfast`|<ul><li>scheme</li><li>step</li></ul>|bool|Instructs the `assert_http_status_code` plugin to stop execution if an unexpected HTTP status code is returned.|
|`base_url`|<ul><li>scheme</li><li>step</li></ul>|string|The base URL which will be used to compose the absolute URL for each HTTP request.|
|`plugins`|<ul><li>scheme</li><li>step</li></ul>|list|The list of plugins that will be executed at each step. If defined on scheme-level, this list will be prepended to the step-level defined plugin list, if one exists.|
|`use_default_plugins`|<ul><li>scheme</li><li>step</li></ul>|bool|Whether to add the list of default plugins (see `plugins`) to the defined list of plugins for a step. If no plugins have been defined for a step and this parameter is set to `true`, only the default plugins will be executed.|
|`use_scheme_plugins`|<ul><li>scheme</li><li>step</li></ul>|bool|Whether to add the list of scheme-level plugin definitions to this step.|
|`requests`|<ul><li>scheme</li></ul>|dict|Parameters to be passed directly to `requests.Request` objects at each HTTP request.|
|`variables`|<ul><li>scheme</li><li>step</li></ul>|dict|Mapping of predefined variables that will be added to the context for each request.|
|`steps`|<ul><li>scheme</li></ul>|list|List of scheme steps.|
|`when`|<ul><li>step</li></ul>|string|Conditional expression determining whether to run this step or not. If combined with a loop statement, will be evaluated in every loop cycle.|
|`with_items`|<ul><li>step</li></ul>|iterable|Execute the step instructions by iterating over the given collection items. Each item will be available in the Jinja2 context as `item`.|
|`with_indexed_items`|<ul><li>step</li></ul>|iterable|Same as `with_items`, but the `item` context variable is a tuple with the zero-based index in the iterable as the first element and the actual item as the second element.|
|`with_nested`|<ul><li>step</li></ul>|list of iterables|Same as `with_items` but has a list of iterables as input and creates a nested loop. The context variable `item` will be a tuple containing the current item of the first iterable at index 0, the current item of the second iterable at index 1 and so on.|


> On step-level definitions, any non-reserved keywords will be passed directly to `requests.Request` e.g. `params`.

| Parameter | Default<sup>*</sup> |
| --------- | ------------------- |
|`processes`|`1`|
|`threads`|`1`|
|`repeat`|`1`|
|`failfast`|`false`|
|`base_url`||
|`plugins`|`['response_as_json', 'assert_status_http_code']`|
|`use_default_plugins`|`true`|
|`use_scheme_plugins`|`true`|
|`requests`|`{}`|
|`variables`|`{}`|
|`steps`||
|`when`|`true`|
|`with_items`|`[None]`|
|`with_indexed_items`|`[None]`|
|`with_nested`|`[None]`|



<strong><sup>*</sup></strong> If no default value is specified, then the parameter is required.

### Available Context Variables

### Rules

- Parameters defined on `step` level will override the same parameter given
  on `scheme` level.
- [Jinja2 template braces](http://jinja.pocoo.org/docs/dev/templates/#variables)
can be omitted in `when` command expressions, as they
will be automatically resolved from the current context.
- Loop expression values must be iterables.
- Plugins are given in a list, because some plugins may depend on others, so the execution sequence is important. Also, a plugin may be requested multiple times.
- The plugin list must contain both request & response plugins. This was introduced for simplicity and less boilerplate syntax. At each phase, the appropriate subset of plugins will be selected and executed.

## Using Plugins

Plugins are divided in two major categories:

- Request Plugins
- Response Plugins

The plugin list is specified at step-level. Each entry is a dictionary specifying the plugin name, while the remaining
key-value pairs will be used for the plugin initialization.

### Example

A simple plugin case is the `request_delay` plugin; it adds a delay before sending the HTTP request.

The implementation of this plugin is the following:

```python
# Module: pitch.plugins.common
class DelayPlugin(BasePlugin):
    # Notice the constructor argument
    def __init__(self, seconds):
        self._delay_seconds = float(seconds)

    def execute(self, plugin_context):
        time.sleep(self._delay_seconds)

# Module: pitch.plugins.request
class RequestDelayPlugin(DelayPlugin, BaseRequestPlugin):
    _name = 'request_delay'
```

The scheme file instructions for calling the plugin are:

```yaml
steps:
  - url: /example
    plugins:
      - plugin: request_delay
        seconds: 1.0
```

## Developing Plugins

New custom plugins can be developed by creating additional modules with subclasses of:

- `pitch.plugins.request.BaseRequestPlugin`
- `pitch.plugins.request.BaseResponsePlugin`

### Example

```python
from pitch.plugins.request import BaseRequestPlugin
from pitch.lib.common.utils import get_exported_plugins

class TestRequestPlugin(BaseRequestPlugin):
    _name = 'request_test'
    def __init__(self, message):
      self._message = message

    def execute(self, plugin_context):
        plugin_context.progress.info(
          'Plugin {} says: {}'.format(self.name, self._message)
        )

exported_plugins = get_exported_plugins(BaseRequestPlugin)
```

Calling the above plugin from the step definition:

```yaml
steps:
  - url: /example
    plugins:
      - plugin: request_test
        message: 'hello world'
        # The above will display during the
        # execution in the progress logs:
        # 'Plugin request_test says: hello world'
```

Available plugins and their parameters can be listed
from the command-line by using the switch `--list-plugins`:

```bash
$ pitch --list-plugins
# Or if additional plugin modules must be loaded:
$ pitch --list-plugins --request-plugins-modules MODULE_NAME
```

### Core Plugins

```

Request
-------

- add_header(header, value)
  * Add a request header

- file_input(filename)
  * Read file from the local filesystem and store in the `result` property

- json_post_data()
  * JSON-serialize the request data property (POST body)

- pre_register(**updates)
  * Add variables to the request template context

- profiler()
  * Keep track of the time required for the HTTP request & processing

- request_delay(seconds)
  * Pause execution for the specified delay interval.

- request_logger(logger_name=None, message=None, **kwargs)
  * Setup a logger, attach a file handler and log a message.

Response
--------

- assert_http_status_code(expect=200)
  * Examine the response HTTP status code and raise error/stop execution

- json_file_output(filename, create_dirs=True)
  * Write a JSON-serializable response to a file

- post_register(**updates)
  * Add variables to the template context after the response has completed

- profiler()
  * Keep track of the time required for the HTTP request & processing

- response_as_json()
  * Serialize the response body as JSON and store in response.as_json

- response_logger(logger_name=None, message=None, **kwargs)
  * Setup a logger, attach a file handler and log a message.

- stdout_writer()
  * Print a JSON-serializable response to STDOUT

```

