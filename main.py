"""
Race Database Console Main Function
"""

import pathlib

from database import MasterDatabase

database = MasterDatabase(input_folder=pathlib.Path('input'))
database.update_statistics()

for series in database.series.values():
    race_num = 1
    for race in series.races:
        print(' Race: {:d}'.format(race_num))
        print(race.get_race_table())
        print()
        race_num += 1
    print(series.get_series_table())
