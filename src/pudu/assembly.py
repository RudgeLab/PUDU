import xlsxwriter
from opentrons import protocol_api
from typing import List, Dict, Optional
from fnmatch import fnmatch
from itertools import product
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pudu.utils import Camera, colors


@dataclass
class ManualReactionRecord:
    """Structured representation of one Golden Gate manual assembly reaction."""
    product_uri: str
    product_name: str
    backbone_uri: str
    backbone_name: str
    part_uris: List[str]
    part_names: List[str]
    restriction_enzyme_uri: str
    restriction_enzyme_name: str
    number_of_dna_components: int
    total_dna_volume: float
    fixed_reagent_volume: float
    water_volume: float
    total_reaction_volume: float
    reagent_additions: List[Dict[str, str]] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

class BaseAssembly(ABC):
    """
    Abstract base class for Loop Assembly protocols.
    Contains shared hardware setup, liquid handling, and tip management functionality.
    """

    def __init__(self,
                 json_params: Optional[Dict] = None,
                 volume_total_reaction: float = 20,
                 volume_part: float = 2,
                 volume_restriction_enzyme: float = 2,
                 volume_t4_dna_ligase: float = 4,
                 volume_t4_dna_ligase_buffer: float = 2,
                 replicates: int = 1,
                 thermocycler_starting_well: int = 0,
                 thermocycler_labware: str = 'nest_96_wellplate_100ul_pcr_full_skirt',
                 temperature_module_labware: str = 'opentrons_24_aluminumblock_nest_1.5ml_snapcap',
                 temperature_module_position: str = '1',
                 tiprack_labware: str = 'opentrons_96_tiprack_20ul',
                 tiprack_positions: Optional[List[str]] = None,
                 pipette: str = 'p20_single_gen2',
                 pipette_position: str = 'left',
                 initial_tip: Optional[str] = None,
                 aspiration_rate: float = 0.5,
                 dispense_rate: float = 1,
                 take_picture: bool = False,
                 take_video: bool = False,
                 water_testing: bool = False,
                 output_xlsx: bool = True,
                 protocol_name: str = ''):

        kwargs_params = {
            'volume_total_reaction': volume_total_reaction,
            'volume_part': volume_part,
            'volume_restriction_enzyme': volume_restriction_enzyme,
            'volume_t4_dna_ligase': volume_t4_dna_ligase,
            'volume_t4_dna_ligase_buffer': volume_t4_dna_ligase_buffer,
            'replicates': replicates,
            'thermocycler_starting_well': thermocycler_starting_well,
            'thermocycler_labware': thermocycler_labware,
            'temperature_module_labware': temperature_module_labware,
            'temperature_module_position': temperature_module_position,
            'tiprack_labware': tiprack_labware,
            'tiprack_positions': tiprack_positions,
            'pipette': pipette,
            'pipette_position': pipette_position,
            'initial_tip' : initial_tip,
            'aspiration_rate': aspiration_rate,
            'dispense_rate': dispense_rate,
            'take_picture': take_picture,
            'take_video': take_video,
            'water_testing': water_testing,
            'output_xlsx': output_xlsx,
            'protocol_name': protocol_name
        }

        params = self._merge_params(json_params, kwargs_params)

        self.volume_total_reaction = params['volume_total_reaction']
        self.volume_part = params['volume_part']
        self.volume_restriction_enzyme = params['volume_restriction_enzyme']
        self.volume_t4_dna_ligase = params['volume_t4_dna_ligase']
        self.volume_t4_dna_ligase_buffer = params['volume_t4_dna_ligase_buffer']
        self.replicates = params['replicates']
        self.thermocycler_starting_well = params['thermocycler_starting_well']
        self.thermocycler_labware = params['thermocycler_labware']
        self.temperature_module_labware = params['temperature_module_labware']
        self.temperature_module_position = params['temperature_module_position']
        self.tiprack_labware = params['tiprack_labware']
        if params['tiprack_positions'] is None:
            self.tiprack_positions = ['2', '3', '4', '5', '6', '9']
        else:
            self.tiprack_positions =  params['tiprack_positions']
        self.pipette = params['pipette']
        self.pipette_position = params['pipette_position']
        self.initial_tip = params['initial_tip']
        self.aspiration_rate = params['aspiration_rate']
        self.dispense_rate = params['dispense_rate']
        self.take_picture = params['take_picture']
        self.take_video = params['take_video']
        self.water_testing = params['water_testing']
        self.output_xlsx = params['output_xlsx']
        self.protocol_name = params['protocol_name']

        # Shared tracking dictionaries
        self.dict_of_parts_in_temp_mod_position = {}
        self.dict_of_parts_in_thermocycler = {}
        self.dna_list_for_transformation_protocol = []
        self.product_uri_to_wells = {}
        self.xlsx_output = None

        #Initialize Camera
        self.camera = Camera()
        # Tip management
        self.tip_management = {
            'all_racks': [],
            'on_deck_racks': [],
            'off_deck_racks': [],
            'available_slots': [],
            'tips_used': 0,
            'tips_per_batch': 0,
            'current_batch': 1,
            'total_batches': 1
        }

    def _merge_params(self, json_params: Dict, kwargs_params: Dict) -> Dict:
        """
        Merge parameters with precedence: defaults <- advanced_params <- kwargs

        Args:
            advanced_params: Dictionary of parameters from JSON/dict (optional)
            kwargs_params: Dictionary of parameters from function kwargs

        Returns:
            Merged parameter dictionary

        Raises:
            ValueError: If advanced_params contains unknown parameters
        """
        # Define all valid parameter names with their defaults
        valid_params = {
            'volume_total_reaction': 20,
            'volume_part': 2,
            'volume_restriction_enzyme': 2,
            'volume_t4_dna_ligase': 4,
            'volume_t4_dna_ligase_buffer': 2,
            'replicates': 1,
            'thermocycler_starting_well': 0,
            'thermocycler_labware': 'nest_96_wellplate_100ul_pcr_full_skirt',
            'temperature_module_labware': 'opentrons_24_aluminumblock_nest_1.5ml_snapcap',
            'temperature_module_position': '1',
            'tiprack_labware': 'opentrons_96_tiprack_20ul',
            'tiprack_positions': None,
            'pipette': 'p20_single_gen2',
            'pipette_position': 'left',
            'initial_tip': None,
            'aspiration_rate': 0.5,
            'dispense_rate': 1,
            'take_picture': False,
            'take_video': False,
            'water_testing': False,
            'output_xlsx': True,
            'protocol_name': ''
        }

        # Start with defaults
        merged = valid_params.copy()

        # Apply json_params if provided
        if json_params is not None:
            self._validate_param_structure(json_params, valid_params)
            merged.update(json_params)

        # Apply kwargs (checking against defaults to see what was explicitly passed)
        # Only update if the kwarg value differs from the default
        for key, value in kwargs_params.items():
            if key in valid_params:
                # Always use kwargs value, even if it matches default
                # This ensures explicit kwargs override advanced_params
                if json_params is None or key not in json_params or value != valid_params[key]:
                    merged[key] = value

        return merged

    def _validate_param_structure(self, advanced_params: Dict, valid_params: Dict):
        """
        Validate that advanced_params only contains known parameter names.

        Args:
            advanced_params: Dictionary to validate
            valid_params: Dictionary of valid parameter names

        Raises:
            ValueError: If unknown parameters are found
        """
        unknown_params = set(advanced_params.keys()) - set(valid_params.keys())
        if unknown_params:
            raise ValueError(
                f"Unknown parameters in advanced_params: {unknown_params}. "
                f"Valid parameters are: {set(valid_params.keys())}"
            )

    def _validate_reaction_volumes(self, num_parts: int):
        """
        Validate that reaction volumes are physically possible.

        Args:
            num_parts: Number of DNA parts (including backbone) in the assembly

        Raises:
            ValueError: If volumes exceed total reaction volume
        """
        volume_reagents = (self.volume_restriction_enzyme +
                          self.volume_t4_dna_ligase +
                          self.volume_t4_dna_ligase_buffer)

        total_parts_volume = self.volume_part * num_parts
        total_needed = volume_reagents + total_parts_volume

        if total_needed >= self.volume_total_reaction:
            water_volume = self.volume_total_reaction - total_needed
            raise ValueError(
                f"Reaction volume error: Cannot fit {num_parts} parts into {self.volume_total_reaction}µL reaction.\n"
                f"  Required volumes:\n"
                f"    - Reagents (enzyme + ligase + buffer): {volume_reagents}µL\n"
                f"    - Parts ({num_parts} × {self.volume_part}µL): {total_parts_volume}µL\n"
                f"    - Water: {water_volume}µL (NEGATIVE!)\n"
                f"  Total needed: {total_needed}µL\n"
                f"  Solutions:\n"
                f"    1. Increase 'volume_total_reaction' to at least {total_needed + 1}µL\n"
                f"    2. Decrease 'volume_part' to at most {(self.volume_total_reaction - volume_reagents - 1) / num_parts:.1f}µL\n"
                f"    3. Decrease reagent volumes"
            )

    def _well_to_index(self, well_name: str) -> int:
        """
        Convert well name (e.g., 'A1', 'H12') to 0-based index in 96-well plate.

        Args:
            well_name: Well position like 'A1', 'B3', 'H12'

        Returns:
            Zero-based index (0-95) for the well

        Raises:
            ValueError: If well_name format is invalid
        """
        if not well_name or len(well_name) < 2:
            raise ValueError(f"Invalid well name: '{well_name}'. Expected format like 'A1', 'B3', 'H12'")

        row = well_name[0]
        try:
            col = int(well_name[1:])
        except ValueError:
            raise ValueError(f"Invalid well name: '{well_name}'. Column must be a number (e.g., 'A1', 'H12')")

        if row not in 'ABCDEFGH':
            raise ValueError(f"Invalid well name: '{well_name}'. Row must be A-H")

        if col < 1 or col > 12:
            raise ValueError(f"Invalid well name: '{well_name}'. Column must be 1-12")

        row_index = ord(row) - ord('A')
        col_index = col - 1
        return row_index + (col_index * 8)

    def _tips_available_from_position(self, well_name: str) -> int:
        """
        Calculate how many tips are available starting from a given position.

        Args:
            well_name: Starting well position like 'A1', 'H12'

        Returns:
            Number of tips available from that position to H12
        """
        start_index = self._well_to_index(well_name)
        return 96 - start_index

    @abstractmethod
    def process_assemblies(self):
        """Process input assemblies - format-specific implementation"""
        pass

    @abstractmethod
    def _load_parts_and_enzymes(self, protocol, alum_block) -> int:
        """Load parts and enzymes onto temperature module - format-specific"""
        pass

    @abstractmethod
    def _process_assembly_combinations(self, protocol, pipette, thermo_plate, alum_block,
                                       dd_h2o, t4_dna_ligase_buffer, t4_dna_ligase,
                                       volume_reagents, thermocycler_well_counter) -> int:
        """Process all assembly combinations - format-specific"""
        pass

    @abstractmethod
    def _calculate_total_tips_needed(self) -> int:
        """Calculate total tips needed - format-specific implementation"""
        pass

    def setup_tip_management(self, protocol):
        """Setup batch tip management for high-throughput applications."""
        total_tips_needed = self._calculate_total_tips_needed()

        first_rack_tips = 96
        if self.initial_tip:
            try:
                first_rack_tips = self._tips_available_from_position(self.initial_tip)
                protocol.comment(f"Starting from tip {self.initial_tip} ({first_rack_tips} tips available on first rack)")
            except ValueError as e:
                raise ValueError(f"Error with initial_tip parameter: {e}")

        # Calculate racks needed, accounting for the partially used first rack
        if total_tips_needed <= first_rack_tips:
            tip_racks_needed = 1
        else:
            remaining_tips = total_tips_needed - first_rack_tips
            additional_racks = (remaining_tips + 95) // 96
            tip_racks_needed = 1 + additional_racks

        available_deck_slots = self.tiprack_positions
        max_racks_on_deck = len(available_deck_slots)

        protocol.comment(f"Protocol requires {total_tips_needed} tips ({tip_racks_needed} racks)")

        all_tip_racks = []
        on_deck_racks = []
        for i in range(min(tip_racks_needed, max_racks_on_deck)):
            rack = protocol.load_labware(self.tiprack_labware, available_deck_slots[i])
            all_tip_racks.append(rack)
            on_deck_racks.append(rack)

        off_deck_racks = []
        for i in range(max_racks_on_deck, tip_racks_needed):
            rack = protocol.load_labware(self.tiprack_labware, protocol_api.OFF_DECK)
            all_tip_racks.append(rack)
            off_deck_racks.append(rack)

        self.tip_management.update({
            'all_racks': all_tip_racks,
            'on_deck_racks': on_deck_racks,
            'off_deck_racks': off_deck_racks,
            'available_slots': available_deck_slots,
            'tips_used': 0,
            'tips_per_batch': max_racks_on_deck * 96,
            'current_batch': 1,
            'total_batches': (tip_racks_needed + max_racks_on_deck - 1) // max_racks_on_deck
        })

        if len(off_deck_racks) > 0:
            protocol.comment(f"Will perform {self.tip_management['total_batches'] - 1} tip rack batch swaps")

        return all_tip_racks

    def liquid_transfer(self, protocol, pipette, volume, source, dest,
                        asp_rate: float = 0.5, disp_rate: float = 1.0,
                        blow_out: bool = True, touch_tip: bool = False,
                        mix_before: float = 0.0, mix_after: float = 0.0,
                        mix_reps: int = 3, new_tip: bool = True,
                        drop_tip: bool = True):
        if new_tip:
            if self._check_if_swap_needed():
                self._perform_tip_rack_batch_swap(protocol)
            try:
                pipette.pick_up_tip()
                self._increment_tip_counter()
            except Exception as e:
                protocol.comment(f"Tip pickup failed with error: {e}")
                raise

        if mix_before > 0:
            pipette.mix(mix_reps, mix_before, source)

        pipette.aspirate(volume, source, rate=asp_rate)
        pipette.dispense(volume, dest, rate=disp_rate)

        if mix_after > 0:
            pipette.mix(mix_reps, mix_after, dest)

        if blow_out:
            pipette.blow_out()

        if touch_tip:
            pipette.touch_tip(radius=0.5, v_offset=-14, speed=20)

        if drop_tip:
            pipette.drop_tip()

    def get_xlsx_output(self, name: str):
        workbook = xlsxwriter.Workbook(f"{name}.xlsx")
        worksheet = workbook.add_worksheet()
        row_num = 0
        col_num = 0
        worksheet.write(row_num, col_num, "Parts in temp_module")
        row_num += 2
        for key, value in self.dict_of_parts_in_temp_mod_position.items():
            worksheet.write(row_num, col_num, key)
            worksheet.write(row_num + 1, col_num, value)
            col_num += 1
        col_num = 0
        row_num += 4
        worksheet.write(row_num, col_num, "Parts in thermocycler_module")
        row_num += 2
        for key, value in self.dict_of_parts_in_thermocycler.items():
            key_str = " + ".join(key) if isinstance(key, tuple) else str(key)
            worksheet.write(row_num, col_num, key_str)
            worksheet.write(row_num + 1, col_num, value)
            col_num += 1
        workbook.close()
        self.xlsx_output = workbook
        return self.xlsx_output

    def run(self, protocol: protocol_api.ProtocolContext):
        """Main protocol execution - uses template method pattern"""
        # Process assemblies (format-specific)
        self.process_assemblies()

        # Load hardware (shared)
        temperature_module = protocol.load_module(module_name='temperature module',
                                                  location=self.temperature_module_position)
        alum_block = temperature_module.load_labware(self.temperature_module_labware)

        thermocycler_module = protocol.load_module('thermocycler module')
        thermo_plate = thermocycler_module.load_labware(name=self.thermocycler_labware)

        all_tip_racks = self.setup_tip_management(protocol)
        pipette = protocol.load_instrument(self.pipette, self.pipette_position, tip_racks=all_tip_racks)
        if self.initial_tip:
            pipette.starting_tip = self.tip_management['on_deck_racks'][0][self.initial_tip]
            protocol.comment(f"Pipette will start from tip {self.initial_tip}")

        # Load common reagents (shared)
        dd_h2o = self._load_reagent(protocol, module_labware=alum_block, well_position=0,
                                    name='Deionized Water')
        t4_dna_ligase_buffer = self._load_reagent(protocol, module_labware=alum_block, well_position=1,
                                                  name='T4 DNA Ligase Buffer')
        t4_dna_ligase = self._load_reagent(protocol, module_labware=alum_block, well_position=2,
                                           name="T4 DNA Ligase")

        # Load parts and enzymes (format-specific)
        temp_module_well_counter = self._load_parts_and_enzymes(protocol, alum_block)

        # Setup temperatures
        thermocycler_module.open_lid()
        if not self.water_testing:
            temperature_module.set_temperature(4)
            thermocycler_module.set_block_temperature(4)

        # Media capture start
        if self.take_picture:
            self.camera.capture_picture(protocol, when="start")
        if self.take_video:
            self.camera.start_video(protocol)

        # Process assemblies (format-specific)
        volume_reagents = self.volume_restriction_enzyme + self.volume_t4_dna_ligase + self.volume_t4_dna_ligase_buffer
        thermocycler_well_counter = self._process_assembly_combinations(
            protocol, pipette, thermo_plate, alum_block, dd_h2o,
            t4_dna_ligase_buffer, t4_dna_ligase, volume_reagents,
            self.thermocycler_starting_well
        )

        protocol.comment('Take out the reagents since the temperature module will be turn off')

        # Thermocycling
        if not self.water_testing:
            thermocycler_module.close_lid()
            thermocycler_module.set_lid_temperature(42)
            temperature_module.deactivate()

        # Media capture end
        if self.take_video:
            self.camera.stop_video(protocol)
        if self.take_picture:
            self.camera.capture_picture(protocol, when="end")

        # Execute thermocycling profiles
        if not self.water_testing:
            profile = [
                {'temperature': 42, 'hold_time_minutes': 2},
                {'temperature': 16, 'hold_time_minutes': 5}
            ]
            denaturation = [
                {'temperature': 60, 'hold_time_minutes': 10},
                {'temperature': 80, 'hold_time_minutes': 10}
            ]
            thermocycler_module.execute_profile(steps=profile, repetitions=75, block_max_volume=30)
            thermocycler_module.execute_profile(steps=denaturation, repetitions=1, block_max_volume=30)
            thermocycler_module.set_block_temperature(4)

        if protocol.is_simulating():
            if self.output_xlsx:
                try:
                    if not self.protocol_name:
                        self.protocol_name = "Loop Assembly"
                    self.get_xlsx_output(self.protocol_name)
                except Exception as e:
                    protocol.comment(f"Could not create Excel file: {e}")
            # Export transformation input for next protocol (simulation only)
            try:
                self._export_transformation_input(protocol)
            except Exception as e:
                protocol.comment(f"Could not export transformation input: {e}")

        # Output results
        print('Parts and reagents in temp_module')
        print(self.dict_of_parts_in_temp_mod_position)
        print('Assembled parts in thermocycler_module')
        print(self.dict_of_parts_in_thermocycler)
        print('DNA list for transformation protocol')
        print(self.dna_list_for_transformation_protocol)

    # Helper methods (shared)
    def _export_transformation_input(self, protocol):
        """
        Export plasmid location JSON during simulation for use by transformation protocol.
        Format: { "product_uri": ["well1", "well2", ...], ... }
        """
        output_path = 'transformation_input.json'
        with open(output_path, 'w') as f:
            json.dump(self.product_uri_to_wells, f, indent=2)

        protocol.comment("\n" + "="*70)
        protocol.comment(f"Generated {output_path} for transformation protocol")
        protocol.comment(f"  Products: {len(self.product_uri_to_wells)}")
        protocol.comment("="*70)

    def _load_reagent(self, protocol, module_labware, well_position, name, description=None,
                      volume=1000, color_index=None):
        """Load a reagent or DNA part onto the temperature module."""
        well = module_labware.wells()[well_position]
        well_name = well.well_name

        if description is None:
            description = name
        if color_index is None:
            color_index = len(self.dict_of_parts_in_temp_mod_position) % len(colors)

        liquid = protocol.define_liquid(name=name, description=description,
                                        display_color=colors[color_index])
        well.load_liquid(liquid, volume=volume)

        self.dict_of_parts_in_temp_mod_position[name] = well_name
        protocol.comment(f"Loaded {name} at position {well_name}")

        return well

    def _increment_tip_counter(self):
        """Increment tip usage counter"""
        self.tip_management['tips_used'] += 1

    def _check_if_swap_needed(self):
        current_batch_tips = self.tip_management['tips_used'] % self.tip_management['tips_per_batch']
        return (current_batch_tips == 0 and
                self.tip_management['tips_used'] > 0 and
                len(self.tip_management['off_deck_racks']) > 0)

    def _perform_tip_rack_batch_swap(self, protocol):
        """Perform tip rack batch swap when current batch is exhausted"""
        available_slots = self.tip_management['available_slots']

        for rack in self.tip_management['on_deck_racks']:
            protocol.move_labware(labware=rack, new_location=protocol_api.OFF_DECK)

        remaining_racks = len(self.tip_management['off_deck_racks'])
        racks_to_move = min(len(available_slots), remaining_racks)

        new_on_deck_racks = []
        for i in range(racks_to_move):
            rack = self.tip_management['off_deck_racks'].pop(0)
            protocol.move_labware(labware=rack, new_location=available_slots[i])
            new_on_deck_racks.append(rack)

        self.tip_management['on_deck_racks'] = new_on_deck_racks
        self.tip_management['current_batch'] += 1

        protocol.comment(f"Tip rack batch {self.tip_management['current_batch']} ready!")

