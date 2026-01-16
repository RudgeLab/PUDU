from opentrons import protocol_api
from typing import List, Dict, Union
from fnmatch import fnmatch
from itertools import product
import xlsxwriter

# utils

#96 well List
plate_96_wells = [
'A1','A2','A3','A4','A5','A6','A7','A8','A9','A10','A11','A12',
'B1','B2','B3','B4','B5','B6','B7','B8','B9','B10','B11','B12',
'C1','C2','C3','C4','C5','C6','C7','C8','C9','C10','C11','C12',
'D1','D2','D3','D4','D5','D6','D7','D8','D9','D10','D11','D12',
'E1','E2','E3','E4','E5','E6','E7','E8','E9','E10','E11','E12',
'F1','F2','F3','F4','F5','F6','F7','F8','F9','F10','F11','F12',
'G1','G2','G3','G4','G5','G6','G7','G8','G9','G10','G11','G12',
'H1','H2','H3','H4','H5','H6','H7','H8','H9','H10','H11','H12'
]

#filler variable equal to well List
thermo_wells = plate_96_wells

#Function to transfer Liquid
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

#new List for temporary wells
temp_wells = [
'A1','A2','A3','A4','A5','A6',
'B1','B2','B3','B4','B5','B6',
'C1','C2','C3','C4','C5','C6',
'D1','D2','D3','D4','D5','D6'
]

