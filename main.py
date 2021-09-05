"""
Race Database Console Main Function
"""

import pathlib

from database import MasterDatabase


def main():
    database = MasterDatabase(input_folder=pathlib.Path('input'))
    series_list = list(database.series.values())
    series_list.sort(key=lambda x: x.name)

    if len(series_list) == 0:
        print('No series provided')
    else:
        series = series_list[-1]
        for i, race in enumerate(series.races):
            print(' Race: {:d}'.format(i + 1))
            print(race.get_race_table())
            print()
        print(series.get_series_table())


if __name__ == '__main__':
    main()
