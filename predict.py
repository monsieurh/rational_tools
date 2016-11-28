#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import os
import pickle
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

    def short_hash(self):
        return self.hash()[:6]

    def __repr__(self):
        return '{s.__class__}' \
               '(' \
               '{s.statement!r}, ' \
               '{s.outcome!s}, ' \
               '{s.confidence!r}, ' \
               '{s.realization_date!r}, ' \
               '{s.emission_date!r}' \
               ')'.format(s=self)


class PredictionStorage:
    def __init__(self):
        self._path = PredictionStorage.__get_storage_path()
        self.create_file_if_not_exists()
        self.content = self.__load_data()

    def create_file_if_not_exists(self):
        if not os.path.exists(self._path):
            pickle.dump(dict(), open(self._path, 'wb'))

    @staticmethod
    def __get_storage_path():
        storage_path = os.environ.get('PREDICTION_DB', None)
        if storage_path:
            return storage_path
        script_path = os.path.dirname(os.path.realpath(__file__))
        return os.path.join(script_path, 'predictions.pickle')

    def __load_data(self) -> dict:
        return pickle.load(open(self._path, 'rb'))

    def add(self, prediction: Prediction):
        self.content[prediction.short_hash()] = prediction

    def save(self):
        pickle.dump(self.content, open(self._path, 'wb'))

    def get(self, short_id: str) -> Prediction:
        if short_id in self.content.keys():
            return self.content[short_id]


class PredictionPrinter(GenericPrinter):
    @staticmethod
    def print_prediction(prediction: Prediction):
        PredictionPrinter.print_header(prediction.short_hash())
        PredictionPrinter.print_tabbed('statement', prediction.statement)
        PredictionPrinter.print_pair('realization', '{0:%Y-%m-%d}'.format(prediction.realization_date))
        PredictionPrinter.print_pair('confidence', '{0:.2%}'.format(prediction.confidence))
        PredictionPrinter.print_pair('hash', prediction.hash())


class InteractivePredictionBuilder:
    def __init__(self):
        self.__prediction = Prediction()

    def get_errors(self) -> list:
        public_attrs = [attr for attr in dir(self.__prediction) if not attr.startswith('__')]
        errors = ['{} not set'.format(attr) for attr in public_attrs if attr is None]
        return errors

    def build_interactive(self):
        self.__prediction.statement = self.__prompt_statement('Statement :\n', self.__prediction.statement)
        self.__prediction.realization_date = self.__prompt_date('Realization date :\n',
                                                                self.__prediction.realization_date)
        self.__prediction.confidence = self.prompt_ratio('Confidence :\n', self.__prediction.confidence)
        self.__fill_input()  # resets filling to ''

    def build(self) -> Prediction:
        if not self.get_errors():
            return self.__prediction

    @staticmethod
    def __prompt_statement(prompt_text: str, previous_input: str = None):
        InteractivePredictionBuilder.__fill_input(previous_input)
        statement = None
        while statement is None:
            statement = str(InteractivePredictionBuilder.__input(prompt_text))
            statement = statement if len(statement) else None

        return statement

    def __prompt_date(self, prompt_text: str, previous_input: str = None):
        InteractivePredictionBuilder.__fill_input(previous_input)
        date_input = None
        while date_input is None:
            try:
                date_input = date_parser.parse(self.__input(prompt_text))
                if self.__prediction.emission_date >= date_input:
                    date_input = None
            except ValueError:
                pass
        return date_input

    @staticmethod
    def __input(prompt_text):
        return input(prompt_text + '\t')

    @staticmethod
    def prompt_ratio(prompt_text: str, previous_input: str = None):
        InteractivePredictionBuilder.__fill_input(previous_input)
        ratio = None
        while ratio is None:
            ratio = InteractivePredictionBuilder.__parse_ratio(InteractivePredictionBuilder.__input(prompt_text))
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
    storage = PredictionStorage()

    while len(builder.get_errors()) or not confirmed:
        builder.build_interactive()
        errors = builder.get_errors()
        if len(errors):
            print(errors)  # todo : check on input instead
        else:
            prediction = builder.build()
            PredictionPrinter.print_prediction(prediction)
            confirmed = input('Is this OK? [y/n]\t').upper() == 'Y'
            storage.add(prediction)
    storage.save()


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

    try:
        args.__func(**vars(args))
    except KeyboardInterrupt:
        exit(0)

"""
behavior :
1 : noarg -> display current score, pending prediction count, next prediction
2 : add -> interactive prompt with new prediction
3 : solve -> solves passed predictions
4 : show -> takes number or hash or date as parameter and show a prediction in detail
5?: stats -> give a tag/range and have stat on this
6?: search -> by tag/date
"""
