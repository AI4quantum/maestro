# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 IBM

"""Common utility functions and classes for the CLI."""

import sys
import yaml
from random import randint

VERBOSE = False

class Colors:
    """Class for ANSI color codes."""
    
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def parse_yaml(file_path):
    """Parse a YAML file and return a list of dictionaries.
    
    Args:
        file_path (str): The path to the YAML file.
        
    Returns:
        list: A list of dictionaries containing the parsed YAML data.
    """
    yaml_data = "--"
    try:
        with open(file_path, "r") as file:
            yaml_data = list(yaml.safe_load_all(file))
        return yaml_data
    except Exception as e:
        Console.error("Could not parse YAML file: {file_path}")


def read_file(file_path):
    """Read the contents of a file and return it as a string.
    
    Args:
        file_path (str): The path to the file.
        
    Returns:
        str: The contents of the file.
    """
    file_content = ''
    try:
        with open(file_path, 'r') as file:
            file_content = file.read()
        return file_content
    except Exception as e:
        Console.error("Could read file: {file_path}")

class Console:
    """Class for console output and input handling."""
    
    def read(message):
        """Read input from the console.
        
        Args:
            message (str): The message to display to the user.
            
        Returns:
            str: The user's input.
        """
        return input(message)

    def verbose(msg):
        if VERBOSE:
            print(f"{Colors.OKBLUE}{msg}{Colors.ENDC}".format(msg=str(msg)))

    def print(msg=''):
        """Print a message to the console.
        
        Args:
            msg (str): The message to print.
        """
        print(msg)

    def println(no=1):
        """Print a message to the console.
        
        Args:
            no (int): The number of times to print the message.
        """
        for i in range(no):
            print()

    def ok(msg):
        """Print a message to the console.
        
        Args:
            msg (str): The message to print.
        """
        print(f"{Colors.OKGREEN}{msg}{Colors.ENDC}".format(msg=str(msg)))

    def error(msg):
        """Print an error message to the console.
        
        Args:
            msg (str): The message to print.
        """
        Console.fail(msg)

    def fail(msg):
        """Print a failure message to the console.
        
        Args:
            msg (str): The message to print.
        """
        print(f"{Colors.FAIL}Error: {msg}{Colors.ENDC}".format(msg=str(msg)))

    def warn(msg):
        """Print a warning message to the console.
        
        Args:
            msg (str): The message to print.
        """
        print(f"{Colors.WARNING}Warning: {msg}{Colors.ENDC}".format(msg=str(msg)))

    def progress(count, total, status=''):
        """Print a progress bar to the console.
        
        Args:
            count (int): The current count.
            total (int): The total count.
            status (str): The status message.
        """
        bar_len = 60
        filled_len = int(round(bar_len * count / float(total)))

        percents = round(100.0 * count / float(total), 1)
        bar = '=' * filled_len + '-' * (bar_len - filled_len)

        sys.stdout.write('[%s] %s%s ...%s\r' % (bar, percents, '%', status))
        sys.stdout.flush()
