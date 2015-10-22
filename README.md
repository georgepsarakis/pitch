# pitch

HTTP handling is very common in daily development and operations tasks alike. 
Writing small scripts using the Python library [requests](http://docs.python-requests.org/en/latest/) 
is already very easy, however a more structured and formalised way of composing a sequence of HTTP operations
would increase reusability, brevity, expandability and clarity.

## Concepts

### Scheme Files

Instructions files containing a list of `steps` which will dynamically generate
a series of HTTP requests.

### Step

A `step` will be translated dynamically to one or more HTTP requests. 

The step definition also may include:

- Conditional
- Request parameters
- List of Request/Response Plugins and their parameters

### Phases

Each step execution is divided in two phases: `request` and `response` phase.

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

| Parameter | Required | Definition | Type | Default | Description |
| --------- | -------- | ---------- | ---- | ------- | ----------- |
| processes | No | <ul><li>scheme</li></ul> | int | 1 | The total number of processes to spawn. Each process will spawn separate threads and each thread will execute all the scheme steps in a separate context and session. |
| threads | No | <ul><li>scheme</li></ul> | int | 1 | Total number of threads for simultaneous scheme executions. |
| repeat | No | <ul><li>scheme</li></ul> | int | 1 | Each thread will repeat the scheme execution this many times. |
| failfast | No | <ul><li>scheme</li><li>step</li></ul> | bool | False | This parameter instructs the `assert_http_status_code` plugin to stop execution if an unexpected HTTP status code is returned. |
| base_url | Yes | <ul><li>scheme</li><li>step</li></ul> | unicode || The base URL which will be used to compose the absolute URL for each HTTP request. If HTTP scheme is omitted, **http** is assumed.|
| plugins | No | <ul><li>scheme</li><li>step</li></ul> | list | <ul><li>response_as_json</li><li>assert_status_http_code</li></ul> | A list of  plugins that will be executed at each step. If defined on `scheme` level, this list will be prepended to the `step` level defined plugin list, if one exists. |
| requests | No | <ul><li>scheme</li></ul> | dict || Parameters to be passed directly to `requests.Request` objects at each HTTP request.|
| variables | No | <ul><li>scheme</li></ul> | dict || Variables that will be added to the context.|

### Rules

- Parameters defined on `step` level will override the same parameter given
  on `scheme` level.
- [Jinja2 template braces](http://jinja.pocoo.org/docs/dev/templates/#variables)
can be omitted in `when` command expressions, as they
will be automatically resolved from the current context.
- Loop expression values must be iterables.
- Plugins are given in a list, because some plugins may depend on others, so the execution sequence is important. Also, a plugin may be requested multiple times.
- The plugin list must contain both request & response plugins. This was introduced for simplicity and less boilerplate syntax. At each phase, the appropriate subset of plugins will be selected and executed.


### Examples

#### GitHub Public API

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
    - response_as_json
    - assert_status_http_code
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
		# The following will always evaluate to true.
        when: >
          {{ 2 > 1 }}
        # Any non-reserved keywords will be passed directly to
		# `requests.Request` objects as parameters.
        # Here we specify GET parameters with `params`.
        params:
            per_page: 3
        plugins:
            - plugin: assert_http_status_code
            - plugin: request_delay
              seconds: 1.0
            - plugin: post_register
              user_list: response.as_json
    # Fetch the list of repositories for each user
	# if the user id is in the range [2,4]
	-
        url: >
            /users/{{ item.login }}/repos
        with_items: user_list
        when: item.id >= 2 and item.id <=4
        plugins:
            - plugin: request_delay
              seconds: 2.0
```
