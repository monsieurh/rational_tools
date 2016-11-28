#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import readline
from datetime import datetime
from hashlib import md5

from dateutil import parser as date_parser

from print_util import GenericPrinter

__version__ = '0.0.1'


class Prediction:
    def __init__(self, realization_date: datetime = None, confidence: float = None, statement: str = None):
        self.statement = statement
        self.outcome = bool
        self.confidence = confidence
        self.realization_date = realization_date
        self.emission_date = datetime.now()

        self.tags = list()  # todo : optional input of tags and notes
        self.proof = str()
        self.notes = str()

    def hash(self):
        return md5(
            str(self.statement).encode('utf-8')
            + str(self.confidence).encode('utf-8')
            + str(self.realization_date).encode('utf-8')
            + str(self.emission_date).encode('utf-8')
        ).hexdigest()

    def __repr__(self):
        return '{s.__class__}' \
               '(' \
               '{s.statement!r}, ' \
               '{s.outcome!s}, ' \
               '{s.confidence!r}, ' \
               '{s.realization_date!r}, ' \
               '{s.emission_date!r}' \
               ')'.format(s=self)


class PredictionPrinter(GenericPrinter):
    @staticmethod
    def print_prediction(prediction: Prediction):
        string = 'Statement :\n' \
                 '{p.statement}\n' \
                 'Realization:\t{p.realization_date:%Y-%m-%d}\n' \
                 'Confidence:\t{p.confidence:.2%}\n' \
                 'Identifier:\t{hash}\n'.format(p=prediction, hash=prediction.hash())
        print(string)


class InteractivePredictionBuilder:
    def __init__(self):
        self.__prediction = Prediction()

    def get_errors(self) -> list:
        public_attrs = [attr for attr in dir(self.__prediction) if not attr.startswith('__')]
        errors = ['{} not set'.format(attr) for attr in public_attrs if attr is None]
        if self.__prediction.emission_date is not None and self.__prediction.realization_date is not None and (
                    self.__prediction.emission_date >= self.__prediction.realization_date):
            errors.append('you can\'t predict the past')
        return errors

    def build_interactive(self):
        self.__prediction.statement = self.__prompt_statement('Statement :\n', self.__prediction.statement)
        self.__prediction.realization_date = self.__prompt_date('Realization date :\n',
                                                                self.__prediction.realization_date)
        self.__prediction.confidence = self.prompt_ratio('Confidence :\n', self.__prediction.confidence)
        self.__fill_input()  # resets fill to ''

    def build(self) -> Prediction:
        if not self.get_errors():
            return self.__prediction

    @staticmethod
    def __prompt_statement(prompt_text: str, previous_input: str = None):
        InteractivePredictionBuilder.__fill_input(previous_input)
        statement = None
        while statement is None:
            statement = str(input(prompt_text))
            statement = statement if len(statement) else None

        return statement

    @staticmethod
    def __prompt_date(prompt_text: str, previous_input: str = None):
        InteractivePredictionBuilder.__fill_input(previous_input)
        date_input = None
        while date_input is None:
            try:
                date_input = date_parser.parse(input(prompt_text))
            except ValueError:
                pass
        return date_input

    @staticmethod
    def prompt_ratio(prompt_text: str, previous_input: str = None):
        InteractivePredictionBuilder.__fill_input(previous_input)
        ratio = None
        while ratio is None:
            ratio = InteractivePredictionBuilder.__parse_ratio(input(prompt_text))
            ratio = ratio if 0 <= ratio <= 1 else None
        return ratio

    @staticmethod
    def __parse_ratio(user_input: str):
        try:
            if '%' in user_input:
                user_input = user_input.replace('%', '')
                return float(user_input) / 100

            if 'in' in user_input:
                user_input = user_input.replace('in', '/')

            if '/' in user_input:
                inputs = user_input.split('/')
                return float(inputs[0]) / float(inputs[1])
            return float(user_input)

        except (ValueError, TypeError):
            return None

    @staticmethod
    def __fill_input(fill_text: str = ''):
        fill_text = fill_text if fill_text is not None else ''
        readline.set_startup_hook(lambda: readline.insert_text(str(fill_text)))


def show_prediction(identifiers: list, __func: callable) -> None:
    print('SHOW PREDICTION FOR identifiers : {} '.format(identifiers))  # todo


def add_prediction(__func: callable):
    builder = InteractivePredictionBuilder()
    confirmed = False
    while len(builder.get_errors()) or not confirmed:
        try:
            builder.build_interactive()
        except KeyboardInterrupt:
            exit(0)
        errors = builder.get_errors()
        if len(errors):
            print(errors)  # todo : check on input instead
        else:
            PredictionPrinter.print_prediction(builder.build())
            confirmed = input('Is this OK? [y/n]\n').upper() == 'Y'


def print_summary(__func: callable):
    print("PRINT SUMMARY")  # todo


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--version', action='version', version='%(prog)s {}'.format(__version__))
    parser.set_defaults(__func=print_summary)

    subparsers = parser.add_subparsers(help='Commands')

    add_parser = subparsers.add_parser('add')
    add_parser.set_defaults(__func=add_prediction)

    show_parser = subparsers.add_parser('show')
    show_parser.set_defaults(__func=show_prediction)
    show_parser.add_argument('identifiers', nargs='+', metavar='IDENTIFIER')

    args = parser.parse_args()

    args.__func(**vars(args))

"""
behavior :
1 : noarg -> display current score, pending prediction count, next prediction
2 : add -> interactive prompt with new prediction
3 : solve -> solves passed predictions
4 : show -> takes number or hash or date as parameter and show a prediction in detail
5?: stats -> give a tag/range and have stat on this
6?: search -> by tag/date
"""
