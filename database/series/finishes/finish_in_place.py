"""
Provides the finish in place race type finish
"""

from ...skippers import Skipper
from ...fleets import BoatType

from .interface import RaceFinishInterface


class RaceFinishFIP(RaceFinishInterface):
    """
    A class to define the database parameters for a Finish-In-Place finish
    """

    def __init__(
            self,
            boat: BoatType,
            skipper: Skipper,
            place: int):
        """
        Defines a finish-in-place race finish
        :param boat: the boat for the skipper
        :param skipper: the associated skipper
        :param place: the place to mark as finishing
        """
        super().__init__(
            boat=boat,
            skipper=skipper)
        self.place = place

    def name(self) -> str:
        """
        Provides the string-name of the finish
        :return: the FIP string of the form FIP_<place>
        """
        return f'FIP_{self.place}'

    def finished(self) -> bool:
        """
        Function to determine if a skipper is considered finished for a race
        :return: True if the race can be considered finished
        """
        return True
