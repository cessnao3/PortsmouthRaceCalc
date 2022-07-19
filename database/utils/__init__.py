"""
Common utilities useful for loading race parameters and performing calculations
"""

import csv
from typing import Any, Callable, Dict, List

import decimal


def load_from_csv(csv_data: str, row_func: Callable[[Dict], Any], expected_header: List[str] = None) -> None:
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
        # and continue to not extract a boat from these
        if header_cols is None:
            header_cols = [v.lower().strip() for v in row]

            if expected_header is not None:
                if len(header_cols) != len(expected_header):
                    raise ValueError(
                        f"Header columns {len(header_cols)} don't match the expected number {len(expected_header)}")
                for i in range(len(expected_header)):
                    if header_cols[i] != expected_header[i]:
                        raise ValueError(
                            f"Header column {i} has {header_cols[i]}, expected {expected_header[i]}")

        # Otherwise, parse a normal row
        else:
            # Otherwise, print error if the row lengths don't match up with the header
            if len(row) != len(header_cols):
                print(f"ERROR! {', '.join(row)}")
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


def round_score(score_in: decimal.Decimal) -> decimal.Decimal:
    """
    Rounds out the score to provide 0 or 1 decimal places
    :param score_in: Input score
    :return: rounded score
    """
    assert isinstance(score_in, decimal.Decimal)

    with decimal.localcontext(ctx=None) as ctx:
        ctx.rounding = decimal.ROUND_HALF_UP
        return decimal.Decimal(round(score_in * 10)) / 10


def format_time(time_s: int) -> str:
    """
    Formats the time in seconds into a mm:ss format
    :param time_s: The input time, in seconds, to format
    :return: string of formatted time
    """
    s_val = time_s % 60
    m_val = int((time_s - s_val) / 60)
    return f"{m_val:02d}:{round(s_val):02d}"
