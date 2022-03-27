from pathlib import Path

import pandas as pd

PATH = Path(__file__).parent / "fish_data"


def get_eod_data(species: str) -> pd.DataFrame:
    """Load the provided EOD data.

    :param species: Name of the species
    :return: EOD Data in 3 columns (x, relative phase, EOD)
    """

    pth = PATH / species.lower()
    return pd.read_csv(pth / "eod.tsv", delimiter="\t", names=["x", "phase", "eod"])


def get_body_data(species: str) -> pd.DataFrame:
    """Load the body coordinates into a dataframe.

    :param species: Optional path to a new body specification
    :return: Body in 2 columns (x, y)
    """

    pth = PATH / species.lower()
    return 100 * pd.read_csv(pth / "body.csv", header=None, names=["x", "y"])  # m -> cm
