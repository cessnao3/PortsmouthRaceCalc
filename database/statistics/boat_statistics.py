"""
Boat Statistics provides overall statistics for a given boat
"""

from typing import Dict, List, Optional, Tuple

from ..skippers import Skipper
from ..fleets import BoatType
from ..series import Series
from ..utils.plotting import figure_to_data

import matplotlib.pyplot as plt


class BoatStatistics:
    """
    Provides statistics for a particular boat type
    """

    def __init__(
            self,
            boat: BoatType,
            point_counts: Dict[int, int],
            skippers: List[Skipper],
            series: List[Series]):
        """
        Defines the statistics for a given boat type
        :param boat: the boat the statistics are computed for
        :param point_counts: a dictionary of the finish places as keys, with number of times finished as values
        :param skippers: the list of skippers that have used the boat
        """
        self.boat = boat
        self.point_counts = point_counts
        self.skippers = skippers
        self.series = series

    def get_point_counts_sorted(self) -> List[Tuple[int, int]]:
        """
        Provides a sorted list of race results
        :return: a list of tuples containing the (race result, number of times for race result), sorted from lowest
        result to highest result
        """
        return [
            (finish, self.point_counts[finish])
            for finish
            in sorted(self.point_counts.keys())]

    def get_total_point_counts(self) -> int:
        """
        Provides the total number of races in the race result dictionary
        :return: number of races finished
        """
        return sum(self.point_counts.values())

    def has_nonzero_races(self) -> bool:
        """
        Returns true if the race has a nonzero race count
        :return: True if the boat has been in one or more series entries
        """
        return self.get_total_point_counts() > 0

    def get_plot_points(self) -> Optional[bytes]:
        """
        Provides the plot string for the race pie chart
        :return: the base64-encoded string, or empty string if unable to plot
        """
        # Determine the total number of races
        num_races = self.get_total_point_counts()

        # Return if no entries are provided
        if num_races == 0:
            return None

        # Determine the race entries (sorted finish values) and resulting percentages
        race_entries = list(sorted(self.point_counts.keys()))
        race_percentages = [self.point_counts[i] / num_races for i in race_entries]

        # Calculate the resulting labels
        race_labels = [
            f'Place {v} ({self.point_counts[v]}, {self.point_counts[v] / num_races * 100:.0f}%)'
            for v
            in race_entries]

        # Plot the results
        f = plt.figure()
        ax = f.gca()
        if self.get_total_point_counts() > 0:
            ax.pie(
                race_percentages,
                labels=race_labels,
                explode=[0.05 for _ in race_entries],
                normalize=True)
        else:
            ax.pie(
                [1],
                labels=['None'],
                normalize=True)

        s = f.get_size_inches()
        f.set_size_inches(w=1.15 * s[0], h=s[1])

        img_data = figure_to_data(f)
        plt.close(f)
        return img_data
