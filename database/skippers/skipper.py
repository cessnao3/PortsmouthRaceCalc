"""
Provides data inherent to a skipper object
"""

from typing import Any, Dict, Optional

from .. import utils


class Skipper:
    def __init__( self, identifier: str):
        """
        Defines a skipper object used in the race
        :param identifier: identification string used to match a skipper object with race performance
        """
        self.identifier = identifier

    def __hash__(self) -> int:
        """
        Provides the identifier as the primary hash method
        :return: the hash of the skipper
        """
        return hash(self.identifier)

    def __eq__(self, other: Any) -> bool:
        """
        Returns true if the other object is a Skipper and if this and the other object share the
        same parameter values
        :param other: the other Skipper object to compare against
        :return: True if the identifiers are equal in lower-case
        """
        if isinstance(other, Skipper):
            return self.identifier == other.identifier
        else:
            return False
