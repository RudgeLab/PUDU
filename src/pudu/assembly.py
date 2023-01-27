from opentrons import protocol_api

class Protocol_from_sbol():
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
    volume_bsai : float
        The volume of BsaI in microliters. By default, 2 microliters.
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
                 volume_total_reaction:float = 20,
                 volume_part:float = 2,
                 volume_bsai:float = 2,
                 volume_t4_dna_ligase:float = 4,
                 volume_t4_dna_ligase_buffer:float = 2,
                 replicates:int=2,
                 aspiration_rate:float=0.5,
                 thermocycler_starting_well:int = 0,
                 thermocycler_labware:str = 'nest_96_wellplate_100ul_pcr_full_skirt',
                 temperature_module_labware:str = 'opentrons_24_aluminumblock_nest_1.5ml_snapcap',
                 temperature_module_position:int = 1,
                 tiprack_labware:str = 'opentrons_96_tiprack_20ul',
                 tiprack_position:int = 9,
                 pipette:str = 'p20_single_gen2',
                 pipette_position:str = 'left',
                 
                     ):
        self.assembly_plan = assembly_plan
        self.volume_total_reaction = volume_total_reaction
        self.volume_part = volume_part
        self.volume_bsai = volume_bsai
        self.volume_t4_dna_ligase = volume_t4_dna_ligase
        self.volume_t4_dna_ligase_buffer = volume_t4_dna_ligase_buffer
        self.replicates = replicates
        self.aspiration_rate = aspiration_rate
        self.thermocycler_starting_well = thermocycler_starting_well
        self.thermocycler_labware = thermocycler_labware
        self.temperature_module_labware = temperature_module_labware
        self.temperature_module_position = temperature_module_position
        self.tiprack_labware = tiprack_labware
        self.tiprack_position = tiprack_position
        self.pipette = pipette
        self.pipette_position = pipette_position
    
        metadata = {
        'protocolName': 'Automated Golden Gate from SBOL',
        'author': 'Gonzalo Vidal <gsvidal@uc.cl>, Carlos Vidal-Céspedes <carlos.vidal.c@ug.uchile.cl>',
        'description': 'Protocol to perform a Golden Gate assembly from SBOL',
        'apiLevel': '2.13'}

    def run(self, protocol: protocol_api.ProtocolContext): #test if self can be an argument

        #Labware
        #Load the magnetic module
        
        ### mag_mod = protocol.load_module('magnetic module', '1') #Not used in this protocol
        ### mag_mod_plate = mag_mod.load_labware('nest_96_wellplate_100ul_pcr_full_skirt')

        #Load the temperature module
        #Temperature module blocks available in the lab:
        #   'opentrons_24_aluminumblock_nest_1.5ml_snapcap'
        #   'opentrons_96_aluminumblock_generic_pcr_strip_200ul'
        tem_mod = protocol.load_module('temperature module', f'{self.temperature_module_position}') #CV: Previously was '3', but the cord was not long enough
        tem_mod_block = tem_mod.load_labware(self.temperature_module_labware)

        #Load the thermocycler module, its default location is on slots 7, 8, 10 and 11
        #Thermocycler module plates available in the lab:
        #   'nest_96_wellplate_100ul_pcr_full_skirt'
        thermocycler_mod = protocol.load_module('thermocycler module')
        thermocycler_mod_plate = thermocycler_mod.load_labware(self.thermocycler_labware)

        #Load the tiprack
        #Tipracks available in the lab:
        #   'opentrons_96_tiprack_20ul'
        #   'opentrons_96_tiprack_300ul'
        tiprack = protocol.load_labware(self.tiprack_labware, f'{self.tiprack_position}')

        #Load the pipette
        #Pipettes available in the lab:
        #   'p20_single_gen2', 'left'
        #   'p300_multi_gen2', 'right'
        left_pipette = protocol.load_instrument(self.pipette, self.pipette_position, tip_racks=[tiprack])

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
        
        #Fixed volumes
        #State volumes. They can be a function of [DNA], the minimun value is 1 uL
        volume_total = self.volume_total_reaction

        #Parts should be diluted to the necessary concentration to aspirate 1 or 2 uL 
        volume_part = self.volume_part
        volume_bsai = self.volume_bsai
        volume_t4_dna_ligase = self.volume_t4_dna_ligase
        volume_t4_dna_ligase_buffer = self.volume_t4_dna_ligase_buffer
        volume_reagents = volume_bsai + volume_t4_dna_ligase + volume_t4_dna_ligase_buffer
        
        #Load the reagents
        bsai = tem_mod_block['A1']
        t4_dna_ligase = tem_mod_block['A2'] 
        t4_dna_ligase_buffer = tem_mod_block['A3'] 
        dd_h2o = tem_mod_block['A4']

        dict_of_parts_in_temp_mod_position = {}
        temp_wells_counter = 4

        assemblies = []
        assemblies_compoent_set = set()
        for composite in self.assembly_plan.composites:
            volume_parts = len(composite.features) * volume_part
            volume_dd_h2o = volume_total - (volume_reagents + volume_parts)
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

        '''
        previous version
        #lists of ubications
        tu1 = [prom, rbs, cds, term, acc_vector]
        tu2 = [prom2, rbs2, cds2, term2, acc_vector]
        tu3 = [prom, rbs, cds2, term, acc_vector]
        tu4 = [prom2, rbs2, cds, term2, acc_vector]

        assemblies = [tu1, tu2, tu3, tu4]
        '''

        #Setup
        #Set the temperature of the temperature module and the thermocycler to 4°C
        tem_mod.set_temperature(4)
        thermocycler_mod.open_lid()
        thermocycler_mod.set_block_temperature(4)

        #set the aspirattion rate, by default, the OT-2 will aspirate and dispense 1 mm above the bottom of the well.
        asp_rate = self.aspiration_rate
        #Commands for the mastermix
        replicates = self.replicates
        starting_well = self.thermocycler_starting_well #starting from 0 thermocycler module
        ending_well = starting_well + len(assemblies)*replicates 
        wells = thermo_wells[starting_well:ending_well] #wells = ['D6', 'D7']
        #can be done with multichannel pipette
        for well in wells:
            left_pipette.pick_up_tip()
            left_pipette.aspirate(volume_dd_h2o, dd_h2o, rate=asp_rate)
            left_pipette.dispense(volume_dd_h2o, thermocycler_mod_plate[well]) #Define place in the thermocycler
            left_pipette.blow_out()
            left_pipette.drop_tip()

            left_pipette.pick_up_tip()
            left_pipette.aspirate(volume_t4_dna_ligase_buffer, t4_dna_ligase_buffer, rate=asp_rate)
            left_pipette.dispense(volume_t4_dna_ligase_buffer, thermocycler_mod_plate[well]) #Define place in the thermocycler
            left_pipette.blow_out()
            left_pipette.drop_tip()

            left_pipette.pick_up_tip()
            left_pipette.aspirate(volume_t4_dna_ligase, t4_dna_ligase, rate=asp_rate)
            left_pipette.dispense(volume_t4_dna_ligase, thermocycler_mod_plate[well]) #Define place in the thermocycler
            left_pipette.blow_out()
            left_pipette.drop_tip()

            left_pipette.pick_up_tip()
            left_pipette.aspirate(volume_bsai, bsai, rate=asp_rate)
            left_pipette.dispense(volume_bsai, thermocycler_mod_plate[well]) #Define place in the thermocycler
            left_pipette.blow_out()
            left_pipette.drop_tip()

        #for well in wells:
        i = starting_well
        for _ in range(replicates):
            for tu in assemblies:
                for part in tu:
                    composite_ubication_in_thermocyler = thermocycler_mod_plate[thermo_wells[i]]
                    left_pipette.pick_up_tip()
                    left_pipette.aspirate(volume_part, part, rate=asp_rate)
                    left_pipette.dispense(volume_part, composite_ubication_in_thermocyler) #Define place in the thermocycler
                    left_pipette.blow_out()
                    left_pipette.drop_tip()
                    i+=1

        for composite in self.assembly_plan.composites:
            for _ in range(replicates):
                #create assembled_dna Implementation that points to the composite
                #create dictionary of implementations in thermocycler position
                for part in composite:
                    composite_ubication_in_thermocyler = thermocycler_mod_plate[thermo_wells[i]]
                    left_pipette.pick_up_tip()
                    left_pipette.aspirate(volume_part, part, rate=asp_rate)
                    left_pipette.dispense(volume_part, composite_ubication_in_thermocyler) #Define place in the thermocycler
                    left_pipette.blow_out()
                    left_pipette.drop_tip()
                    i+=1
        
        #The thermocycler's status can be checked with the following command
        #thermocycler_mod.lid_temperature_status()
        #thermocycler_mod.block_temperature_status()
        
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

        #The thermocycler's lid is opened and the block temperature is set to 4°C
        #thermocycler_mod.open_lid() #The operator can open the lid manually when the experiment is finished
        thermocycler_mod.set_block_temperature(4)
