from pudu.assembly import Loop_assembly
from opentrons import protocol_api
import sbol3

assembly_Odd_1 = {"promoter":["j23101", "j23100"], "rbs":"B0034", "cds":"GFP", "terminator":"B0015", "receiver":"Odd_1"}
assembly_Even_2 = {"c4_receptor":"GD0001", "c4_buff_gfp":"GD0002", "spacer1":"20ins1", "spacer2":"Even_2", "receiver":"Even_2"}
assemblies = [assembly_Odd_1, assembly_Even_2]

# metadata
metadata = {
'protocolName': 'PUDU Loop assembly',
'author': 'Gonzalo Vidal <g.a.vidal-pena2@ncl.ac.uk>',
'description': 'Automated DNA assembly Loop protocol',
'apiLevel': '2.13'}

def run(protocol= protocol_api.ProtocolContext):

    pudu_loop_assembly = Loop_assembly(assemblies=assemblies,)
    pudu_loop_assembly.run(protocol)