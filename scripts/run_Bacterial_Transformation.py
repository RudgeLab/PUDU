from pudu.transformation import HeatShockTransformation
from opentrons import protocol_api

# metadata
metadata = {
'protocolName': 'PUDU Transformation',
'author': 'Gonzalo Vidal <g.a.vidal-pena2@ncl.ac.uk>',
'description': 'Automated transformation protocol',
'apiLevel': '2.22'}

transformation_data = [
    {
        'Strain': 'composite_strain_1',
        'Chassis': 'DH5alpha',
        'Plasmids': ['composite_plasmid_1']
    }
]

def run(protocol= protocol_api.ProtocolContext):

    pudu_transformation = HeatShockTransformation(transformation_data=transformation_data)
    pudu_transformation.run(protocol)
#After simulation look at the beginning of the output to see the position of input reagents and outputs.
