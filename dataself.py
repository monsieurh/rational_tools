#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import os
from datetime import datetime, timedelta

from matplotlib import pyplot as plt

from today import DataLoader


def get_database() -> DataLoader:
    file_path = os.environ.get("TODAY_DB", os.path.realpath("./today.json"))
    return DataLoader(file_path)


def plot(data: DataLoader, props: list, timespan: int) -> None:
    current_date = datetime.today().date()
    dates = [current_date - timedelta(days=i) for i in range(timespan)]
    tag_data_set = [[data.find_prop_value(d, tag.upper()) for d in dates] for tag in props]

    plt.xkcd()

    for tagset in tag_data_set:
        plt.plot(dates, tagset)

    plt.ioff()
    plt.title("dataself over {} days (since {})".format(timespan, dates[0]))
    plt.legend(props)
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