class Domestication(BaseAssembly):
    """
    Domestication Assembly - inserts individual parts into universal acceptor backbone.
    Each part is assembled separately with the backbone to create domesticated parts.
    """

    def __init__(self,
                 assembly_data: Optional[Dict] = None,
                 json_params: Optional[str] = None,
                 assemblies: Optional[List[Dict]] = None,
                 *args, **kwargs):
        """
        Initialize Domestication Assembly protocol.

        Args:
            assembly_data: Dict containing 'assemblies' key (new standardized approach)
            advanced_params: Optional advanced parameters
            assemblies: List of assembly dicts (backward compatibility)
            *args, **kwargs: Passed to BaseAssembly
        """
        # Handle parameter precedence: assembly_data <- assemblies kwarg
        if assembly_data is not None:
            if 'assemblies' in assembly_data:
                assemblies = assembly_data['assemblies']
            else:
                # Allow passing assemblies directly in assembly_data for flexibility
                assemblies = assembly_data

        # Validate that assemblies were provided
        if assemblies is None:
            raise ValueError("Must provide assemblies either via assembly_data or assemblies parameter")

        super().__init__(json_params=json_params, *args, **kwargs)
        self.assemblies = assemblies
        self.parts_list = []
        self.backbone = ""
        self.restriction_enzyme = ""

    def process_assemblies(self):
        """Process domestication assembly input and validate format"""
        self._reset_assembly_state()
        # Domestication should have exactly one assembly
        if len(self.assemblies) != 1:
            raise ValueError(f"Domestication supports exactly one assembly, got {len(self.assemblies)}")

        assembly = self.assemblies[0]
        required_keys = {"parts", "backbone", "restriction_enzyme"}
        assembly_keys = set(assembly.keys())

        if not required_keys.issubset(assembly_keys):
            missing_keys = required_keys - assembly_keys
            raise ValueError(f"Domestication assembly missing required keys: {missing_keys}")

        # Extract and validate parts
        parts = assembly["parts"]
        if isinstance(parts, str):
            self.parts_list = [parts]
        elif isinstance(parts, list):
            self.parts_list = parts
        else:
            raise ValueError("Parts must be a string or list of strings")

        # Extract and validate backbone (must be single value)
        backbone = assembly["backbone"]
        if isinstance(backbone, list):
            if len(backbone) > 1:
                raise ValueError("Domestication supports only one backbone")
            self.backbone = backbone[0]
        else:
            self.backbone = backbone

        # Extract and validate restriction enzyme (must be single value)
        restriction_enzyme = assembly["restriction_enzyme"]
        if isinstance(restriction_enzyme, list):
            if len(restriction_enzyme) > 1:
                raise ValueError("Domestication supports only one restriction enzyme")
            self.restriction_enzyme = restriction_enzyme[0]
        else:
            self.restriction_enzyme = restriction_enzyme

        self._validate_assembly_requirements()

    def _load_parts_and_enzymes(self, protocol, alum_block) -> int:
        """Load restriction enzyme, backbone, and parts for domestication"""
        temp_module_well_counter = 3  # Starting after common reagents (water, ligase buffer, ligase)

        # Load restriction enzyme
        self._load_reagent(protocol, module_labware=alum_block,
                           well_position=temp_module_well_counter,
                           name=f"Restriction Enzyme {self.restriction_enzyme}")
        temp_module_well_counter += 1

        # Load backbone
        self._load_reagent(protocol, module_labware=alum_block,
                           well_position=temp_module_well_counter,
                           name=f"Backbone {self.backbone}")
        temp_module_well_counter += 1

        # Load individual parts
        for part in self.parts_list:
            self._load_reagent(protocol, module_labware=alum_block,
                               well_position=temp_module_well_counter,
                               name=f"Part {part}")
            temp_module_well_counter += 1

        return temp_module_well_counter

    def _process_assembly_combinations(self, protocol, pipette, thermo_plate, alum_block,
                                       dd_h2o, t4_dna_ligase_buffer, t4_dna_ligase,
                                       volume_reagents, thermocycler_well_counter) -> int:
        """Process domestication assemblies - each part with backbone separately"""

        # Get reagent sources
        restriction_enzyme = alum_block[
            self.dict_of_parts_in_temp_mod_position[f"Restriction Enzyme {self.restriction_enzyme}"]]
        backbone_source = alum_block[self.dict_of_parts_in_temp_mod_position[f"Backbone {self.backbone}"]]

        # Process each part
        for part in self.parts_list:
            part_source = alum_block[self.dict_of_parts_in_temp_mod_position[f"Part {part}"]]

            # Process replicates for this part
            for r in range(self.replicates):
                dest_well = thermo_plate.wells()[thermocycler_well_counter]
                dest_well_name = dest_well.well_name

                # Calculate water volume (total - reagents - 2 parts: backbone + part)
                volume_dd_h20 = self.volume_total_reaction - (volume_reagents + self.volume_part * 2)

                # Add reagents
                self.liquid_transfer(protocol=protocol, pipette=pipette, volume=volume_dd_h20,
                                     source=dd_h2o, dest=dest_well,
                                     asp_rate=self.aspiration_rate, disp_rate=self.dispense_rate,
                                     touch_tip=True)

                self.liquid_transfer(protocol=protocol, pipette=pipette, volume=self.volume_t4_dna_ligase_buffer,
                                     source=t4_dna_ligase_buffer, dest=dest_well,
                                     asp_rate=self.aspiration_rate, disp_rate=self.dispense_rate,
                                     mix_before=self.volume_t4_dna_ligase_buffer, touch_tip=True)

                self.liquid_transfer(protocol=protocol, pipette=pipette, volume=self.volume_t4_dna_ligase,
                                     source=t4_dna_ligase, dest=dest_well,
                                     asp_rate=self.aspiration_rate, disp_rate=self.dispense_rate,
                                     mix_before=self.volume_t4_dna_ligase, touch_tip=True)

                self.liquid_transfer(protocol=protocol, pipette=pipette, volume=self.volume_restriction_enzyme,
                                     source=restriction_enzyme, dest=dest_well,
                                     asp_rate=self.aspiration_rate, disp_rate=self.dispense_rate,
                                     mix_before=self.volume_restriction_enzyme, touch_tip=True)

                # Add backbone
                self.liquid_transfer(protocol=protocol, pipette=pipette, volume=self.volume_part,
                                     source=backbone_source, dest=dest_well,
                                     asp_rate=self.aspiration_rate, disp_rate=self.dispense_rate,
                                     mix_before=self.volume_part, touch_tip=True)

                # Add part (don't drop tip yet)
                self.liquid_transfer(protocol=protocol, pipette=pipette, volume=self.volume_part,
                                     source=part_source, dest=dest_well,
                                     asp_rate=self.aspiration_rate, disp_rate=self.dispense_rate,
                                     mix_before=self.volume_part, touch_tip=True, drop_tip=False)

                # Remove air bubbles with mixing
                mix_volume = min(self.volume_total_reaction, pipette.max_volume)
                for _ in range(int(self.volume_total_reaction / 10)):
                    self.liquid_transfer(protocol=protocol, pipette=pipette, volume=mix_volume,
                                         source=dest_well.bottom(), dest=dest_well.bottom(8),
                                         asp_rate=1.0, disp_rate=1.0, new_tip=False, drop_tip=False,
                                         touch_tip=True)
                pipette.drop_tip()

                # Track assembly
                assembly_name = f"Part: {part}, Replicate: {r + 1}"
                self.dict_of_parts_in_thermocycler[assembly_name] = dest_well_name
                self.dna_list_for_transformation_protocol.append(f"{part}_rep{r + 1}")

                # Populate product_uri_to_wells so _export_transformation_input
                # produces a non-empty JSON for the assembly→transformation handoff
                if part not in self.product_uri_to_wells:
                    self.product_uri_to_wells[part] = []
                self.product_uri_to_wells[part].append(dest_well_name)

                thermocycler_well_counter += 1

        return thermocycler_well_counter

    def _calculate_total_tips_needed(self, number_of_constant_reagents: int = 6) -> int:
        """Calculate total tips needed for domestication

        Args:
            number_of_constant_reagents: water + ligase buffer + ligase + enzyme + backbone + part = 6
        """
        total_assemblies = len(self.parts_list) * self.replicates
        return number_of_constant_reagents * total_assemblies

    def _validate_assembly_requirements(self):
        """Validate domestication assembly requirements"""
        if not self.parts_list:
            raise ValueError("No parts provided for domestication")

        if not self.backbone:
            raise ValueError("No backbone provided for domestication")

        if not self.restriction_enzyme:
            raise ValueError("No restriction enzyme provided for domestication")

        # Calculate reagent positions: water(1) + ligase buffer(1) + ligase(1) + enzyme(1) + backbone(1) = 5
        reagent_positions = 5
        max_parts = 24 - reagent_positions

        if len(self.parts_list) > max_parts:
            raise ValueError(
                f'This protocol only supports domestication with up to {max_parts} parts. '
                f'Number of parts provided is {len(self.parts_list)}. '
                f'Parts: {self.parts_list}. '
                f'Reagent positions used: {reagent_positions}/24'
            )

        # Validate thermocycler capacity
        available_wells = 96 - self.thermocycler_starting_well
        wells_needed = len(self.parts_list) * self.replicates

        if wells_needed > available_wells:
            raise ValueError(
                f'This protocol only supports assemblies with up to {available_wells} '
                f'wells. Number of assemblies needed is {wells_needed} '
                f'({len(self.parts_list)} parts × {self.replicates} replicates).'
            )

        self._validate_reaction_volumes(num_parts=2)

    def _reset_assembly_state(self):
        """Reset assembly processing state"""
        self.parts_list = []
        self.backbone = ""
        self.restriction_enzyme = ""


