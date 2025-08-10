"""
Provides the implementation for a did-not-finish race finish
"""

from ...skippers import Skipper
from ...fleets import BoatType

from .interface import RaceFinishInterface

from typing import Union


class RaceFinishDNS(RaceFinishInterface):
    """
    A class to define the database parameters for a DNS finish
    """

    def __init__(
            self,
            boat: BoatType,
            skipper: Skipper):
        """
        Defines a race finish for the Did-Not-Start race type
        :param boat: the boat for the skipper
        :param skipper: the associated skipper
        """
        super().__init__(
            boat=boat,
            skipper=skipper)

    def name(self) -> str:
        """
        Provides the DNS finish string
        :return: the string "DNS"
        """
        return 'DNS'

    def finished(self) -> bool:
        """
        Function to determine if a skipper is considered finished for a race
        :return: True if the race can be considered finished
        """
        return False

    def started(self) -> bool:
        return False

    def perl_entry(self) -> Union[int, str]:
        """
        Provides the resulting finish value for a given finish
        """
        return "DNS"
