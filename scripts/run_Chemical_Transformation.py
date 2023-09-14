from pudu.transformation import Chemical_transformation
from opentrons import protocol_api

# metadata
metadata = {
'protocolName': 'PUDU Transformation',
'author': 'Gonzalo Vidal <gsvidal@uc.cl>',
'description': 'Automated transformation protocol',
'apiLevel': '2.13'}

def run(protocol= protocol_api.ProtocolContext):

    pudu_transformation = Chemical_transformation(list_of_dnas=['pro', 'rbs','cds', 'ter'], competent_cells = 'DH5alpha')
    pudu_transformation.run(protocol)
    #chained actions
    #save sbol
    #doc = sbol3.Document()
    #doc.add(pudu_transformation.sbol_output)
    #doc.write('pudu_domestication.nt', sbol3.SORTED_NTRIPLES)
    #save xlsx
    #pudu_transformation.get_xlsx_output('write_dict_pudu_test_method')


