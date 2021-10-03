"""
Defines the interface to use for "other" files
"""


class OtherFileInterface:
    def get_name(self) -> str:
        raise NotImplementedError()

    def to_html(self) -> str:
        raise NotImplementedError()
