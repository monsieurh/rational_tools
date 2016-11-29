import os

from termcolor import colored

try:
    term_w, _ = os.get_terminal_size()
except OSError:
    term_w = 40
APP_WIDTH = min(40, term_w)


class GenericPrinter:
    @staticmethod
    def print_header(header_name: str):
        print(header_name.upper().center(APP_WIDTH, '_'))

    @staticmethod
    def print_tabbed(key: str, value: str):
        print(colored(key, attrs=["bold"]) + "\t" + value)

    @staticmethod
    def print_pair(key, value, color=None, attrs=None):
        if not attrs:
            attrs = ['bold']

        left = key
        right = value
        padding = "{}".format("".rjust(APP_WIDTH - (len(str(left)) + len(str(right))), " "))

        left = colored(left, color=color, attrs=attrs)
        right = colored(right, color=color, attrs=attrs)
        print(left, padding, right, sep="")
