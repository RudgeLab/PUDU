from opentrons import protocol_api
from typing import List, Dict
from pudu.utils import colors


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
    temperature_module_position : int
        The deck position of the temperature module. By default, 1.
    tiprack_labware : str
        The labware type of the tiprack. By default, 'opentrons_96_tiprack_20ul'.
    tiprack_position : int
        The deck position of the tiprack. By default, 9.
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
                 list_of_dna:List = None,
                 volume_dna:float = 20,
                 competent_cells:str = None,
                 replicates:int=2,
                 thermocycler_starting_well:int = 0,
                 thermocycler_labware:str = "nest_96_wellplate_100ul_pcr_full_skirt",
                 temperature_module_labware:str = "opentrons_24_aluminumblock_nest_1.5ml_snapcap",
                 temperature_module_position:str = '1',
                 dna_plate:str = "nest_96_wellplate_100ul_pcr_full_skirt",
                 dna_plate_position:str = '2',
                 use_dna_96plate:bool = False,
                 tiprack_p20_labware:str = "opentrons_96_tiprack_20ul",
                 tiprack_p20_position:str = "9",
                 tiprack_p200_labware:str = "opentrons_96_filtertiprack_200ul",
                 tiprack_p200_position:str = "6",
                 pipette_p20:str = "p20_single_gen2",
                 pipette_p20_position:str = "left",
                 pipette_p300:str = "p300_single_gen2",
                 pipette_p300_position:str = "right",
                 aspiration_rate:float = 0.5,
                 dispense_rate:float = 1,
                 initial_dna_well:int = 0,
                 water_testing:bool = False
                 ):

        if list_of_dna is None:
            raise ValueError ("Must input a list of DNA strings")
        else:
            self.list_of_dna = list_of_dna
        self.volume_dna = volume_dna
        if competent_cells is None:
            raise ValueError ("Must input a competent cell strings")
        else:
            self.competent_cells = competent_cells
        self.replicates = replicates
        self.thermocycler_starting_well = thermocycler_starting_well
        self.thermocycler_labware = thermocycler_labware
        self.temperature_module_labware = temperature_module_labware
        self.temperature_module_position = temperature_module_position
        self.dna_plate = dna_plate
        self.dna_plate_position = dna_plate_position
        self.use_dna_96plate = use_dna_96plate
        self.tiprack_p20_labware = tiprack_p20_labware
        self.tiprack_p20_position = tiprack_p20_position
        self.tiprack_p200_labware = tiprack_p200_labware
        self.tiprack_p200_position = tiprack_p200_position
        self.pipette_p20 = pipette_p20
        self.pipette_p20_position = pipette_p20_position
        self.pipette_p300 = pipette_p300
        self.pipette_p300_position = pipette_p300_position
        self.aspiration_rate = aspiration_rate
        self.dispense_rate = dispense_rate
        self.initial_dna_well = initial_dna_well
        self.water_testing = water_testing

