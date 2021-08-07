"""
Provides functions to maintain handicapping information
"""

import enum


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

    def get_type(self) -> 'HandicapNumber.HandicapType':
        """
        Provides the current handicap type
        :return: the handicap type for the boat
        """
        return self._handicap_type

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
