"""
Database and type to hold information regarding the boat parameters and handicap values
"""

import enum
import race_utils


class Fleet:
    """
    A class to contain the boats specified for a given fleet, allowing for different generations
    of handicap parameters
    """
    def __init__(self, name, boat_types):
        self.name = name
        self.boat_types = boat_types


class BoatType:
    """
    A class to contain the necessary information to construct a boat type for
    Portsmouth Handicap race parameters
    """
    class BoatClass(enum.Enum):
        """
        Definitions for the class of boat
        """
        UNKNOWN = 0
        CENTERBOARD = 1
        KEELBOAT = 2

    def __init__(self, name, boat_class, code, dpn_vals):
        """
        Initializes the boat parameter
        :param name: The name of the boat
        :type name: str
        :param boat_class: The class of the boat, of type
        :type boat_class: BoatType.BoatClass
        :param code: The unique identification code for the given boat class
        :type code: str
        :param dpn_vals: A list of 5 values, identifying [DPN0, DPN1, DPN2, DPN3, DPN4]
        :type dpn_vals: list of float
        """
        self.name = name
        self.boat_class = boat_class
        self.code = code
        self.dpn_vals = dpn_vals

    def dpn_for_beaufort(self, beaufort):
        """
        Provides the DPN value associated with the input beaufort number. If the boat type doesn't have a specified DPN
        for the provided beaufort number, the highest value that will satisfty the requirements will be returned.
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

        # If there is no number specified (None), reduce the index and try again. Failsafe stop at index 0
        while self.dpn_vals[dpn_ind] is None and dpn_ind > 0:
            dpn_ind -= 1

        # If there is no DPN value at any index, raise an error
        if self.dpn_vals[dpn_ind] is None:
            raise RuntimeError('No DPN provided for code {:s}, index {:d}'.format(self.code, dpn_ind))

        # Return the DPN value
        return self.dpn_vals[dpn_ind]

    @staticmethod
    def load_from_csv(csv_table):
        """
        Reads the Portsmouth precalculated table from an input CSV file contents
        :param csv_table: The filename to read
        :type csv_table: str
        :return: A dictionary of boats, keyed by the type code
        """
        # Initialize the empty dictionary
        boats = dict()
        expected_header = ['boat', 'class', 'code', 'dpn', 'dpn1', 'dpn2', 'dpn3', 'dpn4']

        # Create a function to extract the parameters
        def dpn_to_float(s):
            # Clear out parenthesis and bracket characters
            chars_to_remove = ('(', ')', '[', ']')
            for c in chars_to_remove:
                s = s.replace(c, '')
            s = s.strip()

            # Return None if the length is 0 (no remaining characters)
            if len(s) == 0:
                return None
            # Otherwise, return the float value of the string
            else:
                return float(s)

        def boat_row_func(row_dict):
            # Extract the boat class from the input parameters
            if row_dict['class'].lower() == 'centerboard':
                boat_class = BoatType.BoatClass.CENTERBOARD
            elif row_dict['class'].lower() == 'keelboat':
                boat_class = BoatType.BoatClass.KEELBOAT
            else:
                print('Unknown boat class {:s}'.format(row_dict['class']))
                boat_class = BoatType.BoatClass.UNKNOWN

            # Extract the DPN values, both the initial and Beaufort values
            dpn_values = [dpn_to_float(row_dict['dpn'])]
            dpn_values += [dpn_to_float(row_dict['dpn{:d}'.format(i + 1)]) for i in range(4)]

            # Extract the name and code
            boat_name = row_dict['boat']
            boat_code = row_dict['code'].lower()

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
                    dpn_vals=dpn_values)

        # Call the CSV load function
        race_utils.load_from_csv(
            csv_data=csv_table,
            row_func=boat_row_func,
            expected_header=expected_header)

        return boats
