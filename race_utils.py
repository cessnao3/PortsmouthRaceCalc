"""
Common utilities useful for loading race parameters and performing calculations
"""

import csv
import io
import base64
import typing


def load_from_csv(csv_data: str, row_func: typing.Callable, expected_header: typing.List[str] = None) -> None:
    """
    Reads the input CSV files, checking the headers if applicable. Each of the rows are parsed into a dictionary
    to be input into the row_func function for local calculations
    :param csv_data: string containing all the CSV data
    :param row_func: function to be called with the row dictionary, with lower-case headers used as keys
    :param expected_header: list of expected header strings in lower-case
    """
    # Define the CSV reader
    reader = csv.reader(csv_data.splitlines())

    # Define an empty parameter for the header columns
    header_cols = None

    # Iterate over each row
    for row in reader:
        # Extract the string values for each row
        row = [v.strip() for v in row]

        # If the header columns are None (first row), set the header columns to the string values
        # and continue so as to not extract a boat from these
        if header_cols is None:
            header_cols = [v.lower().strip() for v in row]

            if expected_header is not None:
                if len(header_cols) != len(expected_header):
                    raise ValueError(
                        'Header columns {:d} don\'t match the expected number {:d}'.format(
                            len(header_cols),
                            len(expected_header)))
                for i in range(len(expected_header)):
                    if header_cols[i] != expected_header[i]:
                        raise ValueError(
                            'Header column {:d} has {:s}, expected {:s}'.format(
                                i,
                                header_cols[i],
                                expected_header[i]))

        # Otherwise, parse a normal row
        else:
            # Otherwise, print error if the row lengths don't match up with the header
            if len(row) != len(header_cols):
                print('ERROR! {:s}'.format(', '.join(row)))
                continue

            # Create a dictionary for the row based on the header columns and current values
            row_dict = {v[0]: v[1] for v in zip(header_cols, row)}

            # call the function
            row_func(row_dict)


def capitalize_words(str_in: str) -> str:
    """
    Capitalizes each word in a string
    :param str_in: input string to capitalize
    :return: output string with words capitalized
    """
    return ' '.join([s.capitalize() for s in str_in.split(' ')])


def round_score(score_in: typing.Union[int, float, None]) -> typing.Union[int, float, None]:
    """
    Rounds out the score to provide 0 or 1 decimal places
    :param score_in: Input score
    :return: rounded score
    """
    # Return None
    if score_in is None:
        return score_in

    # Add a small bias so that 0.5 and up get rounded up
    score_in += 1e-4

    # If the score is very close to an integer, return an integer rounding
    if abs(round(score_in) - round(score_in, 1)) < 0.01:
        return round(score_in)
    # Otherwise, return a float rounding to first decimal
    else:
        return round(score_in, 1)


def _create_get_pyplot() -> typing.Callable:
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

    def get_pyplot_inner() -> typing.Union['matplotlib.pyplot', None]:
        """
        Returns the pyplot instance
        """
        return plt

    return get_pyplot_inner


get_pyplot = _create_get_pyplot()


def figure_to_base64(figure) -> str:
    """
    Turns a matplotlib figure into a HTML-compatible image source string
    :param figure: Matplotlib figure object
    :return: HTML data encoding of figure
    """
    # Save the image to a memory buffer
    buf = io.BytesIO()
    figure.savefig(buf, format='png', transparent=True)
    buf.seek(0)

    # Encode the buffer bytes as a string
    return 'data:image/png;base64,{:s}'.format(base64.b64encode(buf.read()).decode('utf-8'))


def format_time(time_s: int) -> str:
    """
    Formats the time in seconds into a mm:ss format
    :param time_s: The input time, in seconds, to format
    :return: string of formatted time
    """
    s_val = time_s % 60
    time_c = int((time_s - s_val) / 60)
    m_val = time_c
    return '{:02d}:{:02d}'.format(m_val, round(s_val))
