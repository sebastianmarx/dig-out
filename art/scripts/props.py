"""Prop builders shared by item renders and character poses."""

import math

from digout_art import bowl, box, cylinder, group

# Grip point of the spoon in its local space (centre of the duct tape) and its length axis (+Y = bowl).
SPOON_GRIP = (0.0, -0.62, 0.1)


def build_spoon(name="tool.spoon"):
    """Improvised digging spoon: steel spoon, handle extended with a wooden stick and duct tape.
    Built along +Y (bowl end) around the origin; returns the parent empty."""
    root = group(name)
    p = root
    tilt = math.radians(-5)  # handle rises slightly towards the stick

    bowl(f"{name}.bowl", (0.19, 0.29, 0.085), (0, 0.42, 0.085), "steel", thickness=0.022, parent=p)
    box(f"{name}.neck", (0.07, 0.2, 0.03), (0, 0.06, 0.035), "steel", rot=(tilt, 0, 0), bevel=0.01,
        parent=p)
    box(f"{name}.handle", (0.1, 0.62, 0.032), (0, -0.33, 0.065), "steel", rot=(tilt, 0, 0),
        bevel=0.012, parent=p)

    cylinder(f"{name}.stick", 0.042, 0.8, (0, -0.95, 0.12), "wood",
             rot=(math.radians(90) + tilt, 0, 0), bevel=0.01, parent=p)
    cylinder(f"{name}.tape", 0.062, 0.3, (0, -0.62, 0.1), "tape",
             rot=(math.radians(90) + tilt, 0, 0), bevel=0.008, parent=p)
    for i, y in enumerate((-0.49, -0.75)):
        cylinder(f"{name}.tape_edge_{i}", 0.066, 0.025, (0, y, 0.1 - (y + 0.62) * 0.09), "tape",
                 rot=(math.radians(90) + tilt + math.radians(6 - 12 * i), 0, 0), bevel=0.005,
                 parent=p)
    return root
