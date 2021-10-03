"""
Provides a class to maintain a particular fleet instance
"""

from typing import Dict, List, Optional

from .. import utils

from .boat_type import BoatType
from .wind_map import WindMap


class Fleet:
    """
    A class to contain the boats specified for a given fleet, allowing for different generations
    of handicap parameters
    """
    def __init__(
            self,
            name: str,
            boat_types: Dict[str, BoatType],
            source: Optional[str],
            wind_map: WindMap):
        """
        Initializes the fleet with the input parameters
        :param name: The name of the fleet
        :param boat_types: List of the boat types within the fleet
        :param wind_map: A wind map to use to provide information
        :param source: A string indicating the source of the information
        """
        self.name = name
        self.boat_types = boat_types
        self.wind_map = wind_map
        self.source = source

        # Set the boat fleet
        for b in self.boat_types.values():
            b.fleet = self

    def boat_types_sorted(self) -> List[BoatType]:
        """
        Returns a list of sorted boats
        :return: list of BoatType
        """
        boat_list = [b for b in self.boat_types.values()]
        boat_list.sort(key=lambda x: x.code)
        return boat_list

    def get_boat(self, boat_code: str) -> BoatType:
        """
        Attempts to find the boat associated with the given boat code. Returns None if no boat exists
        :param boat_code: The input string to check for a boat type. This will be lower-cased
        :return: the boat, if provided. Otherwise, None
        """
        if boat_code.lower() in self.boat_types:
            return self.boat_types[boat_code.lower()]
        else:
            raise ValueError(f'{boat_code} does not exist in {self.name} fleet data')

    def dpn_len(self) -> int:
        """
        Provides the maximum number of DPN values for each boat
        :return: the maximum number of DPN values
        """
        max_len = 0
        for b in self.boat_types.values():
            max_len = max(max_len, len(b.dpn_values))
        return max_len

    def fancy_name(self) -> str:
        """
        Provides the fancy name, removing underscores for spaces and capitalizing
        :return: fancy name string
        """
        return utils.capitalize_words(self.name.replace('_', ' '))
