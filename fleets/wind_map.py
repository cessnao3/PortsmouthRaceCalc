"""
Class to define teh wind mapping to define how Beaufort numbers are translated into DPN values in the boat database
"""


class WindMap:
    """
    A class to map Beaufort wind numbers to an index that can be used to extract DPN
    or similar time correction factors
    """
    class Node:
        """
        A class to keep track of the wind map node parameters
        """
        def __init__(
                self,
                start_bf: int,
                end_bf: int,
                index: int):
            """
            Defines the wind map node
            :param start_bf: starting Beaufort number for wind (inclusive)
            :param end_bf: ending Beaufort number for wind (inclusive)
            :param index: index to obtain for the given wind values
            """
            # Check for type errors
            for v in (start_bf, end_bf, index):
                if type(v) != int:
                    raise TypeError('All types input into WindMap.Node must be of type int')

            # Check that start <= end
            if start_bf > end_bf:
                raise ValueError('Wind mapping start {:d} must be <= end {:d}'.format(start_bf, end_bf))

            # Save the parameters
            self.start_bf = start_bf
            self.end_bf = end_bf
            self.index = index

        def range_str(self) -> str:
            """
            Provides the range string for the given wind mapping
            :return: definitions for the range of the mapping
            :rtype: str
            """
            if self.start_bf == self.end_bf:
                return '{:d}'.format(self.start_bf)
            else:
                return '{:d}-{:d}'.format(self.start_bf, self.end_bf)

    def __init__(self, default_index: int):
        """
        Initializes the Wind Map with a default index
        :param default_index: Default index to use if no other wind mapping parameters fit
        """
        # Create the default index
        self.default = self.Node(
            start_bf=0,
            end_bf=0,
            index=default_index)
        # Initialize the empty wind map list
        self.wind_maps = list()

    def add_wind_parameters(
            self,
            start_wind: int,
            end_wind: int,
            index: int) -> None:
        """
        Adds a wind mapping for a start/end wind speed, with an index
        Raises an error if the mapping overlaps with another
        :param start_wind: starting Beaufort number
        :param end_wind: ending Beaufort number
        :param index: index to associate with the Beaufort number
        """
        # Iterate over all of the wind parameters to ensure that there are no overlaps
        for w in self.wind_maps:
            for v in (start_wind, end_wind):
                if w.start_bf <= v <= w.end_bf:
                    raise ValueError('WindMap parameter {:d} within the range of another map'.format(v))

        # Add the wind map parameter
        self.wind_maps.append(
            self.Node(
                start_bf=start_wind,
                end_bf=end_wind,
                index=index))
        self.wind_maps.sort(key=lambda x: x.start_bf)

    def get_wind_map_for_beaufort(self, bf_num: int) -> 'Node':
        """
        Provides the wind mapping node for the input Beaufort number
        :param bf_num: Input Beaufort number to find a mapping for
        :return: associated mapping for the node
        :rtype: WindMap.Node
        """
        for w in self.wind_maps:
            if w.start_bf <= bf_num <= w.end_bf:
                return w
        return self.default
