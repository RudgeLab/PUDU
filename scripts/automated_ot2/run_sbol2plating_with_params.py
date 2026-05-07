from pudu.plating import Plating
from opentrons import protocol_api


# Protocol metadata
metadata = {
    'protocolName': 'PUDU Plating Test',
    'author': 'Oscar Rodriguez',
    'description': 'Test plating with new parameter approach',
    'apiLevel': '2.21'
}


def run(protocol: protocol_api.ProtocolContext):
    """Main protocol execution function"""

    # NEW APPROACH: Using plating_data + advanced_params (JSON-compatible)
    plating_data = {
        'bacterium_locations': {
            'A1': 'GVD0011',
            'A2': 'GVD0013',
            'A3': 'GVD0015'
        }
    }

    advanced_params = {
        'replicates': 2,
        'number_dilutions': 2,
        'volume_colony': 6,
        'thermocycler_starting_well': 0
    }

    plating = Plating(
        plating_data=plating_data,
        advanced_params=advanced_params
    )

    # OLD APPROACH: Using kwargs directly
    # plating = Plating(
    #     bacterium_locations={
    #         'A1': 'GVD0011',
    #         'A2': 'GVD0013',
    #         'A3': 'GVD0015'
    #     },
    #     replicates=2,
    #     number_dilutions=2,
    #     volume_colony=6,
    #     thermocycler_starting_well=0
    # )

    plating.run(protocol)