class ManualLoopAssembly(BaseAssembly):
    """
    Manual/Combinatorial Loop Assembly - generates combinations from roles.
    Supports Odd/Even pattern detection for automatic enzyme selection.
    """

    def __init__(self,
                 assembly_data: Optional[Dict] = None,
                 json_params: Optional[str] = None,
                 assemblies: Optional[List[Dict]] = None,
                 *args, **kwargs):
        """
        Initialize Manual Loop Assembly protocol.

        Args:
            assembly_data: Dict containing 'assemblies' key (new standardized approach)
            json_params: Optional advanced parameters
            assemblies: List of assembly dicts (backward compatibility)
            *args, **kwargs: Passed to BaseAssembly
        """
        # Handle parameter precedence: assembly_data <- assemblies kwarg
        if assembly_data is not None:
            if 'assemblies' in assembly_data:
                assemblies = assembly_data['assemblies']
            else:
                # Allow passing assemblies directly in assembly_data for flexibility
                assemblies = assembly_data

        # Validate that assemblies were provided
        if assemblies is None:
            raise ValueError("Must provide assemblies either via assembly_data or assemblies parameter")

        super().__init__(json_params=json_params, *args, **kwargs)

        self.assemblies = assemblies
        self.pattern_odd = 'Odd*'
        self.pattern_even = 'Even*'
        self.parts_set = set()
        self.has_odd = False
        self.has_even = False
        self.odd_combinations = []
        self.even_combinations = []

    def process_assemblies(self):
        """Process manual format assemblies and generate combinations"""
        self._reset_assembly_state()

        for assembly in self.assemblies:
            assembly_type = self._get_assembly_type(assembly['receiver'])
            if assembly_type == 'odd':
                self.has_odd = True
                combos = self._generate_combinations_for_assembly(assembly)
                self.odd_combinations.extend(combos)
            if assembly_type == 'even':
                self.has_even = True
                combos = self._generate_combinations_for_assembly(assembly)
                self.even_combinations.extend(combos)

        self._validate_assembly_requirements()

    def _load_parts_and_enzymes(self, protocol, alum_block) -> int:
        """Load enzymes and parts for manual format"""
        temp_module_well_counter = 3  # Starting after common reagents

        # Load enzymes based on Odd/Even detection
        if self.has_odd:
            self._load_reagent(protocol, module_labware=alum_block,
                               well_position=temp_module_well_counter,
                               name="Restriction Enzyme BSAI")
            temp_module_well_counter += 1

        if self.has_even:
            self._load_reagent(protocol, module_labware=alum_block,
                               well_position=temp_module_well_counter,
                               name="Restriction Enzyme SAPI")
            temp_module_well_counter += 1

        # Load parts
        for part in sorted(self.parts_set):
            self._load_reagent(protocol, module_labware=alum_block,
                               well_position=temp_module_well_counter,
                               name=f"{part}")
            temp_module_well_counter += 1

        return temp_module_well_counter

    def _process_assembly_combinations(self, protocol, pipette, thermo_plate, alum_block,
                                       dd_h2o, t4_dna_ligase_buffer, t4_dna_ligase,
                                       volume_reagents, thermocycler_well_counter) -> int:
        """Process manual format combinations with automatic enzyme selection"""

        if self.has_odd:
            restriction_enzyme_bsai = alum_block[self.dict_of_parts_in_temp_mod_position["Restriction Enzyme BSAI"]]
            thermocycler_well_counter = self._process_combinations(
                protocol=protocol, pipette=pipette,
                combinations=self.odd_combinations,
                restriction_enzyme=restriction_enzyme_bsai,
                thermo_plate=thermo_plate, alum_block=alum_block,
                dd_h2o=dd_h2o, t4_dna_ligase_buffer=t4_dna_ligase_buffer,
                t4_dna_ligase=t4_dna_ligase, volume_reagents=volume_reagents,
                thermocycler_well_counter=thermocycler_well_counter
            )

        if self.has_even:
            restriction_enzyme_sapi = alum_block[self.dict_of_parts_in_temp_mod_position["Restriction Enzyme SAPI"]]
            thermocycler_well_counter = self._process_combinations(
                protocol=protocol, pipette=pipette,
                combinations=self.even_combinations,
                restriction_enzyme=restriction_enzyme_sapi,
                thermo_plate=thermo_plate, alum_block=alum_block,
                dd_h2o=dd_h2o, t4_dna_ligase_buffer=t4_dna_ligase_buffer,
                t4_dna_ligase=t4_dna_ligase, volume_reagents=volume_reagents,
                thermocycler_well_counter=thermocycler_well_counter
            )

        return thermocycler_well_counter

    def _calculate_total_tips_needed(self, number_of_constant_reagents: int = 4) -> int:
        """Calculate total tips for manual format"""
        total_combinations = len(self.odd_combinations) + len(self.even_combinations)
        reagent_tips = number_of_constant_reagents
        total_reagent_tips = reagent_tips * total_combinations * self.replicates

        total_part_tips = 0
        for combination in self.odd_combinations + self.even_combinations:
            total_part_tips += len(combination) * self.replicates

        return total_reagent_tips + total_part_tips

    # Manual format helper methods
    def _reset_assembly_state(self):
        """Reset assembly processing state"""
        self.parts_set = set()
        self.has_odd = False
        self.has_even = False
        self.odd_combinations = []
        self.even_combinations = []

    def _get_assembly_type(self, receiver_name):
        """Determine if assembly is odd, even, or neither"""
        if fnmatch(receiver_name, self.pattern_odd):
            return 'odd'
        if fnmatch(receiver_name, self.pattern_even):
            return 'even'
        raise ValueError(
            f"Assembly receiver '{receiver_name}' does not match naming convention. "
            f"Must be odd pattern '{self.pattern_odd}' or even pattern '{self.pattern_even}'. "
            f"Check receiver naming."
        )

    def _generate_combinations_for_assembly(self, assembly):
        """Generate all possible part combinations for a single assembly"""
        parts_per_role = []
        for role, parts in assembly.items():
            if isinstance(parts, str):
                parts_list = [parts]
            else:
                parts_list = list(parts)

            self.parts_set.update(parts_list)
            parts_per_role.append(parts_list)

        return list(product(*parts_per_role))

    def _validate_assembly_requirements(self):
        """Validate manual assembly requirements"""
        if not (self.has_odd or self.has_even):
            raise ValueError(
                "Assembly does not have any Even or Odd receiver. "
                "Check assembly dictionaries for Odd and Even receivers."
            )

        reagent_positions = 3 + int(self.has_odd) + int(self.has_even)
        max_parts = 24 - reagent_positions

        if len(self.parts_set) > max_parts:
            raise ValueError(
                f'This protocol only supports assemblies with up to {max_parts} parts. '
                f'Number of parts in the protocol is {len(self.parts_set)}. '
                f'Parts: {self.parts_set}. '
                f'Reagent positions used: {reagent_positions}/24'
            )

        available_wells = 96 - self.thermocycler_starting_well
        total_combinations = len(self.odd_combinations) + len(self.even_combinations)
        wells_needed = total_combinations * self.replicates

        if wells_needed > available_wells:
            raise ValueError(
                f'This protocol only supports assemblies with up to {available_wells} '
                f'combinations. Number of combinations in the protocol are {wells_needed}.'
            )

        # Validate reaction volumes for all combinations
        for combination in self.odd_combinations + self.even_combinations:
            num_parts = len(combination)
            self._validate_reaction_volumes(num_parts)

    def _process_combinations(self, protocol, pipette, combinations, restriction_enzyme,
                              thermo_plate, alum_block, dd_h2o, t4_dna_ligase_buffer,
                              t4_dna_ligase, volume_reagents, thermocycler_well_counter):
        """Process combinations with specified restriction enzyme"""

        for combination in combinations:
            for r in range(self.replicates):
                dest_well = thermo_plate.wells()[thermocycler_well_counter]
                dest_well_name = dest_well.well_name

                volume_dd_h20 = self.volume_total_reaction - (volume_reagents + self.volume_part * len(combination))

                # Add reagents
                self.liquid_transfer(protocol=protocol, pipette=pipette, volume=volume_dd_h20,
                                     source=dd_h2o, dest=dest_well,
                                     asp_rate=self.aspiration_rate, disp_rate=self.dispense_rate, touch_tip=True)

                self.liquid_transfer(protocol=protocol, pipette=pipette, volume=self.volume_t4_dna_ligase_buffer,
                                     source=t4_dna_ligase_buffer, dest=dest_well,
                                     asp_rate=self.aspiration_rate, disp_rate=self.dispense_rate,
                                     mix_before=self.volume_t4_dna_ligase_buffer, touch_tip=True)

                self.liquid_transfer(protocol=protocol, pipette=pipette, volume=self.volume_t4_dna_ligase,
                                     source=t4_dna_ligase, dest=dest_well,
                                     asp_rate=self.aspiration_rate, disp_rate=self.dispense_rate,
                                     mix_before=self.volume_t4_dna_ligase, touch_tip=True)

                self.liquid_transfer(protocol=protocol, pipette=pipette, volume=self.volume_restriction_enzyme,
                                     source=restriction_enzyme, dest=dest_well,
                                     asp_rate=self.aspiration_rate, disp_rate=self.dispense_rate,
                                     mix_before=self.volume_restriction_enzyme, touch_tip=True)

                # Add parts
                for i, part in enumerate(combination):
                    part_source = alum_block[self.dict_of_parts_in_temp_mod_position[part]]
                    if i == len(combination) - 1:  # Don't drop tip on last part
                        self.liquid_transfer(protocol=protocol, pipette=pipette, volume=self.volume_part,
                                             source=part_source, dest=dest_well,
                                             asp_rate=self.aspiration_rate, disp_rate=self.dispense_rate,
                                             mix_before=self.volume_part, touch_tip=True, drop_tip=False)
                    else:
                        self.liquid_transfer(protocol=protocol, pipette=pipette, volume=self.volume_part,
                                             source=part_source, dest=dest_well,
                                             asp_rate=self.aspiration_rate, disp_rate=self.dispense_rate,
                                             mix_before=self.volume_part, touch_tip=True)

                # Remove air bubbles
                mix_volume = min(self.volume_total_reaction, pipette.max_volume)
                for _ in range(int(self.volume_total_reaction / 10)):
                    self.liquid_transfer(protocol=protocol, pipette=pipette, volume=mix_volume,
                                         source=dest_well.bottom(), dest=dest_well.bottom(8),
                                         asp_rate=1.0, disp_rate=1.0, new_tip=False, drop_tip=False, touch_tip=True)
                pipette.drop_tip()

                # Track combination
                self.dict_of_parts_in_thermocycler[f"Replicate: {r + 1}, Combination: {combination}"] = dest_well_name
                combination_name = "_".join(combination)
                self.dna_list_for_transformation_protocol.append(f"{combination_name}_rep{r + 1}")

                # Populate product_uri_to_wells so _export_transformation_input
                # produces a non-empty JSON for the assembly→transformation handoff
                if combination_name not in self.product_uri_to_wells:
                    self.product_uri_to_wells[combination_name] = []
                self.product_uri_to_wells[combination_name].append(dest_well_name)

                thermocycler_well_counter += 1

        return thermocycler_well_counter


