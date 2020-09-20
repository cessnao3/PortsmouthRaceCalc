"""
Database and type to hold information regarding the boat parameters and handicap values
"""

import race_utils

import typing


class Skipper:
    def __init__(self, identifier: str, first: str = None, last: str = None):
        """
        Defines a skipper object used in the race
        :param identifier: identification string used to match a skipper object with race performance
        :param first: first name of the skipper
        :param last: last name of the skipper
        """
        self.identifier = identifier
        self.first = first
        self.last = last

    @staticmethod
    def load_from_csv(csv_table: str) -> typing.Dict[str, 'Skipper']:
        """
        Loads the skippers from a
        :param csv_table: CSV file contents
        :return: dictionary, by name_code, of skippers in the CSV file
        """
        # Initialize the skipper database
        skippers = dict()

        # Define an empty parameter for the header columns
        expected_header = ['identifier', 'first_name', 'last_name']

        # Define a None-if-empty function
        def none_if_empty(s: str) -> typing.Union[None, str]:
            return s if len(s) > 0 else None

        # Define the skipper row function
        def skipper_row_func(row_dict: typing.Dict[str, str]) -> None:
            identifier = none_if_empty(row_dict['identifier'])
            first = none_if_empty(row_dict['first_name'])
            last = none_if_empty(row_dict['last_name'])

            if identifier is None:
                raise ValueError('Cannot add a skipper without an identifier')
            elif identifier in skippers:
                raise ValueError('Skipper {:s} cannot be added twice in the database'.format(identifier))
            else:
                skippers[identifier] = Skipper(
                    identifier=identifier,
                    first=first,
                    last=last)

        # Load the file
        race_utils.load_from_csv(
            csv_data=csv_table,
            row_func=skipper_row_func,
            expected_header=expected_header)

        # Return the skippers
        return skippers

    def __hash__(self) -> int:
        """
        Provides the identifier as the primary hash method
        :return: the hash of the skipper
        """
        return hash(self.identifier)

    def __eq__(self, other: typing.Any) -> bool:
        """
        Returns true if the other object is a Skipper and if this and the other object share the
        same parameter values
        :param other: the other Skipper object to compare against
        :return: True if the identifiers are equal in lower-case
        """
        if isinstance(other, Skipper):
            return \
                self.identifier == other.identifier and \
                self.first == other.first and \
                self.last == other.last
        else:
            return False
