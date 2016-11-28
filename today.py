#!/usr/bin/env python3
# -*- coding: utf-8 -*-
try:
    import ujson as json
except ImportError:
    import json
import os
import readline
import sys
from datetime import datetime, timedelta

import yaml
from termcolor import colored

from print_util import GenericPrinter

__version__ = "0.4"


# todo : readme and tag++

class InvalidArgumentException(Exception):
    pass


class Config:
    default_name = 'today.yaml'

    @staticmethod
    def get_config() -> dict:
        try:
            with open(Config.__get_config_file_path(), 'r') as stream:
                return yaml.load(stream)
        except IOError:
            return dict()

    @staticmethod
    def __get_config_file_path():
        script_path = os.path.dirname(os.path.realpath(__file__))
        return os.path.join(script_path, Config.default_name)


class ArgumentParser:
    def __init__(self, arguments_list: list, database_file_path: os.path):
        super().__init__()
        self.interactive_log = None
        self.date = datetime.today().date()
        self.file = os.environ.get("TODAY_DB", database_file_path)
        self.payload = dict()

        self.parse_args(arguments_list)

        self.readonly = True if len(self.payload) == 0 and not self.interactive_log else False

    def parse_args(self, params: list) -> None:
        if params[0] == __file__:  # Cleanup the first parameter being the name of the invoked script
            params = params[1:]

        for arg in params:
            if self.is_interactive_arg(arg):
                self.interactive_log = arg.upper()
            elif self.is_date_arg(arg):
                self.update_date(arg)
            elif self.is_file_arg(arg):
                self.update_file(arg)
            else:
                self.update_payload(arg)

    @staticmethod
    def split_arg(arg: str) -> list:
        split = str(arg).split("=")
        split[0] = split[0].strip("-").upper()
        if len(split) != 2:
            raise InvalidArgumentException("The argument '{}' is Invalid".format(arg))
        return split

    def is_date_arg(self, arg: str) -> bool:
        return self.split_arg(arg)[0] == "D" or self.split_arg(arg)[0] == "DATE"

    def is_file_arg(self, arg: str) -> bool:
        return self.split_arg(arg)[0] == "F" or self.split_arg(arg)[0] == "FILE"

    @staticmethod
    def is_interactive_arg(arg: str) -> bool:
        return arg.upper() in DataLoader.interactive_preset.keys()

    def update_date(self, arg: str) -> None:
        assert self.is_date_arg(arg)
        days = self.split_arg(arg)[1]
        self.date = datetime.today().date() - timedelta(days=int(days))

    def update_payload(self, arg: str) -> None:
        name, value = self.split_arg(arg)
        self.payload[name] = value

    def properties(self) -> list:
        return self.payload.keys()

    def as_payload(self) -> dict:
        p = dict(self.payload)
        p['DATE'] = str(self.date)
        return p

    def update_file(self, arg: str) -> None:
        assert self.is_file_arg(arg)
        _, file_path = self.split_arg(arg)

        self.file = os.path.realpath(file_path)


class DataLoader:
    interactive_preset = {'LOG': "Today,"}

    def __init__(self, json_file_path, addendum=None):
        super().__init__()
        self.file_path = json_file_path
        self.addendum = addendum
        self.payload = list()
        self._load()

    def _load(self):
        # noinspection PyBroadException
        try:
            with open(self.file_path, "r+") as file:
                self.payload = json.load(file)
        except:
            print("json file '{}' not found !".format(self.file_path), file=sys.stderr)

    def find(self, date: datetime.date) -> dict:
        record = self._find(date)
        if record:
            return dict(record)
        else:
            return None

    def _find(self, date: datetime.date) -> dict:
        for item in self.payload:
            # noinspection PyTypeChecker
            if "DATE" in item.keys() and item["DATE"] == str(date):
                return item

    def find_prop_value(self, date: datetime.date, prop: str) -> str:
        record = self._find(date)
        if record and prop in record.keys():
            return record[prop]

    def merge(self, addendum):
        row = self._find(addendum["DATE"])
        if row:
            row.update(addendum)
        else:
            self.payload.append(addendum)

    def save(self):
        with open(self.file_path, "w+") as file:
            json.dump(self.payload, file)

    def known_properties(self):
        props = set()
        for item in self.payload:
            for key in item.keys():
                props.add(key)
        return props


class ProgramPrinter:
    @staticmethod
    def print_help() -> None:
        ProgramPrinter.desc()
        ProgramPrinter.usage()

    @staticmethod
    def desc() -> None:
        print("Logs daily data to a JSON database.")
        print("Arguments are in the format 'key=value'. Strings an numbers are accepted")

    @staticmethod
    def usage() -> None:
        print("-v\tprints the version of the script")
        print("-h\tprints this help and exits")
        print("-d\tspecify the number of days to rewind (e.g. '{} -d=1' is for yesterday)".format(
            os.path.basename(sys.argv[0])))
        print("-f\tspecify the JSON file to load/save. Can be specified with TODAY_DB environment variable")
        print("\nCall this script without argument to print today's data.")

    @staticmethod
    def print_version() -> None:
        print("'{}' version {}".format(os.path.basename(sys.argv[0]), __version__))


