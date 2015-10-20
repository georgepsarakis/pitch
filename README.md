# pitch

HTTP handling is very common in daily development and operations tasks alike. 
Writing small scripts using the Python library [requests](http://docs.python-requests.org/en/latest/) 
is already very easy, however a more structured and formalised way of composing a sequence of HTTP operations
would increase reusability, brevity, expandability and clarity.

## Main Features

### Control Flow

`pitch` borrows certain concepts of Ansible's 
[Loops](http://docs.ansible.com/ansible/playbooks_loops.html) & 
[Conditionals](http://docs.ansible.com/ansible/playbooks_conditionals.html) for more advanced logic & processing.

### Templating

`pitch` reads instructions from `scheme` files. `Jinja2` template expressions can be widely used 
to allow dynamic context during execution.

### Plugins

`pitch` allows injection of additional functionality or pre/post-processing operations on `Request`/`Response` objects
with the use of plugins. Apart from the core plugins, custom plugins can be written and loaded separately.