class SBOLLoopAssembly(BaseAssembly):
    """
    SBOL Loop Assembly - handles explicit assembly dictionaries from SBOL format.
    Each assembly dictionary represents one specific construct to build.
    """

    def __init__(self,
                 assembly_data: Optional[Dict] = None,
                 json_params: Optional[str] = None,
                 assemblies: Optional[List[Dict]] = None,
                 *args, **kwargs):
        """
        Initialize SBOL Loop Assembly protocol.

        Args:
            assembly_data: Dict containing 'assemblies' key (new standardized approach)
            advanced_params: Optional advanced parameters
            assemblies: List of assembly dicts (backward compatibility)
            *args, **kwargs: Passed to BaseAssembly
        """
        # Handle parameter precedence: assembly_data <- assemblies kwarg
        if assembly_data is not None:
            if 'assemblies' in assembly_data:
                assemblies = assembly_data['assemblies']
            else:
                # Allow passing assemblies directly in assembly_data for flexibility
                assemblies = assembly_data

        # Validate that assemblies were provided
        if assemblies is None:
            raise ValueError("Must provide assemblies either via assembly_data or assemblies parameter")

        super().__init__(json_params=json_params, *args, **kwargs)
        self.assemblies = assemblies
        self.parts_set = set()
        self.backbone_set = set()
        self.restriction_enzyme_set = set()
        self.combined_set = set()
        self.assembly_combinations = []  # SBOL assemblies are explicit, not combinatorial

    def process_assemblies(self):
        """Process SBOL format assemblies - each is explicit, no combinations needed"""
        self._reset_assembly_state()

        for assembly in self.assemblies:
            # Extract parts from PartsList
            part_names = []
            for part_uri in assembly["PartsList"]:
                part_name = self._extract_name_from_uri(part_uri)
                self.parts_set.add(part_name)
                part_names.append(part_name)

            # Extract backbone
            backbone_name = self._extract_name_from_uri(assembly["Backbone"])
            self.backbone_set.add(backbone_name)

            # Extract restriction enzyme
            enzyme_name = self._extract_name_from_uri(assembly["Restriction Enzyme"])
            self.restriction_enzyme_set.add(enzyme_name)

            # Extract product name
            product_name = self._extract_name_from_uri(assembly["Product"])
            assembly_combo = {
                'parts': [backbone_name] + part_names,  # Include backbone as first part
                'enzyme': enzyme_name,
                'product': product_name,
                'product_uri': assembly["Product"]
            }
            self.assembly_combinations.append(assembly_combo)

        self.combined_set = self.parts_set.union(self.backbone_set)
        self._validate_assembly_requirements()

    def _load_parts_and_enzymes(self, protocol, alum_block) -> int:
        """Load enzymes and parts for SBOL format"""
        temp_module_well_counter = 3  # Starting after common reagents

        # Load all unique restriction enzymes
        for enzyme_name in sorted(self.restriction_enzyme_set):
            self._load_reagent(protocol, module_labware=alum_block,
                               well_position=temp_module_well_counter,
                               name=f"Restriction Enzyme {enzyme_name}")
            temp_module_well_counter += 1

        # Load all unique parts (including backbones)
        for part in sorted(self.combined_set):
            self._load_reagent(protocol, module_labware=alum_block,
                               well_position=temp_module_well_counter,
                               name=f"{part}")
            temp_module_well_counter += 1

        return temp_module_well_counter

    def _process_assembly_combinations(self, protocol, pipette, thermo_plate, alum_block,
                                       dd_h2o, t4_dna_ligase_buffer, t4_dna_ligase,
                                       volume_reagents, thermocycler_well_counter) -> int:
        """Process SBOL assembly combinations with explicit enzyme selection"""

        for assembly_combo in self.assembly_combinations:
            for r in range(self.replicates):
                dest_well = thermo_plate.wells()[thermocycler_well_counter]
                dest_well_name = dest_well.well_name

                parts = assembly_combo['parts']
                enzyme_name = assembly_combo['enzyme']
                product_name = assembly_combo['product']

                volume_dd_h20 = self.volume_total_reaction - (volume_reagents + self.volume_part * len(parts))

                # Add reagents
                self.liquid_transfer(protocol=protocol, pipette=pipette, volume=volume_dd_h20,
                                     source=dd_h2o, dest=dest_well,
                                     asp_rate=self.aspiration_rate, disp_rate=self.dispense_rate, touch_tip=True)

                self.liquid_transfer(protocol=protocol, pipette=pipette, volume=self.volume_t4_dna_ligase_buffer,
                                     source=t4_dna_ligase_buffer, dest=dest_well,
                                     asp_rate=self.aspiration_rate, disp_rate=self.dispense_rate,
                                     mix_before=self.volume_t4_dna_ligase_buffer, touch_tip=True)

                self.liquid_transfer(protocol=protocol, pipette=pipette, volume=self.volume_t4_dna_ligase,
                                     source=t4_dna_ligase, dest=dest_well,
                                     asp_rate=self.aspiration_rate, disp_rate=self.dispense_rate,
                                     mix_before=self.volume_t4_dna_ligase, touch_tip=True)

                # Add restriction enzyme (explicit from SBOL)
                restriction_enzyme = alum_block[
                    self.dict_of_parts_in_temp_mod_position[f"Restriction Enzyme {enzyme_name}"]]
                self.liquid_transfer(protocol=protocol, pipette=pipette, volume=self.volume_restriction_enzyme,
                                     source=restriction_enzyme, dest=dest_well,
                                     asp_rate=self.aspiration_rate, disp_rate=self.dispense_rate,
                                     mix_before=self.volume_restriction_enzyme, touch_tip=True)

                # Add parts (including backbone)
                for i, part in enumerate(parts):
                    part_source = alum_block[self.dict_of_parts_in_temp_mod_position[part]]
                    if i == len(parts) - 1:  # Don't drop tip on last part
                        self.liquid_transfer(protocol=protocol, pipette=pipette, volume=self.volume_part,
                                             source=part_source, dest=dest_well,
                                             asp_rate=self.aspiration_rate, disp_rate=self.dispense_rate,
                                             mix_before=self.volume_part, touch_tip=True, drop_tip=False)
                    else:
                        self.liquid_transfer(protocol=protocol, pipette=pipette, volume=self.volume_part,
                                             source=part_source, dest=dest_well,
                                             asp_rate=self.aspiration_rate, disp_rate=self.dispense_rate,
                                             mix_before=self.volume_part, touch_tip=True)

                # Remove air bubbles
                mix_volume = min(self.volume_total_reaction, pipette.max_volume)
                for _ in range(int(self.volume_total_reaction / 10)):
                    self.liquid_transfer(protocol=protocol, pipette=pipette, volume=mix_volume,
                                         source=dest_well.bottom(), dest=dest_well.bottom(8),
                                         asp_rate=1.0, disp_rate=1.0, new_tip=False, drop_tip=False, touch_tip=True)
                pipette.drop_tip()

                # Track assembly
                self.dict_of_parts_in_thermocycler[f"Replicate: {r + 1}, Product: {product_name}"] = dest_well_name
                self.dna_list_for_transformation_protocol.append(f"{product_name}_rep{r + 1}")

                # Track URI -> well locations for transformation export
                product_uri = assembly_combo['product_uri']
                if product_uri not in self.product_uri_to_wells:
                    self.product_uri_to_wells[product_uri] = []
                self.product_uri_to_wells[product_uri].append(dest_well_name)

                thermocycler_well_counter += 1

        return thermocycler_well_counter

    def _calculate_total_tips_needed(self, number_of_constant_reagents: int = 4) -> int:
        """Calculate total tips for SBOL format"""
        total_assemblies = len(self.assembly_combinations)
        reagent_tips = number_of_constant_reagents
        total_reagent_tips = reagent_tips * total_assemblies * self.replicates

        total_part_tips = 0
        for assembly_combo in self.assembly_combinations:
            total_part_tips += len(assembly_combo['parts']) * self.replicates

        return total_reagent_tips + total_part_tips

    # SBOL format helper methods
    def _reset_assembly_state(self):
        """Reset assembly processing state"""
        self.parts_set = set()
        self.backbone_set = set()
        self.restriction_enzyme_set = set()
        self.combined_set = set()
        self.assembly_combinations = []

    def _extract_name_from_uri(self, uri: str) -> str:
        """Extract part name from SBOL URI"""
        # Extract the last segment after the last '/'
        if '/' in uri:
            name_with_version = uri.split('/')[-2]
            # Remove version number if present (e.g., "GFP/1" -> "GFP")
            if '/' in name_with_version:
                return name_with_version.split('/')[0]
            return name_with_version
        return uri

    def _validate_assembly_requirements(self):
        """Validate SBOL assembly requirements"""
        if not self.assembly_combinations:
            raise ValueError("No valid SBOL assemblies found in input.")

        # Calculate reagent positions: water(1) + ligase(1) + buffer(1) + unique enzymes
        reagent_positions = 3 + len(self.restriction_enzyme_set)
        max_parts = 24 - reagent_positions

        if len(self.combined_set) > max_parts:
            raise ValueError(
                f'This protocol only supports assemblies with up to {max_parts} parts. '
                f'Number of parts in the protocol is {len(self.combined_set)}. '
                f'Parts: {self.combined_set}. '
                f'Reagent positions used: {reagent_positions}/24'
            )

        # Validate thermocycler capacity
        available_wells = 96 - self.thermocycler_starting_well
        wells_needed = len(self.assembly_combinations) * self.replicates

        if wells_needed > available_wells:
            raise ValueError(
                f'This protocol only supports assemblies with up to {available_wells} '
                f'combinations. Number of assemblies in the protocol are {wells_needed}.'
            )

        # Validate reaction volumes for each assembly
        for assembly_combo in self.assembly_combinations:
            num_parts = len(assembly_combo['parts'])
            self._validate_reaction_volumes(num_parts)


