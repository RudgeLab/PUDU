from pudu.test_setup import Plate_setup
from opentrons import protocol_api

# metadata
metadata = {
'protocolName': 'PUDU Plate Setup',
'author': 'Gonzalo Vidal <gsvidal@uc.cl>',
'description': 'Automated 96 well plate setup protocol',
'apiLevel': '2.13'}

def run(protocol= protocol_api.ProtocolContext):

    pudu_plate_setup = Plate_setup(samples=['s1', 's2','s3', 's4', 's5'])
    pudu_plate_setup.run(protocol)
    #chained actions
    #save sbol
    #doc = sbol3.Document()
    #doc.add(pudu_transformation.sbol_output)
    #doc.write('pudu_domestication.nt', sbol3.SORTED_NTRIPLES)
    #save xlsx
    pudu_plate_setup.get_xlsx_output('user_information_for_plate_setup.xlsx')


