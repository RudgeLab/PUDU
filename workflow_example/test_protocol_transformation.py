from pudu.transformation import HeatShockTransformation
from opentrons import protocol_api


# Protocol data
transformation_data = [
    {
        'Strain': 'https://SBOL2Build.org/composite_strain_1/1',
        'Chassis': 'https://sbolcanvas.org/DH5alpha/1',
        'Plasmids': ['https://SBOL2Build.org/composite_plasmid_1/1']
    },
    {
        'Strain': 'https://SBOL2Build.org/composite_strain_2/1',
        'Chassis': 'https://sbolcanvas.org/DH5alpha/1',
        'Plasmids': ['https://SBOL2Build.org/composite_plasmid_2/1']
    },
    {
        'Strain': 'https://SBOL2Build.org/composite_strain_3/1',
        'Chassis': 'https://sbolcanvas.org/BL21/1',
        'Plasmids': ['https://SBOL2Build.org/composite_plasmid_1/1']
    },
    {
        'Strain': 'https://SBOL2Build.org/composite_strain_4/1',
        'Chassis': 'https://sbolcanvas.org/BL21/1',
        'Plasmids': ['https://SBOL2Build.org/composite_plasmid_2/1']
    }
]

# Plasmid well locations from assembly protocol output
plasmid_locations = {
    'https://SBOL2Build.org/composite_plasmid_1/1': ['A1'],
    'https://SBOL2Build.org/composite_plasmid_2/1': ['B1']
}

# Protocol metadata
metadata = {
    'protocolName': 'Test Updated PUDU Transformation Protocol',
    'author': 'Oscar Rodriguez',
    'description': 'Testing protocol generation with custom metadata',
    'apiLevel': '2.21'
}


def run(protocol: protocol_api.ProtocolContext):
    """Main protocol execution function"""

    protocol_instance = HeatShockTransformation(
        transformation_data=transformation_data,
        plasmid_locations=plasmid_locations,
        water_testing=True
    )
    protocol_instance.run(protocol)



