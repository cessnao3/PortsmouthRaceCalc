"""
Parses input files into Python object to parse race information
"""

import boat_database as boat_db
import skipper_database as skipper_db
import race_database as race_db
import series_database as series_db
import race_finishes

import datetime
import pathlib
import typing
import yaml


class MasterDatabase:
    """
    Master database to keep track of all input parameters
    """
    input_folder = pathlib.Path('input')

    fleet_input_name = 'fleets.yaml'
    skipper_input_name = 'skippers.csv'
    series_input_name = 'series.yaml'

    @property
    def fleet_file(self) -> pathlib.Path:
        """
        :return: the fleet file
        """
        return self.input_folder / self.fleet_input_name

    @property
    def skipper_file(self) -> pathlib.Path:
        """
        :return: the skipper file
        """
        return self.input_folder / self.skipper_input_name

    @property
    def series_file(self) -> pathlib.Path:
        """
        :return: the series master file
        """
        return self.input_folder / self.series_input_name

    def __init__(self,
                 input_folder: pathlib.Path = None,
                 fleet_file: str = None,
                 skipper_file: str = None,
                 series_file: str = None):
        """
        Initializes the master database with the provided inputs
        :param input_folder: folder where the input files are provided
        :param fleet_file: filename to override the fleet input file
        :param skipper_file: filename to override the skipper input file
        :param series_file: filename to override the series input file
        """
        # Handle override parameter inputs
        if input_folder is not None:
            self.input_folder = input_folder
        if fleet_file is not None:
            self.fleet_input_name = fleet_file
        if skipper_file is not None:
            self.skipper_input_name = skipper_file
        if series_file is not None:
            self.series_input_name = series_file

        # Load the database
        self.fleets = self._load_fleets()
        self.skippers = self._load_skippers()
        self.series = self._load_series()

    def latest_race_date(self) -> typing.Optional[datetime.datetime]:
        """
        Provides the latest race time
        :return: the latest race time in all series
        """
        latest = None

        for s in self.series.values():
            series_date = s.latest_race_date()
            if series_date is None:
                continue
            elif latest is None or latest < series_date:
                latest = series_date

        return latest

    def latest_race_date_string(self) -> str:
        """
        Provides a string associated with the latest race date
        :return: string for the latest race date in the database
        """
        date = self.latest_race_date()
        if date is None:
            return 'Unknown'
        else:
            return date.strftime('%B %d, %Y')

    def _load_fleets(self) -> typing.Dict[str, boat_db.Fleet]:
        """
        Loads the fleet database from the provided files
        :return: the list of fleets loaded
        """
        # Read the YAML input file
        with self.fleet_file.open('r') as fleet_handle:
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
            portsmouth_file = self.input_folder / fleet_dict['portsmouth_table']
            with portsmouth_file.open('r') as table_handle:
                boat_table = table_handle.read()

            # Obtain the wind mapping
            wind_map_dict = fleet_dict['wind_map']
            wind_map = boat_db.WindMap(default_index=wind_map_dict['default_index'])
            for map_val in wind_map_dict['map_values']:
                wind_map.add_wind_parameters(
                    start_wind=map_val['start_bf'],
                    end_wind=map_val['end_bf'],
                    index=map_val['index'])

            # Define the fleet object
            fleets[fleet_name] = boat_db.Fleet(
                name=fleet_name,
                boat_types=boat_db.BoatType.load_from_csv(boat_table, fleet=None),
                wind_map=wind_map,
                source=fleet_dict['source'] if 'source' in fleet_dict else None)

        # Set the fleet object to the loaded parameters
        return fleets

    def _load_skippers(self) -> typing.Dict[str, skipper_db.Skipper]:
        """
        Loads the skipper database from the provided files
        """
        # Read in the skipper object and load the CSV parameters
        with self.skipper_file.open('r') as skipper_handle:
            skippers = skipper_db.Skipper.load_from_csv(skipper_handle.read())

        # Set the skipper object to the loaded parameters
        return skippers

    def _load_series(self) -> typing.Dict[str, series_db.Series]:
        """
        Loads the series database from the provided files
        """
        # Initialize the series dictionary
        series_values = dict()

        # Read in the series YAML data
        with self.series_file.open('r') as f:
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

            # Define the qualify count overrides
            if 'qualify_count' in series_data:
                qualify_count_override = series_data['qualify_count']
            else:
                qualify_count_override = None

            # Define the series object
            series = series_db.Series(
                name=series_name,
                valid_required_skippers=s['valid_required_skippers'],
                fleet=fleet,
                qualify_count_override=qualify_count_override)

            # Look for a series offset time
            series_offset_time = 0
            if 'offset_time' in s:
                series_offset_time = s['offset_time']

            # Load in the race data YAML object from the provided file
            race_file = self.input_folder / s['race_file']
            with race_file.open('r') as f:
                all_race_data = yaml.safe_load(f)

            # Extract the boat data and set default boats for each skipper
            boat_list = all_race_data['boats']
            for skipper_id, boat_code in boat_list.items():
                series.add_skipper_boat(
                    skipper=self.skippers[skipper_id],
                    boat=series.fleet.get_boat(boat_code))

            # Extract the race data
            race_list = all_race_data['races']

            # Iterate over each race date
            for race_date_dict in race_list:
                # Extract the race committee
                race_committee = [self.skippers[person] for person in race_date_dict['rc']]

                # Iterate over each race
                for race_dict in race_date_dict['races']:
                    # Define the race boat dictionary
                    race_boat_dict = dict(series.boat_dict)

                    if 'boat_overrides' in race_dict:
                        # Extract the race boat overrides
                        race_boat_overrides = race_dict['boat_overrides']

                        # Update the values based on the skipper identifiers provided
                        for skipper_id, boat_code in race_boat_overrides.items():
                            skip = self.skippers[skipper_id]
                            if skip in race_boat_dict:
                                race_boat_dict[skip] = series.fleet.get_boat(boat_code)

                    # Create the race object
                    race = race_db.Race(
                        fleet=series.fleet,
                        boat_dict=race_boat_dict,
                        required_skippers=series.valid_required_skippers,
                        rc=race_committee,
                        date_string=race_date_dict['date'],
                        wind_bf=race_dict['wind_bf'],
                        notes=race_dict['notes'])

                    # Extract the race time results
                    time_values = race_dict['times']

                    # Define the override time
                    offset_time = series_offset_time
                    if 'offset_time' in race_dict:
                        offset_time = race_dict['offset_time']

                    # Set an empty list of no time values are provided
                    if time_values is None:
                        time_values = list()

                    # Iterate over each of the skipper time values, creating a race time and adding it to the race
                    for skipper_id in time_values:
                        # Extract the time result
                        input_finish_result = time_values[skipper_id]

                        # Extract the skipper and boat
                        skipper = self.skippers[skipper_id]

                        if skipper in race.boat_dict:
                            boat = race.boat_dict[skipper]
                        else:
                            raise ValueError(f'unknown boat provided for skipper {skipper.identifier}')

                        # Check for other race types
                        if isinstance(input_finish_result, str):
                            # Define the lowercase values
                            input_finish_result = input_finish_result.lower()

                            # Check for finish in place
                            if input_finish_result == 'dnf':
                                race_finish = race_finishes.RaceFinishDNF(boat=boat, skipper=skipper)
                            elif input_finish_result == 'dq':
                                race_finish = race_finishes.RaceFinishDQ(boat=boat, skipper=skipper)
                            elif input_finish_result[:3] == 'fip':
                                race_finish = race_finishes.RaceFinishFIP(
                                    boat=boat,
                                    skipper=skipper,
                                    place=int(input_finish_result[3:]))
                            else:
                                raise ValueError(f'unknown race finish type "{input_finish_result}"')
                        elif isinstance(input_finish_result, int):
                            race_finish = race_finishes.RaceFinishTime(
                                boat=race.boat_dict[skipper],
                                skipper=skipper,
                                wind_bf=race.wind_bf,
                                input_time_s=input_finish_result,
                                offset_time_s=offset_time)
                        else:
                            raise ValueError('unknown finish time provided')

                        # Add the resulting race finish
                        race.add_skipper_finish(race_finish)

                    # Add the race to the series
                    series.add_race(race)

            # Reset the series to update values
            series.reset()

            # Set the series value to the loaded parameters
            series_values[series_name] = series

        # Set the series object to the loaded parameters
        return series_values
