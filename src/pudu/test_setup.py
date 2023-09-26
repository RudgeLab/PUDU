import sbol3
from opentrons import protocol_api
from typing import List, Union
from pudu.utils import thermo_wells, temp_wells, liquid_transfer
import xlsxwriter

class Test_setup():
    '''
    Creates a protocol for the automated setting of a 96 well plate with a gradient of inducer.

    '''
    def __init__(self,
        test_labware:str = 'corning_96_wellplate_360ul_flat',
        test_position:int = 7,
        aspiration_rate:float=0.5,
        dispense_rate:float=1,):
        
        self.test_labware = test_labware
        self.test_position = test_position
        self.aspiration_rate = aspiration_rate
        self.dispense_rate = dispense_rate

class Plate_setup(Test_setup):
    '''
    Creates a protocol for the automated setting of a 96 well plate from samples.
    '''
    def __init__(self,samples:List,
                 sample_tube_volume:float = 1200,
                 sample_well_volume:float = 200,
                 tube_rack_labware:str = 'opentrons_24_aluminumblock_nest_1.5ml_snapcap',
                 tube_rack_position:int = 4,
                 tiprack_labware:str='opentrons_96_tiprack_300ul',
                 tiprack_position:int=9,
                 pipette:str='p300_single_gen2',
                 pipette_position:str='right',
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.samples = samples
        self.sample_tube_volume = sample_tube_volume
        self.sample_well_volume = sample_well_volume
        self.tube_rack_labware = tube_rack_labware
        self.tube_rack_position = tube_rack_position
        self.tiprack_labware = tiprack_labware
        self.tiprack_position = tiprack_position
        self.pipette = pipette
        self.pipette_position = pipette_position
        self.use_temperature_module = False
        self.dict_of_samples_in_plate = {}
        self.dict_of_samples_in_temp_mod_position = {}

        if len(self.samples) > 24:
            raise ValueError(f'Number of samples cant be greater than 24, you have {len(self.samples)}')

    def run(self, protocol: protocol_api.ProtocolContext):

        #Labware
        tiprack = protocol.load_labware(self.tiprack_labware, f'{self.tiprack_position}')
        pipette = protocol.load_instrument(self.pipette, self.pipette_position, tip_racks=[tiprack])
        plate = protocol.load_labware(self.test_labware, self.test_position)

        if self.use_temperature_module:
            temperature_module = protocol.load_module('Temperature Module', self.tube_rack_position)
            tube_rack = temperature_module.load_labware(self.tube_rack_labware)
        else:
            tube_rack = protocol.load_labware(self.tube_rack_labware, self.tube_rack_position)
        
        #Protocol

        #Define slots
        slot_1 = ['A2', 'B2', 'C2', 'D2']
        slot_2 = ['A3', 'B3', 'C3', 'D3']
        slot_3 = ['A4', 'B4', 'C4', 'D4']
        slot_4 = ['A5', 'B5', 'C5', 'D5']
        slot_5 = ['A6', 'B6', 'C6', 'D6']
        slot_6 = ['A7', 'B7', 'C7', 'D7']
        slot_7 = ['A8', 'B8', 'C8', 'D8']
        slot_8 = ['A9', 'B9', 'C9', 'D9']
        slot_9 = ['A10', 'B10', 'C10', 'D10']
        slot_10 = ['A11', 'B11', 'C11', 'D11']
        slot_11 = ['E2', 'F2', 'G2', 'H2']
        slot_12 = ['E3', 'F3', 'G3', 'H3']
        slot_13 = ['E4', 'F4', 'G4', 'H4']
        slot_14 = ['E5', 'F5', 'G5', 'H5']
        slot_15 = ['E6', 'F6', 'G6', 'H6']
        slot_16 = ['E7', 'F7', 'G7', 'H7']
        slot_17 = ['E8', 'F8', 'G8', 'H8']
        slot_18 = ['E9', 'F9', 'G9', 'H9']
        slot_19 = ['E10', 'F10', 'G10', 'H10']
        slot_20 = ['E11', 'F11', 'G11', 'H11']
        slot_21 = ['A1', 'B1', 'C1', 'D1']
        slot_22 = ['E1', 'F1', 'G1', 'H1']
        slot_23 = ['A12', 'B12', 'C12', 'D12']
        slot_24 = ['E12', 'F12', 'G12', 'H12']

        slots = [slot_1, slot_2, slot_3, slot_4, slot_5, slot_6, slot_7, slot_8, slot_9, slot_10, slot_11, slot_12, slot_13, slot_14, slot_15, slot_16, slot_17, slot_18, slot_19, slot_20, slot_21, slot_22, slot_23, slot_24]


        #Load samples
        temp_wells_counter = 0
        for sample in self.samples:
            self.dict_of_samples_in_temp_mod_position[sample] = temp_wells[temp_wells_counter]
            pipette.pick_up_tip()
            for position in slots[temp_wells_counter]:
                liquid_transfer(pipette, self.sample_well_volume, tube_rack[self.dict_of_samples_in_temp_mod_position[sample]], plate[position], self.aspiration_rate, self.dispense_rate, mix_before=self.sample_well_volume, mix_after=self.sample_well_volume/2, new_tip=False, drop_tip=False)
            pipette.drop_tip()
            self.dict_of_samples_in_plate[sample] = slots[temp_wells_counter]
            temp_wells_counter += 1

        print(self.dict_of_samples_in_temp_mod_position)
        print(self.dict_of_samples_in_plate)
    
    def get_xlsx_output(self, name:str):
        workbook = xlsxwriter.Workbook(f'{name}.xlsx')
        worksheet = workbook.add_worksheet()
        row_num =0
        col_num =0
        worksheet.write(row_num, col_num, 'Samples in temp_module')
        row_num +=2
        for key, value in self.dict_of_samples_in_temp_mod_position.items():
            worksheet.write(row_num, col_num, key)
            worksheet.write(row_num, col_num+1, value)
            row_num +=1
        col_num = 0
        row_num += 4
        worksheet.write(row_num, col_num, 'Samples in 96 well plate')
        row_num += 2
        for key, value in self.dict_of_samples_in_plate.items():
            worksheet.write(row_num, col_num, key)
            worksheet.write_column(row_num+1, col_num, value)
            col_num += 1
        workbook.close()
        self.xlsx_output = workbook
        return self.xlsx_output
        #END



class Single_supplement_test(Test_setup):
    '''
    Creates a protocol for the automated setting of a 96 well plate with a gradient of inducer.

    '''
    def __init__(self,samples:List,
                 sample_volume:float = 2,
                 inducer:str = None,
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
        
        self.samples = samples
        self.sample_volume = sample_volume
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

        #Load media

        #Load supplement

        #Load cells



class Doe_test(Test_setup):
    '''
    Creates a protocol for the automated setting of a 96 well plate with a gradient of inducer.

    '''
