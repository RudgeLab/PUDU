from pudu.calibration import iGEM_gfp_od
from opentrons import protocol_api

# metadata
metadata = {
'protocolName': 'iGEM GFP OD600 calibration',
'author': 'Gonzalo Vidal <g.a.vidal-pena2@ncl.ac.uk>',
'description': 'Protocol to perform serial dilutions of fluorescein and nanoparticles for calibration',
'apiLevel': '2.13'}

def run(protocol= protocol_api.ProtocolContext):

    pudu_calibration = iGEM_gfp_od()
    pudu_calibration.run(protocol)