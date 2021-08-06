"""
Database and type to hold information regarding the boat parameters and handicap values
"""

import enum
import typing

import race_utils


class WindMap:
    """
    A class to map Beaufort wind numbers to an index that can be used to extract DPN
    or similar time correction factors
    """
    class Node:
        """
        A class to keep track of the wind map node parameters
        """
        def __init__(self, start_bf: int, end_bf: int, index: int):
            """
            Defines the wind map node
            :param start_bf: starting Beaufort number for wind (inclusive)
            :param end_bf: ending Beaufort number for wind (inclusive)
            :param index: index to obtain for the given wind values
            """
            # Check for type errors
            for v in (start_bf, end_bf, index):
                if type(v) != int:
                    raise TypeError('All types input into WindMap.Node must be of type int')

            # Check that start <= end
            if start_bf > end_bf:
                raise ValueError('Wind mapping start {:d} must be <= end {:d}'.format(start_bf, end_bf))

            # Save the parameters
            self.start_bf = start_bf
            self.end_bf = end_bf
            self.index = index

        def range_str(self) -> str:
            """
            Provides the range string for the given wind mapping
            :return: definitions for the range of the mapping
            :rtype: str
            """
            if self.start_bf == self.end_bf:
                return '{:d}'.format(self.start_bf)
            else:
                return '{:d}-{:d}'.format(self.start_bf, self.end_bf)

    def __init__(self, default_index: int):
        """
        Initializes the Wind Map with a default index
        :param default_index: Default index to use if no other wind mapping parameters fit
        """
        # Create the default index
        self.default = self.Node(
            start_bf=0,
            end_bf=0,
            index=default_index)
        # Initialize the empty wind map list
        self.wind_maps = list()

    def add_wind_parameters(self, start_wind: int, end_wind: int, index: int) -> None:
        """
        Adds a wind mapping for a start/end wind speed, with an index
        Raises an error if the mapping overlaps with another
        :param start_wind: starting Beaufort number
        :param end_wind: ending Beaufort number
        :param index: index to associate with the Beaufort number
        """
        # Iterate over all of the wind parameters to ensure that there are no overlaps
        for w in self.wind_maps:
            for v in (start_wind, end_wind):
                if w.start_bf <= v <= w.end_bf:
                    raise ValueError('WindMap parameter {:d} within the range of another map'.format(v))

        # Add the wind map parameter
        self.wind_maps.append(
            self.Node(
                start_bf=start_wind,
                end_bf=end_wind,
                index=index))
        self.wind_maps.sort(key=lambda x: x.start_bf)

    def get_wind_map_for_beaufort(self, bf_num: int) -> 'Node':
        """
        Provides the wind mapping node for the input Beaufort number
        :param bf_num: Input Beaufort number to find a mapping for
        :return: associated mapping for the node
        :rtype: WindMap.Node
        """
        for w in self.wind_maps:
            if w.start_bf <= bf_num <= w.end_bf:
                return w
        return self.default


