# coding=UTF-8
"""Container for geometry objects which can perform sanity checks and iterate sequentially."""

from collections import OrderedDict, defaultdict
from itertools import combinations, product
from typing import Callable, DefaultDict, Dict, Optional, Sequence, Union, overload

import matplotlib.pyplot as plt

from fish2eod.geometry.primitives import Polygon
from fish2eod.properties import SpatialFunction


class ModelGeometry:
    """Holding class for all model geometry.

    Validates domains and manages domain names and labels

    Behaves like a DB/dictionary with foreign keys
      - geometry[label: str] -> domain_id: str
      - geometry[id: int] -> domain_label: int

    :param allow_overlaps: If overlaps cause an error or a warning
    """

    BACKGROUND_LABEL = 0

    def __init__(self, allow_overlaps: bool = False):
        """Instantiate ModelGeometry."""
        self.domain_names: Dict[str, int] = dict()  # map between the name and the label

        # map between the label and geometry
        self.geometry_map: Dict[int, Sequence[Polygon]] = OrderedDict()
        self.parameters: DefaultDict[str, SpatialFunction] = defaultdict(SpatialFunction)
        self.allow_overlaps = allow_overlaps

    def clear(self):
        """Reset the model geometry."""
        self.__init__(allow_overlaps=self.allow_overlaps)

    @property
    def next_valid_label(self) -> int:  # todo rule change for default boundaries
        """Determine the next valid domain label my incrementing current max.

        :return: Next valid label
        """
        if self.domain_names:  # if there exists any current labels
            return max(self.domain_names.values()) + 1

        # background_label if no labels exist
        return self.BACKGROUND_LABEL

    def validate_intersections(self, geometry_objects: Sequence[Polygon]) -> None:
        """Validate intersections between objects on the new domain and between the new domain and old domain.

        :param geometry_objects: Geometry objects on new domain to validate
        :return: None
        """
        # abort if overlaps allowed
        if self.allow_overlaps:
            return

        overlap_bg = (self.intersects_background(new_g) for new_g in geometry_objects)
        if not all(overlap_bg):
            raise ValueError("New domain incorrectly overlaps background")

        # Check all pairwise combinations of new geometry for intersections
        new_domain_overlap = (self.check_intersection(None, g1, g2) for g1, g2 in combinations(geometry_objects, 2))
        if any(new_domain_overlap):
            raise ValueError("Overlap within new domain")

        # Check combinations of old geometries and new geometries for intersections
        pairwise_geometries = list(product(self, geometry_objects))
        new_old_overlap = (self.check_intersection(name, old_g, new_g) for (name, old_g), new_g in pairwise_geometries)
        if any(new_old_overlap):
            raise ValueError("New domain incorrectly intersects old domain")

    @overload
    def __getitem__(self, item: int) -> str:
        pass

    @overload
    def __getitem__(self, item: str) -> int:
        pass

    def __getitem__(self, item):
        """Convert a domain name into the label.

        :param item: Name of the domain to convert
        :returns: The label (id) of the domain
        """
        if isinstance(item, str):
            return self.domain_names[item]

        for existing_label, existing_integer in self.domain_names.items():
            if existing_integer == item:
                return existing_label

        raise ValueError(f"Could not look up item {item}")

    def add_domain(self, name: str, *geometry_objects: Polygon, **_) -> int:
        """Add a domain to the existing model geometry.

        :param geometry_objects: Geometry objects to add
        :param name: Name of the new domain (can be omitted for no name)
        :param _: Any optional settings/params a subclass may want to set
        :return: Label of newly added domain
        """
        label = self.next_valid_label
        if label == self.BACKGROUND_LABEL and len(geometry_objects) > 1:
            raise ValueError("Background must be a single element")

        if name in self.domain_names.keys():
            raise ValueError(f"Name: {name} already exists")

        self.validate_intersections(geometry_objects)

        # Save the name, label and the geometry objects
        self.domain_names[name] = label
        self.geometry_map[label] = geometry_objects

        return label

    def draw(self, color="Dark2", legend=False) -> None:
        """Draw the model geometry as a line drawing.

        :parameter color: Color or colormap name to use
        :parameter legend: Whether to use the legend or not

        :return: None
        """

        try:
            cmap = plt.get_cmap(color)
        except ValueError:
            cmap = color

        legend_entries = []
        for domain_name, geometry_object in self:
            if isinstance(cmap, str):
                geometry_object.draw(color=cmap)
            else:
                c = cmap(self.domain_names[domain_name] / (len(self.domain_names) - 1))
                geometry_object.draw(color=c)
            legend_entries.append(domain_name)

        if legend:
            plt.legend(legend_entries)

        plt.gca().set_aspect("equal")

    def check_intersection(self, domain_name: Optional[str], g1: Polygon, g2: Polygon) -> bool:
        """Check if the two geometries overlap and raise an error if so.

        :param domain_name: Name of the existing domain or
        :param g1: First Geometry
        :param g2: Second Geometry
        :return: None
        """
        return g1.intersects(g2) and not self.is_background(domain_name)

    def is_background(self, domain_name: Optional[str]) -> bool:
        """Check if domain name is background.

        :param domain_name: Either the domain_name or None
        :return: IF the domain is background
        """
        if domain_name:
            return self[domain_name] == self.BACKGROUND_LABEL
        return False

    def intersects_background(self, g: Polygon) -> bool:
        """Ensure the new domain intersects with the background.

        :param g: Geometry to check
        :return: None
        """
        # check against everything in the background
        try:
            bg = self.geometry_map[self.BACKGROUND_LABEL][0]
            return bg.intersects(g)
        except KeyError:  # background not yet inserted so this is fine
            return True

    def __iter__(self):
        """Convert the geometry to a list of (name, geometry_object) pairs.

        :return: The geometry sequentially
        """
        for label, geometry_list in self.geometry_map.items():
            for g in geometry_list:
                yield self[label], g


class QESGeometry(ModelGeometry):
    """Extended model geometry which takes an additional argument 'sigma' when adding domain do define conductance."""

    def add_domain(self, name: str, *geometry_objects: Polygon, sigma: Union[float, Callable] = None, **_) -> None:
        """Add domain in a QES model.

        :param name: Name of the domain
        :param geometry_objects: Arbitrary number of geometry objects
        :param sigma: Conductance of the domain (must be set as a kwarg)
        """
        new_label = super().add_domain(name, *geometry_objects)
        self.parameters["sigma"][new_label] = sigma
