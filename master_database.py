"""
Parses input files into Python object to parse race information
"""

import boat_database as bdb
import skipper_database as sdb
import race_database as rdb

import yaml


class MasterDatabase:
    input_folder_name = 'input'
    fleet_input_name = 'fleets.yaml'
    skipper_input_name = 'skippers.csv'

    def __init__(self):
        self.fleets = None
        self.skippers = None
        self.series = None

        self._load_fleets()
        self._load_skippers()
        self._load_series()

    def _data_file(self, file_name):
        """
        Provides a modified filename to read from the input file directory
        :param file_name: filename to add to the path
        :type file_name: str
        :return: modified filename to load from appropriate input file directory
        """
        return '{:s}/{:s}'.format(self.input_folder_name, file_name)

    def _load_fleets(self):
        with open(self._data_file(self.fleet_input_name), 'r') as fleet_handle:
            fleet_data = yaml.safe_load(fleet_handle)

        fleets = dict()

        for fleet in fleet_data:
            if fleet in fleets:
                raise ValueError('Cannot add a duplicate fleet {:s}'.format(fleet))

            fleet_dict = fleet_data[fleet]

            with open(self._data_file(fleet_dict['portsmouth_table']), 'r') as table_handle:
                boat_table = table_handle.read()
            fleets[fleet] = bdb.Fleet(
                name=fleet,
                boat_types=bdb.BoatType.load_from_csv(boat_table))

        self.fleets = fleets

    def _load_skippers(self):
        with open(self._data_file(self.skipper_input_name), 'r') as skipper_handle:
            skippers = sdb.Skipper.load_from_csv(skipper_handle.read())
        self.skippers = skippers

    def _load_series(self):
        series_values = dict()

        with open(self._data_file('series.yaml'), 'r') as f:
            series_data = yaml.safe_load(f)

        for series_name in series_data:
            if series_name in series_values:
                raise ValueError('Cannot add a duplicate series {:s}'.format(series_name))

            s = series_data[series_name]
            fleet_name = s['fleet']

            if fleet_name not in self.fleets:
                raise ValueError('Fleet {:s} does not exist in fleet structure'.format(fleet_name))
            fleet = self.fleets[fleet_name]

            boat_overrides = s['boat_overrides']

            series = rdb.Series(
                name=series_name,
                qualify_count=s['qualify_count'],
                fleet=fleet,
                boat_overrides=boat_overrides)

            with open(self._data_file(s['race_file']), 'r') as f:
                race_data = yaml.safe_load(f)

            for race_date_dict in race_data:
                race_committee = [self.skippers[person] for person in race_date_dict['rc']]
                for race_dict in race_date_dict['races']:
                    race = rdb.Race(
                        series=series,
                        rc=race_committee,
                        date=race_date_dict['date'],
                        wind_bf=race_dict['wind_bf'],
                        notes=race_dict['notes'])

                    time_values = race_dict['times']

                    for skipper_id in time_values:
                        race_time = rdb.RaceTime(
                            race=race,
                            skipper=self.skippers[skipper_id],
                            time_s=time_values[skipper_id])
                        race.add_skipper_time(race_time)

                    series.add_race(race)

            series_values[series_name] = series
            self.series = series_values
