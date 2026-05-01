# metadata
from opentrons import protocol_api

from pudu.plating import Plating

metadata = {
    'protocolName': 'Plating Protocol',
    'author': 'Oscar Rodriguez',
    'description': 'Automated Transformed Bacteria Plating Protocol',
    'apiLevel': '2.23'
}

# constructs = {"A1":["GVP8"],"A2":["GVP10"],"A3":["GVP12"]}
constructs = {'A1': ['Competent_Cell_DH5alpha_1', ('GVP0008', 'B0034', 'sfGFP', 'B0015', 'Odd_1', 'replicate_1'), 'Media_1'], 'B1': ['Competent_Cell_DH5alpha_1', ('GVP0008', 'B0034', 'sfGFP', 'B0015', 'Odd_1', 'replicate_1'), 'Media_1'], 'C1': ['Competent_Cell_DH5alpha_1', ('GVP0008', 'B0034', 'sfGFP', 'B0015', 'Odd_1', 'replicate_2'), 'Media_1'], 'D1': ['Competent_Cell_DH5alpha_1', ('GVP0008', 'B0034', 'sfGFP', 'B0015', 'Odd_1', 'replicate_2'), 'Media_1'], 'E1': ['Competent_Cell_DH5alpha_1', ('GVP0010', 'B0034', 'sfGFP', 'B0015', 'Odd_1', 'replicate_1'), 'Media_1'], 'F1': ['Competent_Cell_DH5alpha_2', ('GVP0010', 'B0034', 'sfGFP', 'B0015', 'Odd_1', 'replicate_1'), 'Media_1'], 'G1': ['Competent_Cell_DH5alpha_2', ('GVP0010', 'B0034', 'sfGFP', 'B0015', 'Odd_1', 'replicate_2'), 'Media_1'], 'H1': ['Competent_Cell_DH5alpha_2', ('GVP0010', 'B0034', 'sfGFP', 'B0015', 'Odd_1', 'replicate_2'), 'Media_1'], 'A2': ['Competent_Cell_DH5alpha_2', ('GVP0012', 'B0034', 'sfGFP', 'B0015', 'Odd_1', 'replicate_1'), 'Media_1'], 'B2': ['Competent_Cell_DH5alpha_2', ('GVP0012', 'B0034', 'sfGFP', 'B0015', 'Odd_1', 'replicate_1'), 'Media_1'], 'C2': ['Competent_Cell_DH5alpha_3', ('GVP0012', 'B0034', 'sfGFP', 'B0015', 'Odd_1', 'replicate_2'), 'Media_1'], 'D2': ['Competent_Cell_DH5alpha_3', ('GVP0012', 'B0034', 'sfGFP', 'B0015', 'Odd_1', 'replicate_2'), 'Media_1']}
def run(protocol: protocol_api.ProtocolContext):
    plating_protocol = Plating(bacterium_locations=constructs,replicates=2)
    plating_protocol.run(protocol)