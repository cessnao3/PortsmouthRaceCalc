"""
Provides functions to help maintain plotting
"""

import base64
import gzip
import importlib
import io


# Define the initial stored result
__plt = None
__plt_import = False

# Define Flags
__COMPRESSION_ENABLED = True


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


def fig_compress(fig_b64: str) -> bytes:
    """
    Compresses the given figure to save space
    :param fig_b64: the figure encoded in Base64
    :return: the associated compressed bytes
    """
    if __COMPRESSION_ENABLED:
        return gzip.compress(fig_b64.encode('utf-8'))
    else:
        return fig_b64.encode('utf-8')


def fig_decompress(fig_bytes: bytes) -> str:
    """
    Decompresses the given figure to Base64
    :param fig_bytes: the figure bytes
    :return: the resulting Base64 string
    """
    if __COMPRESSION_ENABLED:
        return gzip.decompress(fig_bytes).decode('utf-8')
    else:
        return fig_bytes.decode('utf-8')


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
