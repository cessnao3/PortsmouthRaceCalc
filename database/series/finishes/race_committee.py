"""
Provides the race finish for race committee
"""

from ...skippers import Skipper
from ...fleets import BoatType

from .interface import RaceFinishInterface

from typing import Union


class RaceFinishRC(RaceFinishInterface):
    """
    A class to define the database parameters for the race committee finish
    """

    def __init__(
            self,
            boat: BoatType,
            skipper: Skipper):
        """
        Defines a race-committee finish for the skipper
        :param boat: the boat for the skipper
        :param skipper: the associated skipper
        """
        super().__init__(
            boat=boat,
            skipper=skipper)

    def name(self) -> str:
        """
        Provides the RC finish string
        :return: the string "RC"
        """
        return 'RC'

    def finished(self) -> bool:
        """
        Function to determine if a skipper is considered finished for a race
        :return: True if the race can be considered finished
        """
        return True

    def perl_entry(self) -> Union[int, str]:
        """
        Provides the resulting finish value for a given finish
        """
        raise RuntimeError("RC does not have a Perl equivalent")