#class DNA Assembly
class DNA_assembly():
    '''
    Creates a protocol for automated DNA assembly.

    Attributes
    ----------
    volume_total_reaction : float
        The total volume of the reaction mix in microliters. By default, 20 microliters.
    volume_part : float
        The volume of each part in microliters. By default, 2 microliters.
    volume_restriction_enzyme : float
        The volume of the restriction enzyme in microliters. By default, 2 microliters.
    volume_t4_dna_ligase : float
        The volume of T4 DNA Ligase in microliters. By default, 4 microliters.
    volume_t4_dna_ligase_buffer : float
        The volume of T4 DNA Ligase Buffer in microliters. By default, 2 microliters.
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
    #self attributes
    def __init__(self,
        volume_total_reaction:float = 20,
        volume_part:float = 2,
        volume_restriction_enzyme:float = 2,
        volume_t4_dna_ligase:float = 4,
        volume_t4_dna_ligase_buffer:float = 2,
        replicates:int=1,
        thermocycler_starting_well:int = 0,
        thermocycler_labware:str = 'nest_96_wellplate_100ul_pcr_full_skirt',
        temperature_module_labware:str = 'opentrons_24_aluminumblock_nest_1.5ml_snapcap',
        temperature_module_position:int = 1,
        tiprack_labware:str = 'opentrons_96_tiprack_20ul',
        tiprack_position:int = 9,
        pipette:str = 'p20_single_gen2',
        pipette_position:str = 'left',
        aspiration_rate:float=0.5,
        dispense_rate:float=1,):

        self.volume_total_reaction = volume_total_reaction
        self.volume_part = volume_part
        self.volume_restriction_enzyme = volume_restriction_enzyme
        self.volume_t4_dna_ligase = volume_t4_dna_ligase
        self.volume_t4_dna_ligase_buffer = volume_t4_dna_ligase_buffer
        self.replicates = replicates
        self.thermocycler_starting_well = thermocycler_starting_well
        self.thermocycler_labware = thermocycler_labware
        self.temperature_module_labware = temperature_module_labware
        self.temperature_module_position = temperature_module_position
        self.tiprack_labware = tiprack_labware
        self.tiprack_position = tiprack_position
        self.pipette = pipette
        self.pipette_position = pipette_position
        self.aspiration_rate = aspiration_rate
        self.dispense_rate = dispense_rate

class sbol2assembly(DNA_assembly):
    '''
    Creates a protocol from a dictionary for the automated assembly.

    '''
    def __init__(self, assemblies:List[Dict],
        *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.assemblies = assemblies
        self.dict_of_parts_in_temp_mod_position = {}
        self.dict_of_parts_in_thermocycler = {}
        self.assembly_plan = None
        self.parts_set = set()
        self.backbone_set = set()
        self.restriction_enzyme_set = set()
        self.combined_set = set()
        self.has_odd = False
        self.has_even = False
        self.odd_combinations = []
        self.even_combinations = []

        # add parts to a set
        for assembly in self.assemblies:       
            #part parts
            for part in assembly["PartsList"]:
                self.parts_set.add(part)
            #backbone parts
            self.backbone_set.add(assembly["Backbone"])
            #add enzymes
            self.restriction_enzyme_set.add(assembly["Restriction Enzyme"])

        self.combined_set = self.parts_set.union(self.backbone_set)

        max_parts = 19 #TODO check if this olds, 20
        if len(self.combined_set) > max_parts:
            raise ValueError(f'This protocol only supports assemblies with up to {max_parts} parts. Number of parts in the protocol is {len(self.parts_set)}. Printing parts set:{self.parts_set}')
        thermocyler_available_wells = 96 - self.thermocycler_starting_well 
        thermocycler_wells_needed = (len(self.odd_combinations) + len(self.even_combinations))*self.replicates
        if thermocycler_wells_needed > thermocyler_available_wells:
            raise ValueError(f'According to your setup this protocol only supports assemblies with up to {thermocyler_available_wells} combinations. Number of combinations in the protocol is {thermocycler_wells_needed}.')                

    def run(self, protocol: protocol_api.ProtocolContext):
        #Labware
        #Load temperature module
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
        volume_reagents = self.volume_restriction_enzyme + self.volume_t4_dna_ligase + self.volume_t4_dna_ligase_buffer
        #Load the reagents
        dd_h2o = tem_mod_block['A1']
        self.dict_of_parts_in_temp_mod_position['dd_h2o'] = temp_wells[0]
        t4_dna_ligase = tem_mod_block['A2'] 
        self.dict_of_parts_in_temp_mod_position['t4_dna_ligase'] = temp_wells[1]
        t4_dna_ligase_buffer = tem_mod_block['A3'] 
        self.dict_of_parts_in_temp_mod_position['t4_dna_ligase_buffer'] = temp_wells[2]
        temp_wells_counter = 3 
        restriction_enzyme_tube = tem_mod_block[temp_wells[temp_wells_counter]]
        #load the enzymes
        for enzyme in self.restriction_enzyme_set:
            self.dict_of_parts_in_temp_mod_position[enzyme] = temp_wells[temp_wells_counter]
            temp_wells_counter += 1
        #Load the parts(includes backbones)
        for part in self.combined_set:
            self.dict_of_parts_in_temp_mod_position[part] = temp_wells[temp_wells_counter]
            temp_wells_counter += 1
        #Setup
        #Set the temperature of the temperature module and the thermocycler to 4°C
        tem_mod.set_temperature(4)
        thermocycler_mod.open_lid()
        thermocycler_mod.set_block_temperature(4)
        #can be done with multichannel pipette?
        current_thermocycler_well = self.thermocycler_starting_well
        #build combinations
        for assembly in self.assemblies:
            for r in range(self.replicates):
                volume_dd_h2o = self.volume_total_reaction - (volume_reagents + self.volume_part*len(assembly["PartsList"]))
                liquid_transfer(pipette, volume_dd_h2o, dd_h2o, thermocycler_mod_plate[thermo_wells[current_thermocycler_well]], self.aspiration_rate, self.dispense_rate)
                liquid_transfer(pipette, self.volume_t4_dna_ligase_buffer, t4_dna_ligase_buffer, thermocycler_mod_plate[thermo_wells[current_thermocycler_well]], self.aspiration_rate, self.dispense_rate, mix_before=self.volume_t4_dna_ligase_buffer)
                liquid_transfer(pipette, self.volume_t4_dna_ligase, t4_dna_ligase, thermocycler_mod_plate[thermo_wells[current_thermocycler_well]], self.aspiration_rate, self.dispense_rate, mix_before=self.volume_t4_dna_ligase)
                liquid_transfer(pipette, self.volume_restriction_enzyme, tem_mod_block[self.dict_of_parts_in_temp_mod_position[assembly['Restriction Enzyme']]], thermocycler_mod_plate[thermo_wells[current_thermocycler_well]], self.aspiration_rate, self.dispense_rate, mix_before=self.volume_restriction_enzyme)
                #pippeting backbone
                liquid_transfer(pipette, self.volume_part, tem_mod_block[self.dict_of_parts_in_temp_mod_position[assembly["Backbone"]]], thermocycler_mod_plate[thermo_wells[current_thermocycler_well]], self.aspiration_rate, self.dispense_rate, mix_before=self.volume_part)
                #pippeting parts
                for part in assembly["PartsList"]:
                        if type(part) == str:
                            part_name=part  
                        else: raise ValueError(f'Part {part} is not a string nor sbol2.Component') #TODO: improve this check 
                        #part_ubication_in_thermocyler = thermocycler_mod_plate[thermo_wells[current_thermocycler_well]]
                        liquid_transfer(pipette, self.volume_part, tem_mod_block[self.dict_of_parts_in_temp_mod_position[part_name]], thermocycler_mod_plate[thermo_wells[current_thermocycler_well]], self.aspiration_rate, self.dispense_rate, mix_before=self.volume_part)
                #This line under this comment was written to get it to run, not run correctly        
                #need products uri 
                self.dict_of_parts_in_thermocycler[assembly["Product"]] = thermo_wells[current_thermocycler_well]
                current_thermocycler_well+=1     

        protocol.comment('Take out the reagents since the temperature module will be turn off')
        #We close the thermocycler lid and wait for the temperature to reach 42°C
        thermocycler_mod.close_lid()
        #The thermocycler's lid temperature is set with the following command
        thermocycler_mod.set_lid_temperature(42)
        tem_mod.deactivate()
        #Cycles were made following https://pubs.acs.org/doi/10.1021/sb500366v
        profile = [
            {'temperature': 42, 'hold_time_minutes': 2},
            {'temperature': 16, 'hold_time_minutes': 5}]
        thermocycler_mod.execute_profile(steps=profile, repetitions=25, block_max_volume=30)

        denaturation = [
            {'temperature': 60, 'hold_time_minutes': 10},
            {'temperature': 80, 'hold_time_minutes': 10}]
        thermocycler_mod.execute_profile(steps=denaturation, repetitions=1, block_max_volume=30)
        thermocycler_mod.set_block_temperature(4)
        #END

    def get_xlsx_output(self, name:str):
        workbook = xlsxwriter.Workbook(f'{name}.xlsx')
        worksheet = workbook.add_worksheet()
        row_num = 0
        col_num = 0
        worksheet.write(row_num, col_num, 'Parts in temp_module')
        row_num += 2
        for key, value in self.dict_of_parts_in_temp_mod_position.items():
            worksheet.write(row_num, col_num, key)
            worksheet.write(row_num+1, col_num, value)
            col_num += 1
        col_num = 0
        row_num += 4
        worksheet.write(row_num, col_num, 'Parts in thermocycler_module')
        row_num += 2
        for key, value in self.dict_of_parts_in_thermocycler.items():
            worksheet.write(row_num, col_num, key)
            worksheet.write_column(row_num+1, col_num, value)
            col_num += 1
        workbook.close()
        self.xlsx_output = workbook
        return self.xlsx_output

    #Make a print function for later
    #output
    #print('Parts and reagents in temp_module')
    #print(self.dict_of_parts_in_temp_mod_position)
    #print('Assembled parts in thermocycler_module')
    #print(self.dict_of_parts_in_thermocycler)    

#Where dictionary used to be 


#create a recursive function based on the how many times 
#def assemblyRecursion(, duplicate dictionaries, amount):
#   append()

#Todo find product uri

# metadata
metadata = {
'protocolName': 'PUDU Loop assembly',
'author': 'Gonzalo Vidal <g.a.vidal-pena2@ncl.ac.uk>',
'description': 'Automated DNA assembly Loop protocol',
'apiLevel': '2.13'}

def run(protocol= protocol_api.ProtocolContext):

    #Take the Json file from Assembly to Dict then set it to assembly_sbol2_uris
    #I am taking in the name of Json file and make it assembly
    #import using pandas or somthing to convert to usable dictionary
    import json
    with open("scripts/output.json", "r") as f:
        assembly_sbol2_uris = json.load(f)


    pudu_sbol2_assembly = sbol2assembly(assemblies=assembly_sbol2_uris)
    pudu_sbol2_assembly.run(protocol)
    pudu_sbol2_assembly.get_xlsx_output("SBOL_xlsx5")
