from pudu.transformation import HeatShockTransformation
from opentrons import protocol_api


transformation_data = [
    {
        'Strain': 'GVD_strain',
        'Chassis': 'DH5alpha',
        'Plasmids': ['GVD0011', 'GVD0013', 'GVD0015']
    }
]

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
        replicates=3,
        volume_dna=25,
        thermocycler_starting_well=0,
        transfer_volume_dna=5,
        tube_volume_competent_cell=150
    )

    transformation.run(protocol)
