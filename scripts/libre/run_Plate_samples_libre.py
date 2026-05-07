from opentrons import protocol_api
from typing import List, Union

thermo_wells = [
'A1','A2','A3','A4','A5','A6','A7','A8','A9','A10','A11','A12',
'B1','B2','B3','B4','B5','B6','B7','B8','B9','B10','B11','B12',
'C1','C2','C3','C4','C5','C6','C7','C8','C9','C10','C11','C12',
'D1','D2','D3','D4','D5','D6','D7','D8','D9','D10','D11','D12',
'E1','E2','E3','E4','E5','E6','E7','E8','E9','E10','E11','E12',
'F1','F2','F3','F4','F5','F6','F7','F8','F9','F10','F11','F12',
'G1','G2','G3','G4','G5','G6','G7','G8','G9','G10','G11','G12',
'H1','H2','H3','H4','H5','H6','H7','H8','H9','H10','H11','H12'
]

temp_wells = [
'A1','A2','A3','A4','A5','A6',
'B1','B2','B3','B4','B5','B6',
'C1','C2','C3','C4','C5','C6',
'D1','D2','D3','D4','D5','D6'
]


def liquid_transfer(pipette, volume, source, destination, asp_rate:float=0.5, disp_rate:float=1.0, blow_out:bool=True, touch_tip:bool=False, mix_before:float=0.0, mix_after:float=0.0, mix_reps:int=3, new_tip:bool=True, drop_tip:bool=True):
    if new_tip:
        pipette.pick_up_tip()
    if mix_before > 0:
        pipette.mix(mix_reps, mix_before, source)
    pipette.aspirate(volume, source, rate=asp_rate)
    pipette.dispense(volume, destination, rate=disp_rate)
    if mix_after > 0:
        pipette.mix(mix_reps, mix_after, destination)
    if blow_out: 
        pipette.blow_out()
    if touch_tip:
        pipette.touch_tip()
    if drop_tip:
        pipette.drop_tip() 

#Define slots, to allocate 4 samples in each slot, lasts slots allocate in the border where border effects apply
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
                 starting_slot:int = 1,
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
        self.starting_slot = starting_slot

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
        slot_counter = self.starting_slot-1
        for sample in self.samples:
            self.dict_of_samples_in_temp_mod_position[sample] = temp_wells[temp_wells_counter]
            pipette.pick_up_tip()
            for position in slots[slot_counter]:
                liquid_transfer(pipette, self.sample_well_volume, tube_rack[self.dict_of_samples_in_temp_mod_position[sample]], plate[position], self.aspiration_rate, self.dispense_rate, mix_before=self.sample_well_volume, mix_after=self.sample_well_volume/2, new_tip=False, drop_tip=False)
            pipette.drop_tip()
            self.dict_of_samples_in_plate[sample] = slots[slot_counter]
            temp_wells_counter += 1
            slot_counter += 1

        #output
        print('Samples in tube rack')
        print(self.dict_of_samples_in_temp_mod_position)
        print('Samples in plate')
        print(self.dict_of_samples_in_plate)
        #END

# metadata
metadata = {
'protocolName': 'PUDU Plate Setup',
'author': 'Gonzalo Vidal <g.a.vidal-pena2@ncl.ac.uk>',
'description': 'Automated 96 well plate setup protocol',
'apiLevel': '2.13'}

def run(protocol= protocol_api.ProtocolContext):

    pudu_plate_samples = Plate_samples(samples=['s1', 's2','s3', 's4', 's5', 's6'], starting_slot=13)
    pudu_plate_samples.run(protocol)