class HandicapNumber:
    """
    A class to maintain handicap data information
    """
    class HandicapType(enum.Enum):
        """
        Defines the type of the handicap pedigree
        """
        STANDARD = 0
        SUSPECT = 1
        HIGHLY_SUSPECT = 2

    def __init__(
            self,
            value: float,
            handicap_type: 'HandicapNumber.HandicapType'):
        """
        Initializes the handicap based on the input values
        :param value: the actual numeric value, with 100 being unity, for the handicap
        :param handicap_type: the pedigree type for the handicap number
        """
        self._value = value
        self._handicap_type = handicap_type

    def _surround_with_correct_brackets(self, val: str) -> str:
        """
        Provides means to provide brackets around a handicap value
        :param val: the value string to wrap in parenthesis or brackets, based on pedigree
        :return: the formatted string
        """
        if self._handicap_type == self.HandicapType.STANDARD:
            pass
        elif self._handicap_type == self.HandicapType.SUSPECT:
            val = f'({val})'
        elif self._handicap_type == self.HandicapType.HIGHLY_SUSPECT:
            val = f'[{val}]'
        else:
            raise ValueError('unknown bracket type provided')
        return val

    def __str__(self) -> str:
        """
        Provides the base string of the handicap type
        :return: the resulting handicap string, surrounded by brackets if necessary
        """
        return self._surround_with_correct_brackets(f'{self._value:0.03f}')

    def value(self) -> float:
        """
        Provides the base handicap value
        :return: the handicap value
        """
        return self._value

    def handicap_number(self) -> float:
        """
        Provides the handicap number, or the value divided by 100
        :return: the handicap number
        """
        return self._value / 100.0

    def handicap_string(self) -> str:
        """
        Provides the string result for the handicap number
        :return: the string result, surrounded in brackets if necessary, for the handicap number
        """
        return self._surround_with_correct_brackets(f'{self.handicap_number():0.05f}')

    @staticmethod
    def from_string(value: str) -> 'HandicapNumber':
        # Check that the string is valid
        if len(value) == 0:
            raise ValueError('No valid string found')

        # Handicap Type
        handicap_type = HandicapNumber.HandicapType.STANDARD

        # Clear out parenthesis and bracket characters
        if value[0] == '(':
            if value[-1] != ')':
                raise ValueError('did not find matching closing parenthesis )')
            else:
                value = value[1:-1]
                handicap_type = HandicapNumber.HandicapType.SUSPECT
        elif value[0] == '[':
            if value[-1] != ']':
                raise ValueError('did not find matching closing bracket ]')
            else:
                value = value[1:-1]
                handicap_type = HandicapNumber.HandicapType.HIGHLY_SUSPECT

        # Create the handicap number
        return HandicapNumber(
            value=float(value),
            handicap_type=handicap_type)


class Fleet:
    """
    A class to contain the boats specified for a given fleet, allowing for different generations
    of handicap parameters
    """
    def __init__(
            self,
            name: str,
            boat_types: typing.Dict[str, 'BoatType'],
            wind_map: 'WindMap',
            source: typing.Optional[str]):
        """
        Initializes the fleet with the input parameters
        :param name: The name of the fleet
        :param boat_types: List of the boat types within the fleet
        :param wind_map: A wind map to correlate Beaufort numbers to DPN indices
        :param source: A string indicating the source of the information
        """
        self.name = name
        self.boat_types = boat_types
        self.wind_map = wind_map
        self.source = source

        # Set the boat fleet
        for b in self.boat_types.values():
            b.fleet = self

    def boat_types_sorted(self) -> typing.List['BoatType']:
        """
        Returns a list of sorted boats
        :return: list of BoatType
        """
        boat_list = [b for b in self.boat_types.values()]
        boat_list.sort(key=lambda x: x.code)
        return boat_list

    def get_boat(self, boat_code: str) -> typing.Optional['BoatType']:
        """
        Attempts to find the boat associated with the given boat code. Returns None if no boat exists
        :param boat_code: The input string to check for a boat type. This will be lower-cased
        :return: the boat, if provided. Otherwise, None
        """
        if boat_code.lower() in self.boat_types:
            return self.boat_types[boat_code.lower()]
        else:
            return None

    def dpn_len(self) -> int:
        """
        Provides the maximum number of DPN values for each boat
        :return: the maximum number of DPN values
        """
        max_len = 0
        for b in self.boat_types.values():
            max_len = max(max_len, len(b.dpn_values))
        return max_len

    def fancy_name(self) -> str:
        """
        Provides the fancy name, removing underscores for spaces and capitalizing
        :return: fancy name string
        """
        return race_utils.capitalize_words(self.name.replace('_', ' '))