class ManualAssembly(BaseAssembly):
    """
    Manual Golden Gate assembly protocol generator from SBOL-style JSON input.
    Produces structured reaction records and renders human-readable Markdown.
    """

    def __init__(self,
                 assembly_data: Optional[Dict] = None,
                 json_params: Optional[str] = None,
                 assemblies: Optional[List[Dict]] = None,
                 thermocycling_profile: Optional[List[Dict[str, float]]] = None,
                 thermocycling_cycles: int = 75,
                 denaturation_profile: Optional[List[Dict[str, float]]] = None,
                 hold_temperature: float = 4,
                 *args, **kwargs):
        if assembly_data is not None:
            if isinstance(assembly_data, dict) and 'assemblies' in assembly_data:
                assemblies = assembly_data['assemblies']
            else:
                assemblies = assembly_data

        if assemblies is None:
            raise ValueError("Must provide assemblies either via assembly_data or assemblies parameter")
        if not isinstance(assemblies, list) or not assemblies:
            raise ValueError("assemblies must be a non-empty list of SBOL-style assembly dictionaries")

        super().__init__(json_params=json_params, *args, **kwargs)
        self.assemblies = assemblies
        self.reaction_records: List[ManualReactionRecord] = []
        self.thermocycling_profile = thermocycling_profile or [
            {'step': 'Digest', 'temperature': 37, 'hold_time_minutes': 2},
            {'step': 'Ligate', 'temperature': 16, 'hold_time_minutes': 5},
            {'step': 'Final digestion', 'temperature': 50, 'hold_time_minutes': 5, 'cycles': 1},
            {'step': 'Heat inactivation', 'temperature': 80, 'hold_time_minutes': 10, 'cycles': 1},
            {'step': 'Hold', 'temperature': 4, 'hold_time_minutes': 'indefinite', 'cycles': 1},
        ]
        self.thermocycling_cycles = thermocycling_cycles
        self.denaturation_profile = denaturation_profile or []
        self.hold_temperature = hold_temperature

    def process_assemblies(self):
        """Parse and validate input assemblies, then build reaction records."""
        self._validate_input_assemblies()
        self.reaction_records = self._build_reaction_records()
        return self.reaction_records

    def _load_parts_and_enzymes(self, protocol, alum_block) -> int:
        raise NotImplementedError("ManualAssembly does not load reagents onto OT-2 modules.")

    def _process_assembly_combinations(self, protocol, pipette, thermo_plate, alum_block,
                                       dd_h2o, t4_dna_ligase_buffer, t4_dna_ligase,
                                       volume_reagents, thermocycler_well_counter) -> int:
        raise NotImplementedError("ManualAssembly does not generate OT-2 liquid handling commands.")

    def _calculate_total_tips_needed(self, number_of_constant_reagents: int = 0) -> int:
        return 0

    def _validate_input_assemblies(self):
        required_keys = {'Product', 'Backbone', 'PartsList', 'Restriction Enzyme'}

        for idx, assembly in enumerate(self.assemblies, start=1):
            if not isinstance(assembly, dict):
                raise ValueError(f"Assembly #{idx} is not a dictionary.")

            missing = required_keys - set(assembly.keys())
            if missing:
                raise ValueError(
                    f"Assembly #{idx} is missing required keys: {sorted(missing)}. "
                    f"Expected keys: {sorted(required_keys)}"
                )

            if not isinstance(assembly['PartsList'], list) or not assembly['PartsList']:
                raise ValueError(f"Assembly #{idx} has an invalid 'PartsList'. Expected a non-empty list.")

    def _extract_name_from_uri(self, value) -> str:
        """Extract human-readable names from dictionaries, URIs, or plain values."""
        if isinstance(value, dict):
            for key in ("displayId", "display_id", "name", "label"):
                if value.get(key):
                    return value[key]
        uri = self._extract_uri(value) or value
        if not uri:
            return "Unknown"
        segments = [segment for segment in str(uri).rstrip('/').split('/') if segment]
        if len(segments) >= 2 and segments[-1].isdigit():
            return segments[-2]
        return segments[-1] if segments else "Unknown"

    def _extract_uri(self, value) -> Optional[str]:
        if isinstance(value, dict):
            for key in (
                "Implementation",
                "implementation",
                "implementation_uri",
                "implementationUri",
                "Implementation URI",
                "uri",
                "URI",
                "identity",
            ):
                if value.get(key):
                    return value[key]
            return None
        if isinstance(value, str) and value.startswith(("http://", "https://")):
            return value
        return None

    def _markdown_link(self, label: str, uri: Optional[str]) -> str:
        if not uri:
            return label
        escaped_label = str(label).replace("[", "\\[").replace("]", "\\]")
        escaped_uri = str(uri).replace(")", "%29").replace(" ", "%20")
        return f"[{escaped_label}]({escaped_uri})"

    def _calculate_reaction_volumes(self, number_of_dna_components: int) -> Dict[str, float]:
        total_dna_volume = number_of_dna_components * self.volume_part
        fixed_reagent_volume = (
            self.volume_restriction_enzyme +
            self.volume_t4_dna_ligase +
            self.volume_t4_dna_ligase_buffer
        )
        water_volume = self.volume_total_reaction - fixed_reagent_volume - total_dna_volume

        if water_volume < 0:
            raise ValueError(
                f"Reaction volume error: Cannot fit {number_of_dna_components} DNA components into "
                f"{self.volume_total_reaction}µL reaction.\n"
                f"  Required volumes:\n"
                f"    - DNA ({number_of_dna_components} × {self.volume_part}µL): {total_dna_volume}µL\n"
                f"    - Restriction enzyme: {self.volume_restriction_enzyme}µL\n"
                f"    - T4 DNA ligase: {self.volume_t4_dna_ligase}µL\n"
                f"    - T4 DNA ligase buffer: {self.volume_t4_dna_ligase_buffer}µL\n"
                f"  Total required: {total_dna_volume + fixed_reagent_volume}µL"
            )

        return {
            'total_dna_volume': total_dna_volume,
            'fixed_reagent_volume': fixed_reagent_volume,
            'water_volume': water_volume
        }

    def _build_reaction_records(self) -> List[ManualReactionRecord]:
        records: List[ManualReactionRecord] = []
        for assembly in self.assemblies:
            product_uri = self._extract_uri(assembly["Product"]) or str(assembly["Product"])
            backbone_uri = self._extract_uri(assembly["Backbone"]) or str(assembly["Backbone"])
            part_uris = assembly["PartsList"]
            enzyme_uri = self._extract_uri(assembly["Restriction Enzyme"]) or str(assembly["Restriction Enzyme"])

            product_name = self._extract_name_from_uri(product_uri)
            backbone_name = self._extract_name_from_uri(backbone_uri)
            part_names = [self._extract_name_from_uri(uri) for uri in part_uris]
            enzyme_name = self._extract_name_from_uri(enzyme_uri)

            number_of_dna_components = 1 + len(part_uris)
            volume_data = self._calculate_reaction_volumes(number_of_dna_components)

            reagent_additions = [
                {'name': 'nuclease-free water', 'volume_uL': self._fmt_volume(volume_data['water_volume'])},
                {'name': 'T4 DNA ligase buffer', 'volume_uL': self._fmt_volume(self.volume_t4_dna_ligase_buffer)},
                {'name': 'T4 DNA Ligase', 'volume_uL': self._fmt_volume(self.volume_t4_dna_ligase)},
                {'name': f"{enzyme_name} restriction enzyme", 'volume_uL': self._fmt_volume(self.volume_restriction_enzyme)},
                {'name': backbone_name, 'volume_uL': self._fmt_volume(self.volume_part), 'uri': backbone_uri},
            ]

            for part_uri, part_name in zip(part_uris, part_names):
                reagent_additions.append({
                    'name': part_name,
                    'volume_uL': self._fmt_volume(self.volume_part),
                    'uri': self._extract_uri(part_uri)
                })

            record = ManualReactionRecord(
                product_uri=product_uri,
                product_name=product_name,
                backbone_uri=backbone_uri,
                backbone_name=backbone_name,
                part_uris=part_uris,
                part_names=part_names,
                restriction_enzyme_uri=enzyme_uri,
                restriction_enzyme_name=enzyme_name,
                number_of_dna_components=number_of_dna_components,
                total_dna_volume=volume_data['total_dna_volume'],
                fixed_reagent_volume=volume_data['fixed_reagent_volume'],
                water_volume=volume_data['water_volume'],
                total_reaction_volume=self.volume_total_reaction,
                reagent_additions=reagent_additions
            )
            records.append(record)

        return records

    def _fmt_volume(self, value: float) -> str:
        return f"{int(value)}" if float(value).is_integer() else f"{value:.2f}"

    def _render_thermocycling_section(self) -> List[str]:
        lines = [
            "## Thermocycler Program",
            "",
            "| Step | Temperature | Time | Cycles |",
            "| --- | --- | --- | ---: |",
        ]
        total_steps = len(self.thermocycling_profile)
        for index, step in enumerate(self.thermocycling_profile, start=1):
            time_value = step['hold_time_minutes']
            time_text = f"{time_value} min" if isinstance(time_value, (int, float)) else str(time_value)
            step_name = step.get('step') or f"Step {index}"
            if 'cycles' in step:
                cycles = step['cycles']
            elif total_steps >= 2 and index <= 2:
                cycles = self.thermocycling_cycles
            else:
                cycles = 1
            lines.append(f"| {step_name} | {step['temperature']} C | {time_text} | {cycles} |")
        lines.append("")
        return lines

    def render_markdown(self) -> str:
        """Render a complete manual protocol in Markdown format."""
        if not self.reaction_records:
            self.process_assemblies()

        lines = [
            "# Manual Golden Gate Assembly Protocol",
            "",
            "## Overview",
            "Golden Gate assembly is a one-pot DNA cloning method that uses a Type IIS restriction enzyme, "
            "such as BsaI, together with DNA ligase to assemble multiple DNA fragments in a predefined order.",
            "Because Type IIS enzymes cut outside their recognition sites, they generate custom overhangs that "
            "direct fragment assembly and allow the recognition sites to be removed from the final construct.",
            "In this protocol, plasmids containing DNA parts and a destination backbone are combined with the "
            "restriction enzyme and ligase in a single tube, then cycled in a thermocycler between digestion and "
            "ligation temperatures. Repetition of these cycles enriches for the correctly assembled composite "
            "plasmid, after which the enzymes are heat-inactivated and the reaction is held at 4 °C until collection.",
            "",
            "## Reaction Setup",
            "",
            f"- Total reaction volume: {self._fmt_volume(self.volume_total_reaction)} uL",
            f"- DNA input volume: {self._fmt_volume(self.volume_part)} uL per backbone or part",
            f"- Assemblies: {len(self.reaction_records)}",
        ]
        lines.append("")

        for index, record in enumerate(self.reaction_records, start=1):
            lines.extend(
                [
                    f"## Assembly {index}: {record.product_name}",
                    "",
                    "| Reagent | Volume (uL) |",
                    "| --- | ---: |",
                ]
            )
            for reagent in record.reagent_additions:
                lines.append(
                    f"| {self._markdown_link(reagent['name'], reagent.get('uri'))} | {reagent['volume_uL']} |"
                )
            lines.extend(
                [
                    "",
                    "1. Add reagents to a PCR tube or thermocycler plate well in the order listed.",
                    "2. Mix gently by pipetting, then briefly spin down.",
                    "3. Run the thermocycler program below.",
                    "",
                ]
            )

        lines.extend(self._render_thermocycling_section())
        lines.extend([
            "## Notes",
            "- Thermocylcer iterations can be increased to improve the reaction efficiency.",
            "- Assumes all DNA parts are available at suitable concentrations and added at equal molarity. Suggested molarities are 20 fmol/µL for parts and 10 fmol/µL for backbones.",
            "- Store the assembly product at 4 °C for better stability until used for downstream applications.",
            "- Validate assembled plasmids by restriction digest and gel electrophoresis, Sanger sequencing, or whole-plasmid sequencing."
        ])

        return "\n".join(lines) + "\n"

    def write_markdown(self, output_path: str):
        """Write rendered Markdown protocol to disk."""
        markdown = self.render_markdown()
        with open(output_path, "w", encoding="utf-8") as file_handle:
            file_handle.write(markdown)


