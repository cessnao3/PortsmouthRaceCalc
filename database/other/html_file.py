"""
Provides the other file implementation for an HTML file
"""


from os import PathLike
from pathlib import Path
from typing import Union, Optional

from .other_interface import OtherFileInterface


class OtherHtmlFile(OtherFileInterface):
    def __init__(self, filepath: Union[PathLike, str], name: Optional[str] = None):
        self._file = Path(filepath)
        self._name = name if name is not None else self._file.stem

    def get_name(self) -> str:
        return self._name

    def to_html(self) -> str:
        with self._file.open('r') as f:
            return f.read()
