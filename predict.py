#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import os
import pickle
import readline
from collections import Iterable
from datetime import datetime, date
from hashlib import md5
from sys import stderr

from dateutil import parser as date_parser
from termcolor import colored

from print_util import GenericPrinter

__version__ = '0.2'
__friendly_name__ = 'predict'


class Prediction:
    def __init__(self, realization_date: datetime = None, confidence: float = None, statement: str = None):
        self.statement = statement
        self.outcome = None
        self.confidence = confidence
        self.realization_date = realization_date
        self.emission_date = datetime.now()

        self.tags = list()
        self.proof = str()

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
               '{s.outcome}, ' \
               '{s.confidence!r}, ' \
               '{s.realization_date!r}, ' \
               '{s.emission_date!r}' \
               ')'.format(s=self)

    def get_status(self):
        if self.outcome is not None:
            return 'solved'

        if self.realization_date > datetime.now():
            return 'future'

        return 'pending'

class PredictionStorage:
    def __init__(self):
        self._path = PredictionStorage.__get_storage_path()
        self.create_file_if_not_exists()
        self.content = self.__load_data()
        self.now = datetime.now()

    def add(self, prediction: Prediction):
        self.content[prediction.short_hash()] = prediction

    def save(self):
        pickle.dump(self.content, open(self._path, 'wb'))

    def get_next(self) -> Prediction:
        if not len(self.content):
            return None
        return sorted(self.get_future(), key=lambda x: x.realization_date)[0]

    def get_last(self) -> Prediction:
        if not len(self.content):
            return None
        return sorted(self.get_past(), key=lambda x: x.realization_date, reversed=True)[0]

    def get(self, short_id: str) -> Prediction:
        if short_id in self.content.keys():
            return self.content[short_id]

    def get_past(self) -> list:
        return [p for p in self.content.values() if p.realization_date < self.now]

    def get_pending(self):
        return [p for p in self.get_past() if p.get_status() == 'pending']

    def get_solved(self):
        return [p for p in self.get_past() if p.get_status() == 'solved']

    def get_future(self) -> list:
        return [p for p in self.content.values() if p.realization_date > self.now]

    def create_file_if_not_exists(self):
        if not os.path.exists(self._path):
            pickle.dump(dict(), open(self._path, 'wb'))

    def get_brier_score(self):
        return self.compute_brier_score(self.content.values())

    @staticmethod
    def compute_brier_score(prediction_list: Iterable):
        prediction_list = [p for p in prediction_list if p.get_status() == 'solved']
        if not len(prediction_list):
            return 2  # Maximum score is default

        total = 0
        for prediction in prediction_list:
            outcome = 1 if prediction.outcome is True else 0
            total += (prediction.confidence - outcome) ** 2
        return total / len(prediction_list)

    @staticmethod
    def __get_storage_path():
        storage_path = os.environ.get('PREDICTION_DB', None)
        if storage_path:
            return storage_path
        script_path = os.path.dirname(os.path.realpath(__file__))
        return os.path.join(script_path, 'predictions.pickle')

    def __load_data(self) -> dict:
        return pickle.load(open(self._path, 'rb'))

    def get_all(self):
        return [p for p in self.content.values()]

    def delete(self, identifier: str):
        self.content.pop(identifier, None)


