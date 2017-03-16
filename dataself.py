#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
from datetime import datetime, timedelta

from matplotlib import pyplot as plt
from matplotlib.dates import date2num

from today import DataLoader, Config


def get_database() -> DataLoader:
    file_path = os.environ.get("TODAY_DB", os.path.realpath("./today.json"))
    return DataLoader(file_path)


def plot(data: DataLoader, props: list, timespan: int) -> None:
    config = Config.get_config()
    # Create dates
    current_date = datetime.today().date()
    dates = [current_date - timedelta(days=i) for i in range(timespan)]
    begin_date = dates[0]  # Find begin date

    # numeric_tagsets = [[data.find_prop_value(d, tag.upper()) for d in dates if d] for tag in props]
    # numeric data
    numeric_props=[p for p in props if p not in config.get('INTERACTIVE_TAGS')]
    numeric_tagsets = [[data.find_prop_value(d, tag.upper()) for d in dates if d] for tag in props if
                       tag not in config.get('INTERACTIVE_TAGS')]
    text_tagsets = [[data.find_prop_value(d, tag.upper()) for d in dates if d] for tag in props if
                    tag in config.get('INTERACTIVE_TAGS')]

    plt.xkcd()

    # plot numeric
    ycoords = None
    for tagset in numeric_tagsets:
        result = plt.plot_date(date2num(dates), tagset, xdate=True, fmt='-')
        ycoords = result[0]._y

    # plot events
    for events in text_tagsets:
        for i in range(len(events)):
            if events[i] is None: continue
            plt.text(date2num(dates[i]) + 0.1, ycoords[i] + 0.1, events[i],
                     withdash=True, dashdirection=1, dashlength=100.0,
                     dashrotation=135)  # todo:if no numeric event

    plt.title("dataself over {} days (since {})".format(timespan, begin_date))
    plt.legend(numeric_props)
    plt.show()


def main():
    data = get_database()
    parser = argparse.ArgumentParser()
    parser.add_argument(metavar='PROPERTIES', type=str, nargs='+', dest='properties', choices=data.known_properties())
    parser.add_argument('-t', metavar='timespan', type=int, default=10, dest='timespan')

    args = parser.parse_args()
    plot(data, args.properties, args.timespan)


if __name__ == "__main__":
    main()
