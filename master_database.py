"""
Parses input files into Python object to parse race information
"""

import boat_database as bdb
import skipper_database as sdb
import race_database as rdb

import yaml


class MasterDatabase:
    """
    Master database to keep track of all input parameters
    """
    input_folder_name = 'input'
    fleet_input_name = 'fleets.yaml'
    skipper_input_name = 'skippers.csv'
    series_input_name = 'series.yaml'

    def __init__(self, input_folder=None, fleet_file=None, skipper_file=None, series_file=None):
        """
        Initializes the master database with the provided inputs
        :param input_folder: folder where the input files are provided
        :type input_folder: str
        :param fleet_file: filename to override the fleet input file
        :type fleet_file: str
        :param skipper_file: filename to override the skipper input file
        :type skipper_file: str
        :param series_file: filename to override the series input file
        :type series_file: str
        """
        # Handle override parameter inputs
        if input_folder is not None:
            self.input_folder_name = input_folder
        if fleet_file is not None:
            self.fleet_input_name = fleet_file
        if skipper_file is not None:
            self.skipper_input_name = skipper_file
        if series_file is not None:
            self.series_input_name = series_file

        # Initialize the database parameters
        self.fleets = None
        self.skippers = None
        self.series = None

        # Load the database
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
        """
        Loads the fleet database from the provided files
        """
        # Read the YAML input file
        with open(self._data_file(self.fleet_input_name), 'r') as fleet_handle:
            fleet_data = yaml.safe_load(fleet_handle)

        # Initialize the dictionary
        fleets = dict()

        # Iterate over each fleet name
        for fleet_name in fleet_data:
            # Raise error if fleet name already exists
            if fleet_name in fleets:
                raise ValueError('Cannot add a duplicate fleet {:s}'.format(fleet_name))

            # Otherwise, extract the dictionary
            fleet_dict = fleet_data[fleet_name]

            # Read in the portsmouth table for the fleet
            with open(self._data_file(fleet_dict['portsmouth_table']), 'r') as table_handle:
                boat_table = table_handle.read()

            # Define the fleet object
            fleets[fleet_name] = bdb.Fleet(
                name=fleet_name,
                boat_types=bdb.BoatType.load_from_csv(boat_table))

        # Set the fleet object to the loaded parameters
        self.fleets = fleets

    def _load_skippers(self):
        """
        Loads the skipper database from the provided files
        """
        # Read in the skipper object and load the CSV parameters
        with open(self._data_file(self.skipper_input_name), 'r') as skipper_handle:
            skippers = sdb.Skipper.load_from_csv(skipper_handle.read())
        # Set the skipper object to the loaded parameters
        self.skippers = skippers

    def _load_series(self):
        """
        Loads the series database from the provided files
        """
        # Initialize the series dictionary
        series_values = dict()

        # Read in the series YAML data
        with open(self._data_file(self.series_input_name), 'r') as f:
            series_data = yaml.safe_load(f)

        # Iterate over the series name
        for series_name in series_data:
            # Raise an error if the series name already exists
            if series_name in series_values:
                raise ValueError('Cannot add a duplicate series {:s}'.format(series_name))

            # Extract the series dictionary
            s = series_data[series_name]

            # Extract the fleet name, raising an error if it doesn't exist, and extract the fleet if it does
            fleet_name = s['fleet']
            if fleet_name not in self.fleets:
                raise ValueError('Fleet {:s} does not exist in fleet structure'.format(fleet_name))
            fleet = self.fleets[fleet_name]

            # Extract boat override parameters
            boat_overrides = s['boat_overrides']

            # Define the series object
            series = rdb.Series(
                name=series_name,
                qualify_count=s['qualify_count'],
                fleet=fleet,
                boat_overrides=boat_overrides)

            # Load in the race data YAML object from the provided file
            with open(self._data_file(s['race_file']), 'r') as f:
                race_data = yaml.safe_load(f)

            # Iterate over each race date
            for race_date_dict in race_data:
                # Extract the race committee
                race_committee = [self.skippers[person] for person in race_date_dict['rc']]

                # Iterate over each race
                for race_dict in race_date_dict['races']:
                    # Create the race object
                    race = rdb.Race(
                        series=series,
                        rc=race_committee,
                        date=race_date_dict['date'],
                        wind_bf=race_dict['wind_bf'],
                        notes=race_dict['notes'])

                    # Extract the race time results
                    time_values = race_dict['times']

                    # Set an empty list of no time values are provided
                    if time_values is None:
                        time_values = list()

                    # Iterate over each of the skipper time values, creating a race time and adding it to the race
                    for skipper_id in time_values:
                        time_result = time_values[skipper_id]
                        other_result_type = None
                        if type(time_result) is str:
                            other_result_type = rdb.RaceTime.RaceFinishOther[time_result.strip().upper()]
                            time_result = 0

                        race_time = rdb.RaceTime(
                            race=race,
                            skipper=self.skippers[skipper_id],
                            time_s=time_result,
                            other_finish=other_result_type)
                        race.add_skipper_time(race_time)

                    # Add the race to the series
                    series.add_race(race)

            # Set the series value to the loaded parameters
            series_values[series_name] = series

        # Set the series object to the loaded parameters
        self.series = series_values
