"""
Utility functions for checking case
"""


def check_constant_case(input_str: str) -> bool:
    """
    Checks if a string uses constant case

    :param input_str: A string
    :return: Returns a bool of if the string follows constant case
    """
    allowed_characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ" "0123456789" "_"
    return all([char in allowed_characters for char in input_str])


def check_snake_case(input_str: str) -> bool:
    """
    Checks if a string uses snake case

    :param input_str: A string
    :return: Returns a bool of if the string follows snake case
    """
    allowed_characters = "abcdefghijklmnopqrstuvwxyz" "0123456789" "_"
    return all([char in allowed_characters for char in input_str])


def check_variable_name_descriptiveness(input_str: str) -> bool:
    """
    Checks if a string is a descriptive variable identifier

    This follows some rules to determine if a variable identifier is
    not 'descriptive enough'.#

    Generally, single letter variable names are flagged other than
    if they are in {a, b, c, i, j, w, x, y, z}.

    All other variable names are allowed.

    :param input_str: A string
    :return: Returns a bool of if the string is descriptive
    """
    if len(input_str) == 1 and input_str not in "abcdijwxyz":
        return False
    return True