class RecordPrinter(GenericPrinter):
    @staticmethod
    def print_record(loader: DataLoader, record_date: datetime.date, trending: dict) -> None:
        today_data = loader.find(record_date)
        if today_data:
            date_str = today_data.pop("DATE")
            interactive_props = {prop: today_data.pop(prop, None) for prop in DataLoader.interactive_preset.keys()}

            if trending:
                RecordPrinter.print_header("TRENDS")
                RecordPrinter.print_trending_properties(trending, loader, record_date)

            RecordPrinter.print_header("PROPERTIES")
            RecordPrinter.print_regular_properties(today_data)

            RecordPrinter.print_header(date_str)
            RecordPrinter.print_interactive_properties(interactive_props)

        else:
            error_msg = "RECORD '{}' NOT FOUND".format(record_date)
            print(colored(error_msg, "red", attrs=['blink', 'bold']))

    @staticmethod
    def print_regular_properties(today_data):
        for item in today_data.items():
            RecordPrinter.print_pair(item[0], item[1])

    @staticmethod
    def print_interactive_properties(interactive_props):
        for prop in interactive_props:
            if interactive_props[prop] is not None:
                print(colored(prop, attrs=["bold"]) + "\t" + interactive_props[prop])

    @staticmethod
    def print_trend(prop: str, loader: DataLoader, record_date: datetime.date, timespan: int = 1) -> None:
        trend = RecordPrinter._compute_trend(loader, prop, record_date, timespan)

        color, attr = ("red", ['bold']) if trend > 0 else ("green", ['bold'])
        trend_str = "{:+.1f}".format(trend)
        RecordPrinter.print_pair("{}_TREND_{}_DAYS".format(prop, timespan), trend_str, color=color, attrs=attr)

    @staticmethod
    def _compute_trend(loader, prop, record_date, timespan):
        dates = [record_date - timedelta(days=i) for i in range(timespan + 1)]
        all_values = [loader.find_prop_value(d, prop) for d in dates]

        today_value = float(all_values[0]) if all_values[0] else 0
        values = all_values[1:]  # all minus today

        values = [float(v) for v in values if v is not None]
        if not len(values):
            return 0
        average = sum(values) / len(values)
        return today_value - average

    @staticmethod
    def print_trending_properties(trending_props: dict, loader: DataLoader, record_date: datetime.date):
        for prop in trending_props:
            RecordPrinter.print_trend(prop, loader, record_date, trending_props.get(prop))


class DatabasePrinter(GenericPrinter):
    @staticmethod
    def print_database_info(loader):
        DatabasePrinter.print_pair("DATABASE", loader.file_path)
        DatabasePrinter.print_pair("KNOWN_TAGS", ", ".join(loader.known_properties()))
        DatabasePrinter.print_pair("RECORD_COUNT", len(loader.payload))


def check_simple_args() -> bool:
    if "-h" in sys.argv:
        ProgramPrinter.print_help()
        return True

    if "-v" in sys.argv:
        ProgramPrinter.print_version()
        return True


def interactive_input(loader: DataLoader, date: datetime.date, prop: str) -> str:
    current_log = loader.find_prop_value(date, prop)
    if not current_log or not len(current_log):
        current_log = DataLoader.interactive_preset.get(prop, '')
    readline.set_startup_hook(lambda: readline.insert_text(current_log))
    try:
        user_input = input()
    except KeyboardInterrupt:
        user_input = None
    return user_input if user_input and len(user_input) else None


def main():
    if check_simple_args():
        exit(0)

    app_config = Config.get_config()
    DataLoader.interactive_preset = app_config.get('INTERACTIVE_TAGS', DataLoader.interactive_preset)
    try:
        parsed = ArgumentParser(sys.argv, app_config.get('DATABASE_PATH'))
    except InvalidArgumentException as e:
        print(e, file=sys.stderr)
        ProgramPrinter.usage()
        exit(-1)

    # noinspection PyUnboundLocalVariable
    loader = DataLoader(parsed.file)
    if parsed.readonly:
        RecordPrinter.print_record(loader, parsed.date, app_config.get('TRENDING'))

    else:
        payload = parsed.as_payload()
        if parsed.interactive_log:
            payload[parsed.interactive_log] = interactive_input(loader, parsed.date, parsed.interactive_log)

        loader.merge(payload)
        loader.save()
        print("Updated entry for '{}'".format(parsed.date))
        DatabasePrinter.print_database_info(loader)


if __name__ == '__main__':
    main()
