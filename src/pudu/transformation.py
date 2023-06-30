from opentrons import protocol_api
import sbol3
from pudu.utils import thermo_wells, temp_wells, liquid_transfer
from typing import List, Dict, Union
from fnmatch import fnmatch
from itertools import product
import xlsxwriter


class Transformation():
    '''
    Creates a protocol for automated transformation.

    Attributes
    ----------
    volume_dna : float
        The volume DNA in microliters. By default, 2 microliters. We suggest 2 microliters for extracted plasmid and 5 microliters for PCR products.
    volume_competent_cells : float
        The volume of the competent cells in microliters. By default, 50 microliters.
    volume_recovery_media : float
        The volume of recovery media in microliters. By default, 100 microliters.
    replicates : int    
        The number of replicates of the assembly reaction. By default, 2.
    thermocycler_starting_well : int    
        The starting well of the thermocycler module. By default, 0.
    thermocycler_labware : str
        The labware type of the thermocycler module. By default, 'nest_96_wellplate_100ul_pcr_full_skirt'.
    thermocycler_slots : list
        The slots of the thermocycler module. By default, [7, 8, 10, 11].
    temperature_module_labware : str
        The labware type of the temperature module. By default, 'opentrons_24_aluminumblock_nest_1.5ml_snapcap'.
    temperature_module_slot : int
        The slot of the temperature module. By default, 1.
    tiprack_labware : str
        The labware type of the tiprack. By default, 'opentrons_96_tiprack_20ul'.
    tiprack_slot : int
        The slot of the tiprack. By default, 9.
    pipette_type : str
        The type of pipette. By default, 'p20_single_gen2'.
    pipette_mount : str
        The mount of the pipette. By default, 'left'.
    aspiration_rate : float
        The rate of aspiration in microliters per second. By default, 0.5 microliters per second.
    dispense_rate : float
        The rate of dispense in microliters per second. By default, 1 microliter per second.
    '''
    def __init__(self,
        list_of_dnas = [],
        volume_dna:float = 2,
        volume_competent_cell_to_add:float = 20,
        volume_competent_cell_per_tube:float =100,
        volume_recovery_media_to_add:float = 60,
        volume_recovery_media_per_tube:float = 1500,
        replicates:int=2,
        thermocycler_starting_well:int = 0,
        thermocycler_labware:str = 'nest_96_wellplate_100ul_pcr_full_skirt',
        temperature_module_labware:str = 'opentrons_24_aluminumblock_nest_1.5ml_snapcap',
        temperature_module_position:int = 1,
        tiprack_labware:str = 'opentrons_96_tiprack_20ul',
        tiprack_position:int = 9,
        pipette_p20:str = 'p20_single_gen2',
        pipette_p300:str = 'p300_single_gen2',
        pipette_p20_position:str = 'left',
        pipette_p300_position:str = 'right',
        aspiration_rate:float=0.5,
        dispense_rate:float=1,):
        
        self.list_of_dnas = list_of_dnas
        self.volume_dna = volume_dna
        self.volume_competent_cell_to_add = volume_competent_cell_to_add
        self.volume_competent_cell_per_tube = volume_competent_cell_per_tube
        self.volume_recovery_media = volume_recovery_media_to_add
        self.volume_recovery_media_per_tube = volume_recovery_media_per_tube
        self.replicates = replicates
        self.thermocycler_starting_well = thermocycler_starting_well
        self.thermocycler_labware = thermocycler_labware
        self.temperature_module_labware = temperature_module_labware
        self.temperature_module_position = temperature_module_position
        self.tiprack_labware = tiprack_labware
        self.tiprack_position = tiprack_position
        self.pipette_p20 = pipette_p20
        self.pipette_p300 = pipette_p300
        self.pipette_p20_position = pipette_p20_position
        self.pipette_p300_position = pipette_p300_position
        self.aspiration_rate = aspiration_rate
        self.dispense_rate = dispense_rate

