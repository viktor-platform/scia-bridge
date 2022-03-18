import math

import numpy as np
from viktor.external.scia import LineSupport
from viktor.external.scia import LoadCase
from viktor.external.scia import LoadCombination
from viktor.external.scia import LoadGroup
from viktor.external.scia import Material as SciaMaterial
from viktor.external.scia import Model as SciaModel
from viktor.external.scia import PointSupport
from viktor.external.scia import SurfaceLoad

from app.bridge import constants


def create_scia_model(params):
    """ Create SCIA model"""
    scia_model = SciaModel()

    width = params.bridge_layout.width
    length = params.bridge_layout.length
    height = params.bridge_layout.height
    deck_thickness = params.bridge_layout.deck_thickness
    support_amount = params.bridge_layout.support_amount
    support_piles_amount = params.bridge_layout.support_piles_amount
    pile_length = params.bridge_foundations.pile_length
    pile_angle = params.bridge_foundations.pile_angle
    pile_thickness = params.bridge_foundations.pile_thickness * 1e-03
    soil_stiffness = params.bridge_foundations.soil_stiffness * 1e06
    deck_load = params.bridge_foundations.deck_load * -1e03

    talud_x_width = height * math.tan(constants.TALUD_ANGLE)

    support_slab_thickness = deck_thickness

    material = SciaMaterial(0, 'concrete_slab')
    material_cross_section = SciaMaterial(0, 'C30/37')

    # Deck
    deck_nodes = [scia_model.create_node('node_deck_0', 0, 0, height),
                  scia_model.create_node('node_deck_1', 0, width, height),
                  scia_model.create_node('node_deck_2', length, width, height),
                  scia_model.create_node('node_deck_3', length, 0, height)]
    deck_plane = scia_model.create_plane(deck_nodes, deck_thickness, name='deck_plane', material=material)

    x_support_beams = np.linspace(talud_x_width, length - talud_x_width, support_amount + 2)
    y_support_beams = np.linspace(
        constants.SUPPORT_BEAM_DIAMETER,
        width - constants.SUPPORT_BEAM_DIAMETER,
        support_piles_amount
    )
    x_slab_beams_offset = [-constants.SUPPORT_SLAB_WITH / 3, constants.SUPPORT_SLAB_WITH / 3]

    # supports
    foundation_slabs = []
    for x_index, x_support_beam in enumerate(x_support_beams):
        # create the slab underneath the beams
        foundation_slabs.append(scia_model.create_plane(
            corner_nodes=[
                scia_model.create_node(f'node_slab_{x_index}_0', x_support_beam - constants.SUPPORT_SLAB_WITH / 2, 0,
                                       0),
                scia_model.create_node(f'node_slab_{x_index}_1',
                                       x_support_beam - constants.SUPPORT_SLAB_WITH / 2, width, 0),
                scia_model.create_node(f'node_slab_{x_index}_2',
                                       x_support_beam + constants.SUPPORT_SLAB_WITH / 2, width, 0),
                scia_model.create_node(f'node_slab_{x_index}_3', x_support_beam + constants.SUPPORT_SLAB_WITH / 2, 0, 0)
            ],
            thickness=support_slab_thickness,
            name=f'support_plane_{x_index}',
            material=material
        ))

    circular_cross_section_support = scia_model.create_circular_cross_section(
        'circular_cross_section_support',
        material_cross_section,
        constants.SUPPORT_BEAM_DIAMETER
    )
    # create the beams for the support
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
                cross_section=circular_cross_section_support
            ))

    # create foundation piles under support slabs
    rectangular_cross_section_foundation = scia_model.create_rectangular_cross_section(
        'rectangular_cross_section_foundation',
        material_cross_section,
        pile_thickness,
        pile_thickness
    )
    foundation_piles_straight = []
    for x_index, x_support_beam in enumerate(x_support_beams):
        for y_index, y_support_beam in enumerate(y_support_beams):
            for z_index, x_offset in enumerate(x_slab_beams_offset):
                foundation_piles_straight.append(scia_model.create_beam(
                    begin_node=scia_model.create_node(
                        f'node_support_foundation_bottom_{x_index}_{y_index}_{z_index}',
                        x_support_beam + x_offset,
                        y_support_beam,
                        -pile_length
                    ),
                    end_node=scia_model.create_node(
                        f'node_support_foundation_top_{x_index}_{y_index}_{z_index}',
                        x_support_beam + x_offset,
                        y_support_beam,
                        0
                    ),
                    cross_section=rectangular_cross_section_foundation
                ))

    # Left abutments slab
    abutment_nodes_left = [scia_model.create_node('node_abutment_0_0',
                                                  -constants.SUPPORT_SLAB_WITH / 2,
                                                  0,
                                                  height - support_slab_thickness / 2),
                           scia_model.create_node('node_abutment_0_1',
                                                  -constants.SUPPORT_SLAB_WITH / 2,
                                                  width,
                                                  height - support_slab_thickness / 2),
                           scia_model.create_node('node_abutment_0_2',
                                                  constants.SUPPORT_SLAB_WITH / 2,
                                                  width,
                                                  height - support_slab_thickness / 2),
                           scia_model.create_node('node_abutment_0_3',
                                                  constants.SUPPORT_SLAB_WITH / 2,
                                                  0,
                                                  height - support_slab_thickness / 2)]
    foundation_slabs.append(scia_model.create_plane(abutment_nodes_left, support_slab_thickness,
                                                    name='abutment_plane_left', material=material))

    # Left abutments slab
    abutment_nodes_right = [scia_model.create_node('node_abutment_1_0',
                                                   length - constants.SUPPORT_SLAB_WITH / 2,
                                                   0,
                                                   height - support_slab_thickness / 2),
                            scia_model.create_node('node_abutment_1_1',
                                                   length - constants.SUPPORT_SLAB_WITH / 2,
                                                   width,
                                                   height - support_slab_thickness / 2),
                            scia_model.create_node('node_abutment_1_2',
                                                   length + constants.SUPPORT_SLAB_WITH / 2,
                                                   width,
                                                   height - support_slab_thickness / 2),
                            scia_model.create_node('node_abutment_1_3',
                                                   length + constants.SUPPORT_SLAB_WITH / 2,
                                                   0,
                                                   height - support_slab_thickness / 2)]
    foundation_slabs.append(scia_model.create_plane(abutment_nodes_right, support_slab_thickness,
                                                    name='abutment_plane_right', material=material))

    # abutment piles
    foundation_piles_angled = []
    for y_index, y_support_beam in enumerate(y_support_beams):
        # left angled abutment piles
        foundation_piles_angled.append(scia_model.create_beam(
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
            cross_section=rectangular_cross_section_foundation
        ))
        # right angled abutment piles
        foundation_piles_angled.append(scia_model.create_beam(
            begin_node=scia_model.create_node(
                f'node_abutment_foundation_bottom_3_{y_index}',
                length + math.sin(pile_angle * math.pi / 180) * pile_length + x_slab_beams_offset[1],
                y_support_beam,
                height - math.cos(pile_angle * math.pi / 180) * pile_length - support_slab_thickness
            ),
            end_node=scia_model.create_node(
                f'node_abutment_foundation_top_3_{y_index}',
                length + x_slab_beams_offset[1],
                y_support_beam,
                height - support_slab_thickness
            ),
            cross_section=rectangular_cross_section_foundation
        ))
        # middle abutment piles (not angled)
        for x_index, x_abutment_foundation in enumerate([x_slab_beams_offset[1], length + x_slab_beams_offset[0]]):
            foundation_piles_straight.append(scia_model.create_beam(
                begin_node=scia_model.create_node(
                    f'node_abutment_foundation_bottom_{x_index + 1}_{y_index}',
                    x_abutment_foundation,
                    y_support_beam,
                    height - pile_length - support_slab_thickness
                ),
                end_node=scia_model.create_node(
                    f'node_abutment_foundation_top_{x_index + 1}_{y_index}',
                    x_abutment_foundation,
                    y_support_beam,
                    height - support_slab_thickness
                ),
                cross_section=rectangular_cross_section_foundation
            ))

    # create support on foundation slabs
    subsoil = scia_model.create_subsoil(name='subsoil', stiffness=soil_stiffness)
    for foundation_slab in foundation_slabs:
        scia_model.create_surface_support(foundation_slab, subsoil)

    # create support on straight foundation piles on beam and on bottom point
    for pile_index, foundation_pile in enumerate(foundation_piles_straight):
        # create support on beam
        scia_model.create_line_support_on_beam(
            beam=foundation_pile,
            name=f'support_beam_straight_{pile_index}',
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
        # create point support on bottom beam
        scia_model.create_point_support(
            name=f'point_support_beam_straight_{pile_index}',
            node=foundation_pile.end_node,
            spring_type=PointSupport.Type.STANDARD,
            freedom=(
                PointSupport.Freedom.FREE,  # x
                PointSupport.Freedom.FREE,  # y
                PointSupport.Freedom.FLEXIBLE,  # z
                PointSupport.Freedom.FREE,  # rx
                PointSupport.Freedom.FREE,  # ry
                PointSupport.Freedom.FREE,  # rz
            ),
            stiffness=(0, 0, soil_stiffness, 0, 0, 0),
            c_sys=PointSupport.CSys.GLOBAL
        )

    # create support on angled foundation piles
    for foundation_pile in foundation_piles_angled:
        scia_model.create_line_support_on_beam(
            foundation_pile,
            x=LineSupport.Freedom.FLEXIBLE,
            stiffness_x=soil_stiffness,
            y=LineSupport.Freedom.FLEXIBLE,
            stiffness_y=soil_stiffness,
            z=LineSupport.Freedom.FREE,
            rx=LineSupport.Freedom.FREE,
            ry=LineSupport.Freedom.FREE,
            rz=LineSupport.Freedom.FLEXIBLE,
            stiffness_rz=soil_stiffness,
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
