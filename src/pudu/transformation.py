from itertools import groupby
from opentrons import protocol_api
from typing import List, Dict, Optional
from pudu.utils import colors


class Transformation():
    '''
    Base class for automated transformation protocols on the Opentrons OT-2.

    Handles loading transformation data, validating parameters, and providing
    shared utilities used by all transformation subclasses. Subclasses implement
    the specific thermocycler workflow (e.g. heat shock).

    Attributes
    ----------
    volume_dna : float
        Volume of DNA loaded into each source well, in microliters. By default,
        20 microliters. We suggest 2 µL for extracted plasmid and 5 µL for PCR
        products when setting transfer_volume_dna in the subclass.
    replicates : int
        Number of transformation replicates per strain per assembly location.
        By default, 2.
    thermocycler_starting_well : int
        Zero-indexed starting well in the thermocycler plate. By default, 0 (well A1).
    thermocycler_labware : str
        Labware type for the thermocycler plate.
        By default, 'nest_96_wellplate_100ul_pcr_full_skirt'.
    temperature_module_labware : str
        Labware type for the aluminum block on the temperature module.
        By default, 'opentrons_24_aluminumblock_nest_1.5ml_snapcap'.
    temperature_module_position : str
        Deck slot for the temperature module. By default, '1'.
    dna_plate : str
        Labware type for the 96-well DNA source plate (used when use_dna_96plate=True).
        By default, 'nest_96_wellplate_100ul_pcr_full_skirt'.
    dna_plate_position : str
        Deck slot for the 96-well DNA source plate. By default, '2'.
    use_dna_96plate : bool
        If True, DNA is sourced from a 96-well plate at fixed positions given by
        plasmid_locations. Automatically set to True when plasmid_locations is
        provided. By default, False.
    tiprack_p20_labware : str
        Labware type for the p20 tip rack. By default, 'opentrons_96_tiprack_20ul'.
    tiprack_p20_position : str
        Deck slot for the p20 tip rack. By default, '9'.
    tiprack_p200_labware : str
        Labware type for the p200 tip rack.
        By default, 'opentrons_96_filtertiprack_200ul'.
    tiprack_p200_position : str
        Deck slot for the p200 tip rack. By default, '6'.
    pipette_p20 : str
        Pipette model for the p20 single-channel. By default, 'p20_single_gen2'.
    pipette_p20_position : str
        Mount for the p20 pipette ('left' or 'right'). By default, 'left'.
    pipette_p300 : str
        Pipette model for the p300 single-channel. By default, 'p300_single_gen2'.
    pipette_p300_position : str
        Mount for the p300 pipette ('left' or 'right'). By default, 'right'.
    aspiration_rate : float
        Relative aspiration speed as a fraction of the pipette's maximum flow
        rate, where 1.0 is full speed and 0.5 is half speed. Lower values
        reduce bubble formation. By default, 0.5.
    dispense_rate : float
        Relative dispense speed as a fraction of the pipette's maximum flow
        rate, where 1.0 is full speed. By default, 1.0.
    initial_dna_well : int
        Zero-indexed starting well for DNA tubes on the aluminum block (used when
        use_dna_96plate=False). By default, 0.
    water_testing : bool
        If True, uses water in place of competent cells and recovery media during
        simulation/testing runs. By default, False.
    '''
    def __init__(self,
                 transformation_data: Optional[List] = None,
                 plasmid_locations: Optional[Dict] = None,
                 json_params: Optional[Dict] = None,
                 volume_dna:float = 20,
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
                 water_testing:bool = False,
                 **kwargs
                 ):

        kwargs_params = {
            'volume_dna': volume_dna,
            'replicates': replicates,
            'thermocycler_starting_well': thermocycler_starting_well,
            'thermocycler_labware': thermocycler_labware,
            'temperature_module_labware': temperature_module_labware,
            'temperature_module_position': temperature_module_position,
            'dna_plate': dna_plate,
            'dna_plate_position': dna_plate_position,
            'use_dna_96plate': use_dna_96plate,
            'tiprack_p20_labware': tiprack_p20_labware,
            'tiprack_p20_position': tiprack_p20_position,
            'tiprack_p200_labware': tiprack_p200_labware,
            'tiprack_p200_position': tiprack_p200_position,
            'pipette_p20': pipette_p20,
            'pipette_p20_position': pipette_p20_position,
            'pipette_p300': pipette_p300,
            'pipette_p300_position': pipette_p300_position,
            'aspiration_rate': aspiration_rate,
            'dispense_rate': dispense_rate,
            'initial_dna_well': initial_dna_well,
            'water_testing': water_testing
        }
        kwargs_params.update(kwargs)

        self._merged_params = self._merge_params(transformation_data, json_params, kwargs_params)

        # Parse and validate transformation data (new SBOL format)
        if transformation_data is None:
            raise ValueError("Must provide transformation_data as a list of transformation dictionaries")

        self.plasmid_locations = plasmid_locations  # URI -> [well, well, ...] from assembly output
        self.transformations, self.all_plasmids, self.all_chassis = self._parse_transformation_data(transformation_data)

        # Set all attributes from merged parameters
        self.volume_dna = self._merged_params['volume_dna']
        self.replicates = self._merged_params['replicates']
        self.thermocycler_starting_well = self._merged_params['thermocycler_starting_well']
        self.thermocycler_labware = self._merged_params['thermocycler_labware']
        self.temperature_module_labware = self._merged_params['temperature_module_labware']
        self.temperature_module_position = self._merged_params['temperature_module_position']
        self.dna_plate = self._merged_params['dna_plate']
        self.dna_plate_position = self._merged_params['dna_plate_position']
        self.use_dna_96plate = self._merged_params['use_dna_96plate']

        # 96-well plate and plasmid_locations are always paired:
        # positions on the plate are fixed by the assembly run and cannot be assumed sequential
        if self.use_dna_96plate and self.plasmid_locations is None:
            raise ValueError("plasmid_locations must be provided when use_dna_96plate=True. "
                             "Well positions on the assembly plate are fixed and cannot be assumed sequential.")
        if self.plasmid_locations is not None:
            self.use_dna_96plate = True
        self.tiprack_p20_labware = self._merged_params['tiprack_p20_labware']
        self.tiprack_p20_position = self._merged_params['tiprack_p20_position']
        self.tiprack_p200_labware = self._merged_params['tiprack_p200_labware']
        self.tiprack_p200_position = self._merged_params['tiprack_p200_position']
        self.pipette_p20 = self._merged_params['pipette_p20']
        self.pipette_p20_position = self._merged_params['pipette_p20_position']
        self.pipette_p300 = self._merged_params['pipette_p300']
        self.pipette_p300_position = self._merged_params['pipette_p300_position']
        self.aspiration_rate = self._merged_params['aspiration_rate']
        self.dispense_rate = self._merged_params['dispense_rate']
        self.initial_dna_well = self._merged_params['initial_dna_well']
        self.water_testing = self._merged_params['water_testing']

    def _extract_name_from_uri(self, uri: str) -> str:
        """Extract name from SBOL URI"""
        if '/' in uri:
            name_with_version = uri.split('/')[-2]
            if '/' in name_with_version:
                return name_with_version.split('/')[0]
            return name_with_version
        return uri

    def _parse_transformation_data(self, transformation_data):
        """
        Parse new SBOL-style transformation data format.

        Expected format:
        [
          {
            "Strain": "https://SBOL2Build.org/composite_1/1",
            "Chassis": "https://sbolcanvas.org/DH5alpha/1",
            "Plasmids": ["https://...", "https://..."]
          },
          ...
        ]

        Returns:
            transformations: List of dicts with strain, chassis, and plasmids
            all_plasmids: Flat list of all unique plasmids
            all_chassis: List of unique chassis types
        """
        if not isinstance(transformation_data, list):
            raise ValueError("transformation_data must be a list of transformation dictionaries")

        transformations = []
        all_plasmids_set = set()
        all_chassis_set = set()

        for idx, transformation in enumerate(transformation_data):
            # Validate required fields
            if 'Strain' not in transformation:
                raise ValueError(f"Transformation {idx} missing 'Strain' field")
            if 'Chassis' not in transformation:
                raise ValueError(f"Transformation {idx} missing 'Chassis' field")
            if 'Plasmids' not in transformation:
                raise ValueError(f"Transformation {idx} missing 'Plasmids' field")
            if not isinstance(transformation['Plasmids'], list):
                raise ValueError(f"Transformation {idx}: 'Plasmids' must be a list")
            if len(transformation['Plasmids']) == 0:
                raise ValueError(f"Transformation {idx}: 'Plasmids' list cannot be empty")

            # Extract names from URIs
            strain_name = self._extract_name_from_uri(transformation['Strain'])
            chassis_name = self._extract_name_from_uri(transformation['Chassis'])
            plasmid_uris = transformation['Plasmids']
            plasmid_names = [self._extract_name_from_uri(p) for p in plasmid_uris]

            # If plasmid_locations provided, validate all plasmid URIs are present
            if self.plasmid_locations is not None:
                for uri in plasmid_uris:
                    if uri not in self.plasmid_locations:
                        raise ValueError(
                            f"Plasmid URI '{uri}' not found in plasmid_locations. "
                            f"Available URIs: {list(self.plasmid_locations.keys())}"
                        )

            transformations.append({
                'strain': strain_name,
                'chassis': chassis_name,
                'plasmids': plasmid_names,
                'plasmid_uris': plasmid_uris
            })

            all_plasmids_set.update(plasmid_names)
            all_chassis_set.add(chassis_name)

        return transformations, list(sorted(all_plasmids_set)), list(sorted(all_chassis_set))

    def _merge_params(self, transformation_data: Optional[Dict], advanced_params: Optional[Dict], kwargs_params: Dict) -> Dict:
        """
        Merge parameters with precedence: defaults <- transformation_data <- advanced_params <- kwargs

        Args:
            transformation_data: Optional dict containing protocol data (list_of_dna, competent_cells)
            advanced_params: Optional dict containing configuration parameters
            kwargs_params: Dict of parameters passed as kwargs

        Returns:
            Merged parameter dictionary
        """
        # Define defaults for all valid parameters
        # Includes both Transformation and HeatShockTransformation parameters
        valid_params = {
            # Transformation base parameters
            'volume_dna': 20,
            'replicates': 2,
            'thermocycler_starting_well': 0,
            'thermocycler_labware': 'nest_96_wellplate_100ul_pcr_full_skirt',
            'temperature_module_labware': 'opentrons_24_aluminumblock_nest_1.5ml_snapcap',
            'temperature_module_position': '1',
            'dna_plate': 'nest_96_wellplate_100ul_pcr_full_skirt',
            'dna_plate_position': '2',
            'use_dna_96plate': False,
            'tiprack_p20_labware': 'opentrons_96_tiprack_20ul',
            'tiprack_p20_position': '9',
            'tiprack_p200_labware': 'opentrons_96_filtertiprack_200ul',
            'tiprack_p200_position': '6',
            'pipette_p20': 'p20_single_gen2',
            'pipette_p20_position': 'left',
            'pipette_p300': 'p300_single_gen2',
            'pipette_p300_position': 'right',
            'aspiration_rate': 0.5,
            'dispense_rate': 1,
            'initial_dna_well': 0,
            'water_testing': False,
            # HeatShockTransformation-specific parameters
            'transfer_volume_dna': 2,
            'transfer_volume_competent_cell': 20,
            'tube_volume_competent_cell': 100,
            'transfer_volume_recovery_media': 60,
            'tube_volume_recovery_media': 1200,
            'cold_incubation1': None,
            'heat_shock': None,
            'cold_incubation2': None,
            'recovery_incubation': None
        }

        # Start with defaults
        merged = valid_params.copy()

        # Apply advanced_params (if provided)
        if advanced_params is not None:
            self._validate_param_structure(advanced_params, valid_params, 'advanced_params')
            merged.update(advanced_params)

        # Apply kwargs (highest precedence) - only if they differ from defaults
        for key, value in kwargs_params.items():
            if key in valid_params:
                # Only override if the value is explicitly different from the default
                if value != valid_params[key]:
                    merged[key] = value

        return merged

    def _validate_param_structure(self, params: Dict, valid_params: Dict, param_name: str):
        """
        Validate that all parameters in the dict are recognized.

        Args:
            params: Dictionary to validate
            valid_params: Dictionary of valid parameter names
            param_name: Name of the parameter dict (for error messages)

        Raises:
            ValueError: If unknown parameters are found
        """
        unknown_params = set(params.keys()) - set(valid_params.keys())
        if unknown_params:
            raise ValueError(
                f"Unknown parameters in {param_name}: {unknown_params}.\n"
                f"Valid parameters are: {set(valid_params.keys())}"
            )

