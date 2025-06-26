from typing import Tuple, List


# I don't know of the rational of this.
# Someone needs to review this
def canonicalize_category(archive: str, subject_class: str) -> Tuple[str, str]:
    if archive == "math" and subject_class == "MP":
        archive = "math-ph"
        subject_class = ""
    elif archive == "stat" and subject_class == "TH":
        archive = "math"
        subject_class = "ST"
    elif archive == "math" and subject_class == "IT":
        archive = "cs"
    elif archive == "q-fin" and subject_class == "EC":
        archive = "econ"
        subject_class = "GN"
    elif archive == "cs" and subject_class == "NA":
        archive = "math"
        subject_class = "NA"
    elif archive == "cs" and subject_class == "SY":
        archive = "eess"
        subject_class = "SY"

    return archive, subject_class


def pretty_category(archive: str, subject_class: str) -> str:
    if not subject_class:
        subject_class = "*"
    return f"{archive}.{subject_class}"


def join_names(names: List[str]) -> str:
    """
    Join a list of names in a grammatically correct way.
    Equivalent to tapir_en_join in the Perl code.

    Args:
        names: List of names to join

    Returns:
        str: Joined names string
    """
    if not names:
        return ""

    if len(names) == 1:
        return names[0]

    if len(names) == 2:
        return f"{names[0]} and {names[1]}"

    # For three or more names
    return ", ".join(names[:-1]) + f", and {names[-1]}"

