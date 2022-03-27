from dataclasses import dataclass
from typing import Dict

import pandas as pd

from fish2eod.data.load_data import get_body_data, get_eod_data
from fish2eod.data.settings import APTERONOTUS, EIGENMANNIA, FishSettings


@dataclass
class SpeciesData:
    settings: FishSettings
    body: pd.DataFrame
    eod: pd.DataFrame


class SpeciesRegistry(dict):
    """Custom WORM dictionary."""

    def __getitem__(self, item: str):
        return super().__getitem__(item.lower())

    def __setitem__(self, key, value):
        if key in self:
            raise KeyError(f"Species {key} already registered")
        super().__setitem__(key, value)


SPECIES_REGISTRY: Dict[str, SpeciesData] = SpeciesRegistry()


def register_species(name: str, body: pd.DataFrame, eod: pd.DataFrame, settings: FishSettings):
    SPECIES_REGISTRY[name] = SpeciesData(settings=settings, body=body, eod=eod)


register_species("apteronotus", get_body_data("apteronotus"), get_eod_data("apteronotus"), APTERONOTUS)
register_species("eigenmannia", get_body_data("eigenmannia"), get_eod_data("eigenmannia"), EIGENMANNIA)
