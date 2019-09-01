"""
Database and type to hold information regarding the boat parameters and handicap values
"""

import race_utils


class Skipper:
    def __init__(self, identifier, first=None, last=None, default_boat=None):
        """
        Defines a skipper object used in the race
        :param identifier: identification string used to match a skipper object with race performance
        :type identifier: str
        :param first: first name of the skipper
        :type first: str
        :param last: last name of the skipper
        :type last: str
        :param default_boat: default boat code for the skipper
        :type default_boat: str
        """
        self.identifier = identifier
        self.first = first
        self.last = last
        self.default_boat_code = default_boat

    @staticmethod
    def load_from_csv(csv_table):
        """
        Loads the skippers from a
        :param csv_table: CSV file contents
        :type csv_table: str
        :return: dictionary, by name_code, of skippers in the CSV file
        """
        # Initialize the skipper database
        skippers = dict()

        # Define an empty parameter for the header columns
        expected_header = ['identifier', 'first_name', 'last_name', 'default_boat']

        # Define a None-if-empty function
        def none_if_empty(s):
            return s if len(s) > 0 else None

        # Define the skipper row function
        def skipper_row_func(row_dict):
            identifier = none_if_empty(row_dict['identifier'])
            first = none_if_empty(row_dict['first_name'])
            last = none_if_empty(row_dict['last_name'])
            default_boat = none_if_empty(row_dict['default_boat'])

            if identifier is None:
                raise ValueError('Cannot add a skipper without an identifier')
            elif identifier in skippers:
                raise ValueError('Skipper {:s} cannot be added twice in the database'.format(identifier))
            else:
                skippers[identifier] = Skipper(
                    identifier=identifier,
                    first=first,
                    last=last,
                    default_boat=default_boat)

        # Load the file
        race_utils.load_from_csv(
            csv_data=csv_table,
            row_func=skipper_row_func,
            expected_header=expected_header)

        # Return the skippers
        return skippers