class BoatType:
    """
    A class to contain the necessary information to construct a boat type for
    Portsmouth Handicap race parameters
    """

    def __init__(self, name: str, boat_class: str, code: str, dpn_values: typing.List[HandicapNumber], fleet: Fleet):
        """
        Initializes the boat parameter
        :param name: The name of the boat
        :param boat_class: The class of the boat
        :param code: The unique identification code for the given boat class
        :param dpn_values: A list of 5 values, identifying [DPN0, DPN1, DPN2, DPN3, DPN4]
        :param fleet: A fleet to associate the boat type to
        """
        self.name = name
        self.boat_class = boat_class.lower()
        self.code = code
        self.dpn_values = dpn_values
        self.fleet = fleet

    def dpn_for_beaufort(self, beaufort: int) -> HandicapNumber:
        """
        Provides the DPN value associated with the input beaufort number. If the boat type doesn't have a specified DPN
        for the provided beaufort number, the highest value that will satisfy the requirements will be returned.
        :param beaufort: The input Beaufort number
        :type beaufort: int
        :return: The DPN value associated with the given beaufort number, or the highest possible DPN index <= beaufort
        """
        # Ensure that the beaufort number is an integer
        if type(beaufort) != int:
            raise ValueError('Beaufort number must be of type int')

        # Wind Map Node
        dpn_val = None
        current_bf = beaufort

        while dpn_val is None and current_bf >= 0:
            node_val = self.fleet.wind_map.get_wind_map_for_beaufort(current_bf)
            dpn_val = self.dpn_values[node_val.index]
            current_bf -= 1

        # Find the ideal index for the given beaufort number
        if beaufort <= 1:
            dpn_ind = 1
        elif beaufort <= 3:
            dpn_ind = 2
        elif beaufort <= 4:
            dpn_ind = 3
        else:
            dpn_ind = 4

        # If there is no DPN value at any index, raise an error
        if dpn_val is None:
            raise RuntimeError('No DPN provided for code {:s}, index {:d}'.format(self.code, dpn_ind))

        # Return the DPN value
        return self.dpn_values[dpn_ind]

    @staticmethod
    def load_from_csv(csv_table: str, fleet: typing.Optional[Fleet]) -> typing.Dict[str, 'BoatType']:
        """
        Reads the Portsmouth pre-calculated table from an input CSV file contents
        :param csv_table: The filename to read
        :param fleet: A fleet to associate the boat type to
        :return: A dictionary of boats, keyed by the type code
        """
        # Initialize the empty dictionary
        boats = dict()
        expected_header = ['boat', 'class', 'code', 'dpn', 'dpn1', 'dpn2', 'dpn3', 'dpn4']

        def boat_row_func(row_dict):
            # Extract the DPN values, both the initial and Beaufort values
            dpn_len = len([key for key in row_dict if key.startswith('dpn') and len(key) > len('dpn')])
            dpn_string_values = [row_dict['dpn']]
            dpn_string_values += [row_dict[f'dpn{i + 1}'] for i in range(dpn_len)]
            dpn_values = [HandicapNumber.from_string(v) if len(v) > 0 else None for v in dpn_string_values]

            # Extract the name and code
            boat_name = row_dict['boat']
            boat_code = row_dict['code'].lower()

            # Extract the boat class from the input parameters
            boat_class = row_dict['class'].lower()
            if row_dict['class'].lower() not in ('centerboard', 'keelboat'):
                print('Unknown boat class {:s} for {:s}'.format(boat_class, boat_name))
                boat_class = 'unknown'

            # Check that the primary DPN value is not null
            if dpn_values[0] is None:
                print('Skipping {:s} due to no provided DPN values'.format(boat_code))
            # Otherwise, there is a valid boat definition
            else:
                # Check that the boat code doesn't already exist in the dictionary
                if boat_code in boats:
                    raise ValueError('BoatType {:s} already in dictionary'.format(boat_code))

                # Create the boat object and set equal to the dictionary for the code
                boats[boat_code] = BoatType(
                    name=boat_name,
                    boat_class=boat_class,
                    code=boat_code,
                    dpn_values=dpn_values,
                    fleet=fleet)

        # Call the CSV load function
        race_utils.load_from_csv(
            csv_data=csv_table,
            row_func=boat_row_func,
            expected_header=expected_header)

        return boats