# ======================================================================
# PARAMETER REFERENCE — HeatShockTransformation
#
# To customize your protocol, add any of the parameters below
# to the HeatShockTransformation() constructor call in run() above.
# Example:  protocol_instance = HeatShockTransformation(
#               transformation_data=transformation_data,
#               replicates=3,
#               initial_tip='B1',
#           )
# ======================================================================
#
# [HeatShockTransformation]
#   transformation_data             Optional  = None
#   plasmid_locations               Optional  = None
#   json_params                     Optional  = None
#   transfer_volume_dna             float     = 2
#   transfer_volume_competent_cell  float     = 20
#   tube_volume_competent_cell      float     = 100
#   transfer_volume_recovery_media  float     = 60
#   tube_volume_recovery_media      float     = 1200
#   cold_incubation1                Optional  = None
#   heat_shock                      Optional  = None
#   cold_incubation2                Optional  = None
#   recovery_incubation             Optional  = None
#
# [Transformation]
#   volume_dna                      float     = 20
#   replicates                      int       = 2
#   thermocycler_starting_well      int       = 0
#   thermocycler_labware            str       = nest_96_wellplate_100ul_pcr_full_skirt
#   temperature_module_labware      str       = opentrons_24_aluminumblock_nest_1.5ml_snapcap
#   temperature_module_position     str       = 1
#   dna_plate                       str       = nest_96_wellplate_100ul_pcr_full_skirt
#   dna_plate_position              str       = 2
#   use_dna_96plate                 bool      = False
#   tiprack_p20_labware             str       = opentrons_96_tiprack_20ul
#   tiprack_p20_position            str       = 9
#   tiprack_p200_labware            str       = opentrons_96_filtertiprack_200ul
#   tiprack_p200_position           str       = 6
#   pipette_p20                     str       = p20_single_gen2
#   pipette_p20_position            str       = left
#   pipette_p300                    str       = p300_single_gen2
#   pipette_p300_position           str       = right
#   aspiration_rate                 float     = 0.5
#   dispense_rate                   float     = 1
#   initial_dna_well                int       = 0
#   water_testing                   bool      = False
#   initial_tip_p20                 Optional  = None
#   initial_tip_p300                Optional  = None
#   tube_rack_labware               str       = opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap
#   tube_rack_position              str       = 3
#
# ----------------------------------------------------------------------
# Full parameter descriptions:
#
# [HeatShockTransformation]
# Heat shock transformation protocol for the Opentrons OT-2.
#
# Automates the full heat shock transformation workflow: loading DNA and competent
# cells into a thermocycler plate, running the heat shock cycle, adding recovery
# media, and exporting a plating map for the next protocol step.
#
# Inherits all base parameters from Transformation. The attributes below are
# specific to the heat shock transformation protocol.
#
# Attributes
# ----------
# transfer_volume_dna : float
#     Volume of DNA to transfer into each thermocycler well, in microliters.
#     By default, 2 microliters. Note: this is the volume actually pipetted per
#     reaction, distinct from volume_dna (the volume loaded into the source well).
# transfer_volume_competent_cell : float
#     Volume of competent cells to transfer into each thermocycler well, in
#     microliters. By default, 20 microliters.
# tube_volume_competent_cell : float
#     Total usable volume of competent cells per tube, in microliters. Used to
#     calculate how many reactions each tube can supply before switching to the
#     next tube. By default, 100 microliters.
# transfer_volume_recovery_media : float
#     Volume of recovery media to add to each well after heat shock, in
#     microliters. By default, 60 microliters.
# tube_volume_recovery_media : float
#     Total usable volume of recovery media per tube, in microliters. Used to
#     calculate how many wells each tube can supply. By default, 1200 microliters.
# cold_incubation1 : dict
#     First cold incubation step (on ice before heat shock). A dict with keys
#     'temperature' (°C) and 'hold_time_minutes'.
#     By default, {'temperature': 4, 'hold_time_minutes': 30}.
# heat_shock : dict
#     Heat shock step. A dict with keys 'temperature' (°C) and 'hold_time_minutes'.
#     By default, {'temperature': 42, 'hold_time_minutes': 1}.
# cold_incubation2 : dict
#     Second cold incubation immediately after heat shock. A dict with keys
#     'temperature' (°C) and 'hold_time_minutes'.
#     By default, {'temperature': 4, 'hold_time_minutes': 2}.
# recovery_incubation : dict
#     Recovery incubation after recovery media addition. A dict with keys
#     'temperature' (°C) and 'hold_time_minutes'.
#     By default, {'temperature': 37, 'hold_time_minutes': 60}.
#
# [Transformation]
# Base class for automated transformation protocols on the Opentrons OT-2.
#
# Handles loading transformation data, validating parameters, and providing
# shared utilities used by all transformation subclasses. Subclasses implement
# the specific thermocycler workflow (e.g. heat shock).
#
# Attributes
# ----------
# volume_dna : float
#     Volume of DNA loaded into each source well, in microliters. By default,
#     20 microliters. We suggest 2 µL for extracted plasmid and 5 µL for PCR
#     products when setting transfer_volume_dna in the subclass.
# replicates : int
#     Number of transformation replicates per strain per assembly location.
#     By default, 2.
# thermocycler_starting_well : int
#     Zero-indexed starting well in the thermocycler plate. By default, 0 (well A1).
# thermocycler_labware : str
#     Labware type for the thermocycler plate.
#     By default, 'nest_96_wellplate_100ul_pcr_full_skirt'.
# temperature_module_labware : str
#     Labware type for the aluminum block on the temperature module.
#     By default, 'opentrons_24_aluminumblock_nest_1.5ml_snapcap'.
# temperature_module_position : str
#     Deck slot for the temperature module. By default, '1'.
# dna_plate : str
#     Labware type for the 96-well DNA source plate (used when use_dna_96plate=True).
#     By default, 'nest_96_wellplate_100ul_pcr_full_skirt'.
# dna_plate_position : str
#     Deck slot for the 96-well DNA source plate. By default, '2'.
# use_dna_96plate : bool
#     If True, DNA is sourced from a 96-well plate at fixed positions given by
#     plasmid_locations. Automatically set to True when plasmid_locations is
#     provided. By default, False.
# tiprack_p20_labware : str
#     Labware type for the p20 tip rack. By default, 'opentrons_96_tiprack_20ul'.
# tiprack_p20_position : str
#     Deck slot for the p20 tip rack. By default, '9'.
# tiprack_p200_labware : str
#     Labware type for the p200 tip rack.
#     By default, 'opentrons_96_filtertiprack_200ul'.
# tiprack_p200_position : str
#     Deck slot for the p200 tip rack. By default, '6'.
# pipette_p20 : str
#     Pipette model for the p20 single-channel. By default, 'p20_single_gen2'.
# pipette_p20_position : str
#     Mount for the p20 pipette ('left' or 'right'). By default, 'left'.
# pipette_p300 : str
#     Pipette model for the p300 single-channel. By default, 'p300_single_gen2'.
# pipette_p300_position : str
#     Mount for the p300 pipette ('left' or 'right'). By default, 'right'.
# aspiration_rate : float
#     Relative aspiration speed as a fraction of the pipette's maximum flow
#     rate, where 1.0 is full speed and 0.5 is half speed. Lower values
#     reduce bubble formation. By default, 0.5.
# dispense_rate : float
#     Relative dispense speed as a fraction of the pipette's maximum flow
#     rate, where 1.0 is full speed. By default, 1.0.
# initial_dna_well : int
#     Zero-indexed starting well for DNA tubes on the aluminum block (used when
#     use_dna_96plate=False). By default, 0.
# water_testing : bool
#     If True, uses water in place of competent cells and recovery media during
#     simulation/testing runs. By default, False.
# initial_tip_p20 : str, optional
#     Well name of the first tip to use from the p20 tip rack (e.g. 'B1').
#     If None, starts from the first available tip. By default, None.
# initial_tip_p300 : str, optional
#     Well name of the first tip to use from the p300 tip rack (e.g. 'C3').
#     If None, starts from the first available tip. By default, None.
# tube_rack_labware : str
#     Labware type for the tube rack that holds competent cells and recovery
#     media. Moving these off the temperature module frees the entire aluminum
#     block for DNA plasmids, maximising unique constructs per run.
#     By default, 'opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap'.
# tube_rack_position : str
#     Deck slot for the tube rack. By default, '3'.