#We import the protocols API from Opentrons
from opentrons import protocol_api

#The metadata should be included in this part
metadata = {
    'protocolName': 'Automated Golden Gate',
    'author': 'Gonzalo Vidal <gsvidal@uc.cl>, Carlos Vidal-Céspedes <carlos.vidal.c@ug.uchile.cl>',
    'description': 'Protocol to perform a Golden Gate experiment',
    'apiLevel': '2.10'
}

def run(protocol: protocol_api.ProtocolContext):

    #Labware
    #Load the magnetic module
    
    ### mag_mod = protocol.load_module('magnetic module', '1') #Not used in this protocol
    ### mag_mod_plate = mag_mod.load_labware('nest_96_wellplate_100ul_pcr_full_skirt')

    #Load the temperature module
    #Temperature module blocks available in the lab:
    #   'opentrons_24_aluminumblock_nest_1.5ml_snapcap'
    #   'opentrons_96_aluminumblock_generic_pcr_strip_200ul'
    tem_mod = protocol.load_module('temperature module', '1') #CV: Previously was '3', but the cord was not long enough
    tem_mod_block = tem_mod.load_labware('opentrons_24_aluminumblock_nest_1.5ml_snapcap')

    #Load the thermocycler module, its default location is on slots 7, 8, 10 and 11
    #Thermocycler module plates available in the lab:
    #   'nest_96_wellplate_100ul_pcr_full_skirt'
    thermocycler_mod = protocol.load_module('thermocycler module')
    thermocycler_mod_plate = thermocycler_mod.load_labware('nest_96_wellplate_100ul_pcr_full_skirt')

    #Load the tiprack
    #Tipracks available in the lab:
    #   'opentrons_96_tiprack_20ul'
    #   'opentrons_96_tiprack_300ul'
    tiprack = protocol.load_labware('opentrons_96_tiprack_20ul', '9')

    #Load the pipette
    #Pipettes available in the lab:
    #   'p20_single_gen2', 'left'
    #   'p300_multi_gen2', 'right'
    left_pipette = protocol.load_instrument('p20_single_gen2', 'left', tip_racks=[tiprack])

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

    #Load the reagents
    bsai = tem_mod_block['A1'] #Blue
    t4_dna_ligase = tem_mod_block['A2'] #Yellow
    t4_dna_ligase_buffer = tem_mod_block['A3'] #Red
    dd_h2o = tem_mod_block['A4'] #Blue

    #Load the parts
    prom = tem_mod_block['B1'] #Yellow
    rbs = tem_mod_block['B2'] #Red
    cds = tem_mod_block['B3'] #Blue
    term = tem_mod_block['B4'] #Yellow
    acc_vector = tem_mod_block['B5'] #Red
    prom2 = tem_mod_block['B6']
    rbs2 = tem_mod_block['C1']
    cds2 = tem_mod_block['C2']
    term2 = tem_mod_block['C3']

    #State volumes. They can be a function of [DNA], the minimun value is 1 uL
    volume_total = 20

    #Parts should be diluted to the necessary concentration to aspirate 1 uL
    volume_part = 2
    number_parts = 5
    #volume_acc_vector = 0.50
    #volume_prom = 0.50
    #volume_rbs = 0.50
    #volume_cds = 0.50
    #volume_term = 0.50
    volume_parts = volume_part * number_parts

    volume_bsai = 2
    volume_t4_dna_ligase = 5
    volume_t4_dna_ligase_buffer = 2
    volume_reagents = volume_bsai + volume_t4_dna_ligase + volume_t4_dna_ligase_buffer
    volume_dd_h2o = volume_total - (volume_reagents + volume_parts)
    if volume_dd_h2o < 1 and volume_dd_h2o!=0 :
        protocol.comment('The volume of dd_h2o is not enough to perform the experiment')
        return
    
    #Assembling the parts
    assemblies = []
    replicates = 2
    tu1 = [prom, rbs, cds, term, acc_vector]
    tu2 = [prom2, rbs2, cds2, term2, acc_vector]
    tu3 = [prom, rbs, cds2, term, acc_vector]
    tu4 = [prom2, rbs2, cds, term2, acc_vector]

    tus = [tu1, tu2, tu3, tu4]
    for t in tus:
        assemblies.append(t)

    #Setup
    #Set the temperature of the temperature module and the thermocycler to 4°C
    tem_mod.set_temperature(4)
    thermocycler_mod.open_lid()
    thermocycler_mod.set_block_temperature(4)

    #set the aspirattion rate
    asp_rate = 0.5
    #By default, the OT-2 will aspirate and dispense 1 mm above the bottom of the well.
    #diminish aspiration rate
    #Commands for the mastermix
    starting_well = 10 #starting from 0 thermocycler module
    ending_well = starting_well + len(assemblies)
    wells = thermo_wells[starting_well:ending_well] #wells = ['D6', 'D7']
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
                left_pipette.pick_up_tip()
                left_pipette.aspirate(volume_part, part, rate=asp_rate)
                left_pipette.dispense(volume_part, thermocycler_mod_plate[thermo_wells[i]]) #Define place in the thermocycler
                left_pipette.blow_out()
                left_pipette.drop_tip()
                i+=1
    ###        left_pipette.drop_tip()
    
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

    '''
    left_pipette.distribute(
        2,
        [tem_mod_block.wells_by_name()[well_name] for well_name in ['A1', 'A2']],
        thermocycler_mod_plate['A'])

    temp_wells = [
        'A1','A2','A3','A4','A5','A6',
        'B1','B2','B3','B4','B5','B6',
        'C1',
        #'C2','C3','C4','C5',
        'C6',
        'D1','D2','D3','D4','D5','D6'
        ]

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
    '''