class PredictionPrinter(GenericPrinter):
    @staticmethod
    def print_prediction(prediction: Prediction):
        PredictionPrinter.print_line_break()
        PredictionPrinter.print_pair('id', prediction.short_hash())
        PredictionPrinter.print_pair('status', prediction.get_status())
        PredictionPrinter.print_pair('statement', prediction.statement)
        PredictionPrinter.print_pair('realization', '{0:%Y-%m-%d@%H:%M}'.format(prediction.realization_date))
        PredictionPrinter.print_pair('confidence', '{0:.2%}'.format(prediction.confidence))
        PredictionPrinter.print_pair('hash', prediction.hash())
        if prediction.outcome is not None:
            PredictionPrinter.print_pair('outcome', prediction.outcome)
        if len(prediction.proof):
            PredictionPrinter.print_pair('proof', prediction.proof)

        if len(prediction.tags):
            PredictionPrinter.print_pair('tags', ', '.join(prediction.tags))

    @staticmethod
    def print_prediction_short(prediction: Prediction):
        if prediction.outcome is True:
            outcome_color = 'green'
        elif prediction.outcome is False:
            outcome_color = 'red'
        else:
            outcome_color = 'white'
        print('[{}] {:.0%}->\t{}\t{:%Y-%m-%d} ({} days)\t{}'.format(
            prediction.short_hash(),
            prediction.confidence,
            colored(prediction.outcome, color=outcome_color),
            prediction.realization_date,
            (prediction.realization_date - datetime.now()).days,
            ', '.join(prediction.tags)
        ))


class InteractivePrompt:
    @staticmethod
    def fill_input(fill_text: str = ''):
        fill_text = fill_text if fill_text is not None else ''
        readline.set_startup_hook(lambda: readline.insert_text(str(fill_text)))

    @staticmethod
    def input(prompt_text):
        return input(prompt_text + '\t')

    @staticmethod
    def prompt_bool(prompt_text: str, previous_input: str = None):
        InteractivePredictionBuilder.fill_input(previous_input)
        user_input = InteractivePrompt.input(prompt_text)
        return user_input.lower() in ['yes', 'true', '1', 'y']

    @staticmethod
    def prompt_text(prompt_text: str, previous_input: str = None):
        InteractivePredictionBuilder.fill_input(previous_input)
        statement = None
        while statement is None:
            statement = str(InteractivePrompt.input(prompt_text))
            statement = statement if len(statement) else None

        return statement

    @staticmethod
    def clear_prompt():
        InteractivePrompt.fill_input()


class InteractivePredictionBuilder(InteractivePrompt):
    def __init__(self, prediction: Prediction = None):
        self.__prediction = prediction if prediction is not None else Prediction()

    def get_errors(self) -> list:
        public_attrs = [attr for attr in dir(self.__prediction) if not attr.startswith('__')]
        errors = ['{} not set'.format(attr) for attr in public_attrs if attr is None]
        return errors

    def build_interactive(self):
        self.__prediction.statement = self.prompt_text('Statement :\n', self.__prediction.statement)
        self.__prediction.realization_date = self.__prompt_date('Realization date :\n',
                                                                self.__prediction.realization_date)
        self.__prediction.confidence = self.prompt_ratio('Confidence :\n', self.__prediction.confidence)
        self.edit()
        self.clear_prompt()

    def edit(self):
        tag_input = self.prompt_text('Tags (comma separated):\n', ', '.join(self.__prediction.tags))
        self.__prediction.tags = [t.strip().upper() for t in tag_input.split(',') if len(t.strip())]

    def build(self) -> Prediction:
        if not self.get_errors():
            return self.__prediction

    def __prompt_date(self, prompt_text: str, previous_input: str = None):
        InteractivePredictionBuilder.fill_input(previous_input)
        date_input = None
        while date_input is None:
            try:
                date_input = date_parser.parse(self.input(prompt_text))
                if self.__prediction.emission_date >= date_input:
                    date_input = None
            except ValueError:
                pass
        return date_input

    @staticmethod
    def prompt_ratio(prompt_text: str, previous_input: str = None):
        InteractivePredictionBuilder.fill_input(previous_input)
        ratio = None
        while ratio is None:
            ratio = InteractivePredictionBuilder.__parse_ratio(InteractivePredictionBuilder.input(prompt_text))
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


