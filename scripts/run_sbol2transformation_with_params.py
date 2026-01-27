transformation_data = {
    'list_of_dna': ['GVD0011', 'GVD0013', 'GVD0015'],
    'competent_cells': 'DH5alpha'
}

advanced_params = {
    'replicates': 3,
    'volume_dna': 25,
    'thermocycler_starting_well': 0,
    'transfer_volume_dna': 5,
    'tube_volume_competent_cell': 150
}

from pudu.transformation import HeatShockTransformation
from opentrons import protocol_api


# Protocol metadata
metadata = {
    'protocolName': 'PUDU Transformation Test',
    'author': 'Oscar Rodriguez',
    'description': 'Test transformation with new parameter approach',
    'apiLevel': '2.20'
}


def run(protocol: protocol_api.ProtocolContext):
    """Main protocol execution function"""

    transformation = HeatShockTransformation(
        transformation_data=transformation_data,
        advanced_params=advanced_params
    )

    # OLD APPROACH: Using kwargs directly (commented out)
    # transformation = HeatShockTransformation(
    #     list_of_dna=['GVD0011', 'GVD0013', 'GVD0015'],
    #     competent_cells='DH5alpha',
    #     replicates=3,
    #     volume_dna=25,
    #     thermocycler_starting_well=0,
    #     transfer_volume_dna=5,
    #     tube_volume_competent_cell=150
    # )

    transformation.run(protocol)
