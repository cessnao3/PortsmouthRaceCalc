"""
Provides the definition for a disqualification
"""

from ...skippers import Skipper
from ...fleets import BoatType

from .interface import RaceFinishInterface


class RaceFinishDQ(RaceFinishInterface):
    """
    A class to define the database parameters for a disqualification finish
    """

    def __init__(
            self,
            boat: BoatType,
            skipper: Skipper):
        """
        Defines the disqualification race finish
        :param boat: the boat for the skipper
        :param skipper: the associated skipper
        """
        super().__init__(
            boat=boat,
            skipper=skipper)

    def name(self) -> str:
        """
        The disqualification string
        :return: the string 'DQ'
        """
        return 'DQ'

    def finished(self) -> bool:
        """
        Function to determine if a skipper is considered finished for a race
        :return: True if the race can be considered finished
        """
        return False
