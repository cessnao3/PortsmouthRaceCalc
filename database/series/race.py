"""
Provides a database for use in calculating the corrected times for race parameters and scoring
"""

import datetime
import typing


from ..fleets import Fleet, BoatType

from ..skippers import Skipper

from ..utils import round_score, format_time
from ..utils.plotting import get_pyplot, figure_to_base64, fig_compress, fig_decompress

from . import finishes


class Race:
    """
    An object to maintain the information for a single race
    """

    def __init__(self,
                 fleet: Fleet,
                 boat_dict: typing.Dict[Skipper, BoatType],
                 required_skippers: int,
                 rc: typing.List[Skipper],
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
        self.race_times: typing.Dict[Skipper, finishes.RaceFinishInterface] = dict()
        self.fleet = fleet
        self.boat_dict = boat_dict
        self.required_skippers = required_skippers
        self.date = datetime.datetime.strptime(date_string, '%Y_%m_%d')
        self.wind_bf = wind_bf
        self.notes = notes
        self._race_index: typing.Optional[int] = None
        self._results_dict: typing.Optional[typing.Dict[Skipper, int]] = None
        self._race_plot: typing.Optional[bytes] = None

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
        valid_race_times = [
            rt.corrected_time_s
            for rt in self.race_times.values()
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
            for rt in self.race_times.values()
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
        rc_check = skipper in self.race_times and isinstance(self.race_times[skipper], finishes.RaceFinishRC)

        # Determine if we can use the race for RC
        return valid_check or rc_check

    def add_skipper_finish(self, race_finish: finishes.RaceFinishInterface) -> None:
        """
        Adds a skipper's finish to the race results
        :param race_finish: race finish object to add to the database
        """
        # Raise an error if the skipper is already in the list
        if race_finish.skipper in self.race_times:
            raise ValueError(
                'Cannot add duplicate race time for {:s}'.format(race_finish.skipper.identifier))

        # Otherwise, add the race_time object to the dictionary keyed by the skipper
        else:
            self.race_times[race_finish.skipper] = race_finish

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
                result_dict[rt.skipper] = round_score(rt.place)

            # Define the remaining number of points
            if len(result_dict) > 0:
                remaining_points = max(result_dict.values()) + 1
            else:
                remaining_points = None

            # Add in all the other results
            for rt in self.other_results():
                if isinstance(rt, finishes.RaceFinishDNF):
                    result_dict[rt.skipper] = remaining_points
                else:
                    result_dict[rt.skipper] = None

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
        str_list.append('       Name   Boat   mm:ss   sec  /    hc   =  c_sec   mm:ss  Rank')
        str_list.append('-----------   ----   -----   -----------------------   -----  ----')

        # Iterate over each of the race time in the sorted list and add the column value
        for race_result in self.race_times_sorted():
            score = race_result[0]
            race_time = race_result[1]
            if isinstance(race_time, finishes.RaceFinishTime):
                actual_time_value = format_time(race_time.time_s)
                race_time_value = f'{round(race_time.time_s):4d}'
                handicap_string = f'{race_time.boat.dpn_for_beaufort(self.wind_bf).handicap_string():9s}'
                corrected_time_string = f'{race_time.corrected_time_s:4d}'
                formatted_time_string = f'{format_time(race_time.corrected_time_s):5s}'
            else:
                actual_time_value = race_time.name()
                race_time_value = 'na'
                handicap_string = 'na'
                corrected_time_string = 'na'
                formatted_time_string = 'na'

            score_result = f'{score:.2f}' if score is not None else 'N/A'
            str_list.append(
                f'{race_time.skipper.identifier:>11s} {race_time.boat.code:>6s}   '
                f'{actual_time_value:5s}   '
                f'{race_time_value:4s} / {handicap_string:9s} = '
                f'{corrected_time_string:4s}   {formatted_time_string:5s}  {score_result:s}')

        # Return the joined list
        return '\n'.join(str_list)

    def get_skipper_result_string(self, skipper: Skipper) -> typing.Union[str, int, float, None]:
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
                return self.race_times[skipper].name()
        # Return None if no skipper of this name is provided
        else:
            return None

    def rc_skippers(self) -> typing.List[Skipper]:
        """
        Provides the skippers participating in the race committee
        :return: list of Skippers in the race committee
        """
        return [r.skipper for r in self.race_times.values() if isinstance(r, finishes.RaceFinishRC)]

    def other_results(self) -> typing.List[finishes.RaceFinishInterface]:
        """
        Provides a list of other racers that did not finish the race and were not RC
        :return: list of valid race times that did not finish the race and were not RC
        """
        return [r for r in self.race_times.values() if not r.finished()]

    def fip_results(self) -> typing.List[finishes.RaceFinishFIP]:
        """
        Provides a list of the racers that have a Finish-In-Place indication
        :return: list of valid race times for finishing in place
        """
        return [r for r in self.race_times.values() if isinstance(r, finishes.RaceFinishFIP)]

    def finished_race_times(self) -> typing.List[finishes.RaceFinishTime]:
        """
        Provides a list of the finished race times
        :return: a list of the race times that were completed
        """
        return [r for r in self.race_times.values() if isinstance(r, finishes.RaceFinishTime)]

    def race_times_sorted(self) -> typing.List[typing.Tuple[float, finishes.RaceFinishInterface]]:
        """
        Provides a sorted list of the finished race times by score
        :return: a list of tuples containing the score and the race time object
        """
        # Obtain the race results
        scores = self.race_results()

        # Obtain the list of skippers who finished the race and sort by the resulting scores obtained above
        race_time_list: typing.List[finishes.RaceFinishInterface] = self.finished_race_times()
        race_time_list.extend(self.other_results())
        race_time_list.extend(self.fip_results())

        # Create the resulting dictionary
        all_races = [(scores[rt.skipper], rt) for rt in race_time_list]
        race_result_list = list(filter(lambda x: x[0] is not None, all_races))
        race_result_list.sort(key=lambda x: x[0])
        race_result_list.extend(filter(lambda x: x[0] is None, all_races))

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
                score_results, race_times = zip(*[
                    v
                    for v in self.race_times_sorted()
                    if isinstance(v[1], finishes.RaceFinishTime)])
                time_results = [v.corrected_time_s / 60.0 for v in race_times]

                # Plot the results
                f = plt.figure()
                plt.plot(score_results, time_results, 'o--')
                plt.xlabel('Score [points]')
                plt.ylabel('Corrected Time [min]')

                s = f.get_size_inches()
                f.set_size_inches(w=1.15 * s[0], h=s[1])

                img_str = figure_to_base64(f)

            self._race_plot = fig_compress(img_str)

        return fig_decompress(self._race_plot)
