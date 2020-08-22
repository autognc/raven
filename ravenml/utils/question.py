"""
Author(s):      Gavin Martin, Carson Schubert (carson.schubert14@gmail.com)
Data Created:   03/18/2019

Wrapper functions for prompting user input via questionary. Stolen from jigsaw.
"""

import sys
from halo import Halo
from questionary import prompt
from typing import Union

def in_test_mode() -> bool:
    """ Determines if we are running in an automated test or not. 
    This attribute is set via conftest.py in the ravenml/tests directory
    
    Returns:
        bool: true if in test mode, false otherwise
    """
    return hasattr(sys, "_called_from_test")

class Spinner:
    """Wrapper class to prevent bugs with Halo in pytest (see Issue #97)
    """

    def __init__(self, text, text_color):
        self.text = text
        if in_test_mode():
            return
        self._spinner = Halo(text=text, text_color=text_color)

    def start(self):
        if in_test_mode():
            return
        self._spinner.start()

    def succeed(self, text):
        if in_test_mode():
            return
        self._spinner.succeed(text=text)

def user_input(message: str, default="", validator=None) -> str:
    """Prompts the user for input
    
    Args:
        message (str): the message to give to the user before they provide
            input
        default (str, optional): Defaults to "". The default input response
        validator (Validator, optional): Defaults to None. A PyInquirer
            validator used to validate input before proceeding
    
    Returns:
        str: the user's response
    """
    if validator is not None:
        question = [
            {
                "type": "input",
                "name": 'value',
                "message": message,
                "default": default,
                "validate": validator,
            },
        ]
    else:
        question = [
            {
                "type": "input",
                "name": 'value',
                "message": message,
                "default": default
            },
        ]
    answer = prompt(question)
    return answer["value"]

def user_selects(message: str, choices: list, selection_type="list", sort_choices=True) -> Union[str, list]:
    """Prompts the user to select a choice(s) given a message
    
    Args:
        message (str): the message to give to the user before they choose
        choices (list): a list of the options to provide
        selection_type (str, optional): Defaults to "list". Should be "list"
            or "checkbox" for radio-button-style or checkbox-style selections
        sort_choices (bool, optional): Defaults to True. Whether to
            alphabetically sort the choices in the list provided to the user
    
    Returns:
        str or list: the str for the choice selected if "list" is the 
                        selection_type
                     the list of the choices selected if "checkbox" is the 
                        selection_type
    """
    question = [
        {
            "type": selection_type,
            "name": 'value',
            "message": message,
            "choices": sorted(choices) if sort_choices else choices
        },
    ]
    answer = prompt(question)
    return answer['value']
    
def user_confirms(message: str, default=False) -> bool:
    """Prompts the user to confirm an action by typing y/n
    
    Args:
        message (str): the message to give to the user before they choose
        default (bool, optional): Defaults to False.
    
    Returns:
        bool: the user's response in bool format
    """
    question = [
        {
            "type": "confirm",
            "name": "value",
            "message": message,
            "default": default
        },
    ]
    answer = prompt(question)
    return answer["value"]
    
def cli_spinner(text, func, *args, **kwargs):
    """ Halo spinner wrapper.

    Args:
        text (str): text to display while spinner is running
        func (function): function to execute while spinner runs
        *args (tuple, optional): ordered arguments required by func
        
    Raises:
        Automatically re-raises any exception raised by calling func after
        succeeding the spinner with a "Failed" tail
    """
    spinner = Spinner(text=text, text_color="magenta")
    spinner.start()
    try:
        result = func(*args,**kwargs)
    except Exception:
        spinner.succeed(text=text + 'Failed.')
        raise
    spinner.succeed(text=text + 'Complete.')
    return result

def cli_spinner_wrapper(text):
    def spinner(func):
        def wrapper(*args, **kwargs):
            return cli_spinner(text, func, *args, **kwargs)
        wrapper.inherit_decorator = cli_spinner_wrapper
        wrapper.args = text
        return wrapper
    return spinner

class DecoratorSuperClass:
    """Superclass for DatasetWriter. Allows for decorators
        from one class to be inherited to all subclasses. Subclasses can 
        override their decorators if desired.

        Any decorator that is to be used on subclasses of this class must
        set the attribute 'inherit_decorator' to the decorator function itself
        in the inner function that it is passing. 

        This class supports decorators with parameters, but requires that they
        be set as attributes of the passed function as 'args' and 'kwargs'.
    """
    def __init_subclass__(cls):
        decorator_registry = getattr(cls, "_decorator_registry", {}).copy()
        cls._decorator_registry = decorator_registry
        # annotate newly decorated methods in the current subclass:
        for name, obj in cls.__dict__.items():
            if getattr(obj, "inherit_decorator", False) and not name in decorator_registry:
                decorator_registry[name] = (obj.inherit_decorator, getattr(obj, "args", False), getattr(obj, "kwargs", False))
        # decorate methods annotated in the registry
        # decorator[0] = decorator function
        # decorator[1] = decorator args
        # decorator[2] = decorator kwargs
        for name, decorator in decorator_registry.items():
            if name in cls.__dict__ and getattr(getattr(cls,name), "inherit_decorator", None) != decorator[0]:
                if decorator[1] or decorator[2]:
                    if decorator[2]:
                        setattr(cls, name, decorator[0](decorator[1], decorator[2])(cls.__dict__[name]))
                    else:
                        setattr(cls, name, decorator[0](decorator[1])(cls.__dict__[name]))
                elif not decorator[1]:
                    setattr(cls, name, decorator[0](decorator[2])(cls.__dict__[name]))
                else:
                    setattr(cls, name, decorator[0](cls.__dict__[name]))
    