class Chemical_transformation(Transformation): 
    '''
    Creates a protocol for automated transformation.

    Attributes
    ----------
    volume_dna : float
        The volume DNA in microliters. By default, 2 microliters. We suggest 2 microliters for extracted plasmid and 5 microliters for PCR products.
    volume_competent_cells : float
        The volume of the competent cells in microliters. By default, 50 microliters.
    volume_recovery_media : float
        The volume of recovery media in microliters. By default, 100 microliters.
    replicates : int    
        The number of replicates of the assembly reaction. By default, 2.
    thermocycler_starting_well : int    
        The starting well of the thermocycler module. By default, 0.
    thermocycler_labware : str
        The labware type of the thermocycler module. By default, 'nest_96_wellplate_100ul_pcr_full_skirt'.
    thermocycler_slots : list
        The slots of the thermocycler module. By default, [7, 8, 10, 11].
    temperature_module_labware : str
        The labware type of the temperature module. By default, 'opentrons_24_aluminumblock_nest_1.5ml_snapcap'.
    temperature_module_slot : int
        The slot of the temperature module. By default, 1.
    tiprack_labware : str
        The labware type of the tiprack. By default, 'opentrons_96_tiprack_20ul'.
    tiprack_slot : int
        The slot of the tiprack. By default, 9.
    pipette_type : str
        The type of pipette. By default, 'p20_single_gen2'.
    pipette_mount : str
        The mount of the pipette. By default, 'left'.
    aspiration_rate : float
        The rate of aspiration in microliters per second. By default, 0.5 microliters per second.
    dispense_rate : float
        The rate of dispense in microliters per second. By default, 1 microliter per second.
    '''
    def __init__(self, cold_incubation, heat_shock, post_heat_shock_incubation, recovery_incubation,
        *args, **kwargs):
            super().__init__(*args, **kwargs)

            self.cold_incubation = cold_incubation
            self.heat_shock = heat_shock
            self.post_heat_shock_incubation = post_heat_shock_incubation
            self.recovery_incubation = recovery_incubation
            self.dict_of_parts_in_temp_mod_position = {}
            self.dict_of_parts_in_thermocycler = {}
            self.sbol_output = []

            metadata = {
            'protocolName': 'Automated Golden Gate from SBOL',
            'author': 'Gonzalo Vidal <gsvidal@uc.cl>', 'Matt Burridge <m'
            'description': 'Protocol to perform a Golden Gate assembly from SBOL',
            'apiLevel': '2.13'}

    def run(self, protocol: protocol_api.ProtocolContext): 

        #Labware
        #Load the magnetic module
        tem_mod = protocol.load_module('temperature module', f'{self.temperature_module_position}') #CV: Previously was '3', but the cord was not long enough
        tem_mod_block = tem_mod.load_labware(self.temperature_module_labware)
        #Load the thermocycler module, its default location is on slots 7, 8, 10 and 11
        thermocycler_mod = protocol.load_module('thermocycler module')
        thermocycler_mod_plate = thermocycler_mod.load_labware(self.thermocycler_labware)
        #Load the tiprack
        tiprack = protocol.load_labware(self.tiprack_labware, f'{self.tiprack_position}')
        #Load the pipette
        pipette = protocol.load_instrument(self.pipette, self.pipette_position, tip_racks=[tiprack])
        #Fixed volumes
        #State volumes. They can be a function of [DNA], the minimun value is 1 uL
        #Parts should be diluted to the necessary concentration to aspirate 1 or 2 uL 
        volume_reagents =self.volume_restriction_enzyme + self.volume_t4_dna_ligase + self.volume_t4_dna_ligase_buffer
        
        #Load the reagents
        #Check number of compenent cells and DNAs
        total_transformations = len(self.list_of_dnas)
        transformations_per_tube = self.volume_competent_cell_per_tube/self.volume_competent_cell_to_add
        number_of_tubes_with_competent_cells_needed = total_transformations/transformations_per_tube #TODO: make an int, maybe use sail
        if len(self.list_of_dnas)+number_of_tubes_with_competent_cells_needed > 24:
             raise ValueError(f'The number of reagents is more than 24. There are {len(self.list_of_dnas)} DNAs and {number_of_tubes_with_competent_cells_needed} tubes with competent cells. Please change the protocol and try again.')
        temp_wells_counter = 0
        for dna in self.list_of_dnas:
            self.dict_of_parts_in_temp_mod_position[dna] = temp_wells[temp_wells_counter]
            temp_wells_counter += 1
        for i in number_of_tubes_with_competent_cells_needed:
            self.dict_of_parts_in_temp_mod_position[f'Competent_cells_tube_{i}'] = temp_wells[temp_wells_counter]
            temp_wells_counter += 1
        
        #Set Temperature and Thermocycler module to 4
        tem_mod.set_temperature(4)
        thermocycler_mod.open_lid()
        thermocycler_mod.set_block_temperature(4)
        #Load cells into the thermocycler
        current_thermocycler_well_comp = self.thermocycler_starting_well 
        for r in range(self.replicates):
            for i in number_of_tubes_with_competent_cells_needed:
                for j in transformations_per_tube:
                    part_ubication_in_thermocyler = thermocycler_mod_plate[thermo_wells[current_thermocycler_well_comp]]
                    liquid_transfer(pipette, self.volume_competent_cell_to_add, tem_mod_block[self.dict_of_parts_in_temp_mod_position[f'Competent_cells_tube_{i}']], part_ubication_in_thermocyler, self.aspiration_rate, self.dispense_rate, mix_before=self.volume_competent_cell_to_take)
                    if r == 0:
                        self.dict_of_parts_in_thermocycler[f'Competent_cells_tube_{i}'] = [thermo_wells[current_thermocycler_well_comp]]   
                    else:
                        self.dict_of_parts_in_thermocycler[f'Competent_cells_tube_{i}'].append(thermo_wells[current_thermocycler_well_comp]) 
                    current_thermocycler_well_comp+=1
            
        #Load DNA into the thermocycler and mix
        current_thermocycler_well_dna = self.thermocycler_starting_well 
        for r in range(self.replicates):
            for dna in self.list_of_dnas:
                part_ubication_in_thermocyler = thermocycler_mod_plate[thermo_wells[current_thermocycler_well_dna]]
                liquid_transfer(pipette, self.volume_dna, tem_mod_block[self.dict_of_parts_in_temp_mod_position[dna]], part_ubication_in_thermocyler, self.aspiration_rate, self.dispense_rate, mix_before=self.volume_dna)
                if r == 0:
                    self.dict_of_parts_in_thermocycler[dna] = [thermo_wells[current_thermocycler_well_dna]]   
                else:
                    self.dict_of_parts_in_thermocycler[dna].append(thermo_wells[current_thermocycler_well_dna]) 
                current_thermocycler_well_dna+=1
        #Cold incubation
        profile = [
            {'temperature': 4, 'hold_time_minutes': 30}, #1st cold incubation (long)
            {'temperature': 42, 'hold_time_minutes': 1}, #Heatshock
            {'temperature': 4, 'hold_time_minutes': 2}] #2nd cold incubation (short)
        thermocycler_mod.execute_profile(steps=profile, repetitions=1, block_max_volume=30)
        #Add LB and recovery incubation
        current_thermocycler_well_media = self.thermocycler_starting_well 
        position_recovery_media = temp_wells[0] #TODO: review if there is the need for more than one tube
        for _ in range(self.replicates*self.list_of_dnas):
            liquid_transfer(pipette, self.volume_recovery_media, position_recovery_media, thermocycler_mod_plate[thermo_wells[current_thermocycler_well_media]], self.aspiration_rate, self.dispense_rate, mix_after=self.volume_recovery_media)
        #Optionally plate



