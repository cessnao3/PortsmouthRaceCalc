"""
Parses input files into Python object to parse race information
"""

import boat_database as bdb
import skipper_database as sdb

import yaml


with open(data_file('series.yaml'), 'r') as f:
    series_data = yaml.safe_load(f)

with open(data_file('fleets.yaml'), 'r') as f:
    fleet_data = yaml.safe_load(f)

fleets = dict()

for f in fleet_data:
    fleet_dict = fleet_data[f]

    with open(data_file(fleet_dict['portsmouth_table']), 'r') as f_handle:
        boat_table = f_handle.read()
    fleets[f] = bdb.Fleet(name=f, boat_types=bdb.BoatType.load_from_csv(boat_table))

with open(data_file('skippers.csv'), 'r') as f:
    skippers = sdb.Skipper.load_from_csv(f.read())

series = dict()
