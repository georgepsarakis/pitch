from __future__ import unicode_literals
from copy import copy
from functools import partial
from collections import deque
from .control_flow import Loop, Conditional


class CommandClient(object):
    def __init__(self, invoker):
        self._invoker = invoker
        self._command_stack = StepCommandStack()

    def get_last(self):
        return self._command_stack.stack[-1]

    def receive(self, command):
        self._command_stack.append(command)

    def invoke(self):
        results = []
        command = self._command_stack.pop()
        while command is not None:
            if isinstance(command, ControlFlowCommand):
                if isinstance(command.control_flow_structure, Conditional):
                    if not command.control_flow_structure.evaluate():
                        command = self._command_stack.pop()
                        continue
                    else:
                        for sub_command in command.sub_commands:
                            self._command_stack.prepend(sub_command)
                elif isinstance(command.control_flow_structure, Loop):
                    loop = command.control_flow_structure
                    loop.evaluate()
                    for item in loop.items:
                        for sub_command in command.sub_commands:
                            self._command_stack.prepend(sub_command)
                            set_item_command = StepCommand()
                            set_item_command.add_instruction(
                                loop.set_loop_variable, item
                            )
                            self._command_stack.prepend(set_item_command)
            else:
                results.extend(self._invoker(command))
            command = self._command_stack.pop()


class CommandInvoker(object):
    def __call__(self, command):
        results = []
        for instruction in command.instructions:
            results.append(instruction())
        return results


class CommandInstruction(object):
    def __init__(self, fn, *args, **kwargs):
        self._fn = fn
        self._args = args
        self._kwargs = kwargs
        self._composed_fn = partial(fn, *args, **kwargs)

    def __call__(self):
        return self._composed_fn()


class StepCommand(object):
    def __init__(self):
        self._instructions = []

    @property
    def instructions(self):
        return copy(self._instructions)

    def add_instruction(self, fn, *args, **kwargs):
        self._instructions.append(CommandInstruction(fn, *args, **kwargs))


class ControlFlowCommand(object):
    def __init__(self, flow_control_structure):
        self._flow_control_structure = flow_control_structure
        self._sub_commands = []

    @property
    def control_flow_structure(self):
        return self._flow_control_structure

    @property
    def sub_commands(self):
        return self._sub_commands

    def add_sub_command(self, step_command):
        self._sub_commands.append(step_command)


class StepCommandStack(object):
    def __init__(self, *args):
        self._stack = deque(args)

    def __len__(self):
        return len(self._stack)

    @property
    def stack(self):
        return self._stack

    def append(self, command):
        self._stack.append(command)

    def prepend(self, command):
        self._stack.appendleft(command)

    def pop(self):
        try:
            return self._stack.popleft()
        except IndexError:
            return
