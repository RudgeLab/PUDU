# Example SBOL assemblies (would typically come from SynBioSuite)
assemblies = [
    {
        "Product": "https://SBOL2Build.org/composite_1/1",
        "Backbone": "https://sbolcanvas.org/pSB1C3/1",
        "PartsList": [
            "https://sbolcanvas.org/J23101/1",
            "https://sbolcanvas.org/B0034/1",
            "https://sbolcanvas.org/GFP/1",
            "https://sbolcanvas.org/B0015/1"
        ],
        "Restriction Enzyme": "https://SBOL2Build.org/BsaI/1"
    },
    {
        "Product": "https://SBOL2Build.org/composite_2/1",
        "Backbone": "https://sbolcanvas.org/pSB1C3/1",
        "PartsList": [
            "https://sbolcanvas.org/J23100/1",
            "https://sbolcanvas.org/B0034/1",
            "https://sbolcanvas.org/RFP/1",
            "https://sbolcanvas.org/B0015/1"
        ],
        "Restriction Enzyme": "https://SBOL2Build.org/BsaI/1"
    }
]

# Advanced parameters
advanced_params = {
    "volume_part": 3,
    "volume_total_reaction": 25,
    "replicates": 2,  # Want duplicates for this critical experiment
    "initial_tip": "H10",
    "thermocycler_starting_well": 0,
    "protocol_name": "SBOL_GFP_RFP_Assembly"
}


from pudu.assembly import SBOLLoopAssembly
from opentrons import protocol_api


metadata = {
    'protocolName': 'PUDU SBOL Loop Assembly with Advanced Parameters',
    'author': 'Oscar Rodriguez',
    'description': 'Automated DNA assembly from SBOL with custom parameters',
    'apiLevel': '2.14'
}

def run(protocol: protocol_api.ProtocolContext):
    """
    Run SBOL Loop Assembly with advanced parameters.

    This demonstrates three ways to configure the protocol:

    1. Using advanced_params dict (recommended for SynBioSuite integration)
    2. Using kwargs (traditional method, still supported)
    3. Combining both (kwargs override advanced_params)
    """

    # Method 1: Using advanced_params (recommended for programmatic generation)
    protocol.comment("=== Running with advanced_params ===")
    pudu_assembly = SBOLLoopAssembly(
        assemblies=assemblies,
        json_params=advanced_params,
    )
    pudu_assembly.run(protocol)

    # Method 2: Traditional kwargs method (still works for backward compatibility)
    # Uncomment to test:
    # protocol.comment("=== Running with kwargs ===")
    # pudu_assembly = SBOLLoopAssembly(
    #     assemblies=assemblies,
    #     volume_part=3,
    #     replicates=2,
    #     protocol_name="SBOL_Traditional"
    # )
    # pudu_assembly.run(protocol)

    # Method 3: Combining both (kwargs override advanced_params)
    # Uncomment to test:
    # protocol.comment("=== Running with both (kwargs wins) ===")
    # pudu_assembly = SBOLLoopAssembly(
    #     assemblies=assemblies,
    #     advanced_params={"volume_part": 3, "replicates": 2},
    #     replicates=4  # This overrides the replicates=2 in advanced_params
    # )
    # pudu_assembly.run(protocol)