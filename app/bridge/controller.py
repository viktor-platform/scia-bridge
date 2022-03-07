"""Copyright (c) 2022 VIKTOR B.V.

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
Software.

VIKTOR B.V. PROVIDES THIS SOFTWARE ON AN "AS IS" BASIS, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT
NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT
SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import math
import numpy as np

from viktor import Color
from viktor.core import ViktorController
from viktor.geometry import CircularExtrusion
from viktor.geometry import Extrusion
from viktor.geometry import Group
from viktor.geometry import Line
from viktor.geometry import Material
from viktor.geometry import Point
from viktor.views import GeometryResult
from viktor.views import GeometryView

from .parametrization import BridgeParametrization


class BridgeController(ViktorController):
    """Controller class which acts as interface for the Sample entity type."""
    label = "Bridge"
    parametrization = BridgeParametrization
    viktor_convert_entity_field = True

    @GeometryView("3D", duration_guess=1)
    def visualize_bridge_segment(self, params, **kwargs):
        """"create a visualization of a bridge segment"""
        geometry_group = self.create_visualization_bridge_layout(params)
        return GeometryResult(geometry_group)

    def create_visualization_bridge_layout(self, params):
        """Creates a visualization of the bridge"""
        geometry_group = Group([])
        width = params.bridge_layout.width
        length = params.bridge_layout.length
        height = params.bridge_layout.height
        deck_thickness = params.bridge_layout.deck_thickness
        support_amount = params.bridge_layout.support_amount

        bridge_material = Material('bridge', threejs_roughness=1)
        lane_material = Material('lanes', threejs_roughness=1, color=Color.black())
        bike_lane_material = Material('lanes', threejs_roughness=1, color=Color(109, 52, 45))
        lane_markings_material = Material('lanes', threejs_roughness=1, color=Color.white())
        talud_material = Material('talud', threejs_roughness=1, color=Color.green())

        support_beam_diameter = 2

        talud_angle = 60 * math.pi / 180
        talud_x_width = height * math.tan(talud_angle)
        talud_length = height / math.cos(talud_angle)

        deck_points = [
            Point(0, 0),
            Point(0, width),
            Point(length, width),
            Point(length, 0),
            Point(0, 0)
        ]

        bike_lane_points = [
            Point(0, 0),
            Point(0, width / 4),
            Point(length, width / 4),
            Point(length, 0),
            Point(0, 0)
        ]

        lane_points = [
            Point(talud_x_width, -length),
            Point(talud_x_width, length),
            Point(length - talud_x_width, length),
            Point(length - talud_x_width, -length),
            Point(talud_x_width, -length)
        ]

        lane_marking_points = [
            Point(0, -length),
            Point(0, length),
            Point(1, length),
            Point(1, -length),
            Point(0, -length)
        ]

        talud_points = [
            Point(0, -length),
            Point(0, length),
            Point(talud_length, length),
            Point(talud_length, -length),
            Point(0, -length)
        ]

        # deck of the bridge
        deck_obj = Extrusion(deck_points, Line(Point(0, 0, height), Point(0, 0, height + deck_thickness)))
        deck_obj.material = bridge_material
        geometry_group.add(deck_obj)

        # black lane on top of the bridge
        deck_lane_obj = Extrusion(deck_points, Line(
            Point(0, 0, height + deck_thickness),
            Point(0, 0, height + deck_thickness + 0.2)
        ))
        deck_lane_obj.material = lane_material
        geometry_group.add(deck_lane_obj)

        # pink bike lane on the left (back) side of the bridge
        deck_bike_lane_obj_left = Extrusion(bike_lane_points, Line(
            Point(0, 0, height + deck_thickness),
            Point(0, 0, height + deck_thickness + 0.3)
        ))
        deck_bike_lane_obj_left.material = bike_lane_material
        geometry_group.add(deck_bike_lane_obj_left)

        # pink bike lane on the right (front) side of the bridge
        deck_bike_lane_obj_right = Extrusion(bike_lane_points, Line(
            Point(0, width * 0.75, height + deck_thickness),
            Point(0, width * 0.75, height + deck_thickness + 0.3)
        ))
        deck_bike_lane_obj_right.material = bike_lane_material
        geometry_group.add(deck_bike_lane_obj_right)

        # car lane under the bridge
        lane_obj = Extrusion(lane_points, Line(Point(0, 0, -1), Point(0, 0, 0)))
        lane_obj.material = lane_material
        geometry_group.add(lane_obj)

        # white car marking lanes under the bridge
        x_markings = np.linspace(talud_x_width + 2, length - talud_x_width - 4, support_amount + 2)
        for x_marking in x_markings:
            lane_markings_obj = Extrusion(lane_marking_points, Line(Point(x_marking, 0, 0), Point(x_marking, 0, 0.2)))
            lane_markings_obj.material = lane_markings_material
            geometry_group.add(lane_markings_obj)

        # green talud under the bridge left side
        talud_obj_left = Extrusion(talud_points, Line(
            Point(talud_x_width, 0, math.tan(talud_angle) - deck_thickness),
            Point(talud_x_width - 1, 0, -deck_thickness)))
        talud_obj_left.material = talud_material
        geometry_group.add(talud_obj_left)

        # green talud under the bridge left side
        talud_obj_right = Extrusion(talud_points, Line(
            Point(length - talud_x_width, 0, -math.tan(talud_angle)),
            Point(length - talud_x_width - 1, 0, 0)))
        talud_obj_right.material = talud_material
        geometry_group.add(talud_obj_right)

        # support beams under the bridge
        y_support_beams = np.linspace(support_beam_diameter, width - support_beam_diameter, 3)
        for x_support in x_markings:
            for y_support_beam in y_support_beams:
                support_obj = CircularExtrusion(support_beam_diameter, Line(
                    Point(x_support, y_support_beam, 0),
                    Point(x_support, y_support_beam, height)))
                support_obj.material = bridge_material
                geometry_group.add(support_obj)

        return geometry_group
