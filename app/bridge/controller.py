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
from viktor.geometry import RectangularExtrusion
from viktor.geometry import Sphere
from viktor.views import GeometryResult
from viktor.views import GeometryView
from viktor.external.scia import Model as SciaModel
from viktor.external.scia import Material as SciaMaterial

from .parametrization import BridgeParametrization


class BridgeController(ViktorController):
    """Controller class which acts as interface for the Sample entity type."""
    label = "Bridge"
    parametrization = BridgeParametrization
    viktor_convert_entity_field = True

    support_beam_diameter = 2
    talud_angle = 60 * math.pi / 180
    support_slab_width = 7


    @GeometryView("3D", duration_guess=1)
    def visualize_bridge_layout(self, params, **kwargs):
        """"create a visualization of the bridge"""
        geometry_group = self.create_visualization_bridge_layout(params)
        return GeometryResult(geometry_group)

    @GeometryView("3D", duration_guess=1)
    def visualize_bridge_foundations(self, params, **kwargs):
        """"create a visualization of a bridge foundations"""
        scia_bridge_model = self.create_scia_model(params)
        geometry_group_bridge_foundations = self.create_visualization_bridge_foundations(params, scia_bridge_model)
        geometry_group_bridge_layout = self.create_visualization_bridge_layout(params, opacity=0.1)
        for obj in geometry_group_bridge_layout.children:
            geometry_group_bridge_foundations.add(obj)
        return GeometryResult(geometry_group_bridge_foundations)

    def create_visualization_bridge_layout(self, params, opacity=1.0):
        """Creates a visualization of the bridge"""
        geometry_group = Group([])
        width = params.bridge_layout.width
        length = params.bridge_layout.length
        height = params.bridge_layout.height
        deck_thickness = params.bridge_layout.deck_thickness
        support_amount = params.bridge_layout.support_amount

        bridge_material = Material('bridge', threejs_roughness=1, threejs_opacity=opacity)
        lane_material = Material('lanes', threejs_roughness=1, color=Color.black(), threejs_opacity=opacity)
        bike_lane_material = Material('lanes', threejs_roughness=1, color=Color(109, 52, 45), threejs_opacity=opacity)
        lane_markings_material = Material('lanes', threejs_roughness=1, color=Color.white(), threejs_opacity=opacity)
        talud_material = Material('talud', threejs_roughness=1, color=Color.green(), threejs_opacity=opacity)

        talud_x_width = height * math.tan(self.talud_angle)
        talud_length = height / math.cos(self.talud_angle)

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
        x_markings = np.linspace(talud_x_width + 2, length - talud_x_width - 2, support_amount + 2)
        for x_marking in x_markings:
            lane_markings_obj = Extrusion(lane_marking_points, Line(Point(x_marking, 0, 0), Point(x_marking, 0, 0.2)))
            lane_markings_obj.material = lane_markings_material
            geometry_group.add(lane_markings_obj)

        # green talud under the bridge left side
        talud_obj_left = Extrusion(talud_points, Line(
            Point(talud_x_width, 0, math.tan(self.talud_angle) - deck_thickness),
            Point(talud_x_width - 1, 0, -deck_thickness)))
        talud_obj_left.material = talud_material
        geometry_group.add(talud_obj_left)

        # green talud under the bridge left side
        talud_obj_right = Extrusion(talud_points, Line(
            Point(length - talud_x_width, 0, -math.tan(self.talud_angle)),
            Point(length - talud_x_width - 1, 0, 0)))
        talud_obj_right.material = talud_material
        geometry_group.add(talud_obj_right)

        # support beams under the bridge
        x_support_beams = np.linspace(talud_x_width, length - talud_x_width, support_amount + 2)
        y_support_beams = np.linspace(self.support_beam_diameter, width - self.support_beam_diameter, 3)
        for x_support in x_support_beams:
            for y_support_beam in y_support_beams:
                support_obj = CircularExtrusion(self.support_beam_diameter, Line(
                    Point(x_support, y_support_beam, 0),
                    Point(x_support, y_support_beam, height)))
                support_obj.material = bridge_material
                geometry_group.add(support_obj)

        return geometry_group

    def create_visualization_bridge_foundations(self, params, scia_model: SciaModel):
        """Creates a visualization of the bridge"""
        geometry_group = Group([])

        width = params.bridge_layout.width
        length = params.bridge_layout.length
        height = params.bridge_layout.height
        deck_thickness = params.bridge_layout.deck_thickness
        support_amount = params.bridge_layout.support_amount
        pile_length = params.bridge_foundations.pile_length
        pile_angle = params.bridge_foundations.pile_angle
        pile_thickness = params.bridge_foundations.pile_thickness * 1e-03

        support_slab_thickness = deck_thickness

        talud_x_width = height * math.tan(self.talud_angle)

        for node in scia_model.nodes:
            node_obj = Sphere(Point(node.x, node.y, node.z), 0.5)
            node_obj.material = Material('node', color=Color(0, 255, 0))
            geometry_group.add(node_obj)

        pile_diameter = 0.2
        for beam in scia_model.beams:
            point_top = Point(beam.begin_node.x, beam.begin_node.y, beam.begin_node.z)
            point_bottom = Point(beam.end_node.x, beam.end_node.y, beam.end_node.z)
            beam_obj = CircularExtrusion(pile_diameter, Line(point_top, point_bottom))
            beam_obj.material = Material('line', threejs_roughness=1, threejs_opacity=1)
            geometry_group.add(beam_obj)

        for beam in scia_model.beams[(support_amount + 2) * 3:]:
            point_top = Point(beam.begin_node.x, beam.begin_node.y, beam.begin_node.z)
            point_bottom = Point(beam.end_node.x, beam.end_node.y, beam.end_node.z)
            beam_obj = RectangularExtrusion(pile_thickness, pile_thickness, Line(point_top, point_bottom))
            beam_obj.material = Material('beam', threejs_roughness=1, threejs_opacity=0.6)
            geometry_group.add(beam_obj)

        deck_points = [
            Point(0, 0),
            Point(0, width),
            Point(length, width),
            Point(length, 0),
            Point(0, 0)
        ]

        # deck of the bridge
        deck_obj = Extrusion(deck_points, Line(Point(0, 0, height), Point(0, 0, height + deck_thickness)))
        deck_obj.material = Material('deck', threejs_roughness=1, threejs_opacity=0.6)
        geometry_group.add(deck_obj)

        support_slab_points = [
            Point(-self.support_slab_width/2, 0),
            Point(-self.support_slab_width/2, width),
            Point(self.support_slab_width/2, width),
            Point(self.support_slab_width/2, 0),
            Point(-self.support_slab_width/2, 0),
        ]

        x_support_beams = np.linspace(talud_x_width, length - talud_x_width, support_amount + 2)
        for x_support_beam in x_support_beams:
            slab_obj = Extrusion(support_slab_points, Line(
                Point(x_support_beam, 0, -support_slab_thickness/2),
                Point(x_support_beam, 0, support_slab_thickness/2)
            ))
            slab_obj.material = Material('slab', threejs_roughness=1, threejs_opacity=0.6)
            geometry_group.add(slab_obj)

        return geometry_group


    def create_scia_model(self, params):
        """ Create SCIA model"""
        scia_model = SciaModel()

        width = params.bridge_layout.width
        length = params.bridge_layout.length
        height = params.bridge_layout.height
        deck_thickness = params.bridge_layout.deck_thickness
        support_amount = params.bridge_layout.support_amount
        pile_length = params.bridge_foundations.pile_length
        pile_angle = params.bridge_foundations.pile_angle
        pile_thickness = params.bridge_foundations.pile_thickness

        talud_x_width = height * math.tan(self.talud_angle)

        support_slab_thickness = deck_thickness

        material = SciaMaterial(0, 'concrete_slab')

        # Deck
        deck_nodes = [scia_model.create_node('node_deck_0', 0, 0, height),
                      scia_model.create_node('node_deck_1', 0, width, height),
                      scia_model.create_node('node_deck_2', length, width, height),
                      scia_model.create_node('node_deck_3', length, 0, height)]
        deck_plane = scia_model.create_plane(deck_nodes, deck_thickness, name='deck_plane', material=material)

        x_support_beams = np.linspace(talud_x_width, length - talud_x_width, support_amount + 2)
        y_support_beams = np.linspace(self.support_beam_diameter, width - self.support_beam_diameter, 3)

        # supports
        support_slabs = []
        for x_index, x_support_beam in enumerate(x_support_beams):
            # create the slab underneath the 3 beams
            support_slabs.append(scia_model.create_plane(
                corner_nodes=[
                    scia_model.create_node(f'node_slab_{x_index}_0', x_support_beam - self.support_slab_width/2, 0, 0),
                    scia_model.create_node(f'node_slab_{x_index}_1',
                                           x_support_beam - self.support_slab_width/2, width, 0),
                    scia_model.create_node(f'node_slab_{x_index}_2',
                                           x_support_beam + self.support_slab_width/2, width, 0),
                    scia_model.create_node(f'node_slab_{x_index}_3', x_support_beam + self.support_slab_width/2, 0, 0)
                ],
                thickness=support_slab_thickness,
                name=f'support_plane_{x_index}',
                material=material
            ))

        # create the 3 beams for the support
        support_beams = []
        for x_index, x_support_beam in enumerate(x_support_beams):
            for y_index, y_support_beam in enumerate(y_support_beams):
                support_beams.append(scia_model.create_beam(
                    begin_node=scia_model.create_node(
                        f'node_support_bottom_{x_index}_{y_index}',
                        x_support_beam,
                        y_support_beam,
                        0
                    ),
                    end_node=scia_model.create_node(
                        f'node_support_top_{x_index}_{y_index}',
                        x_support_beam,
                        y_support_beam,
                        height
                    ),
                    cross_section=scia_model.create_circular_cross_section(
                        f'circular_cross_section_support_{x_index}_{y_index}',
                        material,
                        self.support_beam_diameter
                    )
                ))

        # create foundation piles
        support_foundations = []
        for x_index, x_support_beam in enumerate(x_support_beams):
            for y_index, y_support_beam in enumerate(y_support_beams):
                for x_offset in [-self.support_slab_width/3, self.support_slab_width/3]:
                    support_foundations.append(scia_model.create_beam(
                        begin_node=scia_model.create_node(
                            f'node_support_foundation_bottom_{x_index}_{y_index}',
                            x_support_beam + x_offset,
                            y_support_beam,
                            -pile_length
                        ),
                        end_node=scia_model.create_node(
                            f'node_support_foundation_top_{x_index}_{y_index}',
                            x_support_beam + x_offset,
                            y_support_beam,
                            0
                        ),
                        cross_section=scia_model.create_rectangular_cross_section(
                            f'rectangular_cross_section_support_foundation_{x_index}_{y_index}',
                            material,
                            pile_thickness,
                            pile_thickness
                        )
                    ))
        return scia_model
