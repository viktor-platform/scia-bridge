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

from viktor import Color
from viktor.core import ViktorController
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
        geometry_group = self.create_visualization_geometries(params)
        return GeometryResult(geometry_group)


    def create_visualization_geometries(self, params):
        """Creates a visualization of the bridge"""
        geometry_group = Group([])
        crossing_angle = params.bridge.crossing_angle
        width = params.bridge.width
        length = params.bridge.length
        height = params.bridge.height
        deck_thickness = params.bridge.deck_thickness
        # support_amount = params.bridge.support_amount
        # pile_length = params.bridge.pile_length
        # pile_angle = params.bridge.pile_angle
        # pile_thickness = params.bridge.pile_thickness

        lane_material = Material('lanes', threejs_roughness=1, color=Color.black())
        talud_material = Material('talud', threejs_roughness=1, color=Color.green())
        bridge_material = Material('bridge', threejs_roughness=1)

        deck_x_dir = length * math.cos(crossing_angle * math.pi / 180)
        deck_y_dir = length * math.sin(crossing_angle * math.pi / 180)

        talud_angle = 60 * math.pi / 180
        talud_width = height * math.tan(talud_angle)
        talud_length = height / math.cos(talud_angle)

        deck_points = [
            Point(0, 0),
            Point(0, width),
            Point(deck_x_dir, deck_y_dir + width),
            Point(deck_x_dir, deck_y_dir),
            Point(0, 0)
        ]

        lane_points = [
            Point(0, -100),
            Point(0, 100),
            Point(deck_x_dir, 100),
            Point(deck_x_dir, -100),
            Point(0, -100)
        ]

        talud_points = [
            Point(0, -100),
            Point(0, 100),
            Point(talud_length, 100),
            Point(talud_length, -100),
            Point(0, -100)
        ]

        deck_obj = Extrusion(deck_points, Line(Point(0, 0, height), Point(0, 0, height + deck_thickness)))
        deck_obj.material = bridge_material
        geometry_group.add(deck_obj)

        lane_obj = Extrusion(lane_points, Line(Point(0, 0, -1), Point(0, 0, 0)))
        lane_obj.material = lane_material
        geometry_group.add(lane_obj)

        talud_obj_left = Extrusion(talud_points, Line(
            Point(talud_width, 0, math.tan(talud_angle) - deck_thickness),
            Point(talud_width - 1, 0, -deck_thickness)))
        talud_obj_left.material = talud_material
        geometry_group.add(talud_obj_left)

        talud_obj_right = Extrusion(talud_points, Line(
            Point(deck_x_dir - talud_width, 0, -math.tan(talud_angle) + deck_thickness),
            Point(deck_x_dir - talud_width - 1, 0, deck_thickness)))
        talud_obj_right.material = talud_material
        geometry_group.add(talud_obj_right)

        return geometry_group
