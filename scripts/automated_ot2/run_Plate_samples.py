from pudu.sample_preparation import PlateSamples
from opentrons import protocol_api

# metadata
metadata = {
'protocolName': 'PUDU Plate Setup',
'author': 'Gonzalo Vidal <g.a.vidal-pena2@ncl.ac.uk>',
'description': 'Automated 96 well plate setup protocol',
'apiLevel': '2.14'}

def run(protocol= protocol_api.ProtocolContext):

    pudu_plate_samples = PlateSamples(samples=['s1', 's2','s3', 's4', 's5'])
    pudu_plate_samples.run(protocol)