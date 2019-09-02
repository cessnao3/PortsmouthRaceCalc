from master_database import MasterDatabase

database = MasterDatabase()

for s in database.series:
    race_num = 1
    for r in database.series[s].races:
        print(' Race: {:d}'.format(race_num))
        print(r.get_race_table())
        print()
        race_num += 1
