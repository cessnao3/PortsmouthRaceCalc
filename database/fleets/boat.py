"""
Provides a class to maintain an instance of a particular boat within a fleet
"""

from typing import Dict, List, Tuple

from .. import utils

from .handicap import HandicapNumber
from .wind_map import WindMap


class BoatType:
    """
    A class to contain the necessary information to construct a boat type for
    Portsmouth Handicap race parameters
    """

    def __init__(
            self,
            name: str,
            fleet_name: str,
            boat_class: str,
            code: str,
            display_code: str,
            dpn_values: List[HandicapNumber],
            wind_map: WindMap):
        """
        Initializes the boat parameter
        :param name: The name of the boat
        :param fleet_name: The name of the fleet the boat is associated with
        :param boat_class: The class of the boat
        :param code: The unique identification code for the given boat class
        :param display_code: Defines the display version of the boat code results
        :param dpn_values: A list of 5 values, identifying [DPN0, DPN1, DPN2, DPN3, DPN4]
        :param wind_map: The wind map to use for obtaining DPN values
        """
        self.name = name
        self.fleet_name = fleet_name
        self.boat_class = boat_class.lower()
        self.code = code
        self.display_code = display_code
        self.dpn_values = dpn_values
        self.wind_map = wind_map
        self.__mem_characteristic_tuple = None

    def needs_handicap_note(self) -> bool:
        """
        Returns true if the note on handicap types is required
        :return: True if any DPN value is not "standard" and may be suspect
        """
        for dpn in self.dpn_values:
            if dpn is None:
                continue
            elif dpn.get_type() != HandicapNumber.HandicapType.STANDARD:
                return True
        return False

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
        dpn_val = self.dpn_values[dpn_ind]
        if dpn_val is None:
            print(f"No HC found for {self.code}/{self.name} from {self.fleet_name} for BF={beaufort} - using default DPN value")
            dpn_val = self.dpn_values[0]

        # Return the DPN value
        return dpn_val

    def __characteristic_tuple(self) -> Tuple[str, str, str, str]:
        """
        Provides a tuple that may be used for internal functions for determining
        equality and hash results
        :return: the characteristic tuple of the boat
        """
        if self.__mem_characteristic_tuple is None:
            self.__mem_characteristic_tuple = self.name, self.fleet_name, self.boat_class, self.code
        return self.__mem_characteristic_tuple

    def __eq__(self, other) -> bool:
        """
        Determines whether the provided object is equal to the current boat class object
        :return: true if the objects are equal
        """
        if isinstance(other, BoatType):
            return self.__characteristic_tuple() == other.__characteristic_tuple()
        else:
            return False

    def __hash__(self) -> int:
        """
        Provides the hash result for the current boat type
        :return: the hash result for the boat
        """
        return hash(self.__characteristic_tuple())

    @staticmethod
    def load_from_csv(
            csv_table: str,
            fleet_name: str,
            wind_map: WindMap) -> Dict[str, 'BoatType']:
        """
        Reads the Portsmouth pre-calculated table from an input CSV file contents
        :param csv_table: The filename to read
        :param fleet_name: The fleet name to associate boats with
        :param wind_map: A wind_map to associate the boat type to
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
            boat_code = row_dict['code'].lower().replace('/', '_')
            boat_display_code = row_dict['code']

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
                    fleet_name=fleet_name,
                    boat_class=boat_class,
                    code=boat_code,
                    display_code=boat_display_code,
                    dpn_values=dpn_values,
                    wind_map=wind_map)

        # Call the CSV load function
        utils.load_from_csv(
            csv_data=csv_table,
            row_func=boat_row_func,
            expected_header=expected_header)

        return boats
