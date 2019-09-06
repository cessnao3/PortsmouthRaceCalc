"""
Provides a database for use in calculating the corrected times for race parameters and scoring
"""

from skipper_database import Skipper
from race_utils import round_score

import base64
import enum
import io

import matplotlib.pylab as plt


class Race:
    """
    An object to maintain the information for a single race
    """
    def __init__(self, series, rc, date, wind_bf, notes):
        """
        Initializes the race object
        :param series: reference to the series associated with the current race
        :type series: Series
        :param rc: a list of the skipper objects participating in the race committee
        :type rc: list of Skipper
        :param date: a string containing the date of the race in the format year_mm_dd
        :type date: str
        :param wind_bf: the Beaufort wind condition number associated with the race
        :type wind_bf: int
        :param notes: any additional notes about the race
        :type notes: str
        """
        self.race_times = dict()
        self.series = series
        self.date = date
        self.wind_bf = wind_bf
        self.notes = notes
        self._results_dict = None

        # Add the RC skippers to the race times as participating in RC
        for rc_skipper in rc:
            self.add_skipper_time(RaceTime(
                race=self,
                skipper=rc_skipper,
                time_s=0,
                other_finish=RaceTime.RaceFinishOther.RC))

    def reset(self):
        """
        Resets any stored calculated parameters
        """
        for rt in self.race_times.values():
            rt.reset()
        self._results_dict = None

    def min_time_s(self):
        """
        Returns the minimum completion time
        :return: minimum completion time in seconds
        :rtype: int or None
        """
        valid_race_times = [rt.corrected_time_s for rt in self.race_times.values() if rt.finished()]

        if len(valid_race_times) >= 0:
            return min(valid_race_times)
        else:
            return None

    def valid(self):
        """
        Determines if a race is valid or not
        :return: True if the race is valid, false otherwise
        :rtype: bool
        """
        # Calculate the wind condition
        bf_condition = self.wind_bf is not None

        # Calculate the starting race times
        starting_race_times = [rt for rt in self.race_times.values() if not rt.is_rc()]
        num_condition = len(starting_race_times) >= self.series.valid_required_skippers

        # Return true if all conditions are true
        return bf_condition and num_condition

    def add_skipper_time(self, race_time):
        """
        Adds a skipper's time to the race results
        :param race_time: race_time object to add to the database
        :type race_time: RaceTime
        """
        # Obtain the skipper's identifier
        skip_id = race_time.skipper.identifier

        # Raise an error if the skipper is already in the list
        if skip_id in self.race_times:
            raise ValueError(
                'Cannot add duplicate {:s} race time for {:s}'.format(
                    self.series.name,
                    skip_id))

        # Otherwise, add the race_time object to the dictionary keyed by the skipper identifier
        else:
            self.race_times[skip_id] = race_time

        # Call reset
        self.reset()

    def race_results(self):
        """
        Provides the scores for each skipper in the race
        :return: dictionary of the skipper identifier keyed to the resulting point score
        :rtype: {str: float}
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
                if ct_s in result_times:
                    result_times[ct_s] += 1
                else:
                    result_times[ct_s] = 1

            # Next, define a dictionary for the points for each corrected time
            place_dict = dict()
            current_place = 1
            for time_s in sorted(result_times.keys()):
                # Extract the number of times the result has been repeated
                num_for_time = result_times[time_s]

                # We define the score as the average of the scores that would be taken by all results with the same tie.
                # For example, with a tie between 2 and 3 places, we would get
                #       (2 + 3) / 2 = 2.5
                # For a tie between 4 and 5 places, we would get
                #       (4 + 5) / 2 = 4.5
                place_dict[time_s] = sum(range(current_place, current_place + num_for_time)) / num_for_time
                current_place += num_for_time

            # Result Dictionary Creation
            result_dict = {rt.skipper.identifier: place_dict[rt.corrected_time_s] for rt in race_results}

            # Add in all the other results
            for rt in self.other_results():
                result_dict[rt.skipper.identifier] = len(self.race_times) - len(self.rc_skippers())

            # Round all race results
            for key in result_dict:
                result_dict[key] = round_score(result_dict[key])

            # Set the memoization value
            self._results_dict = result_dict

        # Return pre-computed results
        return self._results_dict

    def get_race_table(self):
        """
        Calculates the resulting scores, sorts, and prints out in a table
        :return: a string table of the race results that can be printed to the console
        :rtype: str
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
            actual_time_value = race_time.format_time(race_time.time_s)
            if race_time.other_finish is not None:
                actual_time_value = race_time.other_finish.name
            str_list.append('{:>11s} {:>6s}   {:5s}   {:4d} / {:0.03f} = {:4d}   {:5s}  {:.2f}'.format(
                race_time.skipper.identifier,
                race_time.boat.code,
                actual_time_value,
                round(race_time.time_s),
                race_time.boat.dpn_for_beaufort(self.wind_bf) / 100.0,
                race_time.corrected_time_s,
                race_time.format_time(race_time.corrected_time_s),
                score))

        # Return the joined list
        return '\n'.join(str_list)

    def get_skipper_result(self, skipper_id):
        """
        Provides the resulting score text for the skipper ID provided.
        :param skipper_id: the skipper identifier
        :type skipper_id: str
        :return: The score parameter for the given skipper value
        :rtype: int or float or str or None
        """
        # Check if the skipper is in the race times
        if skipper_id in self.race_times:
            # Obtain the results
            results = self.race_results()

            # If the skipper has result points, obtain those
            if skipper_id in results:
                # Extract the result value
                result_val = results[skipper_id]

                # Return a rounded value if we are close enough
                return result_val
            # Otherwise, return the other finish name for printing
            else:
                return self.race_times[skipper_id].other_finish.name
        # Return None if no skipper of this name is provided
        else:
            return None

    def rc_skippers(self):
        """
        Provides the skippers participating in the race committee
        :return: list of Skippers in the race committee
        :rtype: list of Skipper
        """
        return [r.skipper for r in self.race_times.values() if r.is_rc()]

    def other_results(self):
        """
        Provides a list of other racers that did not finish the race and were not RC
        :return: list of valid race times
        :rtype: list of RaceTime
        """
        return [r for r in self.race_times.values() if not r.finished() and not r.is_rc()]

    def finished_race_times(self):
        """
        Provides a list of the finished race times
        :return: a list of the race times that were completed
        :rtype: list of RaceTime
        """
        return [r for r in self.race_times.values() if r.finished()]

    def race_times_sorted(self):
        """
        Provides a sorted list of the finished race times by score
        :return: a list of tuples containing the score and the race time object
        :rtype: list of (float, RaceTime)
        """
        # Obtain the race results
        scores = self.race_results()

        # Obtain the list of skippers who finished the race and sort by the resulting scores obtained above
        race_time_list = self.finished_race_times()
        race_time_list.extend(self.other_results())

        # Create the resulting dictionary
        race_result_list = [(scores[rt.skipper.identifier], rt) for rt in race_time_list]
        race_result_list.sort(key=lambda x: x[0])

        # Return the results
        return race_result_list

    def race_plot(self):
        """
        Provides a PNG image string in Base 64 providing a plot of result points vs. finishing time
        :return: encoded string value for the resulting figure in base64 for embedding
        :rtype: str
        """
        # Extract the score and time results from finished scores
        finished_results_sorted = [v for v in self.race_times_sorted() if v[1].finished()]
        score_results = [v[0] for v in finished_results_sorted]
        time_results = [v[1].corrected_time_s / 60.0 for v in finished_results_sorted]

        # Plot the results
        f = plt.figure()
        plt.plot(score_results, time_results, 'o--')
        plt.xlabel('Score [points]')
        plt.ylabel('Corrected Time [min]')

        # Save the image to a memory buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)

        # Encode the buffer bytes as a string and return
        return base64.b64encode(buf.read()).decode('utf-8')


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

    def __init__(self, race, skipper, time_s, other_finish=None):
        """
        Initializes the race time object with the input parameters
        :param race: race to associate the time with
        :type race: Race
        :param skipper: skipper to associate the result with
        :type skipper: Skipper
        :param time_s: raw time, in seconds, of the result, or one of the other RaceFinishOther types
        :type time_s: int
        :param other_finish: parameter to define a different type of race finish other than a time
        :type other_finish: None or RaceFinishOther
        """
        # Initialize the race parameters
        self.race = race
        self.skipper = skipper
        self.other_finish = other_finish
        self.time_s = time_s

        if self.other_finish is not None:
            self.time_s = 0

        # Initialize memoization parameters
        self._corrected_time_s = None

        # Extract the boat ID, from the override (if available), or the default in the skipper database
        boat_id = self.skipper.default_boat_code
        if skipper.identifier in race.series.boat_overrides:
            boat_id = race.series.boat_overrides[skipper.identifier]

        # Define the boat type object
        self.boat = race.series.fleet.get_boat(boat_id)

    def reset(self):
        """
        Resets any stored calculated parameters
        """
        self._corrected_time_s = None

    def finished(self):
        """
        Return whether the skipper finished the race
        :return: True if the time_s is not one of the RaceFinishOther types
        :rtype: bool
        """
        return self.other_finish is None

    def has_other_result(self):
        """
        Whether the skipper did not finish the race and did not participate in RC
        :return: True if the skipper didn't finish the race and wasn't in RC
        :rtype: bool
        """
        return not self.finished() and not self.is_rc()

    def is_rc(self):
        """
        Return whether a skipper participated in the RC
        :return: True if time_s is RaceFinishOther.RC
        :rtype: bool
        """
        return not self.finished() and self.other_finish is RaceTime.RaceFinishOther.RC

    @property
    def corrected_time_s(self):
        """
        Calculates the corrected time from the beaufort DPN value, and rounds the result
        :return: rounded corrected time in seconds with the provided boat and wind speed
        :rtype: int
        """
        if self._corrected_time_s is None:
            self._corrected_time_s = round(self.time_s * 100.0 / self.boat.dpn_for_beaufort(self.race.wind_bf))
        return self._corrected_time_s

    @staticmethod
    def format_time(time_s):
        """
        Formats the time in seconds into a mm:ss format
        :param time_s: The input time, in seconds, to format
        :type time_s: int
        :return: string of formatted time
        :rtype: str
        """
        s_val = time_s % 60
        time_c = int((time_s - s_val) / 60)
        m_val = time_c
        return '{:02d}:{:02d}'.format(m_val, round(s_val))
