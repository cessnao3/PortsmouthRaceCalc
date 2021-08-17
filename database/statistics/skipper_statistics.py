"""

"""

from typing import Optional, Dict

from ..skippers import Skipper
from ..utils.plotting import get_pyplot, figure_to_base64


class SkipperStatistics:
    """

    """

    def __init__(
            self,
            skipper: Skipper,
            race_counts: Dict[int, int]):
        self.skipper = skipper
        self.race_counts = race_counts
        self._race_plot: Optional[str] = None

    def get_race_plot(self) -> str:
        if self._race_plot is None:
            # Get the plot instance
            plt = get_pyplot()
            img_str = ''

            if plt is not None:
                # Determine the total number of races
                num_races = sum(self.race_counts.values())

                # Determine the race entries (sorted finish values) and resulting percentages
                race_entries = list(sorted(self.race_counts.keys()))
                race_percentages = [self.race_counts[i] / num_races for i in race_entries]

                # Calculate the resulting labels
                race_labels = [f'Place {v} ({self.race_counts[v]}, {self.race_counts[v] / num_races * 100:.0f}%)' for v in race_entries]

                # Plot the results
                f = plt.figure()
                ax = f.gca()
                ax.pie(race_percentages, labels=race_labels, explode=[0.05 for _ in race_entries])

                s = f.get_size_inches()
                f.set_size_inches(w=1.15 * s[0], h=s[1])

                img_str = figure_to_base64(f)

            self._race_plot = img_str
        return self._race_plot
