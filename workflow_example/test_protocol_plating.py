from pudu.plating import Plating
from opentrons import protocol_api


# Protocol data
plating_data = {
    'bacterium_locations': {
        'A1': ['composite_strain_1', 'Competent_Cell_DH5alpha', 'composite_plasmid_1', 'Media_1'],
        'B1': ['composite_strain_1', 'Competent_Cell_DH5alpha', 'composite_plasmid_1', 'Media_1'],
        'C1': ['composite_strain_2', 'Competent_Cell_DH5alpha', 'composite_plasmid_2', 'Media_1'],
        'D1': ['composite_strain_2', 'Competent_Cell_DH5alpha', 'composite_plasmid_2', 'Media_1'],
        'E1': ['composite_strain_3', 'Competent_Cell_BL21', 'composite_plasmid_1', 'Media_1'],
        'F1': ['composite_strain_3', 'Competent_Cell_BL21', 'composite_plasmid_1', 'Media_1'],
        'G1': ['composite_strain_4', 'Competent_Cell_BL21', 'composite_plasmid_2', 'Media_1'],
        'H1': ['composite_strain_4', 'Competent_Cell_BL21', 'composite_plasmid_2', 'Media_1']
    }
}

# Protocol metadata
metadata = {
    'protocolName': 'Test Updated PUDU Plating Protocol',
    'author': 'Researcher',
    'description': 'Automated protocol',
    'apiLevel': '2.21'
}


def run(protocol: protocol_api.ProtocolContext):
    """Main protocol execution function"""

    protocol_instance = Plating(plating_data=plating_data,
                                protocol_name=metadata['protocolName'])
    protocol_instance.run(protocol)



# ======================================================================
# PARAMETER REFERENCE — Plating
#
# To customize your protocol, add any of the parameters below
# to the Plating() constructor call in run() above.
# Example:  protocol_instance = Plating(
#               plating_data=plating_data,
#               replicates=3,
#               initial_tip='B1',
#           )
# ======================================================================
#
# [Plating]
#   plating_data                Optional  = None
#   json_params                 Optional  = None
#   volume_total_reaction       float     = 20
#   volume_bacteria_transfer    float     = 2
#   volume_colony               float     = 4
#   dilution_factor             float     = 10
#   volume_lb                   float     = 10000
#   replicates                  int       = 1
#   number_dilutions            int       = 2
#   max_colonies                int       = 192
#   thermocycler_starting_well  int       = 0
#   thermocycler_labware        str       = biorad_96_wellplate_200ul_pcr
#   small_tiprack               str       = opentrons_96_filtertiprack_20ul
#   small_tiprack_position      str       = 9
#   initial_small_tip           Optional  = None
#   large_tiprack               str       = opentrons_96_filtertiprack_200ul
#   large_tiprack_position      str       = 1
#   initial_large_tip           Optional  = None
#   small_pipette               str       = p20_single_gen2
#   small_pipette_position      str       = left
#   large_pipette               str       = p300_single_gen2
#   large_pipette_position      str       = right
#   dilution_plate              str       = nest_96_wellplate_100ul_pcr_full_skirt
#   dilution_plate_position1    str       = 2
#   dilution_plate_position2    str       = 3
#   agar_plate                  str       = nest_96_wellplate_100ul_pcr_full_skirt
#   agar_plate_position1        str       = 5
#   agar_plate_position2        str       = 6
#   tube_rack                   str       = opentrons_15_tuberack_falcon_15ml_conical
#   tube_rack_position          str       = 4
#   lb_tube_position            int       = 0
#   aspiration_rate             float     = 0.5
#   dispense_rate               float     = 1
#   bacterium_locations         Optional  = None
#
# ----------------------------------------------------------------------
# Full parameter descriptions:
#
# [Plating]
# Creates a protocol for automated plating of transformed bacteria
#
# Attributes: