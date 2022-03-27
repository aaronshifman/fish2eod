from fish2eod import BaseFishModel, Circle, plotting

"""
Boilerplate to solve the model
"""


class PreyClass(BaseFishModel):
    def add_geometry(self, **kwargs):
        prey = Circle((3, 2), 0.5)

        self.model_geometry.add_domain("prey", prey, sigma=1)


model = PreyClass()
parameters = {"fish_x": [-15, 15], "fish_y": [0, 0]}
model.compile(**parameters)
model.solve(**parameters)

"""
Extract the solution object

Plot the "FEM solution"
"""

model_solution = model.solution  # pull solution
plotting.mesh_plot_2d(model_solution, "solution")  # plot the result named solution
