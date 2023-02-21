import sbol3
from opentrons import protocol_api
from typing import List, Union

class Test_setup():
    '''
    Creates a protocol for the automated setting of a 96 well plate with a gradient of inducer.

    '''
    def __init__(self,
        test_labware:str = 'corning_96_wellplate_360ul_flat',
        test_position:int = 7,
        media_labware:str = 'opentrons_24_aluminumblock_nest_2ml_snapcap',
        media_position:List = ['A2','A3'],
        supplement_labware:str = 'opentrons_24_aluminumblock_nest_2ml_snapcap',
        supplement_position:List = ['A1'],
        aspiration_rate:float=0.5,
        dispense_rate:float=1,
        tiprack20_labware:str='opentrons_96_tiprack_20ul',
        tiprack20_position:int=9,
        tiprack300_labware:str='opentrons_96_tiprack_300ul',
        tiprack300_position:int=6,
        pipette_right:str='p20_single_gen2',
        pipette_left:str='p300_single_gen2',):
        
        self.test_labware = test_labware
        self.test_position = test_position
        self.media_position = media_position
        self.media_labware = media_labware
        self.supplement_labware = supplement_labware
        self.supplement_position = supplement_position
        self.aspiration_rate = aspiration_rate
        self.dispense_rate = dispense_rate
        self.tiprack20_labware = tiprack20_labware
        self.tiprack20_position = tiprack20_position
        self.tiprack300_labware = tiprack300_labware
        self.tiprack300_position = tiprack300_position
        self.pipette_right = pipette_right
        self.pipette_left = pipette_left


        if self.number_of_inducer_step == 0:
            raise ValueError('Number of inducer steps must be greater than 0')
        if self.number_of_replicates < 3:
            raise ValueError('Number of replicates must be greater than 3') 
        if self.number_of_inducer_step * self.number_of_replicates > 64:
            raise ValueError('Number of inducer steps with their replicates must be less than 64')

class Single_supplement_test(Test_setup):
    '''
    Creates a protocol for the automated setting of a 96 well plate with a gradient of inducer.

    '''
    def __init__(self,inducer:sbol3.Component,
                 inducer_initial_concentration:float = 0.0,
                 inducer_final_concentration:float = 0.0,
                 number_of_inducer_step:int = 0,
                 number_of_replicates:int = 3,
                 
                 media_labware:str = '96 well plate',
                 media_position:int = 20,
                 inducer_labware:str = '96 well plate',
                 inducer_position:int = 20,
                 aspiration_rate:float=0.5,
                 dispense_rate:float=1,
                 tiprack_labware:str='opentrons_96_tiprack_300ul',
                 tiprack_position:int=9,
                 pipette:str='p300_single_gen2',
                 pipette_position:str='left'):
        
        self.inducer = inducer
        self.inducer_initial_concentration = inducer_initial_concentration
        self.inducer_final_concentration = inducer_final_concentration
        self.number_of_inducer_step = number_of_inducer_step
        self.number_of_replicates = number_of_replicates
        self.media_labware = media_labware
        self.media_position = media_position
        self.inducer_labware = inducer_labware
        self.inducer_position = inducer_position
        self.aspiration_rate = aspiration_rate
        self.dispense_rate = dispense_rate
        self.tiprack_labware = tiprack_labware
        self.tiprack_position = tiprack_position
        self.pipette = pipette
        self.pipette_position = pipette_position


        if self.number_of_inducer_step == 0:
            raise ValueError('Number of inducer steps must be greater than 0')
        if self.number_of_replicates < 3:
            raise ValueError('Number of replicates must be greater than 3') 
        if self.number_of_inducer_step * self.number_of_replicates > 56:
            raise ValueError('Number of inducer steps with their replicates must be less than 56')

    def run(self, protocol: protocol_api.ProtocolContext):

        #Labware
        tiprack = protocol.load_labware(self.tiprack_labware, f'{self.tiprack_position}')
        pipette = protocol.load_instrument(self.pipette, self.pipette_position, tip_racks=[tiprack])
        plate = protocol.load_labware(self.calibration_plate_labware, self.calibration_plate_position)
        if self.use_temperature_module:
            temperature_module = protocol.load_module('Temperature Module', self.tube_rack_position)
            tube_rack = temperature_module.load_labware(self.tube_rack_labware)
        else:
            tube_rack = protocol.load_labware(self.tube_rack_labware, self.tube_rack_position)
        if self.use_falcon_tubes:
            falcon_tube_rack = protocol.load_labware(self.falcon_tube_rack_labware, self.falcon_tube_rack_position)
        #Protocol
        #set deck



class Double_supplement_test(Test_setup):
    '''
    Creates a protocol for the automated setting of a 96 well plate with a gradient of inducer.

    '''
