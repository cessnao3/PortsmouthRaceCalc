"""
Provides a database for use in calculating and scoring a race series
"""

from ..fleets import Fleet, BoatType
from ..skippers import Skipper

from ..utils import capitalize_words, round_score
from ..utils.plotting import figure_to_data

import matplotlib.pyplot as plt

from . import Race, finishes

import datetime
import math

from typing import Union, List, Dict, Optional


class Series:
    """
    Defines a series of series, defined by a fleet type and a list of series
    """
    def __init__(
            self,
            name: str,
            valid_required_skippers: int,
            fleet: Fleet,
            qualify_count_override: Union[int, None] = None):
        """
        Initializes the series with the input parameters
        :param name: The unique name of the series
        :param valid_required_skippers: The number of racers needed to indicate a valid race
        :param fleet: The fleet object to be used to define the corrected scoring parameters
        :param qualify_count_override: The number of series required to qualify for a scoring place
        """
        # Save input values and setup for races
        self.name = name
        self.qualify_count_override = qualify_count_override
        self.valid_required_skippers = valid_required_skippers
        self.fleet = fleet
        self.races: List[Race] = list()
        self.boat_dict: Dict[Skipper, BoatType] = dict()

        # Define memoization parameters
        self.__skipper_rc_pts = None
        self.__skippers: Optional[List[Skipper]] = None
        self.__points: Optional[Dict[Skipper, List[Union[float, int]]]] = None
        self.__ranks: Optional[Dict[Skipper, int]] = None
        self.__plot_scatter_results: Optional[bytes] = None
        self.__plot_boat_pie_chart: Optional[bytes] = None
        self.__plot_series_rank_history: Optional[bytes] = None
        self.__plot_series_point_history: Optional[bytes] = None

    def reset(self) -> None:
        """
        Resets any stored calculated parameters and sets the race index parameter for each race
        """
        # Clear all memoization parameters
        self.__skipper_rc_pts = None
        self.__skippers = None
        self.__points = None
        self.__ranks = None
        self.__plot_scatter_results = None
        self.__plot_boat_pie_chart = None
        self.__plot_series_rank_history = None
        self.__plot_series_point_history = None

        # Clear the race counter and reset all races
        for i, r in enumerate(self.races):
            r.reset()
            r.set_index(i)

    def latest_race_date(self) -> Optional[datetime.datetime]:
        """
        Provides the latest race date for the given series
        :return: datetime for the latest race
        """
        latest = None
        for r in self.races:
            if latest is None or latest < r.date:
                latest = r.date
        return latest

    def add_skipper_boat(self, skipper: Skipper, boat: BoatType) -> None:
        """
        Adds the given skipper and boat to the race boat dictionary
        :param skipper: the skipper to add to the database
        :param boat: the boat to associate by default for the skipper
        """
        if skipper not in self.boat_dict:
            self.boat_dict[skipper] = boat
        else:
            raise ValueError('Cannot add duplicate boat entry to series {:s} for {:s}'.format(
                self.name,
                skipper.identifier))

    def skipper_num_finished(self, skipper: Skipper) -> int:
        """
        :param skipper: the skipper to check
        :return: the number of series that a skipper has finished with a time
        """
        count = 0
        for r in self.races:
            if skipper in r.race_finishes:
                res = r.race_finishes[skipper]
                if res.finished() and not isinstance(res, finishes.RaceFinishRC):
                    count += 1
        return count

    def skipper_num_rc(self, skipper: Skipper) -> int:
        """
        :param skipper: the skipper to check
        :return: the number of series that a skipper has been RC for
        """
        count = 0
        for r in self.races:
            if skipper in r.race_finishes:
                res = r.race_finishes[skipper]
                if isinstance(res, finishes.RaceFinishRC):
                    count += 1
        return count

    def skipper_num_dnf(self, skipper: Skipper) -> int:
        """
        :param skipper: the skipper to check
        :return: the number of races that a skipper has had a DNF finish
        """
        count = 0
        for r in self.races:
            if skipper in r.race_finishes:
                res = r.race_finishes[skipper]
                if isinstance(res, finishes.RaceFinishDNF):
                    count += 1
        return count

    def skipper_qualifies(self, skipper: Skipper) -> bool:
        """
        Returns whether a skipper has met the qualification count for the series
        :param skipper: The skipper to check
        :return: True if the skipper qualifies, False otherwise
        """
        # Initialize a count for valid series and valid RC (RC may only be counted twice for qualification)
        count = self.skipper_num_finished(skipper)
        count_rc = self.skipper_num_rc(skipper)
        count_dnf = self.skipper_num_dnf(skipper)

        # Return true if the count meets the qualify-count threshold
        return count + min(2, count_rc) + count_dnf >= self.qualify_count

    def skipper_rc_points(self, skipper: Skipper) -> Optional[float]:
        """
        Returns the number of points associated with RC for a given Skipper
        :param skipper: skipper to get RC points for
        :return: Number of points estimated for RC series for a given Skipper
        """
        if self.__skipper_rc_pts is None:
            # Initialize the dictionary
            self.__skipper_rc_pts = dict()

            # Calculate RC point parameters
            for skip in self.get_all_skippers():
                # Obtain the series for the skipper
                skipper_races = [r for r in self.valid_races() if skip in r.race_finishes]

                # Obtain the results from each of the finished series and sort
                point_values = [r.race_results()[skip] for r in skipper_races if skip in r.race_results()]
                point_values = [p for p in point_values if p is not None]
                point_values.sort()

                # Set the score to None if no point values
                if len(point_values) == 0:
                    score = None
                else:
                    # Pop the highest value if we have more than one entry
                    if len(point_values) > 1:
                        point_values.pop()

                    # Calculate the score
                    score = round_score(sum(point_values) / len(point_values))

                # Set the results
                self.__skipper_rc_pts[skip] = score

        # Return points if the skipper is in the list
        if skipper in self.__skipper_rc_pts:
            return self.__skipper_rc_pts[skipper]
        else:
            return None

    def skipper_points_list(self, skipper: Skipper) -> Optional[List[Union[int, float]]]:
        """
        Returns the points used to calculate the resulting score for a series
        :param skipper: the skipper identifier to search for
        :return: list of points equal to the qualification, or DNQ if no qualification
        """
        if self.__points is None:
            # Initialize the dictionary
            points = dict()

            # Calculate for all skippers
            for skip in self.get_all_skippers():
                # Obtain the results for a given skipper for all series
                points_list = list()

                # Ignore if the skipper doesn't qualify
                if not self.skipper_qualifies(skip):
                    continue

                # Define the number of RC points added
                rc_points_added_count = 0

                # Iterate over each race
                for r in [r for r in self.races if r.valid_for_rc(skip)]:
                    # Obtain the results
                    results = r.race_results()

                    value_to_add = None

                    # Define flags
                    can_add_rc = skip in r.race_finishes and isinstance(r.race_finishes[skip], finishes.RaceFinishRC)
                    can_add_rc = can_add_rc and rc_points_added_count < 2

                    # Add the results to the list if the skipper has a result
                    if skip in results:
                        value_to_add = results[skip]
                    elif can_add_rc:
                        value_to_add = self.skipper_rc_points(skip)
                        rc_points_added_count += 1

                    if value_to_add is not None:
                        points_list.append(value_to_add)

                # Add the sum of the lowest to qualify
                points_list.sort()

                if len(points_list) > 0:
                    points[skip] = points_list[:self.qualify_count]

            # Append the result to the static variable
            self.__points = points

        # Return the pre-calculated result
        if skipper in self.__points:
            return self.__points[skipper]
        else:
            return None

    def get_skipper_points(self, skipper: Skipper) -> Optional[Union[int, float]]:
        """
        Returns the number of points found for the given Skipper
        :param skipper: skipper identifier
        :return: Number of points calculated for the given skipper
        """
        # Determine the points list
        points_list = self.skipper_points_list(skipper)

        # Return None if skipper not in the dictionary, otherwise return dictionary value
        if points_list is not None:
            # Calculate the point values and round accordingly
            return round_score(sum(self.__points[skipper]))
        else:
            return None

    def skipper_points_string(self, skipper: Skipper) -> str:
        """
        Provides the resulting points list string for a given skipper
        :param skipper: the skipper to get the points for
        :return: comma-separated list of points used in the scoring process
        """
        point_list = self.skipper_points_list(skipper=skipper)
        if point_list is None:
            return ""
        else:
            return ', '.join([f'{v}' for v in point_list])

    def add_race(self, race: Race) -> None:
        """
        Adds a race to the race list. Races are in the order they are added to the list
        :param race: The race object to add
        """
        self.races.append(race)
        self.reset()

    @property
    def qualify_count(self) -> int:
        """
        Provides the qualification count for the series
        """
        if self.qualify_count_override is not None:
            return self.qualify_count_override
        else:
            qualify_count = int(math.ceil(len(self.valid_races()) / 2))
            return qualify_count

    def valid_races(self) -> List[Race]:
        """
        Returns the number of valid series held
        :return: count of valid series
        """
        return [r for r in self.races if r.valid()]

    def get_all_skippers(self) -> List[Skipper]:
        """
        Provides all skippers in the series
        :return: list of unique skipper objects between all series
        """
        if self.__skippers is None:
            # Define the output list
            skippers = list()

            # Check each race for skippers
            all_skipper_instances = [rt.skipper for r in self.races for rt in r.race_finishes.values()]

            # Iterate over all skipper values
            for s in all_skipper_instances:
                if s not in skippers:
                    skippers.append(s)

            # Save the resulting skipper dictionary
            self.__skippers = skippers

        # Return the skipper list
        return self.__skippers

    def get_skipper_rank(self, skipper: Skipper) -> Optional[int]:
        """
        Provides the rank in the series for the given skipper
        :param skipper: the skipper to check
        :return: the resulting rank, or None if skipper does not qualify
        """
        # Construct the ranks if needed
        if self.__ranks is None:
            self.__ranks = dict()
            for i, skip_point in enumerate(self.get_all_skippers_sorted()):
                if self.skipper_qualifies(skipper=skip_point):
                    self.__ranks[skip_point] = i + 1

        # Return the resulting rank
        if skipper in self.__ranks:
            return self.__ranks[skipper]
        else:
            return None

    def get_all_skippers_sorted(self) -> List[Skipper]:
        """
        Provides all skippers in the series, sorted first by points, and then by alphabet
        :return: list of unique skipper objects between all series, sorted
        """
        # Get all skippers and scores
        skippers = self.get_all_skippers()
        scores = {s: self.get_skipper_points(s) for s in skippers}

        # Determine a maximum score value and apply to all skippers that haven't finished to push to the end
        max_score = round(sum([s for s in scores.values() if s is not None]))

        for s in scores:
            if scores[s] is None:
                scores[s] = max_score

        # Sort first by alphabet
        skippers.sort(key=lambda x: x.identifier)

        # Then, sort by RC points
        def rc_pts_sort(s):
            rc_pts = self.skipper_rc_points(s)
            if rc_pts is None:
                return 100
            else:
                return rc_pts
        skippers.sort(key=lambda x: rc_pts_sort(x))

        # Next, sort by the score
        skippers.sort(key=lambda x: scores[x])

        # Return the result
        return skippers

    def get_plot_normalized_race_time_results(self) -> bytes:
        """
        Provides a plot of the fraction of corrected / minimum race time as a function of race score
        :return: An encoded base64 HTML source string of figure, empty on failure
        """
        plt.ioff()
        f = plt.figure()

        for race in self.valid_races():
            # Define the result list for the scatter plot
            results_list = list()

            # Add each valid item to the scatter plot
            for skipper, score in race.race_results().items():
                rt = race.race_finishes[skipper]
                if isinstance(rt, finishes.RaceFinishTime):
                    results_list.append((score, rt.corrected_time_s / race.min_time_s()))

            # Sort the values
            results_list.sort(key=lambda x: x[0])

            # Plot results
            plt.plot([x[0] for x in results_list], [y[1] for y in results_list], 'o--')

        s = f.get_size_inches()
        f.set_size_inches(
            w=1.15 * s[0],
            h=s[1])

        # Assign the legend and axes labels
        plt.legend(
            ['Race {:d}'.format(r.race_num) for r in self.valid_races()],
            loc='upper left',
            bbox_to_anchor=(1.04, 1),
            borderaxespad=0)
        plt.xlabel('Score [points]')
        plt.ylabel('Normalized Finish Time [corrected / shortest]')
        plt.tight_layout(rect=(0, 0, 1, 1))

        # Encode the image
        img_val = figure_to_data(f)
        plt.close(f)
        return img_val

    def get_plot_boat_pie_chart(self) -> bytes:
        """
        Provides a pie chart for the count for each existing boat in the series
        :return: An encoded base64 HTML source string of figure, empty on failure
        """
        # Obtain the boats for each skipper
        skip_boat_dict = dict()
        boat_type_dict = dict()

        # Iterate over each race to calculate the boat result
        for r in self.races:
            for rt in r.race_finishes.values():
                if rt.skipper not in skip_boat_dict and rt.skipper in r.race_results():
                    skip_boat_dict[rt.skipper] = rt.boat.code

                    if rt.boat.code not in boat_type_dict:
                        boat_type_dict[rt.boat.code] = 0
                    boat_type_dict[rt.boat.code] += 1

        # Combine values together
        combined = [(key, val) for key, val in boat_type_dict.items()]
        labels = [v[0].upper() for v in combined]
        sizes = [v[1] for v in combined]

        def percent2count(percent):
            return '{:1.0f}'.format(round(percent/100.0 * sum(sizes)))

        # Plot
        plt.ioff()
        f = plt.figure()
        ax = plt.gca()
        ax.pie(
            sizes,
            labels=labels,
            autopct=percent2count,
            explode=[0.03 for _ in combined])
        ax.axis('equal')

        # Save resulting image and close
        byte_val = figure_to_data(f)
        plt.close(f)
        return byte_val

    def _setup_point_rank_plots(self) -> None:
        """
        Generates the plots for the rank and point histories
        :return:
        """
        # Initialize plotting requirements
        img_types = ['Rank', 'Points']
        img_vals = [bytes() for _ in range(len(img_types))]

        # Plot if able
        if plt is not None:
            # Define the skipper list
            skipper_db = {skipper: (list(), list()) for skipper in self.get_all_skippers() if
                          self.get_skipper_points(skipper) is not None}

            # Create an inner series object to track point values
            series = Series(
                name=self.name,
                valid_required_skippers=self.valid_required_skippers,
                fleet=self.fleet,
                qualify_count_override=self.qualify_count_override)

            # Iterate over each race to return a list of point values
            race_vals = list()
            for i, race in enumerate(self.races):
                series.add_race(race)

                if len(series.valid_races()) == 0:
                    continue

                race_vals.append(i + 1)
                for skipper, (list_val_rank, list_val_points) in skipper_db.items():
                    list_val_rank.append(series.get_skipper_rank(skipper))
                    list_val_points.append(series.get_skipper_points(skipper))

            # Iterate for each figure
            for i in range(len(img_vals)):
                # Define the figure
                plt.ioff()
                f = plt.figure()

                # Plot each skipper that has finished
                for skipper in sorted(skipper_db.keys(), key=lambda x: self.get_skipper_rank(skipper=x)):
                    plt.plot(
                        race_vals,
                        skipper_db[skipper][i],
                        '*--',
                        label=skipper.identifier)

                # Label the plot
                plt.xlabel('Race Number')
                plt.ylabel(f'Skipper {img_types[i]}')
                plt.legend(bbox_to_anchor=(1.04, 1), borderaxespad=0)
                plt.tight_layout(rect=(0, 0, 1, 1))

                # Save results
                img_vals[i] = figure_to_data(f)

                # Close figure
                plt.close(f)

        # Compress and save the result
        self.__plot_series_rank_history = img_vals[0]
        self.__plot_series_point_history = img_vals[1]

    def get_plot_series_points(self) -> bytes:
        """
        Provides a plot of skipper point values over time for those that qualified at the end of the series
        :return: the resulting figure
        """
        if self.__plot_series_point_history is None:
            self._setup_point_rank_plots()

        return self.__plot_series_point_history

    def get_plot_series_rank(self) -> bytes:
        """
        Provides a plot of skipper rank values over time for those that qualified at the end of the series
        :return: the resulting figure
        """
        if self.__plot_series_rank_history is None:
            self._setup_point_rank_plots()

        return self.__plot_series_rank_history

    def fancy_name(self) -> str:
        """
        Provides the fancy name, removing underscores for spaces and capitalizing
        :return: fancy name string
        """
        return capitalize_words(self.name.replace('_', ' '))

    def get_series_table(self) -> str:
        """
        Calculates the resulting scores, sorts, and prints out in a table
        :return: a string table of the race results that can be printed to the console
        """
        # Initialize the string list
        str_list = list()

        # Append header parameters
        str_list.append('{:>24s}: {:d}'.format('Races Held', len(self.races)))
        str_list.append('{:>24s}: {:d}'.format('Races Needed to Qualify', self.qualify_count))
        str_list.append(('{:>20s}{:>' + '{:d}'.format(6 * len(self.races)) + 's}{:>8s}{:>8s}').format(
            'Name / Boat',
            'Races',
            'RC Pts',
            'Points'))

        tmp_str = ''.join([' '] * 20)
        tmp_str_1 = tmp_str
        tmp_str_2 = tmp_str
        for i in range(len(self.races)):
            tmp_str_1 += '{:6d}'.format(i + 1)
            tmp_str_2 += '{:>6s}'.format('----')

        str_list.append(tmp_str_1)
        str_list.append(tmp_str_2)

        for skipper in self.get_all_skippers_sorted():
            skipper_line = '{:>20s}'.format(skipper.identifier)

            for race in self.races:
                result = race.get_skipper_result_string(skipper)
                if result is not None:
                    skipper_line += '{:>6s}'.format(str(result))
                else:
                    skipper_line += '{:>6s}'.format('-')

            skipper_line += ' |'

            points = self.get_skipper_points(skipper)
            rc_pts = self.skipper_rc_points(skipper)

            if rc_pts is not None:
                skipper_line += f'{rc_pts:6.1f}'
            else:
                skipper_line += f'{"na":>6s}'

            if points is not None:
                skipper_line += f'{points:8.1f}'
            else:
                skipper_line += f'{"DNQ":>8s}'

            str_list.append(skipper_line)

        # Return the results
        return '\n'.join(str_list)
