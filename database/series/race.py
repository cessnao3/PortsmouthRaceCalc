"""
Provides a database for use in calculating the corrected times for race parameters and scoring
"""

import datetime
import decimal
from typing import List, Dict, Optional, Tuple, Union

from ..fleets import Fleet, BoatType
from ..skippers import Skipper
from ..utils import round_score, format_time
from ..utils.plotting import figure_to_data

import matplotlib.pyplot as plt

from . import finishes


class Race:
    """
    An object to maintain the information for a single race
    """

    def __init__(
            self,
            fleet: Fleet,
            boat_dict: Dict[Skipper, BoatType],
            required_skippers: int,
            rc: List[Skipper],
            date_string: str,
            wind_bf: int,
            notes: str):
        """
        Initializes the race object
        :param fleet: the fleet to use for the boat handicap values
        :param boat_dict: the boat dictionary to use for finding default skipper boats
        :param required_skippers: the number of required skippers for the race to be considered valid
        :param rc: a list of the skipper objects participating in the race committee
        :param date_string: a string containing the date of the race in the format year_mm_dd
        :param wind_bf: the Beaufort wind condition number associated with the race
        :param notes: any additional notes about the race
        """
        self._race_finishes: Dict[Skipper, finishes.RaceFinishInterface] = dict()
        self.fleet = fleet
        self.boat_dict = boat_dict
        self.required_skippers = required_skippers
        self.date = datetime.datetime.strptime(date_string, '%Y_%m_%d')
        self.wind_bf = wind_bf
        self.notes = notes
        self.__race_index: Optional[int] = None
        self.__results_dict: Optional[Dict[Skipper, int]] = None
        self.__plot_race_time: Optional[bytes] = None

        # Add the RC skippers to the race times as participating in RC
        for rc_skipper in rc:
            self.add_skipper_finish(finishes.RaceFinishRC(
                boat=self.boat_dict[rc_skipper],
                skipper=rc_skipper))

    def date_string(self) -> str:
        """
        Provides the date string for the current race
        :return: the associated date string
        """
        return self.date.strftime('%B %d, %Y')

    def reset(self) -> None:
        """
        Resets any stored calculated parameters
        """
        self.__race_index = None
        for rt in self._race_finishes.values():
            rt.reset()
        self.__results_dict = None

    def set_index(self, i: int) -> None:
        """
        Sets the index to the provided value
        :param i: Value to set the race index to
        """
        self.__race_index = i

    @property
    def race_num(self) -> int:
        """
        Provides the 1's indexed race number
        :return: race index + 1
        """
        if self.__race_index is not None:
            return self.__race_index + 1
        else:
            return 0

    def min_time_s(self) -> Union[None, int]:
        """
        Returns the minimum completion time
        :return: minimum completion time in seconds
        """
        valid_race_times = [
            rt.corrected_time_s
            for rt in self._race_finishes.values()
            if isinstance(rt, finishes.RaceFinishTime)]

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
        starting_race_times = [
            rt
            for rt in self._race_finishes.values()
            if not isinstance(rt, finishes.RaceFinishRC)]
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
        rc_check = skipper in self._race_finishes and isinstance(self._race_finishes[skipper], finishes.RaceFinishRC)

        # Determine if we can use the race for RC
        return valid_check or rc_check

    def add_skipper_finish(self, race_finish: finishes.RaceFinishInterface) -> None:
        """
        Adds a skipper's finish to the race results
        :param race_finish: race finish object to add to the database
        """
        # Raise an error if the skipper is already in the list
        if race_finish.skipper in self._race_finishes:
            raise ValueError(
                'Cannot add duplicate race time for {:s}'.format(race_finish.skipper.identifier))

        # Otherwise, add the race_time object to the dictionary keyed by the skipper
        else:
            self._race_finishes[race_finish.skipper] = race_finish

        # Call reset
        self.reset()

    def starting_boat_results(self) -> List[finishes.RaceFinishInterface]:
        """
        Provides a list of race result values for boats that start
        :return: the list of starting skippers
        """
        return [r for r in self._race_finishes.values() if not isinstance(r, finishes.RaceFinishRC)]

    def skipper_race_points(self) -> Dict[Skipper, decimal.Decimal]:
        """
        Provides the scores for each skipper in the race
        :return: dictionary of the skipper keyed to the resulting point score
        """
        if self.__results_dict is None:
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
                place_dict[time_s] = decimal.Decimal(
                    sum(range(current_place, current_place + num_for_time)) / num_for_time)
                current_place += num_for_time

            # Result Dictionary Creation
            result_dict: Dict[Skipper, Optional[decimal.Decimal]] = {
                rt.skipper: round_score(place_dict[rt.corrected_time_s])
                for rt
                in race_results}

            # Add in the finish-in-place values
            for rt in self.fip_results():
                result_dict[rt.skipper] = round_score(decimal.Decimal(rt.place))

            # Define the remaining number of points
            if len(result_dict) > 0:
                starting_skippers_count = decimal.Decimal(len(self.starting_boat_results()))
            else:
                starting_skippers_count = None

            # Add in all the other results
            for rt in self.other_results():
                if isinstance(rt, finishes.RaceFinishDNF):
                    result_dict[rt.skipper] = starting_skippers_count
                elif isinstance(rt, finishes.RaceFinishDQ):
                    result_dict[rt.skipper] = starting_skippers_count + 2
                else:
                    result_dict[rt.skipper] = None

            # Round all race results
            for key, val in result_dict.items():
                if val is not None:
                    result_dict[key] = round_score(val)

            # Set the memoization value
            self.__results_dict = result_dict

        # Return pre-computed results
        return self.__results_dict

    def get_skipper_result_string(self, skipper: Skipper) -> Optional[Union[str, decimal.Decimal]]:
        """
        Provides the resulting score text for the skipper ID provided.
        :param skipper: the skipper identifier
        :return: The score parameter for the given skipper value
        """
        # Check if the skipper is in the race times
        if skipper in self._race_finishes:
            # Obtain the results
            results = self.skipper_race_points()

            # If the skipper has result points, obtain those
            if skipper in results:
                # Extract the result value
                result_val = results[skipper]

                # Return a rounded value if we are close enough
                return result_val
            # Otherwise, return the other finish name for printing
            else:
                return self._race_finishes[skipper].name()
        # Return None if no skipper of this name is provided
        else:
            return None

    def rc_skippers(self) -> List[Skipper]:
        """
        Provides the skippers participating in the race committee
        :return: list of Skippers in the race committee
        """
        return [r.skipper for r in self._race_finishes.values() if isinstance(r, finishes.RaceFinishRC)]

    def other_results(self) -> List[finishes.RaceFinishInterface]:
        """
        Provides a list of other racers that did not finish the race and were not RC
        :return: list of valid race times that did not finish the race and were not RC
        """
        return [r for r in self._race_finishes.values() if not r.finished()]

    def fip_results(self) -> List[finishes.RaceFinishFIP]:
        """
        Provides a list of the racers that have a Finish-In-Place indication
        :return: list of valid race times for finishing in place
        """
        return [r for r in self._race_finishes.values() if isinstance(r, finishes.RaceFinishFIP)]

    def finished_race_times(self) -> List[finishes.RaceFinishTime]:
        """
        Provides a list of the finished race times
        :return: a list of the race times that were completed
        """
        return [r for r in self._race_finishes.values() if isinstance(r, finishes.RaceFinishTime)]

    def race_times_sorted(self) -> List[Tuple[decimal.Decimal, finishes.RaceFinishInterface]]:
        """
        Provides a sorted list of the finished race times by score
        :return: a list of tuples containing the score and the race time object
        """
        # Obtain the race results
        scores = self.skipper_race_points()

        # Obtain the list of skippers who finished the race and sort by the resulting scores obtained above
        race_time_list: List[finishes.RaceFinishInterface] = self.finished_race_times()
        race_time_list.extend(self.other_results())
        race_time_list.extend(self.fip_results())

        # Create the resulting dictionary
        all_races = [(scores[rt.skipper], rt) for rt in race_time_list]
        race_result_list = list(filter(lambda x: x[0] is not None, all_races))
        race_result_list.sort(key=lambda x: x[0])
        race_result_list.extend(filter(lambda x: x[0] is None, all_races))

        # Return the results
        return race_result_list

    def get_plot_race_time_results(self) -> bytes:
        """
        Provides a PNG image string in Base 64 providing a plot of result points vs. finishing time
        :return: encoded string value for the resulting figure in base64 for embedding, empty on failure
        """
        # Extract the score and time results from finished scores
        temp_list = [
            v
            for v in self.race_times_sorted()
            if isinstance(v[1], finishes.RaceFinishTime)]

        if len(temp_list) > 0:
            score_results, race_times = zip(*temp_list)
            time_results = [v.corrected_time_s / 60.0 for v in race_times]

            # Plot the results
            plt.ioff()
            f = plt.figure()
            plt.plot(score_results, time_results, 'o--')
            plt.xlabel('Score [points]')
            plt.ylabel('Corrected Time [min]')

            s = f.get_size_inches()
            f.set_size_inches(w=1.15 * s[0], h=s[1])

            img_data = figure_to_data(f)
            plt.close(f)
            return img_data
        else:
            return bytes()
