"""
Boat Statistics provides overall statistics for a given boat
"""

from typing import Dict, List, Optional, Tuple, Callable

from ..skippers import Skipper
from ..fleets import BoatType
from ..series import Series
from ..utils.plotting import get_pyplot, figure_to_base64, fig_compress, fig_decompress


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
        self.__plot_points: Optional[bytes] = None

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

    def _can_plot(self) -> bool:
        """
        Determines if the plot can be plotted
        :return: true if a plot can exist
        """
        return self.get_total_point_counts() > 0


    def get_figure_functions(self) -> List[Tuple[str, Callable[[], str]]]:
        """
        Provides a list of all figure generation values
        :return: a list of functions to call to generate figures
        """
        # Skip plot if no races provided
        if self._can_plot():
            return [(f'Boat_{self.boat.code}_Points', self.get_plot_points)]
        else:
            return list()

    def get_plot_points(self) -> str:
        """
        Provides the plot string for the race pie chart
        :return: the base64-encoded string, or empty string if unable to plot
        """
        if self.__plot_points is None:
            # Get the plot instance
            plt = get_pyplot()
            img_str = ''

            if plt is not None:
                # Skip if no races were performed
                if self._can_plot():
                    # Determine the total number of races
                    num_races = self.get_total_point_counts()

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
                    ax.pie(
                        race_percentages,
                        labels=race_labels,
                        explode=[0.05 for _ in race_entries],
                        normalize=True)

                    s = f.get_size_inches()
                    f.set_size_inches(w=1.15 * s[0], h=s[1])

                    img_str = figure_to_base64(f)
                    plt.close(f)

            self.__plot_points = fig_compress(img_str)

        return fig_decompress(self.__plot_points)
