import os
import textwrap

from termcolor import colored

try:
    term_w, _ = os.get_terminal_size()
except OSError:
    term_w = 45
APP_WIDTH = min(45, term_w)


class GenericPrinter:
    @staticmethod
    def print_header(header_name: str):
        print(header_name.upper().center(APP_WIDTH, '_'))

    @staticmethod
    def print_line_break():
        print('-' * APP_WIDTH)

    @staticmethod
    def print_tabbed(key: str, value: str):
        print(colored(key, attrs=["bold"]) + "\t" + value)

    @staticmethod
    def print_pair(key, value, color=None, attrs=None):
        if not attrs:
            attrs = ['bold']

        left = str(key) + ':'
        right = str(value)

        left = colored(left, color=color, attrs=attrs)
        right = colored(right, color=color)
        print(textwrap.fill(left, APP_WIDTH))
        print(textwrap.fill('\n\t' + right, APP_WIDTH))