class HeatShockTransformation(Transformation):
    '''
       Creates a protocol for automated transformation.
    '''
    def __init__(self,
                transfer_volume_dna:float = 2,
                transfer_volume_competent_cell:float = 20,
                tube_volume_competent_cell:float =100,
                transfer_volume_recovery_media:float = 60,
                tube_volume_recovery_media:float = 1200, #add a bit more to pick it properly
                cold_incubation1:Dict = None,
                heat_shock:Dict = None,
                cold_incubation2:Dict = None,
                recovery_incubation:Dict = None,
                *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.transfer_volume_dna = transfer_volume_dna
        self.transfer_volume_competent_cell = transfer_volume_competent_cell
        self.tube_volume_competent_cell = tube_volume_competent_cell
        self.transfer_volume_recovery_media = transfer_volume_recovery_media
        self.tube_volume_recovery_media = tube_volume_recovery_media
        if cold_incubation1 is None:
            self.cold_incubation1 = {'temperature': 4, 'hold_time_minutes': 30}
        else:
            self.cold_incubation1 = cold_incubation1
        if heat_shock is None:
            self.heat_shock = {'temperature': 42, 'hold_time_minutes': 1}
        else:
            self.heat_shock = heat_shock
        if cold_incubation2 is None:
            self.cold_incubation2 = {'temperature': 4, 'hold_time_minutes': 2}
        else:
            self.cold_incubation2 = cold_incubation2
        if recovery_incubation is None:
            self.recovery_incubation = {'temperature': 37, 'hold_time_minutes': 60}
        else:
            self.recovery_incubation = recovery_incubation
        self.dict_of_parts_in_temp_mod_position = {}
        self.dict_of_parts_in_thermocycler = {}

    def liquid_transfer(self, protocol, pipette, volume, source, dest,
                        asp_rate: float = 0.5, disp_rate: float = 1.0,
                        blow_out: bool = True, touch_tip: bool = False,
                        mix_before: float = 0.0, mix_after: float = 0.0,
                        mix_reps: int = 3, new_tip: bool = True,
                        remove_air:bool = True, drop_tip: bool = True):
        if new_tip:
            pipette.pick_up_tip()

        if mix_before > 0:
            pipette.mix(mix_reps, mix_before, source)

        pipette.aspirate(volume, source, rate=asp_rate)
        pipette.dispense(volume, dest, rate=disp_rate)

        if mix_after > 0:
            pipette.mix(mix_reps, mix_after, dest)

        if blow_out:
            pipette.blow_out()

        if remove_air:
            for _ in range(2):
                pipette.aspirate(20, dest.bottom(), rate=disp_rate)
                pipette.dispense(20, dest.bottom(8), rate=disp_rate)

        if touch_tip:
            pipette.touch_tip(radius=0.5, v_offset=-14, speed=20)

        if drop_tip:
            pipette.drop_tip()

    def run(self, protocol: protocol_api.ProtocolContext):
        # Force water testing mode during simulation
        if protocol.is_simulating():
            self.water_testing = True
            protocol.comment("Simulation detected - enabling water testing mode")
        # Labware
        # Load the temperature module
        temperature_module = protocol.load_module('temperature module', self.temperature_module_position)
        alumblock = temperature_module.load_labware(self.temperature_module_labware)
        # Load the thermocycler module, its default location is on slots 7, 8, 10 and 11
        thermocycler_module = protocol.load_module('thermocycler module')
        pcr_plate = thermocycler_module.load_labware(self.thermocycler_labware)
        #If using the 96-well pcr plate as a dna construct source
        if self.use_dna_96plate:
            dna_plate = protocol.load_labware(self.dna_plate, self.dna_plate_position)
        # Load the tiprack
        tiprack_p20 = protocol.load_labware(self.tiprack_p20_labware, self.tiprack_p20_position)
        tiprack_p200 = protocol.load_labware(self.tiprack_p200_labware, self.tiprack_p200_position)
        # Load the pipette
        pipette_p20 = protocol.load_instrument(self.pipette_p20, self.pipette_p20_position, tip_racks=[tiprack_p20])
        pipette_p300 = protocol.load_instrument(self.pipette_p300, self.pipette_p300_position,
                                                tip_racks=[tiprack_p200])
        #Validate protocol
        self._validate_protocol(protocol, alumblock)

        #Load Reagents
        if self.use_dna_96plate:
            DNA_wells = self._load_dna_list(protocol, dna_plate, self.volume_dna, self.list_of_dna, initial_well=self.initial_dna_well)
            competent_cell_wells = self._load_reagents(protocol, alumblock, self.tube_volume_competent_cell, f"Competent Cell {self.competent_cells}", self.competent_cell_tubes_needed)
            media_wells = self._load_reagents(protocol, alumblock, self.tube_volume_recovery_media, "Media", self.media_tubes_needed, initial_well=len(competent_cell_wells))

        else:
            DNA_wells = self._load_dna_list(protocol, alumblock, self.volume_dna, self.list_of_dna)
            competent_cell_wells = self._load_reagents(protocol, alumblock, self.tube_volume_competent_cell, f"Competent Cell {self.competent_cells}", self.competent_cell_tubes_needed, initial_well=len(DNA_wells))
            media_wells = self._load_reagents(protocol, alumblock, self.tube_volume_recovery_media, "Media", self.media_tubes_needed, initial_well=len(DNA_wells)+len(competent_cell_wells))

        #Set Temperature module and Thermocycler module to 4
        thermocycler_module.open_lid()
        if not self.water_testing:
            temperature_module.set_temperature(4)
            thermocycler_module.set_block_temperature(4)

        #Load competent cells into the thermocycler
        pipette = pipette_p300
        self._transfer_competent_cells(protocol, pipette, pcr_plate, competent_cell_wells, self.transfer_volume_competent_cell, self.thermocycler_starting_well)

        #Load DNA into the thermocycler
        if self.transfer_volume_dna > 20:
            pipette = pipette_p300
        else:
            pipette = pipette_p20
        self._transfer_DNA(protocol, pipette, pcr_plate, DNA_wells, self.transfer_volume_dna, self.thermocycler_starting_well)

        # Cold Incubation
        thermocycler_module.close_lid()
        profile = [
            self.cold_incubation1,  # 1st cold incubation (long)
            self.heat_shock,  # Heat shock
            self.cold_incubation2  # 2nd cold incubation (short)
        ]
        if not self.water_testing:
            thermocycler_module.execute_profile(steps=profile, repetitions=1, block_max_volume=30)
        thermocycler_module.open_lid()

        #Load liquid broth
        pipette = pipette_p300
        self._transfer_liquid_broth(protocol, pipette, pcr_plate, media_wells, self.transfer_volume_recovery_media, self.thermocycler_starting_well)

        # Recovery Incubation
        thermocycler_module.close_lid()
        recovery = [
            self.recovery_incubation
        ]
        if not self.water_testing:
            thermocycler_module.execute_profile(steps=recovery, repetitions=1, block_max_volume=30)

        # output
        print('Strain and media tube in temp_mod')
        print(self.dict_of_parts_in_temp_mod_position)
        print('Genetically modified organisms in thermocycler')
        print(self.dict_of_parts_in_thermocycler)

    def _validate_protocol(self, protocol, labware):
        #Number of available wells to load into
        module_wells = len(labware.wells())
        #Number of dna constructs to be used
        total_constructs = len(self.list_of_dna)
        #Number of tubes with competent cells to be used
        self.total_transformations = total_constructs*self.replicates
        self.transformations_per_cell_tube = self.tube_volume_competent_cell//self.transfer_volume_competent_cell
        self.competent_cell_tubes_needed = (self.total_transformations + self.transformations_per_cell_tube - 1) // self.transformations_per_cell_tube
        #Number of tubes with media to be used
        self.transformations_per_media_tube = self.tube_volume_recovery_media//self.transfer_volume_recovery_media
        self.media_tubes_needed = (self.total_transformations + self.transformations_per_media_tube - 1) // self.transformations_per_media_tube
        if self.use_dna_96plate:
            if self.competent_cell_tubes_needed + self.media_tubes_needed > module_wells:
                raise ValueError(f'The number of reagents is more that {module_wells}.'
                                 f'There are {self.competent_cell_tubes_needed} tubes with competent cells.'
                                 f'{self.media_tubes_needed} tubes with media.'
                                 f'Please modify the protocol and try again.')
        else:
            if total_constructs + self.competent_cell_tubes_needed + self.media_tubes_needed > module_wells:
                raise ValueError(f'The number of reagents is more than {module_wells}.'
                                 f'There are {total_constructs} DNA constructs.'
                                 f'{self.competent_cell_tubes_needed} tubes with competent cells.'
                                 f'{self.media_tubes_needed} tubes with media.'
                                 f'Please modify the protocol and try again.')


    def _load_dna_list(self, protocol, labware, volume, dna_list, initial_well=0, description=None, color_index = None):
        """
        Load individual DNA constructs into wells, one construct per well.

        Parameters:
        - protocol: Protocol context
        - labware: Labware object (temperature module or DNA plate)
        - volume: Volume to load in µL
        - construct_list: List of construct names (e.g., ['GVD0011', 'GVD0013'])
        - initial_well: Starting well index
        - color_index: Starting color index (auto-increments if None)

        Returns:
        - List of well objects
        """
        wells = []
        current_color = color_index if color_index is not None else 0
        for i, construct in enumerate(dna_list):
            #Get the well
            well = labware.wells()[initial_well+i]
            wells.append(well)

            #Covert tuple to string if needed
            if isinstance(construct, tuple):
                construct_name = '_'.join(construct)
            else:
                construct_name = construct
            #Define and load "liquid"
            liquid = protocol.define_liquid(
                name = construct_name,
                description= description if description is not None else f"{construct} DNA construct",
                display_color= colors[current_color%len(colors)]
            )
            well.load_liquid(liquid, volume=volume)

            #Track in dictionary
            if not self.use_dna_96plate:
                self.dict_of_parts_in_temp_mod_position[construct_name] = well.well_name
            current_color += 1
        return wells

    def _load_reagents(self, protocol, labware, volume, reagent_name, tube_count, initial_well=0, color_index=None):
        """
        Load multiple tubes of the same reagent type.

        Parameters:
        - protocol: Protocol context
        - labware: Labware object (temperature module)
        - volume: Volume to load in µL
        - reagent_base_name: Base name for reagent (e.g., "Competent_Cell", "Media")
        - tube_count: Number of tubes to load
        - initial_well: Starting well index
        - color_index: Starting color index (auto-increments if None)

        Returns:
        - List of well objects
        """
        wells = []
        current_color = color_index if color_index is not None else 0
        for i in range(tube_count):
            well = labware.wells()[initial_well+i]
            wells.append(well)
            name = f"{reagent_name}_{i+1}"

            liquid = protocol.define_liquid(
                name = name,
                display_color= colors[current_color%len(colors)]
            )

            well.load_liquid(liquid, volume=volume)
            self.dict_of_parts_in_temp_mod_position[name] = well.well_name
            current_color += 1
        return wells

    def _transfer_competent_cells(self, protocol, pipette, pcr_plate, competent_cell_wells,
                                  transfer_volume_competent_cell, thermocycler_starting_well):
        """
        Transfer competent cells to thermocycler wells using distribute method.

        Parameters:
        - protocol: Protocol context
        - pipette: Pipette instrument
        - pcr_plate: Thermocycler plate
        - competent_cell_wells: List of wells containing competent cells
        - transfer_volume_competent_cell: Volume to transfer per well
        - thermocycler_starting_well: Starting well index in thermocycler
        """
        well_index = thermocycler_starting_well

        for tube_index, source_well in enumerate(competent_cell_wells):
            #Calculate how many wells this cell tube will fill
            remaining_transformations = self.total_transformations - (tube_index * self.transformations_per_cell_tube)
            wells_to_fill = min(self.transformations_per_cell_tube, remaining_transformations)

            #Destination wells
            dest_wells = pcr_plate.wells()[well_index:well_index+wells_to_fill]

            #Distribute
            pipette.distribute(
                volume=transfer_volume_competent_cell,
                source=source_well,
                dest=dest_wells,
                mix_before=(3,50),
                disposal_volume=0,
                new_tip='once'
            )

            #Thermocycler Dictionary
            name = f"Competent_Cell_{self.competent_cells}_{tube_index+1}"
            for well in dest_wells:
                if well.well_name not in self.dict_of_parts_in_thermocycler:
                    self.dict_of_parts_in_thermocycler[well.well_name] = []
                self.dict_of_parts_in_thermocycler[well.well_name].append(name)

            well_index += wells_to_fill

    def _transfer_DNA(self, protocol, pipette, pcr_plate, DNA_wells, transfer_volume_dna, thermocycler_starting_well):
        """
        Transfer DNA constructs to thermocycler wells with replicates grouped together.

        Parameters:
        - protocol: Protocol context
        - pipette: Pipette instrument
        - pcr_plate: Thermocycler plate
        - DNA_wells: List of wells containing DNA constructs
        - transfer_volume_dna: Volume to transfer per well
        - thermocycler_starting_well: Starting well index in thermocycler
        """
        for construct_index, (construct_name, source_well) in enumerate(zip(self.list_of_dna, DNA_wells)):
            construct_well = construct_index * self.replicates + thermocycler_starting_well

            for replicate in range(self.replicates):
                dest_well = pcr_plate.wells()[construct_well+replicate]
                #Transfer liquid
                self.liquid_transfer(
                    protocol=protocol,
                    pipette=pipette,
                    volume=transfer_volume_dna,
                    source=source_well,
                    dest=dest_well,
                    asp_rate=self.aspiration_rate,
                    disp_rate=self.dispense_rate,
                    mix_before=transfer_volume_dna,
                    touch_tip=True
                )

                #Track in dictionary
                if dest_well.well_name not in self.dict_of_parts_in_thermocycler:
                    self.dict_of_parts_in_thermocycler[dest_well.well_name] = []
                self.dict_of_parts_in_thermocycler[dest_well.well_name].append(construct_name)

    def _transfer_liquid_broth(self, protocol, pipette, pcr_plate, media_wells, transfer_volume_recovery_media,
                               thermocycler_starting_well):
        """
        Transfer recovery media to thermocycler wells using distribute method.

        Parameters:
        - protocol: Protocol context
        - pipette: Pipette instrument
        - pcr_plate: Thermocycler plate
        - media_wells: List of wells containing recovery media
        - transfer_volume_recovery_media: Volume to transfer per well
        - thermocycler_starting_well: Starting well index in thermocycler
        """
        well_index = thermocycler_starting_well

        for tube_index, source_well in enumerate(media_wells):
            #Calculate how many wells this media tube will fill
            remaining_transformations = self.total_transformations - (tube_index * self.transformations_per_media_tube)
            wells_to_fill = min(self.transformations_per_media_tube, remaining_transformations)

            # Get destination wells for this tube using .top() to avoid contamination
            dest_wells = [pcr_plate.wells()[well_index+i].top(2) for i in range(int(wells_to_fill))]

            #Distribute recovery media
            pipette.distribute(
                volume=transfer_volume_recovery_media,
                source=source_well,
                dest=dest_wells,
                disposal_volume=0,
                new_tip='once',
                air_gap=10
            )

            #Track in dictionary
            media_name = f"Media_{tube_index+1}"
            for i in range(int(wells_to_fill)):
                well_name = pcr_plate.wells()[well_index + i].well_name
                if well_name not in self.dict_of_parts_in_thermocycler:
                    self.dict_of_parts_in_thermocycler[well_name] = []
                self.dict_of_parts_in_thermocycler[well_name].append(media_name)

            well_index += wells_to_fill

