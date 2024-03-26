from opentrons import protocol_api
from typing import List, Union
from pudu.utils import thermo_wells, temp_wells, liquid_transfer, slots, rows, row_letter_to_number

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

class Plate_samples(Test_setup):
    '''
    Creates a protocol for the automated setting of a 96 well plate from samples. Each sample is distributed in 4 wells of the plate.
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
                 use_temperature_module:bool = False,
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
        self.use_temperature_module = use_temperature_module
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

        #output
        print('Samples in tube rack')
        print(self.dict_of_samples_in_temp_mod_position)
        print('Samples in plate')
        print(self.dict_of_samples_in_plate)
        #END



class Plate_supplemented_samples(Test_setup):
    '''
    Creates a protocol for the automated setting of a 96 well plate with a gradient of inducer.

    '''
    def __init__(self,sample_name:str,
                 inducer_name:str,
                 inducer_initial_concentration:float = 1,
                 initial_mix_inducer_volume:float = 50.0,
                 initial_mix_sample_volume:float = 50.0,
                 serial_dilution_volume:float = 20,
                 serial_dilution_steps:int = 10,
                 number_of_replicates:int = 3,
                 starting_row:str = 'A',
                 sample_volume_plate:float = 200,
                 sample_labware:str = '96 well plate',
                 aspiration_rate:float=0.5,
                 dispense_rate:float=1,
                 tube_rack_labware:str = 'opentrons_24_aluminumblock_nest_1.5ml_snapcap',
                 tube_rack_position:int = 4,
                 tiprack_labware:str='opentrons_96_tiprack_300ul',
                 tiprack_position:int=9,
                 pipette:str='p300_single_gen2',
                 pipette_position:str='left',
                 use_temperature_module:bool = False,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.sample_name = sample_name
        self.inducer_name = inducer_name
        self.inducer_initial_concentration = inducer_initial_concentration
        self.initial_mix_sample_volume = initial_mix_sample_volume
        self.initial_mix_inducer_volume = initial_mix_inducer_volume
        self.serial_dilution_volume = serial_dilution_volume
        self.serial_dilution_steps = serial_dilution_steps
        self.number_of_replicates = number_of_replicates
        self.starting_row = starting_row
        self.sample_volume_plate = sample_volume_plate
        self.sample_labware = sample_labware
        self.aspiration_rate = aspiration_rate
        self.dispense_rate = dispense_rate
        self.tube_rack_labware = tube_rack_labware
        self.tube_rack_position = tube_rack_position
        self.tiprack_labware = tiprack_labware
        self.tiprack_position = tiprack_position
        self.pipette = pipette
        self.pipette_position = pipette_position
        self.use_temperature_module = use_temperature_module
        self.dict_of_samples_in_plate = {}
        self.dict_of_tubes_in_temp_mod_position = {}

        if self.serial_dilution_steps == 0:
            raise ValueError('Number of serial dilution steps must be greater than 0')
        if self.number_of_replicates < 3:
            raise Warning('Number of replicates must be greater than 3 for statistical analysis') 
        if self.number_of_replicates > 8:
            raise ValueError('Number of replicates must be less than 8 to fit in the 96 well plate')
        
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
        
        # Protocol
            
        # Load inducer
        temp_wells_counter = 0
        self.dict_of_tubes_in_temp_mod_position[self.inducer_name] = temp_wells[temp_wells_counter]
        temp_wells_counter += 1
        
        # Load samples and distribute them in the plate
        start_at_row = row_letter_to_number[self.starting_row] - 1

        for replicate_number in range(self.number_of_replicates + 1):
            working_row_index = start_at_row + replicate_number
            self.dict_of_tubes_in_temp_mod_position[f'replicate_{replicate_number}'] = temp_wells[temp_wells_counter]
            pipette.pick_up_tip()
            for dilution_step in range(self.serial_dilution_steps):
                position = rows[working_row_index][dilution_step+1]
                liquid_transfer(pipette, self.sample_volume_plate, tube_rack[self.dict_of_tubes_in_temp_mod_position[f'replicate_{replicate_number}']], plate[position], self.aspiration_rate, self.dispense_rate, new_tip=False, drop_tip=False)
            pipette.drop_tip()
            temp_wells_counter += 1
            working_row_index += 1


        # Create initial mix on the first row
        initial_mix_position = rows[start_at_row][0]
        self.dict_of_samples_in_plate['initial_mix'] = initial_mix_position
        #pipette sample to initial mix
        liquid_transfer(pipette, self.initial_mix_sample_volume, tube_rack[self.dict_of_tubes_in_temp_mod_position['replicate_1']], plate[initial_mix_position], self.aspiration_rate, self.dispense_rate)
        #pipette inducer to initial mix
        liquid_transfer(pipette, self.initial_mix_inducer_volume, tube_rack[self.dict_of_tubes_in_temp_mod_position[self.inducer_name]], plate[initial_mix_position], self.aspiration_rate, self.dispense_rate,mix_after=self.initial_mix_sample_volume/2)

        # Serial dilution
        for replicate_number in range(self.number_of_replicates):
            working_row_index = start_at_row + replicate_number
            pipette.pick_up_tip()
            for dilution_step in range(self.serial_dilution_steps):
                position = rows[working_row_index][dilution_step+1]
                liquid_transfer(pipette, self.serial_dilution_volume, tube_rack[self.dict_of_tubes_in_temp_mod_position[f'replicate_{replicate_number}']], plate[position], self.aspiration_rate, self.dispense_rate, mix_before=self.sample_volume_plate/2, new_tip=False, drop_tip=False)
                self.dict_of_samples_in_plate[f'replicate_{replicate_number}_dilution{dilution_step}'] = position
            pipette.drop_tip()
            working_row_index += 1
        
        #output
        print('Samples and inducer in tube rack')
        print(self.dict_of_tubes_in_temp_mod_position)
        print('Samples in plate')
        print(self.dict_of_samples_in_plate)
        #END



class Doe_test(Test_setup):
    '''
    Creates a protocol for the automated setting of a 96 well plate with a gradient of inducer.

    '''
