from opentrons import protocol_api
import sbol3
from pudu.utils import thermo_wells, temp_wells, liquid_transfer
from typing import List, Dict
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
        list_of_dnas:List = [],
        competent_cells: str = None,
        replicates:int=2,
        thermocycler_starting_well:int = 0,
        thermocycler_labware:str = 'nest_96_wellplate_100ul_pcr_full_skirt',
        temperature_module_labware:str = 'opentrons_24_aluminumblock_nest_1.5ml_snapcap',
        temperature_module_position:int = 1,

        tiprack_p20_labware:str = 'opentrons_96_tiprack_20ul',
        tiprack_p20_osition:int = 9,
        tiprack_p300_labware:str = 'opentrons_96_tiprack_300ul',
        tiprack_p300_osition:int = 6,
        pipette_p20:str = 'p20_single_gen2',
        pipette_p300:str = 'p300_single_gen2',
        pipette_p20_position:str = 'left',
        pipette_p300_position:str = 'right',
        aspiration_rate:float=0.5,
        dispense_rate:float=1,):
        
        self.list_of_dnas = list_of_dnas
        self.competent_cells = competent_cells
        self.replicates = replicates
        self.thermocycler_starting_well = thermocycler_starting_well
        self.thermocycler_labware = thermocycler_labware
        self.temperature_module_labware = temperature_module_labware
        self.temperature_module_position = temperature_module_position
        self.tiprack_p20_labware = tiprack_p20_labware
        self.tiprack_p20_position = tiprack_p20_osition
        self.tiprack_p300_labware = tiprack_p300_labware
        self.tiprack_p300_position = tiprack_p300_osition
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
    def __init__(self, 
                volume_dna:float = 2,
                volume_competent_cell_to_add:float = 20,
                volume_competent_cell_per_tube:float =100,
                volume_recovery_media_to_add:float = 60,
                volume_recovery_media_per_tube:float = 1200, #add a bit more to pick it properly
                cold_incubation1:Dict = {'temperature': 4, 'hold_time_minutes': 30}, 
                heat_shock:Dict = {'temperature': 42, 'hold_time_minutes': 1}, 
                cold_incubation2:Dict = {'temperature': 4, 'hold_time_minutes': 2}, 
                recovery_incubation:Dict = {'temperature': 37, 'hold_time_minutes': 60},
                *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.volume_dna = volume_dna
        self.volume_competent_cell_to_add = volume_competent_cell_to_add
        self.volume_competent_cell_per_tube = volume_competent_cell_per_tube
        self.volume_recovery_media = volume_recovery_media_to_add
        self.volume_recovery_media_per_tube = volume_recovery_media_per_tube
        self.cold_incubation1 = cold_incubation1
        self.heat_shock = heat_shock
        self.cold_incubation2 = cold_incubation2
        self.recovery_incubation = recovery_incubation
        self.dict_of_parts_in_temp_mod_position = {}
        self.dict_of_parts_in_thermocycler = {}
        self.sbol_output = []
        self.xlsx_output = None

        metadata = {
        'protocolName': 'PUDU Transformation',
        'author': 'Gonzalo Vidal <gsvidal@uc.cl>',
        'description': 'Automated transformation protocol',
        'apiLevel': '2.13'}

    def run(self, protocol: protocol_api.ProtocolContext): 

        #Labware
        #Load the magnetic module
        tem_mod = protocol.load_module('temperature module', f'{self.temperature_module_position}') 
        tem_mod_block = tem_mod.load_labware(self.temperature_module_labware)
        #Load the thermocycler module, its default location is on slots 7, 8, 10 and 11
        thermocycler_mod = protocol.load_module('thermocycler module')
        thermocycler_mod_plate = thermocycler_mod.load_labware(self.thermocycler_labware)
        #Load the tiprack
        tiprack_p20 = protocol.load_labware(self.tiprack_p20_labware, f'{self.tiprack_p20_position}')
        tiprack_p300 = protocol.load_labware(self.tiprack_p300_labware, f'{self.tiprack_p300_position}')
        #Load the pipette
        pipette_p20 = protocol.load_instrument(self.pipette_p20, self.pipette_p20_position, tip_racks=[tiprack_p20])
        pipette_p300 = protocol.load_instrument(self.pipette_p300, self.pipette_p300_position, tip_racks=[tiprack_p300])
        
        #Load the reagents
        #Check number of compenent cells and DNAs
        total_transformations = len(self.list_of_dnas)*self.replicates
        transformations_per_tube = int(self.volume_competent_cell_per_tube//self.volume_competent_cell_to_add)
        number_of_tubes_with_competent_cells_needed = int(total_transformations//transformations_per_tube+1) #TODO: make an int, maybe use sail
        #Check number of tubes with media
        transformations_per_media_tube = int(self.volume_recovery_media_per_tube//self.volume_recovery_media)
        number_of_tubes_with_media_needed = int(total_transformations//transformations_per_media_tube+1) #TODO: make an int, maybe use sail
        if len(self.list_of_dnas)+number_of_tubes_with_competent_cells_needed+number_of_tubes_with_media_needed > 24:
             raise ValueError(f'The number of reagents is more than 24. There are {len(self.list_of_dnas)} DNAs, {number_of_tubes_with_competent_cells_needed} tubes with competent cells and {number_of_tubes_with_media_needed} tubes with media. Please change the protocol and try again.')
        temp_wells_counter = 0
        for dna in self.list_of_dnas:
            self.dict_of_parts_in_temp_mod_position[dna] = temp_wells[temp_wells_counter]
            temp_wells_counter += 1
        for i in range(number_of_tubes_with_competent_cells_needed):
            self.dict_of_parts_in_temp_mod_position[f'Competent_cells_tube_{i}'] = temp_wells[temp_wells_counter]
            temp_wells_counter += 1
        for i in range(number_of_tubes_with_media_needed):
            self.dict_of_parts_in_temp_mod_position[f'Media_tube_{i}'] = temp_wells[temp_wells_counter]
            temp_wells_counter += 1
        #Set Temperature and Thermocycler module to 4
        tem_mod.set_temperature(4)
        thermocycler_mod.open_lid()
        thermocycler_mod.set_block_temperature(4)
        #Load cells into the thermocycler
        if self.volume_competent_cell_to_add > 20:
            pipette = pipette_p300
        else:
            pipette = pipette_p20
        current_thermocycler_well_comp = self.thermocycler_starting_well 
        transformation_well = 1
        #for r in range(self.replicates):
        for i in range(number_of_tubes_with_competent_cells_needed):
            for j in range(transformations_per_tube):
                part_ubication_in_thermocyler = thermocycler_mod_plate[thermo_wells[current_thermocycler_well_comp]]
                liquid_transfer(pipette, self.volume_competent_cell_to_add, tem_mod_block[self.dict_of_parts_in_temp_mod_position[f'Competent_cells_tube_{i}']], part_ubication_in_thermocyler, self.aspiration_rate, self.dispense_rate, mix_before=self.volume_competent_cell_to_add -5)
                if j == 0:
                    self.dict_of_parts_in_thermocycler[f'Competent_cells_tube_{i}'] = [thermo_wells[current_thermocycler_well_comp]]   
                else:
                    self.dict_of_parts_in_thermocycler[f'Competent_cells_tube_{i}'].append(thermo_wells[current_thermocycler_well_comp]) 
                current_thermocycler_well_comp+=1
                if transformation_well == total_transformations:
                    break
                transformation_well+=1
            
        #Load DNA into the thermocycler and mix
        if self.volume_dna > 20:
            pipette = pipette_p300
        else:
            pipette = pipette_p20
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
        thermocycler_mod.close_lid()
        profile = [
            self.cold_incubation1, #1st cold incubation (long)
            self.heat_shock, #Heatshock
            self.cold_incubation2] #2nd cold incubation (short)
        thermocycler_mod.execute_profile(steps=profile, repetitions=1, block_max_volume=30)
        #Load LB and recovery incubation
        thermocycler_mod.open_lid()
        #TODO: check if there is the need for more than one tube
        if self.volume_recovery_media > 20:
            pipette = pipette_p300
        else:
            pipette = pipette_p20
        current_thermocycler_well_media = self.thermocycler_starting_well 
        transformation_well = 1
        for i in range(number_of_tubes_with_media_needed):
            for j in range(transformations_per_media_tube):
                part_ubication_in_thermocyler = thermocycler_mod_plate[thermo_wells[current_thermocycler_well_media]]
                liquid_transfer(pipette, self.volume_recovery_media, tem_mod_block[self.dict_of_parts_in_temp_mod_position[f'Media_tube_{i}']], part_ubication_in_thermocyler, self.aspiration_rate, self.dispense_rate, mix_after=self.volume_recovery_media -5)
                if j == 0:
                    self.dict_of_parts_in_thermocycler[f'Media_tube_{i}'] = [thermo_wells[current_thermocycler_well_media]]   
                else:
                    self.dict_of_parts_in_thermocycler[f'Media_tube_{i}'].append(thermo_wells[current_thermocycler_well_media]) 
                current_thermocycler_well_media+=1
                if transformation_well == total_transformations:
                    break
                transformation_well+=1
        thermocycler_mod.close_lid()
        recovery = [
            self.recovery_incubation]
        thermocycler_mod.execute_profile(steps=recovery, repetitions=1, block_max_volume=30)
        #Optionally plate
        #END

    def get_xlsx_output(self, name:str):
        workbook = xlsxwriter.Workbook(f'{name}.xlsx')
        worksheet = workbook.add_worksheet()
        row_num =0
        col_num =0
        worksheet.write(row_num, col_num, 'Reagents in temp_module')
        row_num +=2
        for key, value in self.dict_of_parts_in_temp_mod_position.items():
            worksheet.write(row_num, col_num, key)
            worksheet.write(row_num, col_num+1, value)
            row_num +=1
        col_num = 0
        row_num += 4
        worksheet.write(row_num, col_num, 'GMOs in thermocycler_module')
        row_num += 2
        for key, value in self.dict_of_parts_in_thermocycler.items():
            worksheet.write(row_num, col_num, key)
            worksheet.write_column(row_num+1, col_num, value)
            col_num += 1
        workbook.close()
        self.xlsx_output = workbook
        return self.xlsx_output
        #END