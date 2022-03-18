import math

import numpy as np
from viktor import Color
from viktor.geometry import CircularExtrusion
from viktor.geometry import Extrusion
from viktor.geometry import Group
from viktor.geometry import Line
from viktor.geometry import Material
from viktor.geometry import Point
from viktor.geometry import RectangularExtrusion
from viktor.geometry import Sphere
from viktor.external.scia import Model as SciaModel

from app.bridge import constants


def create_visualization_bridge_layout(params, opacity=1.0):
    """Creates a visualization of the bridge"""
    geometry_group = Group([])
    width = params.bridge_layout.width
    length = params.bridge_layout.length
    height = params.bridge_layout.height
    deck_thickness = params.bridge_layout.deck_thickness
    support_amount = params.bridge_layout.support_amount
    support_piles_amount = params.bridge_layout.support_piles_amount

    bridge_material = Material('bridge', threejs_roughness=1, threejs_opacity=opacity)
    support_material = Material('suport_piles', threejs_roughness=1, threejs_opacity=max(opacity, 0.5))
    lane_material = Material('lanes', threejs_roughness=1, color=Color(42, 41, 34), threejs_opacity=opacity)
    bike_lane_material = Material('lanes', threejs_roughness=1, color=Color(109, 52, 45), threejs_opacity=opacity)
    lane_markings_material = Material('lanes', threejs_roughness=1, color=Color.white(), threejs_opacity=opacity)
    talud_material = Material('talud', threejs_roughness=1, color=Color.green(), threejs_opacity=opacity)

    talud_x_width = height * math.tan(constants.TALUD_ANGLE)
    talud_length = height / math.cos(constants.TALUD_ANGLE)

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
        Point(talud_x_width, 0, math.tan(constants.TALUD_ANGLE) - deck_thickness),
        Point(talud_x_width - 1, 0, -deck_thickness)))
    talud_obj_left.material = talud_material
    geometry_group.add(talud_obj_left)

    # green talud under the bridge left side
    talud_obj_right = Extrusion(talud_points, Line(
        Point(length - talud_x_width, 0, -math.tan(constants.TALUD_ANGLE)),
        Point(length - talud_x_width - 1, 0, 0)))
    talud_obj_right.material = talud_material
    geometry_group.add(talud_obj_right)

    # support beams under the bridge
    x_support_beams = np.linspace(talud_x_width, length - talud_x_width, support_amount + 2)
    y_support_beams = np.linspace(
        constants.SUPPORT_BEAM_DIAMETER,
        width - constants.SUPPORT_BEAM_DIAMETER,
        support_piles_amount
    )
    for x_support in x_support_beams:
        for y_support_beam in y_support_beams:
            support_obj = CircularExtrusion(constants.SUPPORT_BEAM_DIAMETER, Line(
                Point(x_support, y_support_beam, 0),
                Point(x_support, y_support_beam, height)))
            support_obj.material = support_material
            geometry_group.add(support_obj)

    return geometry_group


def create_visualization_bridge_foundations(params, scia_model: SciaModel, opacity=1.0):
    """Creates a visualization of the bridge"""
    geometry_group = Group([])

    width = params.bridge_layout.width
    length = params.bridge_layout.length
    height = params.bridge_layout.height
    deck_thickness = params.bridge_layout.deck_thickness
    support_amount = params.bridge_layout.support_amount
    support_piles_amount = params.bridge_layout.support_piles_amount

    pile_thickness = params.bridge_foundations.pile_thickness * 1e-03

    foundation_material = Material('foundation', threejs_roughness=1, threejs_opacity=opacity)
    node_material = Material('node', color=Color(0, 255, 0))
    deck_material = Material('deck', threejs_roughness=1, threejs_opacity=opacity)

    support_slab_thickness = deck_thickness

    talud_x_width = height * math.tan(constants.TALUD_ANGLE)

    deck_points = [
        Point(0, 0),
        Point(0, width),
        Point(length, width),
        Point(length, 0),
        Point(0, 0)
    ]

    support_slab_points = [
        Point(-constants.SUPPORT_SLAB_WITH / 2, 0),
        Point(-constants.SUPPORT_SLAB_WITH / 2, width),
        Point(constants.SUPPORT_SLAB_WITH / 2, width),
        Point(constants.SUPPORT_SLAB_WITH / 2, 0),
        Point(-constants.SUPPORT_SLAB_WITH / 2, 0),
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
    for beam in scia_model.beams[(support_amount + 2) * support_piles_amount:]:
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
