"""
Provides the interface for race finishing information
"""

from skipper_database import Skipper
from boat_database import BoatType


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
            self._corrected_time_s = round(self.time_s * 100.0 / self.boat.dpn_for_beaufort(self.wind_bf))
        return self._corrected_time_s
