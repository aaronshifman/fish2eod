Computing Electric Images
=========================

Computing electric images in fish2eod is quite simple and only requires a bit of additional metadata. The electric image
is the field perturbation causes by an object being introduced to the EOD. Conceptually this is the simulation run
twice. Once with an area of choice (some set of domains) and a second simulation with those domains removed.

Computationally this is much easier to perform is the domains aren't removed but made electrically invisible (set the
conductivity to that of the background). Using the `.ElectricImageParameters` you can specify a list of domains with
the ``domains`` argument, and the background conductivity (often that of water, however it can be any conductivity)
through the ``values`` argument.

.. plot:: examples/basic/code/example_prey_image.py
   :include-source:

To analyse the electric images, `.compute_transdermal_potential` is used to compute the data after the model is solved.
You'll get back a set of geometry data for the left and right sides of the body, and the transdermal potential for
the right and left sides of the body.

The skin geometry returned has the following fields

* left_inner
* left_outer
* right_inner
* right_outer
* left_arc_length
* right_arc_length

Where `_inner` is (x, y) coordinates of the inner skin, and similarly for `_outer`. The arc lengths are the corresponding
arc length along the inner skin (distance travelled if you followed along the skin).