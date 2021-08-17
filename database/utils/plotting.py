"""
Provides functions to help maintain plotting
"""

import base64
import importlib
import io


# Define the initial stored result
__plt = None
__plt_import = False


def get_pyplot():
    """
    Imports matplotlib and provides a function to provide the matplotlib.pyplot instance
    """
    global __plt
    global __plt_import

    # Only try to get matplotlib once
    if not __plt_import:
        # Attempt to get imports
        try:
            matplotlib = importlib.import_module('matplotlib')
            matplotlib.use('Agg')
            plt = importlib.import_module('matplotlib.pyplot')
            __plt = plt
        except ImportError:
            print('Could not import pyplot')

        __plt_import = True

    return __plt


def figure_to_base64(figure) -> str:
    """
    Turns a matplotlib figure into a HTML-compatible image source string
    :param figure: Matplotlib figure object
    :return: HTML data encoding of figure
    """
    # Save the image to a memory buffer
    buf = io.BytesIO()
    figure.savefig(
        buf,
        format='png',
        transparent=True)
    buf.seek(0)

    # Encode the buffer bytes as a string
    return 'data:image/png;base64,{:s}'.format(base64.b64encode(buf.read()).decode('utf-8'))
