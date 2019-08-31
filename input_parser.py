import boat_database as bdb
import skipper_database as sdb

import yaml

with open('race_input.yaml', 'r') as f:
    data = yaml.safe_load(f)

fleets = dict()

for f in data['fleets']:
    fleet_dict = data['fleets'][f]
    fleets[f] = bdb.Fleet(name=f, boat_types=bdb.BoatType.from_csv_file(fleet_dict['portsmouth_table']))

skippers = dict()

for s in data['skippers']:
    skip_dict = data['skippers'][s]
    skippers[s] = sdb.Skipper(name_code=s, **skip_dict)

series = dict()

print(data)
