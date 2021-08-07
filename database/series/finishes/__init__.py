"""
Defines the race finish types
"""

from .interface import RaceFinishInterface

from .time import RaceFinishTime

from .did_not_finish import RaceFinishDNF
from .disqualification import RaceFinishDQ
from .finish_in_place import RaceFinishFIP
from .race_committee import RaceFinishRC
