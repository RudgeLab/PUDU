from pudu.assembly import Domestication
from opentrons import protocol_api

# metadata
metadata = {
'protocolName': 'PUDU Domestication',
'author': 'Gonzalo Vidal <g.a.vidal-pena2@ncl.ac.uk>',
'description': 'Automated DNA domestication protocol',
'apiLevel': '2.13'}

def run(protocol= protocol_api.ProtocolContext):

    pudu_domestication = Domestication(parts=['pro', 'rbs','cds', 'ter'], acceptor_backbone='UA')
    pudu_domestication.run(protocol)

#After simulation look at the beginning of the output to see the position of input reagents and outputs.