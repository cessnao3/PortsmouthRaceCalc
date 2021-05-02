"""
Provides a database for use in calculating the corrected times for race parameters and scoring
"""

from boat_database import Fleet, BoatType
from skipper_database import Skipper
from race_utils import round_score, get_pyplot, figure_to_base64, format_time

import enum
import typing


class Race:
    """
    An object to maintain the information for a single race
    """
    def __init__(self,
                 fleet: Fleet,
                 boat_dict: typing.Dict[Skipper, BoatType],
                 required_skippers: int,
                 rc: typing.List[Skipper],
                 date: str,
                 wind_bf: int,
                 notes: str):
        """
        Initializes the race object
        :param fleet: the fleet to use for the boat handicap values
        :param boat_dict: the boat dictionary to use for finding default skipper boats
        :param required_skippers: the number of required skippers for the race to be considered valid
        :param rc: a list of the skipper objects participating in the race committee
        :param date: a string containing the date of the race in the format year_mm_dd
        :param wind_bf: the Beaufort wind condition number associated with the race
        :param notes: any additional notes about the race
        """
        self.race_times = dict()
        self.fleet = fleet
        self.boat_dict = boat_dict
        self.required_skippers = required_skippers
        self.date = date
        self.wind_bf = wind_bf
        self.notes = notes
        self._race_index = None
        self._results_dict = None
        self._race_plot = None

        # Add the RC skippers to the race times as participating in RC
        for rc_skipper in rc:
            self.add_skipper_time(RaceTime(
                race=self,
                skipper=rc_skipper,
                input_time_s=0,
                offset_time_s=0,
                other_finish=RaceTime.RaceFinishOther.RC))

    def reset(self) -> None:
        """
        Resets any stored calculated parameters
        """
        self._race_index = None
        for rt in self.race_times.values():
            rt.reset()
        self._results_dict = None

    def set_index(self, i: int) -> None:
        """
        Sets the index to the provided value
        :param i: Value to set the race index to
        """
        self._race_index = i

    @property
    def race_num(self) -> int:
        """
        Provides the 1's indexed race number
        :return: race index + 1
        """
        if self._race_index is not None:
            return self._race_index + 1
        else:
            return 0

    def min_time_s(self) -> typing.Union[None, int]:
        """
        Returns the minimum completion time
        :return: minimum completion time in seconds
        """
        valid_race_times = [rt.corrected_time_s for rt in self.race_times.values() if rt.finished_with_time()]

        if len(valid_race_times) >= 0:
            return min(valid_race_times)
        else:
            return None

    def valid(self) -> bool:
        """
        Determines if a race is valid or not
        :return: True if the race is valid, false otherwise
        """
        # Calculate the wind condition
        bf_condition = self.wind_bf is not None

        # Calculate the starting race times
        starting_race_times = [rt for rt in self.race_times.values() if not rt.is_rc()]
        num_condition = len(starting_race_times) >= self.required_skippers

        # Return true if all conditions are true
        return bf_condition and num_condition

    def valid_for_rc(self, skipper: Skipper) -> bool:
        """
        Determines if a race is valid for RC points with a given skipper
        :param skipper: skipper to check
        :return: True if the race time can be counted for RC points for the skipper, otherwise False
        """
        # Determine if the race was valid
        valid_check = self.valid()

        # Determine if the skipper was RC for the race
        rc_check = skipper in self.race_times and self.race_times[skipper].is_rc()

        # Determine if we can use the race for RC
        return valid_check or rc_check

    def add_skipper_time(self, race_time: 'RaceTime') -> None:
        """
        Adds a skipper's time to the race results
        :param race_time: race_time object to add to the database
        """
        # Raise an error if the skipper is already in the list
        if race_time.skipper in self.race_times:
            raise ValueError(
                'Cannot add duplicate race time for {:s}'.format(race_time.skipper.identifier))

        # Otherwise, add the race_time object to the dictionary keyed by the skipper
        else:
            self.race_times[race_time.skipper] = race_time

        # Call reset
        self.reset()

    def race_results(self) -> typing.Dict[Skipper, float]:
        """
        Provides the scores for each skipper in the race
        :return: dictionary of the skipper keyed to the resulting point score
        """
        if self._results_dict is None:
            # Create a variable to hold the current list
            result_times = dict()

            # Race result list
            race_results = self.finished_race_times()
            race_results.sort(key=lambda x: x.corrected_time_s)

            # Add each result to the list based on bucket to provide a count for the number of times each result appears
            for result in race_results:
                ct_s = result.corrected_time_s
                if ct_s not in result_times:
                    result_times[ct_s] = 0
                result_times[ct_s] += 1

            # Next, define a dictionary for the points for each corrected time
            place_dict = dict()
            current_place = 1
            for time_s in sorted(result_times.keys()):
                # Extract the number of times the result has been repeated
                num_for_time = result_times[time_s]

                # We define the score as the average of the scores that would be taken by all results with the same tie.
                # For example, with a tie between 2 and 3 places, we would get
                #       (2 + 3) / 2 = 2.5
                # For a tie between 4, 5, and 6 places, we would get
                #       (4 + 5 + 6) / 3 = 5
                place_dict[time_s] = sum(range(current_place, current_place + num_for_time)) / num_for_time
                current_place += num_for_time

            # Result Dictionary Creation
            result_dict = {rt.skipper: round_score(place_dict[rt.corrected_time_s]) for rt in race_results}

            # Add in the finish-in-place values
            for rt in self.fip_results():
                result_dict[rt.skipper] = round_score(rt.fip_val)

            # Add in all the other results
            for rt in self.other_results():
                result_dict[rt.skipper] = round_score(len(self.race_times) - len(self.rc_skippers()))

            # Round all race results
            for key in result_dict:
                result_dict[key] = round_score(result_dict[key])

            # Define override parameters

            # Set the memoization value
            self._results_dict = result_dict

        # Return pre-computed results
        return self._results_dict

    def get_race_table(self) -> str:
        """
        Calculates the resulting scores, sorts, and prints out in a table
        :return: a string table of the race results that can be printed to the console
        """
        # Initialize the string list
        str_list = list()

        # Append header parameters
        str_list.append(' Wind: {:d} (BFT)'.format(self.wind_bf if self.wind_bf else 0))
        str_list.append('   RC: {:s}'.format(', '.join([s.identifier for s in self.rc_skippers()])))
        str_list.append(' Date: {:s}'.format(self.date))
        str_list.append('Notes: {:s}'.format(self.notes))
        str_list.append('                    a_time                        c_time')
        str_list.append('       Name   Boat   mm:ss   sec  /   hc  =c_sec   mm:ss  Rank')
        str_list.append('-----------   ----   -----   -------------------   -----  ----')

        # Iterate over each of the race time in the sorted list and add the column value
        for race_result in self.race_times_sorted():
            score = race_result[0]
            race_time = race_result[1]
            actual_time_value = format_time(race_time.time_s)
            if race_time.other_finish is not None:
                actual_time_value = race_time.other_finish.name
            str_list.append('{:>11s} {:>6s}   {:5s}   {:4d} / {:0.03f} = {:4d}   {:5s}  {:.2f}'.format(
                race_time.skipper.identifier,
                race_time.boat.code,
                actual_time_value,
                round(race_time.time_s),
                race_time.boat.dpn_for_beaufort(self.wind_bf) / 100.0,
                race_time.corrected_time_s,
                format_time(race_time.corrected_time_s),
                score))

        # Return the joined list
        return '\n'.join(str_list)

    def get_skipper_result(self, skipper: Skipper) -> typing.Union[str, int, float, None]:
        """
        Provides the resulting score text for the skipper ID provided.
        :param skipper: the skipper identifier
        :return: The score parameter for the given skipper value
        """
        # Check if the skipper is in the race times
        if skipper in self.race_times:
            # Obtain the results
            results = self.race_results()

            # If the skipper has result points, obtain those
            if skipper in results:
                # Extract the result value
                result_val = results[skipper]

                # Return a rounded value if we are close enough
                return result_val
            # Otherwise, return the other finish name for printing
            else:
                return self.race_times[skipper].other_finish.name
        # Return None if no skipper of this name is provided
        else:
            return None

    def rc_skippers(self) -> typing.List[Skipper]:
        """
        Provides the skippers participating in the race committee
        :return: list of Skippers in the race committee
        """
        return [r.skipper for r in self.race_times.values() if r.is_rc()]

    def other_results(self) -> typing.List['RaceTime']:
        """
        Provides a list of other racers that did not finish the race and were not RC
        :return: list of valid race times that did not finish the race and were not RC
        """
        return [r for r in self.race_times.values() if not r.finished() and not r.is_rc()]

    def fip_results(self) -> typing.List['RaceTime']:
        """
        Provides a list of the racers that have a Finish-In-Place indication
        :return: list of valid race times for finishing in place
        """
        return [r for r in self.race_times.values() if r.finished_without_time()]

    def finished_race_times(self) -> typing.List['RaceTime']:
        """
        Provides a list of the finished race times
        :return: a list of the race times that were completed
        """
        return [r for r in self.race_times.values() if r.finished_with_time()]

    def race_times_sorted(self) -> typing.List[typing.Tuple[float, 'RaceTime']]:
        """
        Provides a sorted list of the finished race times by score
        :return: a list of tuples containing the score and the race time object
        """
        # Obtain the race results
        scores = self.race_results()

        # Obtain the list of skippers who finished the race and sort by the resulting scores obtained above
        race_time_list = self.finished_race_times()
        race_time_list.extend(self.other_results())
        race_time_list.extend(self.fip_results())

        # Create the resulting dictionary
        race_result_list = [(scores[rt.skipper], rt) for rt in race_time_list]
        race_result_list.sort(key=lambda x: x[0])

        # Return the results
        return race_result_list

    def race_plot(self) -> str:
        """
        Provides a PNG image string in Base 64 providing a plot of result points vs. finishing time
        :return: encoded string value for the resulting figure in base64 for embedding, empty on failure
        """
        if self._race_plot is None:
            # Get the plot instance
            plt = get_pyplot()
            img_str = ''

            if plt is not None:
                # Extract the score and time results from finished scores
                finished_results_sorted = [v for v in self.race_times_sorted() if v[1].finished_with_time()]
                score_results = [v[0] for v in finished_results_sorted]
                time_results = [v[1].corrected_time_s / 60.0 for v in finished_results_sorted]

                # Plot the results
                f = plt.figure()
                plt.plot(score_results, time_results, 'o--')
                plt.xlabel('Score [points]')
                plt.ylabel('Corrected Time [min]')

                s = f.get_size_inches()
                f.set_size_inches(w=1.15*s[0], h=s[1])

                img_str = figure_to_base64(f)

            self._race_plot = img_str

        return self._race_plot


