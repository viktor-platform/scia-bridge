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
from io import BytesIO
from pathlib import Path

import numpy as np
from viktor import Color
from viktor.core import ViktorController
from viktor.external.scia import LineSupport
from viktor.external.scia import LoadCase
from viktor.external.scia import LoadCombination
from viktor.external.scia import LoadGroup
from viktor.external.scia import Material as SciaMaterial
from viktor.external.scia import Model as SciaModel
from viktor.external.scia import SurfaceLoad
from viktor.geometry import CircularExtrusion
from viktor.geometry import Extrusion
from viktor.geometry import Group
from viktor.geometry import Line
from viktor.geometry import Material
from viktor.geometry import Point
from viktor.geometry import RectangularExtrusion
from viktor.geometry import Sphere
from viktor.result import DownloadResult
from viktor.views import GeometryResult
from viktor.views import GeometryView

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

    def download_scia_input_esa(self, params, **kwargs):
        """"Download scia input esa file"""
        scia_input_esa = self.get_scia_input_esa()
        filename = "model.esa"
        return DownloadResult(scia_input_esa, filename)

    def download_scia_input_xml(self, params, **kwargs):
        """"Download scia input xml file"""
        scia_model = self.create_scia_model(params)
        input_xml, _ = scia_model.generate_xml_input()

        return DownloadResult(input_xml, 'viktor.xml')

    def download_scia_input_def(self, params, **kwargs):
        """"Download scia input def file."""
        scia_model = SciaModel()
        _, input_def = scia_model.generate_xml_input()
        return DownloadResult(input_def, 'viktor.xml.def')

    def get_scia_input_esa(self) -> BytesIO:
        """Retrieves the model.esa file."""
        esa_path = Path(__file__).parent / 'scia' / 'model.esa'
        scia_input_esa = BytesIO()
        with open(esa_path, "rb") as esa_file:
            scia_input_esa.write(esa_file.read())
        return scia_input_esa

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
        pile_thickness = params.bridge_foundations.pile_thickness * 1e-03

        foundation_material = Material('foundation', threejs_roughness=1, threejs_opacity=1)
        node_material = Material('node', color=Color(0, 255, 0))
        deck_material = Material('deck', threejs_roughness=1, threejs_opacity=1)

        support_slab_thickness = deck_thickness

        talud_x_width = height * math.tan(self.talud_angle)

        deck_points = [
            Point(0, 0),
            Point(0, width),
            Point(length, width),
            Point(length, 0),
            Point(0, 0)
        ]

        support_slab_points = [
            Point(-self.support_slab_width / 2, 0),
            Point(-self.support_slab_width / 2, width),
            Point(self.support_slab_width / 2, width),
            Point(self.support_slab_width / 2, 0),
            Point(-self.support_slab_width / 2, 0),
        ]

        # Green sphere for all nodes in model
        for node in scia_model.nodes:
            node_obj = Sphere(Point(node.x, node.y, node.z), 0.5)
            node_obj.material = node_material
            geometry_group.add(node_obj)

        # line for all beams in model
        pile_diameter = 0.2
        for beam in scia_model.beams:
            point_top = Point(beam.begin_node.x, beam.begin_node.y, beam.begin_node.z)
            point_bottom = Point(beam.end_node.x, beam.end_node.y, beam.end_node.z)
            beam_obj = CircularExtrusion(pile_diameter, Line(point_top, point_bottom))
            beam_obj.material = deck_material
            geometry_group.add(beam_obj)

        # rectangular pile under support slabs
        for beam in scia_model.beams[(support_amount + 2) * 3:]:
            point_top = Point(beam.begin_node.x, beam.begin_node.y, beam.begin_node.z)
            point_bottom = Point(beam.end_node.x, beam.end_node.y, beam.end_node.z)
            beam_obj = RectangularExtrusion(pile_thickness, pile_thickness, Line(point_top, point_bottom))
            beam_obj.material = foundation_material
            geometry_group.add(beam_obj)

        # deck of the bridge
        deck_obj = Extrusion(deck_points, Line(Point(0, 0, height), Point(0, 0, height + deck_thickness)))
        deck_obj.material = foundation_material
        geometry_group.add(deck_obj)

        # support slabs
        x_support_beams = np.linspace(talud_x_width, length - talud_x_width, support_amount + 2)
        for x_support_beam in x_support_beams:
            slab_obj = Extrusion(support_slab_points, Line(
                Point(x_support_beam, 0, -support_slab_thickness / 2),
                Point(x_support_beam, 0, support_slab_thickness / 2)
            ))
            slab_obj.material = foundation_material
            geometry_group.add(slab_obj)

        # abutment slab left
        abutment_obj_left = Extrusion(support_slab_points, Line(
            Point(0, 0, height - support_slab_thickness),
            Point(0, 0, height)
        ))
        abutment_obj_left.material = foundation_material
        geometry_group.add(abutment_obj_left)

        # abutment slab right
        abutment_obj_right = Extrusion(support_slab_points, Line(
            Point(length, 0, height - support_slab_thickness),
            Point(length, 0, height)
        ))
        abutment_obj_right.material = foundation_material
        geometry_group.add(abutment_obj_right)

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
        soil_stiffness = params.bridge_foundations.soil_stiffness * 1e06
        deck_load = params.bridge_foundations.deck_load * -1e03

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
        x_slab_beams_offset = [-self.support_slab_width / 3, self.support_slab_width / 3]

        # supports
        foundation_slabs = []
        for x_index, x_support_beam in enumerate(x_support_beams):
            # create the slab underneath the 3 beams
            foundation_slabs.append(scia_model.create_plane(
                corner_nodes=[
                    scia_model.create_node(f'node_slab_{x_index}_0', x_support_beam - self.support_slab_width / 2, 0,
                                           0),
                    scia_model.create_node(f'node_slab_{x_index}_1',
                                           x_support_beam - self.support_slab_width / 2, width, 0),
                    scia_model.create_node(f'node_slab_{x_index}_2',
                                           x_support_beam + self.support_slab_width / 2, width, 0),
                    scia_model.create_node(f'node_slab_{x_index}_3', x_support_beam + self.support_slab_width / 2, 0, 0)
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

        # create foundation piles under support slabs
        foundation_piles = []
        for x_index, x_support_beam in enumerate(x_support_beams):
            for y_index, y_support_beam in enumerate(y_support_beams):
                for x_offset in x_slab_beams_offset:
                    foundation_piles.append(scia_model.create_beam(
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

        # Left abutments slab
        abutment_nodes_left = [scia_model.create_node('node_abutment_0_0',
                                                      -self.support_slab_width / 2,
                                                      0,
                                                      height - support_slab_thickness / 2),
                               scia_model.create_node('node_abutment_0_1',
                                                      -self.support_slab_width / 2,
                                                      width,
                                                      height - support_slab_thickness / 2),
                               scia_model.create_node('node_abutment_0_2',
                                                      self.support_slab_width / 2,
                                                      width,
                                                      height - support_slab_thickness / 2),
                               scia_model.create_node('node_abutment_0_3',
                                                      self.support_slab_width / 2,
                                                      0,
                                                      height - support_slab_thickness / 2)]
        foundation_slabs.append(scia_model.create_plane(abutment_nodes_left, support_slab_thickness,
                                                        name='abutment_plane_left', material=material))

        # Left abutments slab
        abutment_nodes_right = [scia_model.create_node('node_abutment_0_0',
                                                       length - self.support_slab_width / 2,
                                                       0,
                                                       height - support_slab_thickness / 2),
                                scia_model.create_node('node_abutment_0_1',
                                                       length - self.support_slab_width / 2,
                                                       width,
                                                       height - support_slab_thickness / 2),
                                scia_model.create_node('node_abutment_0_2',
                                                       length + self.support_slab_width / 2,
                                                       width,
                                                       height - support_slab_thickness / 2),
                                scia_model.create_node('node_abutment_0_3',
                                                       length + self.support_slab_width / 2,
                                                       0,
                                                       height - support_slab_thickness / 2)]
        foundation_slabs.append(scia_model.create_plane(abutment_nodes_right, support_slab_thickness,
                                                        name='abutment_plane_right', material=material))

        # all the foundation piles under abutment slab
        for y_index, y_support_beam in enumerate(y_support_beams):
            foundation_piles.append(scia_model.create_beam(
                begin_node=scia_model.create_node(
                    f'node_abutment_foundation_bottom_0_{y_index}',
                    -math.sin(pile_angle * math.pi / 180) * pile_length + x_slab_beams_offset[0],
                    y_support_beam,
                    height - math.cos(pile_angle * math.pi / 180) * pile_length - support_slab_thickness
                ),
                end_node=scia_model.create_node(
                    f'node_abutment_foundation_top_0_{y_index}',
                    x_slab_beams_offset[0],
                    y_support_beam,
                    height - support_slab_thickness
                ),
                cross_section=scia_model.create_rectangular_cross_section(
                    f'rectangular_cross_section_abutment_foundation_0_{y_index}',
                    material,
                    pile_thickness,
                    pile_thickness
                )
            ))
            foundation_piles.append(scia_model.create_beam(
                begin_node=scia_model.create_node(
                    f'node_abutment_foundation_bottom_1_{y_index}',
                    length + math.sin(pile_angle * math.pi / 180) * pile_length + x_slab_beams_offset[1],
                    y_support_beam,
                    height - math.cos(pile_angle * math.pi / 180) * pile_length - support_slab_thickness
                ),
                end_node=scia_model.create_node(
                    f'node_abutment_foundation_top_1_{y_index}',
                    length + x_slab_beams_offset[1],
                    y_support_beam,
                    height - support_slab_thickness
                ),
                cross_section=scia_model.create_rectangular_cross_section(
                    f'rectangular_cross_section_abutment_foundation_1_{y_index}',
                    material,
                    pile_thickness,
                    pile_thickness
                )
            ))
            for x_index, x_abutment_foundation in enumerate([x_slab_beams_offset[1], length + x_slab_beams_offset[0]]):
                foundation_piles.append(scia_model.create_beam(
                    begin_node=scia_model.create_node(
                        f'node_abutment_foundation_bottom_{x_index}_{y_index}',
                        x_abutment_foundation,
                        y_support_beam,
                        height - pile_length - support_slab_thickness
                    ),
                    end_node=scia_model.create_node(
                        f'node_abutment_foundation_top_{x_index}_{y_index}',
                        x_abutment_foundation,
                        y_support_beam,
                        height - support_slab_thickness
                    ),
                    cross_section=scia_model.create_rectangular_cross_section(
                        f'rectangular_cross_section_abutment_foundation_{x_index}_{y_index}',
                        material,
                        pile_thickness,
                        pile_thickness
                    )
                ))

        # create support on foundation slabs
        subsoil = scia_model.create_subsoil(name='subsoil', stiffness=soil_stiffness)
        for foundation_slab in foundation_slabs:
            scia_model.create_surface_support(foundation_slab, subsoil)

        # create support on foundation piles
        for foundation_pile in foundation_piles:
            scia_model.create_line_support_on_beam(
                foundation_pile,
                x=LineSupport.Freedom.FLEXIBLE,
                stiffness_x=soil_stiffness,
                y=LineSupport.Freedom.FLEXIBLE,
                stiffness_y=soil_stiffness,
                z=LineSupport.Freedom.FREE,
                rx=LineSupport.Freedom.FREE,
                ry=LineSupport.Freedom.FREE,
                rz=LineSupport.Freedom.FREE,
                c_sys=LineSupport.CSys.GLOBAL
            )

        # create the load group
        load_group = scia_model.create_load_group('LG1', LoadGroup.LoadOption.VARIABLE,
                                                  LoadGroup.RelationOption.STANDARD, LoadGroup.LoadTypeOption.CAT_G)

        # create the load case
        load_case = scia_model.create_variable_load_case('LC1', 'first load case', load_group,
                                                         LoadCase.VariableLoadType.STATIC,
                                                         LoadCase.Specification.STANDARD, LoadCase.Duration.SHORT)

        # create the load combination
        load_cases = {
            load_case: 1
        }
        scia_model.create_load_combination('C1', LoadCombination.Type.ENVELOPE_SERVICEABILITY, load_cases)

        # create the load
        scia_model.create_surface_load('SF:1', load_case, deck_plane, SurfaceLoad.Direction.Z, SurfaceLoad.Type.FORCE,
                                       deck_load, SurfaceLoad.CSys.GLOBAL, SurfaceLoad.Location.LENGTH)

        return scia_model