class LoopAssembly:
    """
    Factory class that auto-detects input format and returns appropriate subclass.
    Supports both manual/combinatorial and SBOL format assemblies.
    """

    def __new__(cls, assemblies: List[Dict], *args, **kwargs):
        """Factory method that detects format and returns appropriate instance"""
        if not assemblies:
            raise ValueError("No assemblies provided")

        # Detect format based on first assembly
        first_assembly = assemblies[0]

        if cls._is_sbol_format(first_assembly):
            print("Detected SBOL format - using SBOLLoopAssembly")
            return SBOLLoopAssembly(assemblies, *args, **kwargs)
        elif cls._is_manual_format(first_assembly):
            print("Detected Manual format - using ManualLoopAssembly")
            return ManualLoopAssembly(assemblies, *args, **kwargs)
        else:
            raise ValueError(
                f"Unknown assembly format. Assembly must contain either:\n"
                f"- SBOL format: 'Product', 'Backbone', 'PartsList', 'Restriction Enzyme'\n"
                f"- Manual format: 'receiver' and role keys like 'promoter', 'rbs', etc.\n"
                f"Found keys: {list(first_assembly.keys())}"
            )

    @staticmethod
    def _is_sbol_format(assembly: Dict) -> bool:
        """Check if assembly matches SBOL format"""
        sbol_keys = {'Product', 'Backbone', 'PartsList', 'Restriction Enzyme'}
        assembly_keys = set(assembly.keys())

        # Check for SBOL-specific keys
        has_sbol_keys = sbol_keys.issubset(assembly_keys)

        # Check for URI patterns (https://)
        has_uri_patterns = any(
            isinstance(v, str) and v.startswith('https://')
            for v in assembly.values()
        ) or any(
            isinstance(v, list) and any(
                isinstance(item, str) and item.startswith('https://')
                for item in v
            )
            for v in assembly.values()
        )

        return has_sbol_keys and has_uri_patterns

    @staticmethod
    def _is_manual_format(assembly: Dict) -> bool:
        """Check if assembly matches manual/combinatorial format"""
        # Must have 'receiver' key
        if 'receiver' not in assembly:
            return False

        # Should have role-based keys (not SBOL keys)
        sbol_keys = {'Product', 'Backbone', 'PartsList', 'Restriction Enzyme'}
        assembly_keys = set(assembly.keys())

        # Should not have SBOL keys
        has_sbol_keys = bool(sbol_keys.intersection(assembly_keys))

        # Should have role keys beyond 'receiver'
        role_keys = assembly_keys - {'receiver'}
        has_role_keys = len(role_keys) > 0

        return not has_sbol_keys and has_role_keys

# Default assemblies for testing
DEFAULT_DOMESTICATION_ASSEMBLY = [
    {"parts": ["part1", "part2"], "backbone": "acceptor", "restriction_enzyme": "BsaI"},
]

DEFAULT_MANUAL_ASSEMBLIES = [
    {"promoter": ["GVP0008"], "rbs": "B0034",
     "cds": "sfGFP", "terminator": "B0015", "receiver": "Odd_1"}
]

DEFAULT_SBOL_ASSEMBLIES = [
    {
        "Product": "https://SBOL2Build.org/composite_1/1",
        "Backbone": "https://sbolcanvas.org/Cir_qxow/1",
        "PartsList": [
            "https://sbolcanvas.org/GFP/1",
            "https://sbolcanvas.org/B0015/1",
            "https://sbolcanvas.org/J23101/1",
            "https://sbolcanvas.org/B0034/1"
        ],
        "Restriction Enzyme": "https://SBOL2Build.org/BsaI/1"
    }
]
