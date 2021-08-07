"""
Provides the interface for race finishing information
"""

from ...skippers import Skipper
from ...fleets import BoatType


class RaceFinishInterface:
    """
    Defines a common interface to race finish types
    """

    def __init__(
            self,
            boat: BoatType,
            skipper: Skipper):
        """
        Saves common parameters to all race finishes
        :param boat: the boat for the skipper
        :param skipper: the associated skipper
        """
        # Save Values
        self.boat = boat
        self.skipper = skipper

    def finished(self) -> bool:
        """
        Function to determine if a skipper is considered finished for a race
        :return: True if the race can be considered finished
        """
        raise NotImplementedError()

    def name(self) -> str:
        """
        The associated name for the race finish type
        :return: a string for the given race finish type
        """
        raise NotImplementedError()

    def reset(self) -> None:
        """
        Resets any stored parameters associated with the current race interface
        """
        pass
