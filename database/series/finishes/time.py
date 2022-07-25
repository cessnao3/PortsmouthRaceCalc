"""
Provides the implementation for a race finish with a recorded time
"""

from ...skippers import Skipper
from ...fleets import BoatType

from .interface import RaceFinishInterface

from typing import Union


class RaceFinishTime(RaceFinishInterface):
    """
    A class to define the database parameters for the race time
    """

    def __init__(self,
                 boat: BoatType,
                 skipper: Skipper,
                 wind_bf: int,
                 input_time_s: int,
                 offset_time_s: int,
                 ):
        """
        Initializes the race time object with the input parameters
        :param boat: the boat database to use
        :param skipper: skipper to associate the result with
        :param input_time_s: raw time, in seconds, of the result, or one of the other RaceFinishOther types
        :param offset_time_s: offset time, in seconds, to subtract from the input time
        """
        # Initialize the super class
        super().__init__(
            boat=boat,
            skipper=skipper)

        # Save the boat and wind
        self.boat = boat
        self.wind_bf = wind_bf

        # Initialize the race parameters
        self.input_time_s = input_time_s
        self.offset_time_s = offset_time_s

        # Initialize memoization parameters
        self._corrected_time_s = None

    def name(self) -> str:
        """
        Provides the name for the time value
        :return: the string "Time"
        """
        return 'Time'

    @property
    def time_s(self) -> int:
        """
        Provides the elapsed time for the skipper's race
        :return: the time in seconds of the race, not including any offset time
        """
        return self.input_time_s - self.offset_time_s

    def reset(self) -> None:
        """
        Resets any stored calculated parameters
        """
        self._corrected_time_s = None

    def finished(self) -> bool:
        """
        Function to determine if a skipper is considered finished for a race
        :return: True if the race can be considered finished
        """
        return True

    @property
    def corrected_time_s(self) -> int:
        """
        Calculates the corrected time from the beaufort DPN value, and rounds the result
        :return: rounded corrected time in seconds with the provided boat and wind speed
        """
        if self._corrected_time_s is None:
            self._corrected_time_s = round(self.time_s * 100.0 / self.boat.dpn_for_beaufort(self.wind_bf).value())
        return self._corrected_time_s

    def perl_entry(self) -> Union[int, str]:
        """
        Provides the resulting finish value for a given finish
        """
        min_val = self.time_s // 60
        sec_val = self.time_s % 60

        if min_val > 0 or sec_val > 0:
            return f"{min_val:02d}:{sec_val:02d}"
        else:
            return 0
