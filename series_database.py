"""
Provides a database for use in calculating and scoring a race series
"""

from boat_database import Fleet
from skipper_database import Skipper
from race_utils import capitalize_words, round_score, get_pyplot, figure_to_base64


class Series:
    """
    Defines a series of races, defined by a fleet type and a list of races
    """
    def __init__(self, name, qualify_count, valid_required_skippers, fleet, boat_overrides):
        """
        Initializes the series with the input parameters
        :param name: The unique name of the series
        :type name: str
        :param qualify_count: The number of races required to qualify for a scoring place
        :type qualify_count: int
        :param valid_required_skippers: The number of racers needed to indicate a valid race
        :type valid_required_skippers: int
        :param fleet: The fleet object to be used to define the corrected scoring parameters
        :type fleet: Fleet
        :param boat_overrides: A dictionary of boat overrides, containing {skipper_identifier: boat_identifier}
        :type boat_overrides: {str: str}
        """
        self.name = name
        self.qualify_count = qualify_count
        self.valid_required_skippers = valid_required_skippers
        self.fleet = fleet
        self.races = list()
        self.boat_overrides = boat_overrides if boat_overrides is not None else dict()
        self._skipper_rc_pts = None
        self._skippers = None
        self._points = None

    def reset(self):
        """
        Resets any stored calculated parameters and sets the race index parameter for each race
        """
        race_counter = 0
        for r in self.races:
            r.reset()
            r.race_index = race_counter
            race_counter += 1
        self._skipper_rc_pts = None
        self._skippers = None
        self._points = None

    def skipper_qualifies(self, skipper_id):
        """
        Returns whether a skipper has met the qualification count for the series
        :param skipper_id: The skipper identifier to check
        :type skipper_id: str
        :return: True if the skipper qualifies, False otherwise
        :rtype: bool
        """
        # Initialize a count
        count = 0

        # Iterate over all valid races
        for r in [r for r in self.valid_races() if skipper_id in r.race_times]:
            # Extract the race time object
            rt = r.race_times[skipper_id]

            # Add to the count if finished or rc
            if skipper_id in r.race_results() or rt.is_rc():
                count += 1

        # Return true if the count meets the qualify count threshold
        return count >= self.qualify_count

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
                # Extract the skipper_id
                skip_id = skip.identifier

                # Obtain the races for the skipper
                skipper_races = [r for r in self.valid_races() if skip_id in r.race_times]

                # Obtain the results from each of the finished races and sort
                point_values = [r.race_results()[skip_id] for r in skipper_races if skip_id in r.race_results()]
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
                self._skipper_rc_pts[skip_id] = score

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
                # Extract the skipper identifier
                skip_id = skip.identifier

                # Obtain the results for a given skipper for all races
                points_list = list()

                # Ignore if the skipper doesn't qualify
                if not self.skipper_qualifies(skip_id):
                    continue

                # Iterate over each race
                for r in self.valid_races():
                    # Obtain the results
                    results = r.race_results()

                    # Add the results to the list if the skipper has a result
                    if skip_id in results:
                        points_list.append(results[skip_id])
                    elif skip_id in r.race_times and r.race_times[skip_id].is_rc():
                        points_list.append(self.skipper_rc_points(skip_id))

                # Add the sum of the lowest to qualify
                points_list.sort()
                self._points[skip_id] = points_list[:self.qualify_count]

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

    def valid_races(self):
        """
        Returns the number of valid races held
        :return: count of valid races
        :rtype: list of Race
        """
        return [r for r in self.races if r.valid()]

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

    def scatter_plot(self):
        """
        Provides a plot of the fraction of corrected / minimum race time as a function of race score
        :return: An encoded base64 HTML source string of figure, or None if errors
        :rtype: str or none
        """
        plt = get_pyplot()
        img_str = None

        if plt is not None:
            f = plt.figure()

            for race in self.valid_races():
                results_list = list()

                for skipper, score in race.race_results().items():
                    if race.race_times[skipper].finished():
                        results_list.append((score, race.race_times[skipper].corrected_time_s / race.min_time_s()))

                # Sort the values
                results_list.sort(key=lambda x: x[0])

                # Plot results
                plt.plot([x[0] for x in results_list], [y[1] for y in results_list], 'o--')

            # Assign the legend and axes labels
            plt.legend(['Race {:d}'.format(r.race_index + 1) for r in self.valid_races()], loc='upper_left')
            plt.xlabel('Score [points]')
            plt.ylabel('Normalized Finish Time [corrected / shortest]')

            img_str = figure_to_base64(f)

        return img_str

    def fancy_name(self):
        """
        Provides the fancy name, removing underscores for spaces and capitalizing
        :return: fancy name string
        :rtype: str
        """
        return capitalize_words(self.name.replace('_', ' '))
