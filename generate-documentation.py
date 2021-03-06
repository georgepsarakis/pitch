#!/usr/bin/env python
import re
from subprocess import check_output

from jinja2 import Template


with open('docs/README.md.tmpl') as f:
    readme_template = Template(f.read())

with open('docs/github_api_example.yml.tmpl') as f:
    github_api_example = f.read()

replace_whitespace = re.compile('\s+')

sequence_file_reference = [
    [
        'processes', ['sequence'], 'int', '1',
        """The total number of processes to spawn.
           Each process will initialize separate threads.""",
    ],
    [
        'threads',  ['sequence'], 'int', '1',
        """Total number of threads for simultaneous sequence executions.
        Each thread will execute all sequence steps in a
        separate context and session."""
    ],
    [
        'repeat',  ['sequence'], 'int', '1',
        """sequence execution repetition count for each thread."""
    ],
    [
        'failfast', ['sequence', 'step'], 'bool', 'false',
        """Instructs the `assert_http_status_code` plugin to stop execution
        if an unexpected HTTP status code is returned."""
    ],
    [
        'base_url', ['sequence', 'step'], 'string', '',
        """The base URL which will be used to compose the
        absolute URL for each HTTP request."""
    ],
    [
        'plugins' , ['sequence', 'step'], 'list',
        "['response_as_json', 'assert_status_http_code']",
        """The list of plugins that will be executed at each step.
        If defined on sequence-level, this list will be prepended
        to the step-level defined plugin list, if one exists."""
    ],
    [
        'use_default_plugins', ['sequence', 'step'], 'bool', 'true',
        """Whether to add the list of default plugins (see `plugins`)
        to the defined list of plugins for a step. If no plugins have been
        defined for a step and this parameter is set to `true`, only
        the default plugins will be executed."""
    ],
    [
        'use_sequence_plugins', ['sequence', 'step'], 'bool', 'true',
        """Whether to add the list of sequence-level plugin definitions to
        this step."""
    ],
    [
        'requests', ['sequence'], 'dict', '{}',
        """Parameters to be passed directly to `requests.Request`
        objects at each HTTP request."""
    ],
    [
        'variables', ['sequence', 'step'], 'dict', '{}',
        """Mapping of predefined variables
        that will be added to the context for each request."""
    ],
    [
        'steps', ['sequence'], 'list', '', "List of sequence steps."
    ],
    [
        'when', ['step'], 'string', 'true',
        """Conditional expression determining whether to run this step or not.
        If combined with a loop statement,
        will be evaluated in every loop cycle."""
    ],
    [
        'with_items', ['step'], 'iterable', '[None]',
        """Execute the step instructions by iterating over the
        given collection items. Each item will be available
        in the Jinja2 context as `item`."""
    ],
    [
        'with_indexed_items', ['step'], 'iterable', '[None]',
        """Same as `with_items`, but the `item` context variable
        is a tuple with the zero-based index in the
        iterable as the first element and the actual item
        as the second element."""
    ],
    [
        'with_nested', ['step'], 'list of iterables', '[None]',
        """Same as `with_items` but has a list of iterables as input
        and creates a nested loop. The context variable `item` will
        be a tuple containing the current item of the first iterable at
        index 0, the current item of the second iterable at
        index 1 and so on."""
    ]
]

list_item_wrap = '<li>{}</li>'.format
list_wrap = '<ul>{}</ul>'.format
code_wrap = '`{}`'.format
for parameter_details in sequence_file_reference:
    for index, detail in enumerate(parameter_details):
        if index in [0, 2, 3]:
            if detail != '':
                parameter_details[index] = code_wrap(detail)
        elif index == 1:
            parameter_details[index] = ', '.join(detail)
        elif index == 4:
            parameter_details[index] = replace_whitespace.sub(' ', detail)

sequence_file_reference_desc = [
    [detail[0], detail[1], detail[2], detail[4]]
    for detail in sequence_file_reference
]

sequence_file_reference_defaults = [
    [detail[0], detail[3]]
    for detail in sequence_file_reference
]


plugins_list = check_output(
    ['pitch', 'plugins', 'list'],
    universal_newlines=True
)

with open('README.md', 'w') as f:
    f.write(
        readme_template.render(
            plugins_list=plugins_list,
            github_api_example=github_api_example,
            sequence_file_reference_desc=sequence_file_reference_desc,
            sequence_file_reference_defaults=sequence_file_reference_defaults
        )
    )
