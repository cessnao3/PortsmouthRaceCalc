"""
Provides functions to help maintain plotting
"""

from typing import Callable, Union


def _create_get_pyplot() -> Callable:
    """
    Imports matplotlib and provides a function to provide the matplotlib.pyplot instance
    """
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ImportError:
        print('Could not import pyplot')
        matplotlib = None
        plt = None

    def get_pyplot_inner() -> Union['matplotlib.pyplot', None]:
        """
        Returns the pyplot instance
        """
        return plt

    return get_pyplot_inner


get_pyplot = _create_get_pyplot()