class HeatShockTransformation(Transformation):
    '''
    Heat shock transformation protocol for the Opentrons OT-2.

    Automates the full heat shock transformation workflow: loading DNA and competent
    cells into a thermocycler plate, running the heat shock cycle, adding recovery
    media, and exporting a plating map for the next protocol step.

    Inherits all base parameters from Transformation. The attributes below are
    specific to the heat shock transformation protocol.

    Attributes
    ----------
    transfer_volume_dna : float
        Volume of DNA to transfer into each thermocycler well, in microliters.
        By default, 2 microliters. Note: this is the volume actually pipetted per
        reaction, distinct from volume_dna (the volume loaded into the source well).
    transfer_volume_competent_cell : float
        Volume of competent cells to transfer into each thermocycler well, in
        microliters. By default, 20 microliters.
    tube_volume_competent_cell : float
        Total usable volume of competent cells per tube, in microliters. Used to
        calculate how many reactions each tube can supply before switching to the
        next tube. By default, 100 microliters.
    transfer_volume_recovery_media : float
        Volume of recovery media to add to each well after heat shock, in
        microliters. By default, 60 microliters.
    tube_volume_recovery_media : float
        Total usable volume of recovery media per tube, in microliters. Used to
        calculate how many wells each tube can supply. By default, 1200 microliters.
    cold_incubation1 : dict
        First cold incubation step (on ice before heat shock). A dict with keys
        'temperature' (°C) and 'hold_time_minutes'.
        By default, {'temperature': 4, 'hold_time_minutes': 30}.
    heat_shock : dict
        Heat shock step. A dict with keys 'temperature' (°C) and 'hold_time_minutes'.
        By default, {'temperature': 42, 'hold_time_minutes': 1}.
    cold_incubation2 : dict
        Second cold incubation immediately after heat shock. A dict with keys
        'temperature' (°C) and 'hold_time_minutes'.
        By default, {'temperature': 4, 'hold_time_minutes': 2}.
    recovery_incubation : dict
        Recovery incubation after recovery media addition. A dict with keys
        'temperature' (°C) and 'hold_time_minutes'.
        By default, {'temperature': 37, 'hold_time_minutes': 60}.
    '''
    def __init__(self,
                transformation_data: Optional[List] = None,
                plasmid_locations: Optional[Dict] = None,
                json_params: Optional[Dict] = None,
                transfer_volume_dna:float = 2,
                transfer_volume_competent_cell:float = 20,
                tube_volume_competent_cell:float =100,
                transfer_volume_recovery_media:float = 60,
                tube_volume_recovery_media:float = 1200, #add a bit more to pick it properly
                cold_incubation1:Optional[Dict] = None,
                heat_shock:Optional[Dict] = None,
                cold_incubation2:Optional[Dict] = None,
                recovery_incubation:Optional[Dict] = None,
                *args, **kwargs):
        super().__init__(
            transformation_data=transformation_data,
            plasmid_locations=plasmid_locations,
            json_params=json_params,
            transfer_volume_dna=transfer_volume_dna,
            transfer_volume_competent_cell=transfer_volume_competent_cell,
            tube_volume_competent_cell=tube_volume_competent_cell,
            transfer_volume_recovery_media=transfer_volume_recovery_media,
            tube_volume_recovery_media=tube_volume_recovery_media,
            cold_incubation1=cold_incubation1,
            heat_shock=heat_shock,
            cold_incubation2=cold_incubation2,
            recovery_incubation=recovery_incubation,
            *args, **kwargs)

        self.transfer_volume_dna = self._merged_params['transfer_volume_dna']
        self.transfer_volume_competent_cell = self._merged_params['transfer_volume_competent_cell']
        self.tube_volume_competent_cell = self._merged_params['tube_volume_competent_cell']
        self.transfer_volume_recovery_media = self._merged_params['transfer_volume_recovery_media']
        self.tube_volume_recovery_media = self._merged_params['tube_volume_recovery_media']

        cold_incubation1 = self._merged_params['cold_incubation1']
        heat_shock = self._merged_params['heat_shock']
        cold_incubation2 = self._merged_params['cold_incubation2']
        recovery_incubation = self._merged_params['recovery_incubation']

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
        self.dict_of_parts_in_dna_plate = {}
        self.plasmid_name_to_wells = {}  # plasmid name -> [well_obj, ...], populated during loading

    def _export_plating_input(self, protocol):
        """
        Export plating input JSON during simulation.
        Args:
            protocol: Protocol context
        """
        import json

        plating_input = {
            'bacterium_locations': self.dict_of_parts_in_thermocycler
        }

        output_path = 'plating_input.json'
        with open(output_path, 'w') as f:
            json.dump(plating_input, f, indent=2)

        protocol.comment("\n" + "="*70)
        protocol.comment(f"Generated {output_path} for next protocol")
        protocol.comment(f"  Bacteria locations: {len(self.dict_of_parts_in_thermocycler)}")
        protocol.comment("="*70)

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
        pipette_p300 = protocol.load_instrument(self.pipette_p300, self.pipette_p300_position, tip_racks=[tiprack_p200])
        #Validate protocol
        self._validate_protocol(protocol, alumblock)

        #Load Reagents (also populates self.plasmid_name_to_wells)
        if self.use_dna_96plate:
            competent_cell_wells_by_chassis, media_wells = self._load_reagents_96plate(protocol, dna_plate, alumblock)
        else:
            competent_cell_wells_by_chassis, media_wells = self._load_reagents_temp_module(protocol, alumblock)

        #Set Temperature module and Thermocycler module to 4
        thermocycler_module.open_lid()
        if not self.water_testing:
            temperature_module.set_temperature(4)
            thermocycler_module.set_block_temperature(4)

        #Load competent cells into the thermocycler
        pipette = pipette_p300
        self._transfer_competent_cells(protocol, pipette, pcr_plate, competent_cell_wells_by_chassis, self.transfer_volume_competent_cell, self.thermocycler_starting_well)

        #Load DNA into the thermocycler
        if self.transfer_volume_dna > 20:
            pipette = pipette_p300
        else:
            pipette = pipette_p20
        self._transfer_DNA(protocol, pipette, pcr_plate, self.transfer_volume_dna, self.thermocycler_starting_well)

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

        # Export plating input for next protocol (simulation only)
        if protocol.is_simulating():
            try:
                self._export_plating_input(protocol)
            except Exception as e:
                protocol.comment(f"Could not export plating input: {e}")

        # output
        print('Strain and media tube in temp_mod')
        print(self.dict_of_parts_in_temp_mod_position)
        if self.use_dna_96plate:
            print('DNA constructs in DNA plate (slot 2)')
            print(self.dict_of_parts_in_dna_plate)
        print('Genetically modified organisms in thermocycler')
        print(self.dict_of_parts_in_thermocycler)

    def _validate_protocol(self, protocol, labware):
        """
        Validate protocol requirements and compute all derived counts used throughout run().
        Sets: self.location_replicates, self.total_transformations,
              self.transformations_per_cell_tube, self.competent_cell_tubes_by_chassis,
              self.reactions_by_chassis, self.transformations_per_media_tube,
              self.media_tubes_needed.
        Raises ValueError if reagents exceed available alumblock wells.
        """
        #Number of available wells to load into
        module_wells = len(labware.wells())

        #Number of strains to transform
        total_strains = len(self.transformations)

        #Number of total plasmid wells needed (one well per unique plasmid)
        total_plasmid_wells = len(self.all_plasmids)

        # Number of location replicates per strain (assembly replicates of the same plasmid in plate,
        # always 1 for temp module since plasmids are in a single sequential well)
        if self.plasmid_locations is not None:
            self.location_replicates = len(next(iter(self.plasmid_locations.values())))
        else:
            self.location_replicates = 1

        #Total transformation reactions
        self.total_transformations = total_strains * self.location_replicates * self.replicates

        #Calculate competent cell tubes needed per chassis type
        self.transformations_per_cell_tube = self.tube_volume_competent_cell // self.transfer_volume_competent_cell
        self.competent_cell_tubes_by_chassis = {}
        self.reactions_by_chassis = {}
        total_competent_cell_tubes = 0

        for chassis in self.all_chassis:
            # Count how many transformations use this chassis
            transformations_for_chassis = sum(1 for t in self.transformations if t['chassis'] == chassis)
            reactions_for_chassis = transformations_for_chassis * self.location_replicates * self.replicates
            self.reactions_by_chassis[chassis] = reactions_for_chassis
            tubes_needed = (reactions_for_chassis + self.transformations_per_cell_tube - 1) // self.transformations_per_cell_tube
            self.competent_cell_tubes_by_chassis[chassis] = tubes_needed
            total_competent_cell_tubes += tubes_needed

        #Number of tubes with media to be used
        self.transformations_per_media_tube = self.tube_volume_recovery_media // self.transfer_volume_recovery_media
        self.media_tubes_needed = (self.total_transformations + self.transformations_per_media_tube - 1) // self.transformations_per_media_tube

        #Validate wells
        if self.use_dna_96plate:
            # DNA is on a separate plate, only cells and media on the temp module
            if total_competent_cell_tubes + self.media_tubes_needed > module_wells:
                raise ValueError(f'The number of reagents is more than {module_wells}.'
                                 f'There are {total_competent_cell_tubes} tubes with competent cells ({self.competent_cell_tubes_by_chassis}).'
                                 f'{self.media_tubes_needed} tubes with media.'
                                 f'Please modify the protocol and try again.')
        else:
            # DNA, cells, and media all on the temp module
            if total_plasmid_wells + total_competent_cell_tubes + self.media_tubes_needed > module_wells:
                raise ValueError(f'The number of reagents is more than {module_wells}.'
                                 f'There are {total_plasmid_wells} plasmid wells.'
                                 f'{total_competent_cell_tubes} tubes with competent cells ({self.competent_cell_tubes_by_chassis}).'
                                 f'{self.media_tubes_needed} tubes with media.'
                                 f'Please modify the protocol and try again.')


    def _load_reagents_96plate(self, protocol, dna_plate, alumblock):
        """
        Load all reagents for the 96-well plate workflow (plasmid_locations provided).
        DNA constructs are loaded from the assembly output plate at their fixed positions —
        populates self.plasmid_name_to_wells. Competent cells and media are loaded
        sequentially onto the alumblock starting at well 0.

        Parameters:
        - protocol: Protocol context
        - dna_plate: 96-well plate labware object (slot 2)
        - alumblock: Temperature module labware object

        Returns:
        - competent_cell_wells_by_chassis: dict mapping chassis name to list of well objects
        - media_wells: list of well objects
        """
        # Load DNA from dna_plate at actual well positions from plasmid_locations
        # Populates self.plasmid_name_to_wells
        self._load_dna_into_dna_plate(protocol, dna_plate)

        # Load competent cells for each chassis onto alumblock
        competent_cell_wells_by_chassis = {}
        current_well = 0
        for chassis in self.all_chassis:
            tubes_needed = self.competent_cell_tubes_by_chassis[chassis]
            wells = self._load_reagents(protocol, alumblock, self.tube_volume_competent_cell,
                                        f"Competent Cell {chassis}", tubes_needed, initial_well=current_well)
            competent_cell_wells_by_chassis[chassis] = wells
            current_well += tubes_needed

        # Load media onto alumblock
        media_wells = self._load_reagents(protocol, alumblock, self.tube_volume_recovery_media,
                                          "Media", self.media_tubes_needed, initial_well=current_well)

        return competent_cell_wells_by_chassis, media_wells

    def _load_dna_into_dna_plate(self, protocol, dna_plate):
        """
        Load DNA constructs into their fixed positions on the 96-well DNA plate.
        Positions are determined by plasmid_locations (from assembly output or MoClo kit layout).
        Each construct may occupy multiple wells (assembly replicates).
        Populates self.plasmid_name_to_wells: {construct_name: [well_obj, ...]}

        Parameters:
        - protocol: Protocol context
        - dna_plate: 96-well plate labware object on slot 2
        """
        current_color = 0
        name_to_uri = {self._extract_name_from_uri(uri): uri for uri in self.plasmid_locations}

        for construct_name in self.all_plasmids:
            uri = name_to_uri[construct_name]
            well_names = self.plasmid_locations[uri]
            well_objects = []

            for i, well_name in enumerate(well_names):
                well = dna_plate.wells_by_name()[well_name]
                well_objects.append(well)
                if i == 0:
                    liquid = protocol.define_liquid(
                        name=construct_name,
                        description=f"{construct_name} DNA construct",
                        display_color=colors[current_color % len(colors)]
                    )
                well.load_liquid(liquid, volume=self.volume_dna)

            self.plasmid_name_to_wells[construct_name] = well_objects
            self.dict_of_parts_in_dna_plate[construct_name] = well_names
            current_color += 1

    def _load_reagents_temp_module(self, protocol, alumblock):
        """
        Load all reagents for the temp module workflow (no plasmid_locations).
        DNA constructs are loaded sequentially starting at initial_dna_well —
        populates self.plasmid_name_to_wells. Competent cells and media follow
        sequentially on the same alumblock.

        Parameters:
        - protocol: Protocol context
        - alumblock: Temperature module labware object

        Returns:
        - competent_cell_wells_by_chassis: dict mapping chassis name to list of well objects
        - media_wells: list of well objects
        """
        # Load DNA sequentially onto alumblock starting at initial_dna_well
        # Populates self.plasmid_name_to_wells
        self._load_dna_into_temp_module(protocol, alumblock)

        # Load competent cells for each chassis, starting after the DNA wells
        competent_cell_wells_by_chassis = {}
        current_well = self.initial_dna_well + len(self.all_plasmids)
        for chassis in self.all_chassis:
            tubes_needed = self.competent_cell_tubes_by_chassis[chassis]
            wells = self._load_reagents(protocol, alumblock, self.tube_volume_competent_cell,
                                        f"Competent Cell {chassis}", tubes_needed, initial_well=current_well)
            competent_cell_wells_by_chassis[chassis] = wells
            current_well += tubes_needed

        # Load media onto alumblock after competent cells
        media_wells = self._load_reagents(protocol, alumblock, self.tube_volume_recovery_media,
                                          "Media", self.media_tubes_needed, initial_well=current_well)

        return competent_cell_wells_by_chassis, media_wells

    def _load_dna_into_temp_module(self, protocol, alumblock):
        """
        Load DNA constructs sequentially into the temperature module alumblock.
        Positions are assigned sequentially starting at initial_dna_well.
        Populates self.plasmid_name_to_wells: {construct_name: [well_obj]} (single-element list).

        Parameters:
        - protocol: Protocol context
        - alumblock: Temperature module labware object
        """
        current_color = 0

        for i, construct_name in enumerate(self.all_plasmids):
            well = alumblock.wells()[self.initial_dna_well + i]
            liquid = protocol.define_liquid(
                name=construct_name,
                description=f"{construct_name} DNA construct",
                display_color=colors[current_color % len(colors)]
            )
            well.load_liquid(liquid, volume=self.volume_dna)
            self.plasmid_name_to_wells[construct_name] = [well]
            self.dict_of_parts_in_temp_mod_position[construct_name] = well.well_name
            current_color += 1

    def _load_reagents(self, protocol, labware, volume, reagent_name, tube_count, initial_well=0, color_index=None):
        """
        Load multiple tubes of the same reagent type onto a labware object.
        Tubes are named {reagent_name}_1, {reagent_name}_2, etc. and tracked
        in self.dict_of_parts_in_temp_mod_position.

        Parameters:
        - protocol: Protocol context
        - labware: Labware object to load reagents onto
        - volume: Volume per tube in µL
        - reagent_name: Base name for the reagent (e.g., "Competent Cell DH5alpha", "Media")
        - tube_count: Number of tubes to load
        - initial_well: Starting well index on the labware
        - color_index: Starting color index for Opentrons UI (cycles through colors list)

        Returns:
        - List of well objects in order
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

    def _transfer_competent_cells(self, protocol, pipette, pcr_plate, competent_cell_wells_by_chassis,
                                  transfer_volume_competent_cell, thermocycler_starting_well):
        """
        Transfer competent cells into thermocycler wells.
        Iterates self.transformations as ground truth. For each strain, fills
        location_replicates * replicates wells with the appropriate chassis cells.
        Tube selection is per-chassis (chassis_reaction_count) so multiple chassis
        types each consume only their own tubes independently.

        Tips are reused within each consecutive source tube block (one pickup per tube)
        by batching destinations with distribute(). A new tip is picked up whenever the
        source tube changes, preventing cross-chassis contamination.

        Parameters:
        - protocol: Protocol context
        - pipette: Pipette instrument (p300)
        - pcr_plate: Thermocycler plate labware
        - competent_cell_wells_by_chassis: Dict mapping chassis name to list of well objects
        - transfer_volume_competent_cell: Volume to transfer per well in µL
        - thermocycler_starting_well: Starting well index in thermocycler plate
        """
        # Pre-compute all transfers as (source_well, dest_well, chassis, strain)
        transfers = []
        well_index = thermocycler_starting_well
        chassis_reaction_count = {chassis: 0 for chassis in self.all_chassis}

        for transformation in self.transformations:
            chassis = transformation['chassis']
            cell_wells = competent_cell_wells_by_chassis[chassis]

            for _ in range(self.location_replicates * self.replicates):
                dest_well = pcr_plate.wells()[well_index]
                tube_index = chassis_reaction_count[chassis] // self.transformations_per_cell_tube
                source_well = cell_wells[tube_index]
                transfers.append((source_well, dest_well, chassis, transformation['strain']))

                chassis_reaction_count[chassis] += 1
                well_index += 1

        # Distribute per consecutive source tube — one tip pickup per tube.
        # dict_of_parts_in_thermocycler is updated after each distribute() call
        # so it reflects only wells that have actually been filled.
        for source_well, group in groupby(transfers, key=lambda t: t[0]):
            group_list = list(group)
            dest_wells = [t[1] for t in group_list]
            pipette.distribute(
                volume=transfer_volume_competent_cell,
                source=source_well,
                dest=dest_wells,
                mix_before=(3, 50),
                disposal_volume=0,
                new_tip='once'
            )
            for _, dest_well, chassis, strain in group_list:
                name = f"Competent_Cell_{chassis}"
                if dest_well.well_name not in self.dict_of_parts_in_thermocycler:
                    self.dict_of_parts_in_thermocycler[dest_well.well_name] = [strain]
                self.dict_of_parts_in_thermocycler[dest_well.well_name].append(name)

    def _transfer_DNA(self, protocol, pipette, pcr_plate, transfer_volume_dna, thermocycler_starting_well):
        """
        Transfer DNA plasmids to thermocycler wells. Multiple plasmids per strain go to the same well.
        Uses self.plasmid_name_to_wells (populated during loading) for all source well lookups —
        no positional indexing, fully name-driven from self.transformations.

        For the temp module path: each plasmid has one well → location_replicates = 1
        For the dna plate path: each plasmid has N wells (assembly replicates) → location_replicates = N

        Parameters:
        - protocol: Protocol context
        - pipette: Pipette instrument
        - pcr_plate: Thermocycler plate
        - transfer_volume_dna: Volume to transfer per plasmid
        - thermocycler_starting_well: Starting well index in thermocycler
        """
        well_index = thermocycler_starting_well

        for transformation in self.transformations:
            plasmids = transformation['plasmids']

            for loc_idx in range(self.location_replicates):
                for replicate in range(self.replicates):
                    dest_well = pcr_plate.wells()[well_index]

                    for plasmid_name in plasmids:
                        source_well = self.plasmid_name_to_wells[plasmid_name][loc_idx]

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

                        if dest_well.well_name not in self.dict_of_parts_in_thermocycler:
                            self.dict_of_parts_in_thermocycler[dest_well.well_name] = []
                        self.dict_of_parts_in_thermocycler[dest_well.well_name].append(plasmid_name)

                    well_index += 1

    def _transfer_liquid_broth(self, protocol, pipette, pcr_plate, media_wells, transfer_volume_recovery_media,
                               thermocycler_starting_well):
        """
        Distribute recovery media into all thermocycler wells using the pipette distribute method.
        Each media tube fills up to transformations_per_media_tube wells before moving to the next.
        Uses .top(2) on dest wells to avoid contamination from the pipette tip.
        Covers self.total_transformations wells in total.

        Parameters:
        - protocol: Protocol context
        - pipette: Pipette instrument (p300)
        - pcr_plate: Thermocycler plate labware
        - media_wells: List of well objects containing recovery media
        - transfer_volume_recovery_media: Volume to distribute per well in µL
        - thermocycler_starting_well: Starting well index in thermocycler plate
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