class RaceTime:
    """
    A class to define the database parameters for the race time
    """
    class RaceFinishOther(enum.Enum):
        """
        Enumeration to define other types of race finishes
        """
        RC = 0
        DNF = 1
        DQ = 2
        FIP = 3

    def __init__(self,
                 race: 'Race',
                 skipper: Skipper,
                 input_time_s: int,
                 offset_time_s: int,
                 other_finish: 'RaceFinishOther' = None,
                 finish_in_place: int = None):
        """
        Initializes the race time object with the input parameters
        :param race: race to associate the time with
        :param skipper: skipper to associate the result with
        :param input_time_s: raw time, in seconds, of the result, or one of the other RaceFinishOther types
        :param offset_time_s: offset time, in seconds, to subtract from the input time
        :param other_finish: parameter to define a different type of race finish other than a time
        :param finish_in_place: parameter to define a type of finish to assign points
        """
        # Initialize the race parameters
        self.race = race
        self.skipper = skipper
        self.other_finish = other_finish
        self.input_time_s = input_time_s
        self.offset_time_s = offset_time_s

        if self.other_finish == self.RaceFinishOther.FIP:
            self.fip_val = finish_in_place
        elif finish_in_place is not None:
            raise ValueError('Cannot have a FIP value without the associated result')
        else:
            self.fip_val = None

        # Initialize memoization parameters
        self._corrected_time_s = None

        # Extract the boat based on the skipper provided
        if skipper in race.boat_dict:
            self.boat = race.boat_dict[skipper]
        else:
            raise ValueError('No boat provided for skipper {:s}'.format(skipper.identifier))

    @property
    def time_s(self) -> int:
        """
        Provides the elapsed time for the skipper's race
        :return: the time in seconds of the race, not including any offset time
        """
        if self.other_finish is not None:
            return 0
        else:
            return self.input_time_s - self.offset_time_s

    def reset(self) -> None:
        """
        Resets any stored calculated parameters
        """
        self._corrected_time_s = None

    def finished(self) -> bool:
        """
        Return whether the skipper finished the race
        :return: True if the time_s is not one of the RaceFinishOther types or is FIP
        """
        return self.finished_with_time() or self.finished_without_time()

    def finished_with_time(self) -> bool:
        """
        Return whether the skipper finished the race with a time
        :return: True if the time_s is not one of the RaceFinishOther types
        """
        return self.other_finish is None

    def finished_without_time(self) -> bool:
        """
        Return whether the skipper finished the race without a time
        :return: True if the time_s is FIP
        """
        return self.other_finish == self.RaceFinishOther.FIP

    def has_other_result(self) -> bool:
        """
        Whether the skipper did not finish the race and did not participate in RC
        :return: True if the skipper didn't finish the race and wasn't in RC
        """
        return not self.finished() and not self.is_rc()

    def is_rc(self) -> bool:
        """
        Return whether a skipper participated in the RC
        :return: True if time_s is RaceFinishOther.RC
        """
        return not self.finished() and self.other_finish is RaceTime.RaceFinishOther.RC

    @property
    def corrected_time_s(self) -> int:
        """
        Calculates the corrected time from the beaufort DPN value, and rounds the result
        :return: rounded corrected time in seconds with the provided boat and wind speed
        """
        if self._corrected_time_s is None:
            self._corrected_time_s = round(self.time_s * 100.0 / self.boat.dpn_for_beaufort(self.race.wind_bf))
        return self._corrected_time_s
