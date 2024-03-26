from pudu.test_setup import Plate_supplemented_samples
from opentrons import protocol_api

# metadata
metadata = {
'protocolName': 'PUDU Plate Setup',
'author': 'Gonzalo Vidal <g.a.vidal-pena2@ncl.ac.uk>',
'description': 'Automated 96 well plate setup protocol',
'apiLevel': '2.13'}

def run(protocol= protocol_api.ProtocolContext):

    pudu_plate_supplemented_samples = Plate_supplemented_samples(sample_name='sample1', inducer_name='IPTG' )
    pudu_plate_supplemented_samples.run(protocol)