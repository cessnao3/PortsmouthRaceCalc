"""
Race Database Console Main Function
"""

from master_database import MasterDatabase

database = MasterDatabase()

for series in database.series.values():
    race_num = 1
    for race in series.races:
        print(' Race: {:d}'.format(race_num))
        print(race.get_race_table())
        print()
        race_num += 1
