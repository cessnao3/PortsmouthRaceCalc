"""
Provides the implementation for a did-not-finish race finish
"""

from ...skippers import Skipper
from ...fleets import BoatType

from .interface import RaceFinishInterface


class RaceFinishDNF(RaceFinishInterface):
    """
    A class to define the database parameters for a DNF finish
    """

    def __init__(
            self,
            boat: BoatType,
            skipper: Skipper):
        """
        Defines a race finish for the Did-Not-Finish race type
        :param boat: the boat for the skipper
        :param skipper: the associated skipper
        """
        super().__init__(
            boat=boat,
            skipper=skipper)

    def name(self) -> str:
        """
        Provides the DNF finish string
        :return: the string "DNF"
        """
        return 'DNF'

    def finished(self) -> bool:
        """
        Function to determine if a skipper is considered finished for a race
        :return: True if the race can be considered finished
        """
        return False
