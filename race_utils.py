"""
Common utilities useful for loading race parameters and performing calculations
"""

import csv


def load_from_csv(csv_data, row_func, expected_header=None):
    """
    Reads the input CSV files, checking the headers if applicable. Each of the rows are parsed into a dictionary
    to be input into the row_func function for local calculations
    :param csv_data: string containing all the CSV data
    :type csv_data: str
    :param row_func: function to be called with the row dictionary, with lower-case headers used as keys
    :param expected_header: list of expected header strings in lower-case
    :type expected_header: list of str
    :return: None
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


def capitalize_words(str_in):
    """
    Capitalizes each word in a string
    :param str_in: input string to capitalize
    :type str_in: str
    :return: output string with words capitalized
    :rtype: str
    """
    return ' '.join([s.capitalize() for s in str_in.split(' ')])


def round_score(score_in):
    """
    Rounds out the score to provide 0 or 1 decimal places
    :param score_in: Input score
    :type score_in: int or float
    :return: rounded score
    :rtype: int or float
    """
    # Add a small bias so that 0.5 and up get rounded up
    score_in += 1e-4

    # If the score is very close to an integer, return an integer rounding
    if abs(round(score_in) - round(score_in, 1)) < 0.01:
        return round(score_in)
    # Otherwise, return a float rounding to first decimal
    else:
        return round(score_in, 1)