# noinspection PyUnusedLocal
class InteractivePredictionSolver(InteractivePrompt):
    @staticmethod
    def solve(prediction: Prediction):
        prediction.outcome = InteractivePrompt.prompt_bool('Outcome: (True/False)', prediction.outcome)

        prediction.proof = InteractivePrompt.prompt_text('Proof:', prediction.proof)
        prediction.proof = prediction.proof if len(prediction.proof) else None


# noinspection PyUnusedLocal
def show_predictions(identifiers: list, __func: callable) -> None:
    storage = PredictionStorage()
    for short_hash in identifiers:
        prediction = storage.get(short_hash)
        if prediction:
            PredictionPrinter.print_prediction(prediction)


# noinspection PyUnusedLocal
def solve_predictions(identifiers: list, __func: callable) -> None:
    storage = PredictionStorage()
    if not len(identifiers):
        identifiers = [p.short_hash() for p in storage.get_pending()]
    predictions = [storage.get(i) for i in identifiers if storage.get(i) is not None]

    for prediction in predictions:
        PredictionPrinter.print_prediction(prediction)
        if input('Solve ? [y/n] ').upper() == 'Y':
            confirmed = False
            while not confirmed:
                InteractivePredictionSolver.solve(prediction)
                PredictionPrinter.print_prediction(prediction)
                confirmed = input('Is this OK? [y/n] ').upper() == 'Y'

    storage.save()


# noinspection PyUnusedLocal
def add_prediction(__func: callable):
    builder = InteractivePredictionBuilder()
    confirmed = False
    storage = PredictionStorage()

    while len(builder.get_errors()) or not confirmed:
        builder.build_interactive()
        errors = builder.get_errors()
        if len(errors):
            print(errors)
        else:
            prediction = builder.build()
            PredictionPrinter.print_prediction(prediction)
            confirmed = input('Is this OK? [y/n] ').upper() == 'Y'

    # noinspection PyUnboundLocalVariable
    storage.add(prediction)
    storage.save()


# noinspection PyUnusedLocal
def edit_prediction(identifier: str, __func: callable):
    storage = PredictionStorage()
    prediction = storage.get(identifier)
    if not prediction:
        print('Prediction \'{}\' not found'.format(identifier), file=stderr)
        exit(-1)
    builder = InteractivePredictionBuilder(prediction)
    builder.edit()
    builder.build()
    storage.save()


# noinspection PyUnusedLocal
def list_tag(tag: str, __func: callable):
    storage = PredictionStorage()
    tagged_predictions = list()
    if tag:
        tag = tag.upper()
        tagged_predictions = [p for p in storage.get_all() if tag in p.tags]
    else:
        tagged_predictions = storage.get_all()

    tagged_predictions = sorted(tagged_predictions, key=lambda x: x.realization_date)
    for prediction in tagged_predictions:
        PredictionPrinter.print_prediction_short(prediction)


# noinspection PyUnusedLocal
def print_stats(__func: callable, tag: str = None):
    storage = PredictionStorage()
    predictions = storage.get_all()
    if tag:
        predictions = [p for p in predictions if tag.upper() in p.tags]

    solved_list = [p for p in predictions if p.get_status() == 'solved']
    future_list = [p for p in predictions if p.get_status() == 'future']
    pending_list = [p for p in predictions if p.get_status() == 'pending']

    PredictionPrinter.print_pair('solved', len(solved_list))
    PredictionPrinter.print_pair('future', len(future_list))

    if len(future_list):
        next_prediction = sorted(future_list, key=lambda x: x.realization_date)[0]
        next_prediction = next_prediction if next_prediction.realization_date > datetime.now() else None
        if next_prediction:
            date_str = date.strftime(next_prediction.realization_date, '%Y-%m-%d')
            id_str = next_prediction.short_hash()
            PredictionPrinter.print_pair('next', '\'{}\' on {}'.format(id_str, date_str))

    if len(solved_list):
        GenericPrinter.print_pair('brier_score', '{:.2f}'.format(storage.compute_brier_score(solved_list)))

    if len(pending_list):
        reminder_string = 'You have {} predictions waiting to be solved ({})'.format(len(pending_list), ', '.join(
            [p.short_hash() for p in pending_list]))
        print(colored(reminder_string, color='red', attrs=['blink']))

