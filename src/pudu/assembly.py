from opentrons import protocol_api
import sbol3
from sbol_utilities.helper_functions import find_top_level
from .utils import thermo_wells, temp_wells, liquid_transfer
from typing import List, Dict, Union
from fnmatch import fnmatch
from itertools import product


class DNA_assembly():
    '''
    Creates a protocol for the automated assembly of DNA.

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
    def __init__(self,
        volume_total_reaction:float = 20,
        volume_part:float = 2,
        volume_restriction_enzyme:float = 2,
        volume_t4_dna_ligase:float = 4,
        volume_t4_dna_ligase_buffer:float = 2,
        replicates:int=2,
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

class Protocol_from_sbol(DNA_assembly):
    '''
    Creates a protocol for the automated assembly of a SBOL Composite.

    Attributes
    ----------
    assembly_plan : sbol3.Component
        The SBOL Composite to be assembled.
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
    aspiration_rate : float
        The rate of aspiration in microliters per second. By default, 0.5 microliters per second.
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
    '''
    def __init__(self, assembly_plan:sbol3.Component,
       *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.assembly_plan = assembly_plan
        self.dict_of_parts_in_temp_mod_position = {}
        self.dict_of_parts_in_thermocycler = {}
        self.sbol_output = []
    
        metadata = {
        'protocolName': 'Automated Golden Gate from SBOL',
        'author': 'Gonzalo Vidal <gsvidal@uc.cl>',
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
        restriction_enzyme = tem_mod_block['A1']
        t4_dna_ligase = tem_mod_block['A2'] 
        t4_dna_ligase_buffer = tem_mod_block['A3'] 
        dd_h2o = tem_mod_block['A4']

        dict_of_parts_in_temp_mod_position = {}
        temp_wells_counter = 4

        assemblies = []
        assemblies_compoent_set = set()
        for composite in self.assembly_plan.composites:
            volume_parts = len(composite.features) * self.volume_part
            volume_dd_h2o = self.volume_total_reaction - (volume_reagents + volume_parts)
            if volume_dd_h2o < 1 and volume_dd_h2o!=0 :
                raise ValueError('The volume of dd_h2o is not enough to perform the experiment')
            composite_parts = []
            for part_extract_sc in composite.features:
                #get parts
                part = find_top_level(part_extract_sc.instance_of)
                assemblies_compoent_set.add(part)
                #get part's ubication
                part_ubication = dict_of_parts_in_temp_mod_position[part]
                #append parts_in_bb and acceptor_backbone
                composite_parts.append(part_ubication)
            assemblies.append(composite_parts)

        if len(assemblies_compoent_set) > 20:
            raise ValueError('Number of parts in the assembly plan is greater than 20. This protocol only supports assemblies with up to 20 parts')
        for part_component in assemblies_compoent_set:
            dict_of_parts_in_temp_mod_position[part_component] = tem_mod_block[temp_wells[temp_wells_counter]]
            temp_wells_counter += 1

        #Setup
        #Set the temperature of the temperature module and the thermocycler to 4°C
        tem_mod.set_temperature(4)
        thermocycler_mod.open_lid()
        thermocycler_mod.set_block_temperature(4)
        #Commands for the mastermix
        starting_well = self.thermocycler_starting_well #starting from 0 thermocycler module
        ending_well = starting_well + len(assemblies)*self.replicates 
        wells = thermo_wells[starting_well:ending_well] #wells = ['D6', 'D7']
        #can be done with multichannel pipette
        for well in wells:
            liquid_transfer(pipette, volume_dd_h2o, dd_h2o, thermocycler_mod_plate[well], self.aspiration_rate, self.dispense_rate)
            liquid_transfer(pipette, volume_t4_dna_ligase_buffer, t4_dna_ligase_buffer, thermocycler_mod_plate[well], self.aspiration_rate, self.dispense_rate, mix_before=volume_t4_dna_ligase_buffer)
            liquid_transfer(pipette, volume_restriction_enzyme, restriction_enzyme, thermocycler_mod_plate[well], self.aspiration_rate, self.dispense_rate, mix_before=volume_restriction_enzyme)
        #for well in wells:
        i = self.thermocycler_starting_well
        for composite in self.assembly_plan.composites:
            for r in range(replicates):
                #create assembled_dna Implementation that points to the composite
                assembled_dna = sbol3.Implementation(f'assembled_dna_{r}', composite, description=f'Thermocycler well {thermo_wells[i]}')
                self.sbol_output.append(assembled_dna)
                #create virtual plate
                for part in composite:
                    composite_ubication_in_thermocyler = thermocycler_mod_plate[thermo_wells[i]]
                    liquid_transfer(pipette, volume_part, part, composite_ubication_in_thermocyler, self.aspiration_rate, self.dispense_rate, mix_before=volume_restriction_enzyme)
                    i+=1
        
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
        
class Domestication(DNA_assembly):
    '''
    Creates a protocol for automated domestication, assembly of parts into universal acceptor backbone.

    '''
    def __init__(self, parts:Union[List,Dict], acceptor_backbone:Union[str, sbol3.Component],
        *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.parts = parts
        self.acceptor_backbone = acceptor_backbone
        self.dict_of_parts_in_temp_mod_position = {}
        self.dict_of_parts_in_thermocycler = {}
        self.sbol_output = []

        if len(parts) > 19:
            raise ValueError(f'This protocol only supports assemblies with up to 20 parts. Number of parts in the protocol is {len(parts)}')
        
        metadata = {
        'protocolName': 'Automated Odd Level Loop Assembly',
        'author': 'Gonzalo Vidal <gsvidal@uc.cl>',
        'description': 'Protocol to perform Odd level Loop assembly',
        'apiLevel': '2.13'}

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
        volume_dd_h2o = self.volume_total_reaction - (volume_reagents + self.volume_part*2)
        #Load the reagents
        restriction_enzyme = tem_mod_block['A1']
        t4_dna_ligase = tem_mod_block['A2'] 
        t4_dna_ligase_buffer = tem_mod_block['A3'] 
        dd_h2o = tem_mod_block['A4']
        backbone = tem_mod_block['A5']
        temp_wells_counter = 5
        #Setup
        #Set the temperature of the temperature module and the thermocycler to 4°C
        tem_mod.set_temperature(4)
        thermocycler_mod.open_lid()
        thermocycler_mod.set_block_temperature(4)
        #Commands for the mastermix
        ending_well = self.thermocycler_starting_well + len(self.parts)*self.replicates 
        wells = thermo_wells[self.thermocycler_starting_well:ending_well] #wells = ['D6', 'D7']
        #can be done with multichannel pipette
        for well in wells:
            liquid_transfer(pipette, volume_dd_h2o, dd_h2o, thermocycler_mod_plate[well], self.aspiration_rate, self.dispense_rate)
            liquid_transfer(pipette, self.volume_t4_dna_ligase_buffer, t4_dna_ligase_buffer, thermocycler_mod_plate[well], self.aspiration_rate, self.dispense_rate, mix_before=self.volume_t4_dna_ligase_buffer)
            liquid_transfer(pipette, self.volume_t4_dna_ligase, t4_dna_ligase, thermocycler_mod_plate[well], self.aspiration_rate, self.dispense_rate, mix_before=self.volume_t4_dna_ligase)
            liquid_transfer(pipette, self.volume_restriction_enzyme, restriction_enzyme, thermocycler_mod_plate[well], self.aspiration_rate, self.dispense_rate, mix_before=self.volume_restriction_enzyme)
            liquid_transfer(pipette, self.volume_part, backbone, thermocycler_mod_plate[well], self.aspiration_rate, self.dispense_rate, mix_before=self.volume_part)
        #for well in wells:
        i = self.thermocycler_starting_well
        #TODO map parts to wells
        for part in self.parts:
            if type(part) == str:
                    part_name=part
            elif type(part) == sbol3.Component:
                part_name=part.name     
            else: raise ValueError(f'Part {part} is not a string or an sbol3.Component')  
            self.dict_of_parts_in_temp_mod_position[part_name] = temp_wells[temp_wells_counter]
            for r in range(self.replicates):
                #Add sbol implementation
                if type(part) == sbol3.Component: 
                    #create assembled_dna Implementation that points to the part
                    assembled_dna = sbol3.Implementation(f'assembled_dna_{part_name}_{r}', part, description=f'Thermocycler well {thermo_wells[i]}')
                    self.sbol_output.append(assembled_dna)
                part_ubication_in_thermocyler = thermocycler_mod_plate[thermo_wells[i]]
                self.dict_of_parts_in_thermocycler[part_name] = thermo_wells[i]
                liquid_transfer(pipette, self.volume_part, tem_mod_block[self.dict_of_parts_in_temp_mod_position[part_name]], part_ubication_in_thermocyler, self.aspiration_rate, self.dispense_rate, mix_before=self.volume_restriction_enzyme)
                self.dict_of_parts_in_temp_mod_position[part_name] = temp_wells[i]
                i+=1
            temp_wells_counter += 1
        
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

class Loop_assembly(DNA_assembly):
    '''
    Creates a protocol for the automated Odd and/or Even level Loop assembly.

    '''
    def __init__(self, assemblies:List[Dict],
        *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.assemblies = assemblies
        self.dict_of_parts_in_temp_mod_position = {}
        self.dict_of_parts_in_thermocycler = {}
        self.assembly_plan = None
        self.sbol_output = []
        self.pattern_odd = 'Odd*'
        self.pattern_even = 'Even*'
        self.parts_set = set()
        self.has_odd = False
        self.has_even = False
        self.odd_combinations = []
        self.even_combinations = []
            
        # add parts to a set
        for assembly in self.assemblies:
            list_of_list_of_parts_per_role = []
            if fnmatch(assembly['receiver'], self.pattern_odd):
                self.has_odd = True
                for role in assembly:
                    parts = assembly[role]
                    if type(parts) is str:
                        parts_per_role = [parts]
                    elif type(parts) is list:
                        for part in parts:
                            self.parts_set.add(part)
                    list_of_list_of_parts_per_role.append(parts_per_role)
                list_of_combinations_per_assembly = list(product(*list_of_list_of_parts_per_role))
                for combination in list_of_combinations_per_assembly:
                    self.odd_combinations.append(combination)
            if fnmatch(assembly['receiver'], self.pattern_even):
                self.has_even = True   
                for role in assembly:
                    parts = assembly[role]
                    if type(parts) is str:
                        parts_per_role = [parts]
                    elif type(parts) is list:
                        for part in parts:
                            self.parts_set.add(part)
                    list_of_list_of_parts_per_role.append(parts_per_role)
                list_of_combinations_per_assembly = list(product(*list_of_list_of_parts_per_role))
                for combination in list_of_combinations_per_assembly:
                    self.even_combinations.append(combination)

        if self.has_odd and self.has_even:
            max_parts = 18
        elif self.has_odd or self.has_even:
            max_parts = 19
        else:
            raise ValueError('Assembly does not have any Even or Odd receiver')
        if len(self.parts_set) > max_parts:
            raise ValueError(f'This protocol only supports assemblies with up to {max_parts} parts. Number of parts in the protocol is {len(self.parts_set)}')
                        

        for assembly in self.assemblies:
            list_of_list_of_parts_per_role = []
            for role in assembly:
                parts = assembly[role]
                if type(parts) is str:
                    parts_per_role = [parts]
                elif type(parts) is list:
                    parts_per_role = parts
                list_of_list_of_parts_per_role.append(parts_per_role)
            list_of_combinations = list(product(*list_of_list_of_parts_per_role))
    
        metadata = {
        'protocolName': 'Automated Loop assembly',
        'author': 'Gonzalo Vidal <gsvidal@uc.cl>',
        'description': 'Protocol to perform Loop assembly',
        'apiLevel': '2.13'}

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
        t4_dna_ligase = tem_mod_block['A2'] 
        t4_dna_ligase_buffer = tem_mod_block['A3'] 
        temp_wells_counter = 3 
        if self.has_odd:
            restriction_enzyme_bsai = tem_mod_block[temp_wells[temp_wells_counter]]
            temp_wells_counter += 1
        if self.has_even:
            restriction_enzyme_even = tem_mod_block[temp_wells[temp_wells_counter]]
            temp_wells_counter += 1 
        #Setup
        #Set the temperature of the temperature module and the thermocycler to 4°C
        tem_mod.set_temperature(4)
        thermocycler_mod.open_lid()
        thermocycler_mod.set_block_temperature(4)
        #Commands for the mastermix
        ending_well = self.thermocycler_starting_well + len(self.assemblies)*self.replicates 
        wells = thermo_wells[self.thermocycler_starting_well:ending_well] #wells = ['D6', 'D7']
        #can be done with multichannel pipette?
        for assembly in self.assemblies:
            list_of_list_of_parts_per_role = []
            for role in assembly:
                parts = assembly[role]
                if type(parts) is str:
                    parts_per_role = [parts]
                elif type(parts) is list:
                    parts_per_role = parts
                list_of_list_of_parts_per_role.append(parts_per_role)
            list_of_combinations = list(product(*list_of_list_of_parts_per_role))

                    for part in parts:
                        self.parts_set.add(part)
        # calculate the volume of water needed
        volume_dd_h2o = self.volume_total_reaction - (volume_reagents + self.volume_part*2)
        for well in wells:
            liquid_transfer(pipette, volume_dd_h2o, dd_h2o, thermocycler_mod_plate[well], self.aspiration_rate, self.dispense_rate)
            liquid_transfer(pipette, self.volume_t4_dna_ligase_buffer, t4_dna_ligase_buffer, thermocycler_mod_plate[well], self.aspiration_rate, self.dispense_rate, mix_before=self.volume_t4_dna_ligase_buffer)
            liquid_transfer(pipette, self.volume_t4_dna_ligase, t4_dna_ligase, thermocycler_mod_plate[well], self.aspiration_rate, self.dispense_rate, mix_before=self.volume_t4_dna_ligase)
            
            liquid_transfer(pipette, self.volume_restriction_enzyme, restriction_enzyme, thermocycler_mod_plate[well], self.aspiration_rate, self.dispense_rate, mix_before=self.volume_restriction_enzyme)
            liquid_transfer(pipette, self.volume_part, backbone, thermocycler_mod_plate[well], self.aspiration_rate, self.dispense_rate, mix_before=self.volume_part)
        #for well in wells:
        i = self.thermocycler_starting_well
        #TODO map parts to wells
        for part in self.parts:
            if type(part) == str:
                    part_name=part
            elif type(part) == sbol3.Component:
                part_name=part.name     
            else: raise ValueError(f'Part {part} is not a string or an sbol3.Component')  
            self.dict_of_parts_in_temp_mod_position[part_name] = temp_wells[temp_wells_counter]
            for r in range(self.replicates):
                #Add sbol implementation
                if type(part) == sbol3.Component: 
                    #create assembled_dna Implementation that points to the part
                    assembled_dna = sbol3.Implementation(f'assembled_dna_{part_name}_{r}', part, description=f'Thermocycler well {thermo_wells[i]}')
                    self.sbol_output.append(assembled_dna)
                part_ubication_in_thermocyler = thermocycler_mod_plate[thermo_wells[i]]
                self.dict_of_parts_in_thermocycler[part_name] = thermo_wells[i]
                liquid_transfer(pipette, self.volume_part, tem_mod_block[self.dict_of_parts_in_temp_mod_position[part_name]], part_ubication_in_thermocyler, self.aspiration_rate, self.dispense_rate, mix_before=self.volume_restriction_enzyme)
                self.dict_of_parts_in_temp_mod_position[part_name] = temp_wells[i]
                i+=1
            temp_wells_counter += 1
        
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



assembly_Odd_1 = {"promoter":["j23101", "j23100"], "rbs":"B0034", "cds":"GFP", "terminator":"B0015", "receiver":"Odd_1"}
assembly_Even_2 = {"promoter":["j23101", "j23100"], "rbs":"B0034", "cds":"GFP", "terminator":"B0015", "receiver":"Even_2"}
assemblies = [assembly_Odd_1, assembly_Even_2]