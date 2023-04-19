from pudu.assembly import Domestication
from opentrons import protocol_api
import sbol3

# metadata
metadata = {
'protocolName': 'PUDU Domestication',
'author': 'Gonzalo Vidal <gsvidal@uc.cl>',
'description': 'Automated DNA domestication protocol',
'apiLevel': '2.13'}

def run(protocol= protocol_api.ProtocolContext):

    pudu_domestication = Domestication(parts=['pro', 'rbs','cds', 'ter'], acceptor_backbone='UA')
    pudu_domestication.run(protocol)
    #chained actions
    #save sbol
    doc = sbol3.Document()
    doc.add(pudu_domestication.sbol_output)
    doc.write('pudu_domestication.nt', sbol3.SORTED_NTRIPLES)
    #save xlsx
    pudu_domestication.get_xlsx_output('write_dict_pudu_test_method')