def print_next(__func: callable):
    storage = PredictionStorage()
    next_prediction = storage.get_next()
    if next_prediction is not None:
        PredictionPrinter.print_prediction(next_prediction)
    else:
        print('No next prediction found')


# noinspection PyUnusedLocal
def print_action_required(__func: callable):
    storage = PredictionStorage()
    predictions = storage.get_all()

    pending_list = [p for p in predictions if p.get_status() == 'pending']

    print('{} : '.format(__friendly_name__), end='')
    if len(pending_list):
        reminder_string = 'You have {} predictions waiting to be solved ({})'.format(len(pending_list), ', '.join(
            [p.short_hash() for p in pending_list]))
        print(colored(reminder_string, color='red', attrs=['blink']))
        exit(-1)
    else:
        future_list = [p for p in predictions if p.get_status() == 'future']
        next_prediction = storage.get_next()
        if next_prediction:
            delta = next_prediction.realization_date - datetime.now()
            reminder_string = 'Next prediction in {} days'.format(delta.days)
            print(colored(reminder_string, color='green'))
        else:
            solved_list = [p for p in predictions if p.get_status() == 'solved']
            GenericPrinter.print_pair('brier_score', '{:.2f}'.format(storage.compute_brier_score(solved_list)))


# noinspection PyUnusedLocal
def del_prediction(identifier: str, __func: callable):
    storage = PredictionStorage()
    storage.delete(identifier)
    storage.save()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='%(prog)s : a python command line tool to note and test the accuracy of your predictions')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s {}'.format(__version__))
    parser.set_defaults(__func=print_action_required)

    subparsers = parser.add_subparsers(help='Available commands:')

    add_parser = subparsers.add_parser('add', help='Adds a new prediction')
    add_parser.set_defaults(__func=add_prediction)

    edit_parser = subparsers.add_parser('edit', help='Edits tags and proof of a prediction')
    edit_parser.set_defaults(__func=edit_prediction)
    edit_parser.add_argument('identifier', metavar='IDENTIFIER')

    show_parser = subparsers.add_parser('show', help='Shows full details of a prediction')
    show_parser.set_defaults(__func=show_predictions)
    show_parser.add_argument('identifiers', nargs='+', metavar='IDENTIFIER')

    list_parser = subparsers.add_parser('list', help='Lists predictions in one-line format')
    list_parser.set_defaults(__func=list_tag)
    list_parser.add_argument('tag', nargs='?', metavar='TAG')

    solve_parser = subparsers.add_parser('solve', help='Solves predictions that have come to term')
    solve_parser.set_defaults(__func=solve_predictions)
    solve_parser.add_argument('identifiers', nargs='*', metavar='IDENTIFIER')

    summary = subparsers.add_parser('summary',
                                    help='Prints only one line relative to the next action. '
                                         'Can be a countdown to the next precision, the Brier score, '
                                         'or a reminder to solve')
    summary.set_defaults(__func=print_action_required)

    next_parser = subparsers.add_parser('next', help='Prints the next prediction')
    next_parser.set_defaults(__func=print_next)

    stats_parser = subparsers.add_parser('stats', help='Prints various statistics')
    stats_parser.set_defaults(__func=print_stats)
    stats_parser.add_argument('tag', nargs='?', metavar='TAG')

    del_parser = subparsers.add_parser('del', help='Deletes a prediction')
    del_parser.set_defaults(__func=del_prediction)
    del_parser.add_argument('identifier', metavar='IDENTIFIER')

    args = parser.parse_args()

    try:
        args.__func(**vars(args))  # Calls the function associated with the parser in the '__func' field
    except KeyboardInterrupt:
        exit(0)
