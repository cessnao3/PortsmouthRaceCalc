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
        self.boat_overrides = boat_overrides
        self._skipper_rc_pts = None
        self._skippers = None
        self._points = None
        self._scatter_plot = None
        self._pie_plot = None

    def reset(self):
        """
        Resets any stored calculated parameters and sets the race index parameter for each race
        """
        race_counter = 0
        for r in self.races:
            r.reset()
            r.set_index(race_counter)
            race_counter += 1
        self._skipper_rc_pts = None
        self._skippers = None
        self._points = None
        self._scatter_plot = None
        self._pie_plot = None

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
        for r in [r for r in self.races if skipper_id in r.race_times]:
            # Add to the count if finished or rc
            if r.valid_for_rc(skipper_id):
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
            points = dict()

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
                for r in [r for r in self.races if r.valid_for_rc(skip_id)]:
                    # Obtain the results
                    results = r.race_results()

                    value_to_add = None

                    # Add the results to the list if the skipper has a result
                    if skip_id in results:
                        value_to_add = results[skip_id]
                    elif skip_id in r.race_times and r.race_times[skip_id].is_rc():
                        value_to_add = self.skipper_rc_points(skip_id)

                    if value_to_add is not None:
                        points_list.append(value_to_add)

                # Add the sum of the lowest to qualify
                points_list.sort()

                if len(points_list) > 0:
                    points[skip_id] = points_list[:self.qualify_count]

            # Append the result to the static variable
            self._points = points

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

            all_skipper_instances = [rt.skipper for r in self.races for rt in r.race_times.values()]

            for s in all_skipper_instances:
                if s not in skippers:
                    skippers.append(s)

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

        # Then, sort by RC points
        def rc_pts_sort(s):
            rc_pts = self.skipper_rc_points(s.identifier)
            if rc_pts is None:
                return 100
            else:
                return rc_pts
        skippers.sort(key=lambda x: rc_pts_sort(x))

        # Next, sort by the score
        skippers.sort(key=lambda x: scores[x.identifier])

        # Return the result
        return skippers

    def scatter_plot(self):
        """
        Provides a plot of the fraction of corrected / minimum race time as a function of race score
        :return: An encoded base64 HTML source string of figure, empty on failure
        :rtype: str
        """
        if self._scatter_plot is None:
            plt = get_pyplot()
            img_str = ''

            if plt is not None:
                f = plt.figure()

                for race in self.valid_races():
                    # Define the result list for the scatter plot
                    results_list = list()

                    # Add each valid item to the scatter plot
                    for skipper, score in race.race_results().items():
                        rt = race.race_times[skipper]
                        if rt.finished() and rt.fip_val is None:
                            results_list.append((score, rt.corrected_time_s / race.min_time_s()))

                    # Sort the values
                    results_list.sort(key=lambda x: x[0])

                    # Plot results
                    plt.plot([x[0] for x in results_list], [y[1] for y in results_list], 'o--')

                # Assign the legend and axes labels
                leg = plt.legend(['Race {:d}'.format(r.race_num) for r in self.valid_races()], loc='upper left')
                leg.get_frame().set_alpha(0.5)
                plt.xlabel('Score [points]')
                plt.ylabel('Normalized Finish Time [corrected / shortest]')

                # Encode the image
                img_str = figure_to_base64(f)

            # Memoize the plot
            self._scatter_plot = img_str

        # Return the result
        return self._scatter_plot

    def boat_pie_chart(self):
        """
        Provides a pie chart for the count for each existing boat in the series
        :return: An encoded base64 HTML source string of figure, empty on failure
        :rtype: str
        """
        if self._pie_plot is None:
            # Initialize plotting requirements
            plt = get_pyplot()
            img_str = ''

            if plt is not None:
                # Obtain the boats for each skipper
                skip_boat_dict = dict()
                boat_type_dict = dict()

                for r in self.races:
                    for rt in r.race_times.values():
                        if rt.skipper.identifier not in skip_boat_dict and rt.skipper.identifier in r.race_results():
                            skip_boat_dict[rt.skipper.identifier] = rt.boat.code

                            if rt.boat.code not in boat_type_dict:
                                boat_type_dict[rt.boat.code] = 0
                            boat_type_dict[rt.boat.code] += 1

                combined = [(key, val) for key, val in boat_type_dict.items()]
                labels = [v[0].upper() for v in combined]
                sizes = [v[1] for v in combined]

                def percent2count(percent):
                    return '{:1.0f}'.format(round(percent/100.0 * sum(sizes)))

                f = plt.figure()
                ax = plt.gca()
                ax.pie(sizes, labels=labels, autopct=percent2count, explode=[0.03 for i in combined])
                ax.axis('equal')

                img_str = figure_to_base64(f)

            self._pie_plot = img_str

        return self._pie_plot

    def fancy_name(self):
        """
        Provides the fancy name, removing underscores for spaces and capitalizing
        :return: fancy name string
        :rtype: str
        """
        return capitalize_words(self.name.replace('_', ' '))

    def get_series_table(self):
        """
        Calculates the resulting scores, sorts, and prints out in a table
        :return: a string table of the race results that can be printed to the console
        :rtype: str
        """
        # Initialize the string list
        str_list = list()

        # Append header parameters
        str_list.append('{:>24s}: {:d}'.format('Races Held', len(self.races)))
        str_list.append('{:>24s}: {:d}'.format('Races Needed to Qualify', self.qualify_count))
        str_list.append(('{:>20s}{:>' + '{:d}'.format(4 * len(self.races)) + 's}{:>8s}{:>8s}').format(
            'Name / Boat',
            'Races',
            'RC Pts',
            'Points'))

        tmp_str = ''.join([' '] * 20)
        tmp_str_1 = tmp_str
        tmp_str_2 = tmp_str
        for i in range(len(self.races)):
            tmp_str_1 += '{:4d}'.format(i + 1)
            tmp_str_2 += '{:>4s}'.format('--')

        str_list.append(tmp_str_1)
        str_list.append(tmp_str_2)

        for skipper in self.get_all_skippers_sorted():
            skipper_line = '{:>20s}'.format(skipper.identifier)

            for race in self.races:
                result = race.get_skipper_result(skipper.identifier)
                if result is not None:
                    skipper_line += '{:>4s}'.format(str(result))
                else:
                    skipper_line += '{:>4s}'.format('-')

            skipper_line += ' |'

            points = self.skipper_points(skipper.identifier)
            rc_pts = self.skipper_rc_points(skipper.identifier)

            if rc_pts is not None:
                skipper_line += '{:6.1f}'.format(rc_pts)
            else:
                skipper_line += '{:>6s}'.format('na')

            if points is not None:
                skipper_line += '{:8.1f}'.format(points)
            else:
                skipper_line += '{:>8s}'.format('DNQ')



            str_list.append(skipper_line)




        # Return the results
        return '\n'.join(str_list)