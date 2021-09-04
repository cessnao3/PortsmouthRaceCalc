"""
Skipper Statistics provides overall statistics for a given sailor
"""

from typing import Dict, List, Optional, Tuple

from ..fleets import BoatType
from ..skippers import Skipper
from ..utils.plotting import get_pyplot, figure_to_base64, fig_compress, fig_decompress


class SkipperStatistics:
    """
    Provides statistics for a particular sailor
    """

    def __init__(
            self,
            skipper: Skipper,
            point_counts: Dict[int, int],
            boats_used: Dict[BoatType, int]):
        """
        Defines the statistics for a given skipper
        :param skipper: the skipper the statistics are computed for
        :param point_counts: a dictionary of the finish places as keys, with number of times finished as values
        :param boats_used: a dictionary of the boats used as keys, with the number of races finished as values
        """
        self.skipper = skipper
        self.race_counts = point_counts
        self.boats_used = boats_used
        self._plot_race_results: Optional[bytes] = None
        self.__plot_boats_used: Optional[bytes] = None

    def get_race_counts_sorted(self) -> List[Tuple[int, int]]:
        """
        Provides a sorted list of race results
        :return: a list of tuples containing the (race result, number of times for race result), sorted from lowest
        result to highest result
        """
        return [
            (finish, self.race_counts[finish])
            for finish
            in sorted(self.race_counts.keys())]

    def get_total_race_counts(self) -> int:
        """
        Provides the total number of races in the race result dictionary
        :return: number of races finished
        """
        return sum(self.race_counts.values())

    def get_total_boat_counts(self) -> int:
        """
        Provides the total number of boat races in the boat dictionary
        :return: the total number of boats used
        """
        return sum(self.boats_used.values())

    def generate_figures(self) -> None:
        """
        Generates all figures at once when requested
        """
        self.get_plot_race_results()
        self.get_plot_boats()

    def get_plot_race_results(self) -> str:
        """
        Provides the plot string for the race pie chart
        :return: the base64-encoded string, or empty string if unable to plot
        """
        if self._plot_race_results is None:
            # Get the plot instance
            plt = get_pyplot()
            img_str = ''

            if plt is not None:
                # Determine the total number of races
                num_races = self.get_total_race_counts()

                # Skip if no races were done
                if num_races > 0:
                    # Determine the race entries (sorted finish values) and resulting percentages
                    race_entries = list(sorted(self.race_counts.keys()))
                    race_percentages = [self.race_counts[i] / num_races for i in race_entries]

                    # Calculate the resulting labels
                    race_labels = [
                        f'Place {v} ({self.race_counts[v]}, {self.race_counts[v] / num_races * 100:.0f}%)'
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

            self._plot_race_results = fig_compress(img_str)
        return fig_decompress(self._plot_race_results)

    def get_plot_boats(self) -> str:
        """
        Provides the plot string for the boat pie chart
        :return: the base64-encoded string, or empty string if unable to plot
        """
        if self.__plot_boats_used is None:
            # Get the plot instance
            plt = get_pyplot()
            img_str = ''

            if plt is not None:
                # Determine the total number of boats
                num_boats = self.get_total_boat_counts()

                if num_boats > 0:
                    # Determine the boats list and the percentage each boat was used
                    boats_list = list(self.boats_used.keys())
                    boat_percentages = [self.boats_used[boat] / num_boats for boat in boats_list]

                    # Calculate the resulting labels
                    boat_labels = [
                        f'{boat.code} ({self.boats_used[boat]}, {self.boats_used[boat] / num_boats * 100:.0f}%)'
                        for boat
                        in boats_list]

                    # Plot the results
                    f = plt.figure()
                    ax = f.gca()
                    ax.pie(
                        boat_percentages,
                        labels=boat_labels,
                        explode=[0.05 for _ in boats_list],
                        normalize=True)

                    s = f.get_size_inches()
                    f.set_size_inches(w=1.15 * s[0], h=s[1])

                    img_str = figure_to_base64(f)
                    plt.close(f)

            # Save the figure
            self.__plot_boats_used = fig_compress(img_str)

        # Return the resulting value
        return fig_decompress(self.__plot_boats_used)
