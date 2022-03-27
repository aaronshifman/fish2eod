from dataclasses import dataclass
from typing import Union

import dolfin as df


@dataclass
class BoundaryCondition:
    """Helper named tuple for boundary conditions.

    value is the value of the boundary condition; it can be a number, a string-like expression i.e. "1+x[0]" or a full
    dolfin expression

    label is the boundary label to apply the value to
    """

    value: Union[float, str, df.Expression]
    label: int

    def to_fenics_representation(self) -> df.Expression:
        if isinstance(self.value, (int, float, str)):
            return df.Expression(str(self.value), degree=2)

        return self.value

    def to_dirichlet_condition(self, v, boundaries):
        self_fenics_repr = self.to_fenics_representation()
        return df.DirichletBC(v, self_fenics_repr, boundaries, self.label)

    def to_neumann_condition(self, v: df.TestFunction, ds: df.Measure) -> df.Form:
        source = self.to_fenics_representation()
        return source("+") * v("+") * ds(self.label)
