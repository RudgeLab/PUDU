from pudu.transformation import Chemical_transformation
from opentrons import protocol_api

# metadata
metadata = {
'protocolName': 'PUDU Transformation',
'author': 'Gonzalo Vidal <g.a.vidal-pena2@ncl.ac.uk>',
'description': 'Automated transformation protocol',
'apiLevel': '2.13'}

def run(protocol= protocol_api.ProtocolContext):

    pudu_transformation = Chemical_transformation(list_of_dnas=['pro', 'rbs','cds', 'ter'], competent_cells = 'DH5alpha')
    pudu_transformation.run(protocol)
#After simulation look at the beginning of the output to see the position of input reagents and outputs.