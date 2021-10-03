"""
Provides functions to help maintain plotting
"""

import io


def figure_to_data(figure) -> bytes:
    # Save the image to a memory buffer
    buf = io.BytesIO()
    figure.savefig(
        buf,
        format='png',
        transparent=True)
    buf.seek(0)
    return buf.read()
