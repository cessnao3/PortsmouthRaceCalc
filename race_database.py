"""
Provides a database for use in calculating the corrected times for race parameters and scoring
"""

from boat_database import Fleet
from skipper_database import Skipper
from race_utils import capitalize_words, round_score
import enum


class Series:
    """
    Defines a series of races, defined by a fleet type and a list of races
    """
    def __init__(self, name, qualify_count, fleet, boat_overrides):
        """
        Initializes the series with the input parameters
        :param name: The unique name of the series
        :type name: str
        :param qualify_count: The number of races required to qualify for a scoring place
        :type qualify_count: int
        :param fleet: The fleet object to be used to define the corrected scoring parameters
        :type fleet: Fleet
        :param boat_overrides: A dictionary of boat overrides, containing {skipper_identifier: boat_identifier}
        :type boat_overrides: {str: str}
        """
        self.name = name
        self.qualify_count = qualify_count
        self.fleet = fleet
        self.races = list()
        self.boat_overrides = boat_overrides if boat_overrides is not None else dict()
        self._skipper_rc_pts = None
        self._skippers = None
        self._points = None

    def reset(self):
        """
        Resets any stored calculated parameters
        """
        for r in self.races:
            r.reset()
        self._skipper_rc_pts = None
        self._skippers = None
        self._points = None

    def skipper_rc_points(self, skipper_id):
        """
        Returns the number of points associated with RC for a given Skipper
        :param skipper_id: skipper identifier
        :type skipper_id: str
        :return: Number of points estimated for RC races for a given Skipper
        :rtype: int or float
        """
        if self._skipper_rc_pts is None:
            # Initialize the dictionary
            self._skipper_rc_pts = dict()

            # Calculate RC point parameters
            for skip in self.get_all_skippers():
                self._skipper_rc_pts[skip.identifier] = 0

        # Return points if the skipper is in the list
        if skipper_id in self._skipper_rc_pts:
            return self._skipper_rc_pts[skipper_id]
        else:
            return None

    def skipper_points_list(self, skipper_id):
        """
        Returns the points used to calculate the resulting score for a series
        :return: list of points equal to the qualification, or DNQ if no qualification
        :rtype: None or list of (float or int)
        """
        if self._points is None:
            # Initialize the dictionary
            self._points = dict()

            # Calculate for all skippers
            for skip in self.get_all_skippers():
                # Obtain the results for a given skipper for all races
                point_values = []
                for r in self.races:
                    results = r.race_results()
                    if skip.identifier in results:
                        point_values.append(results[skip.identifier])
                    elif skip.identifier in r.race_times and r.race_times[skip.identifier].is_rc():
                        point_values.append(self.skipper_rc_points(skip.identifier))

                # Return None if there aren't enough races to qualify
                if len(point_values) < self.qualify_count:
                    self._points[skip.identifier] = None
                # Otherwise, return the sum of the lowest to qualify
                else:
                    point_values.sort()
                    self._points[skip.identifier] = point_values[:self.qualify_count]

        # Return the pre-calculated result
        if skipper_id in self._points:
            return self._points[skipper_id]
        else:
            return None

    def skipper_points(self, skipper_id):
        """
        Returns the number of points found for the given Skipper
        :param skipper_id: skipper identifier
        :type skipper_id: str
        :return: Number of points calculated for the given skipper
        :rtype: int or float or None
        """
        # Determine the points list
        points_list = self.skipper_points_list(skipper_id)

        # Return None if skipper not in the dictionary, otherwise return dictionary value
        if points_list is not None:
            # Calculate the point values and round accordingly
            return round_score(sum(self._points[skipper_id]))
        else:
            return None

    def add_race(self, race):
        """
        Adds a race to the race list. Races are in the order they are added to the list
        :param race: The race object to add
        :type race: Race
        """
        self.races.append(race)
        self.reset()

    def valid_races_held(self):
        """
        Returns the number of valid races held
        :return: count of valid races
        :rtype: int
        """
        return len([r for r in self.races if r.valid_race()])

    def get_all_skippers(self):
        """
        Provides all skippers in the series
        :return: list of unique skipper objects between all races
        :rtype: list of Skipper
        """
        if self._skippers is None:
            # Define the output list
            skippers = list()

            # Iterate over each race
            for race in self.races:
                # Iterate over each time
                for rt in race.race_times:
                    race_time = race.race_times[rt]
                    # Add the skipper to the list if not already in the list
                    if race_time.skipper not in skippers:
                        skippers.append(race_time.skipper)
            self._skippers = skippers

        # Return the skipper list
        return self._skippers

    def get_all_skippers_sorted(self):
        """
        Provides all skippers in the series, sorted first by points, and then by alphabet
        :return: list of unique skipper objects between all races, sorted
        :rtype: list of Skipper
        """
        # Get all skippers and scores
        skippers = self.get_all_skippers()
        scores = {s.identifier: self.skipper_points(s.identifier) for s in skippers}

        # Determine a maximum score value and apply to all skippers that haven't finished to push to the end
        max_score = round(sum([s for s in scores.values() if s is not None]))

        for s in scores:
            if scores[s] is None:
                scores[s] = max_score

        # Sort first by alphabet
        skippers.sort(key=lambda x: x.identifier)

        # Next, sort by the score
        skippers.sort(key=lambda x: scores[x.identifier])

        # Return the result
        return skippers

    def fancy_name(self):
        """
        Provides the fancy name, removing underscores for spaces and capitalizing
        :return: fancy name string
        :rtype: str
        """
        return capitalize_words(self.name.replace('_', ' '))


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

    def valid_race(self):
        """
        Determines if a race is valid or not
        :return: True if the race is valid, false otherwise
        :rtype: bool
        """
        return len(self.race_times) > 3

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
        return not self.finished() and self.other_finish == self.RaceFinishOther.RC

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
