from abc import ABC, abstractmethod
from opentrons import protocol_api
from typing import List, Dict, Optional
import xlsxwriter
from pudu.utils import SmartPipette, Camera, colors

class BaseCalibration(ABC):
    """
    Abstract base class for calibration protocols.
    Contains shared hardware setup, liquid handling, and serial dilution functionality.
    Reference: `iGEM 2022 InterLab Calibration Protocol
    <https://old.igem.org/wiki/images/a/a4/InterLab_2022_-_Calibration_Protocol_v2.pdf>`_
    """

    def __init__(self,
                 aspiration_rate: float = 0.5,
                 dispense_rate: float = 1.0,
                 tiprack_labware: str = 'opentrons_96_tiprack_300ul',
                 tiprack_position: str = '9',
                 pipette: str = 'p300_single_gen2',
                 pipette_position: str = 'left',
                 calibration_plate_labware: str = 'corning_96_wellplate_360ul_flat',
                 calibration_plate_position: str = '7',
                 tube_rack_labware: str = 'opentrons_24_aluminumblock_nest_1.5ml_snapcap',
                 tube_rack_position: str = '1',
                 use_falcon_tubes: bool = False,
                 falcon_tube_rack_labware: str = 'opentrons_6_tuberack_falcon_50ml_conical',
                 falcon_tube_rack_position: str = '2',
                 take_picture: bool = False,
                 take_video: bool = False,
                 water_testing: bool = False):
        """
        Initialize shared calibration protocol parameters.

        Args:
            aspiration_rate: Aspiration speed as a fraction of the pipette's
                maximum flow rate (``1.0`` = full speed). Lower values reduce
                bubble formation with viscous calibrants.
            dispense_rate: Dispense speed as a fraction of the pipette's maximum
                flow rate.
            tiprack_labware: Opentrons labware definition string for the tip rack.
            tiprack_position: Deck slot string for the tip rack.
            pipette: Opentrons pipette model string (e.g. ``'p300_single_gen2'``).
            pipette_position: Mount side for the pipette (``'left'`` or ``'right'``).
            calibration_plate_labware: Opentrons labware definition string for the
                96-well calibration plate where serial dilutions are performed.
            calibration_plate_position: Deck slot string for the calibration plate.
            tube_rack_labware: Opentrons labware definition string for the 24-well
                aluminum block / tube rack holding calibrant stocks and buffers.
            tube_rack_position: Deck slot string for the tube rack.
            use_falcon_tubes: If ``True``, PBS and water buffers are sourced from
                50 mL Falcon tubes instead of 1.5 mL microtubes. Enables the
                ``SmartPipette`` conical-tube height calculation for accurate
                aspiration as the tube empties.
            falcon_tube_rack_labware: Opentrons labware definition string for the
                Falcon tube rack. Only used when ``use_falcon_tubes=True``.
            falcon_tube_rack_position: Deck slot string for the Falcon tube rack.
            take_picture: If ``True``, capture an image at the start and end of
                the protocol.
            take_video: If ``True``, record video for the duration of the protocol.
            water_testing: If ``True``, skip any steps that require real reagents
                (reserved for future dry-run support; not fully implemented in all
                subclasses).
        """
        self.aspiration_rate = aspiration_rate
        self.dispense_rate = dispense_rate
        self.tiprack_labware = tiprack_labware
        self.tiprack_position = tiprack_position
        self.pipette = pipette
        self.pipette_position = pipette_position
        self.calibration_plate_labware = calibration_plate_labware
        self.calibration_plate_position = calibration_plate_position
        self.tube_rack_labware = tube_rack_labware
        self.tube_rack_position = tube_rack_position
        self.use_falcon_tubes = use_falcon_tubes
        self.falcon_tube_rack_labware = falcon_tube_rack_labware
        self.falcon_tube_rack_position = falcon_tube_rack_position
        self.take_picture = take_picture
        self.take_video = take_video
        self.water_testing = water_testing

        # Shared tracking
        self.calibrant_positions = {}
        self.buffer_positions = {}
        self.camera = Camera()
        self.smart_pipette = None

    @abstractmethod
    def _get_calibrant_layout(self) -> Dict:
        """Return the specific calibrant layout for this protocol"""
        pass

    @abstractmethod
    def _load_calibrants(self, protocol, tube_rack) -> None:
        """Load calibrants specific to this protocol"""
        pass

    @abstractmethod
    def _dispense_initial_calibrants(self, protocol, pipette, plate) -> None:
        """Dispense initial calibrants to starting positions"""
        pass

    @abstractmethod
    def _perform_serial_dilutions(self, protocol, pipette, plate) -> None:
        """Perform serial dilutions specific to this protocol"""
        pass

    def _define_and_load_liquid(self, protocol, well, name: str, description: str = None,
                                volume: float = 1000, color_index: int = None):
        """Define liquid and load it into specified well"""
        if description is None:
            description = name
        if color_index is None:
            color_index = len(self.calibrant_positions) % len(colors)

        liquid = protocol.define_liquid(
            name=name,
            description=description,
            display_color=colors[color_index]
        )
        well.load_liquid(liquid, volume=volume)
        protocol.comment(f"Loaded {name} at position {well.well_name}")
        return well

    def _setup_hardware(self, protocol):
        """Setup shared hardware components"""
        tiprack = protocol.load_labware(self.tiprack_labware, self.tiprack_position)
        pipette = protocol.load_instrument(self.pipette, self.pipette_position, tip_racks=[tiprack])
        self.smart_pipette = SmartPipette(pipette, protocol)
        plate = protocol.load_labware(self.calibration_plate_labware, self.calibration_plate_position)
        tube_rack = protocol.load_labware(self.tube_rack_labware, self.tube_rack_position)

        falcon_tube_rack = None
        if self.use_falcon_tubes:
            falcon_tube_rack = protocol.load_labware(
                self.falcon_tube_rack_labware,
                self.falcon_tube_rack_position
            )

        return pipette, plate, tube_rack, falcon_tube_rack

    def _load_dilution_buffers(self, protocol, tube_rack, falcon_tube_rack) -> Dict:
        """Load PBS and water buffers with falcon tube remapping if needed"""
        buffers = {}

        if self.use_falcon_tubes and falcon_tube_rack:
            # Use falcon tubes with liquid definition
            pbs_falcon = self._define_and_load_liquid(
                protocol, falcon_tube_rack['A1'], "PBS Buffer",
                "Phosphate Buffered Saline for dilutions", volume=15000, color_index=0
            )
            water_falcon = self._define_and_load_liquid(
                protocol, falcon_tube_rack['A2'], "Deionized Water",
                "Deionized Water for dilutions", volume=15000, color_index=1
            )
            buffers['pbs_sources'] = [pbs_falcon, pbs_falcon]
            buffers['water_sources'] = [water_falcon, water_falcon]
        else:
            # Use individual tubes with liquid definition
            pbs_1 = self._define_and_load_liquid(
                protocol, tube_rack['A3'], "PBS Buffer 1", volume=1000, color_index=0
            )
            pbs_2 = self._define_and_load_liquid(
                protocol, tube_rack['A4'], "PBS Buffer 2", volume=1000, color_index=0
            )
            water_1 = self._define_and_load_liquid(
                protocol, tube_rack['A5'], "Deionized Water 1", volume=1000, color_index=1
            )
            water_2 = self._define_and_load_liquid(
                protocol, tube_rack['A6'], "Deionized Water 2", volume=1000, color_index=1
            )
            buffers['pbs_sources'] = [pbs_1, pbs_2]
            buffers['water_sources'] = [water_1, water_2]

        self.buffer_positions = buffers
        return buffers

    def _dispense_dilution_buffers(self, protocol, pipette, plate, buffers, wells_layout):
        """Dispense PBS and water to designated wells"""
        # Dispense PBS
        pipette.pick_up_tip()
        for wells_range, source_idx in wells_layout['pbs']:
            target_wells = plate.wells()[wells_range[0]:wells_range[1]]
            source = buffers['pbs_sources'][source_idx]
            use_conical = self.use_falcon_tubes  # Enable conical tube handling for falcon tubes

            for well in target_wells:
                self.smart_pipette.liquid_transfer(
                    volume=100, source=source, destination=well,
                    asp_rate=self.aspiration_rate, disp_rate=self.dispense_rate,
                    new_tip=False, drop_tip=False, use=use_conical
                )
        pipette.drop_tip()

        # Dispense water
        pipette.pick_up_tip()
        for wells_range, source_idx in wells_layout['water']:
            target_wells = plate.wells()[wells_range[0]:wells_range[1]]
            source = buffers['water_sources'][source_idx]
            use_conical = self.use_falcon_tubes  # Enable conical tube handling for falcon tubes

            for well in target_wells:
                self.smart_pipette.liquid_transfer(
                    volume=100, source=source, destination=well,
                    asp_rate=self.aspiration_rate, disp_rate=self.dispense_rate,
                    new_tip=False, drop_tip=False, use=use_conical
                )
        pipette.drop_tip()

    def run(self, protocol: protocol_api.ProtocolContext):
        """Main protocol execution using template method pattern"""
        # Setup hardware
        pipette, plate, tube_rack, falcon_tube_rack = self._setup_hardware(protocol)

        # Load calibrants (protocol-specific)
        self._load_calibrants(protocol, tube_rack)

        # Load dilution buffers
        buffers = self._load_dilution_buffers(protocol, tube_rack, falcon_tube_rack)

        # Get layout for this specific protocol
        layout = self._get_calibrant_layout()

        # Media capture start
        if self.take_picture:
            self.camera.capture_picture(protocol, when="start")
        if self.take_video:
            self.camera.start_video(protocol)

        # Dispense dilution buffers
        self._dispense_dilution_buffers(protocol, pipette, plate, buffers, layout)

        # Dispense initial calibrants (protocol-specific)
        self._dispense_initial_calibrants(protocol, pipette, plate)

        # Perform serial dilutions (protocol-specific)
        self._perform_serial_dilutions(protocol, pipette, plate)

        # Media capture end
        if self.take_video:
            self.camera.stop_video(protocol)
        if self.take_picture:
            self.camera.capture_picture(protocol, when="end")

class GFPODCalibration(BaseCalibration):
    """
    GFP and OD600 calibration using fluorescein and nanoparticles.
    Based on iGEM 2022 calibration protocol.
    """

    def _get_calibrant_layout(self) -> Dict:
        """Layout for GFP/OD600 calibration (2 calibrants, 2 replicates each)"""
        return {
            'pbs': [((1, 12), 0), ((13, 24), 1)],  # (well_range, source_index)
            'water': [((25, 36), 0), ((37, 48), 1)],
            'calibrants': {
                'fluorescein': ['A1', 'B1'],
                'microspheres': ['C1', 'D1']
            },
            'dilution_series': [
                (0, 11),  # Row A fluorescein
                (12, 23),  # Row B fluorescein
                (24, 35),  # Row C microspheres
                (36, 47)  # Row D microspheres
            ]
        }

    def _load_calibrants(self, protocol, tube_rack) -> None:
        """Load fluorescein and microspheres"""
        fluorescein_well = self._define_and_load_liquid(
            protocol, tube_rack['A1'], "Fluorescein 1x",
            "Fluorescein calibration standard", volume=1000, color_index=2
        )
        microspheres_well = self._define_and_load_liquid(
            protocol, tube_rack['A2'], "Microspheres 1x",
            "Silica nanoparticles for OD600 calibration", volume=1000, color_index=3
        )

        self.calibrant_positions['fluorescein_1x'] = fluorescein_well
        self.calibrant_positions['microspheres_1x'] = microspheres_well

    def _dispense_initial_calibrants(self, protocol, pipette, plate) -> None:
        """Dispense fluorescein and microspheres to starting wells"""
        # Fluorescein to A1, B1
        for well_name in ['A1', 'B1']:
            self.smart_pipette.liquid_transfer(
                volume=200, source=self.calibrant_positions['fluorescein_1x'],
                destination=plate[well_name], asp_rate=self.aspiration_rate,
                disp_rate=self.dispense_rate, mix_before=200, mix_reps=4
            )

        # Microspheres to C1, D1
        for well_name in ['C1', 'D1']:
            self.smart_pipette.liquid_transfer(
                volume=200, source=self.calibrant_positions['microspheres_1x'],
                destination=plate[well_name], asp_rate=self.aspiration_rate,
                disp_rate=self.dispense_rate, mix_before=200, mix_reps=4
            )

    def _perform_serial_dilutions(self, protocol, pipette, plate) -> None:
        """Perform 1:2 serial dilutions for fluorescein and microspheres"""
        layout = self._get_calibrant_layout()

        for start_idx, end_idx in layout['dilution_series']:
            pipette.pick_up_tip()
            for i in range(start_idx, end_idx):
                source_well = plate.wells()[i]
                dest_well = plate.wells()[i + 1]
                self.smart_pipette.liquid_transfer(
                    volume=100, source=source_well, destination=dest_well,
                    asp_rate=self.aspiration_rate, disp_rate=self.dispense_rate,
                    mix_before=200, mix_reps=4, new_tip=False, drop_tip=False
                )
            pipette.drop_tip()


class RGBODCalibration(BaseCalibration):
    """
    RGB and OD600 calibration using fluorescein, sulforhodamine 101, cascade blue, and nanoparticles.
    Extended iGEM calibration protocol.
    """

    def _get_calibrant_layout(self) -> Dict:
        """Layout for RGB/OD600 calibration (4 calibrants, 2 replicates each)"""
        return {
            'pbs': [((1, 12), 0), ((13, 24), 1), ((25, 36), 2), ((37, 48), 3)],
            'water': [((49, 60), 0), ((61, 72), 1), ((73, 84), 2), ((85, 96), 3)],
            'calibrants': {
                'fluorescein': ['A1', 'B1'],
                'sulforhodamine': ['C1', 'D1'],
                'cascade_blue': ['E1', 'F1'],
                'microspheres': ['G1', 'H1']
            },
            'dilution_series': [
                (0, 10),  # Row A fluorescein (to well 11, discard to binit)
                (12, 22),  # Row B fluorescein
                (24, 34),  # Row C sulforhodamine
                (36, 46),  # Row D sulforhodamine
                (48, 58),  # Row E cascade blue
                (60, 70),  # Row F cascade blue
                (72, 82),  # Row G microspheres (to well 83, discard to binit)
                (84, 94)  # Row H microspheres
            ]
        }

    def _load_calibrants(self, protocol, tube_rack) -> None:
        """Load all RGB calibrants and microspheres"""
        sulforhodamine_well = self._define_and_load_liquid(
            protocol, tube_rack['A1'], "Sulforhodamine 101 1x",
            "Sulforhodamine 101 red fluorescent calibrant", volume=1000, color_index=2
        )
        fluorescein_well = self._define_and_load_liquid(
            protocol, tube_rack['B1'], "Fluorescein 1x",
            "Fluorescein green fluorescent calibrant", volume=1000, color_index=3
        )
        cascade_blue_well = self._define_and_load_liquid(
            protocol, tube_rack['C1'], "Cascade Blue 1x",
            "Cascade Blue blue fluorescent calibrant", volume=1000, color_index=4
        )
        microspheres_well = self._define_and_load_liquid(
            protocol, tube_rack['D1'], "Microspheres 1x",
            "Silica nanoparticles for OD600 calibration", volume=1000, color_index=5
        )
        binit_well = self._define_and_load_liquid(
            protocol, tube_rack['A6'], "Waste Container",
            "Container for waste disposal", volume=0, color_index=6
        )

        self.calibrant_positions.update({
            'sulforhodamine_1x': sulforhodamine_well,
            'fluorescein_1x': fluorescein_well,
            'cascade_blue_1x': cascade_blue_well,
            'microspheres_1x': microspheres_well,
            'binit': binit_well
        })

    def _load_dilution_buffers(self, protocol, tube_rack, falcon_tube_rack) -> Dict:
        """Extended buffer loading for RGB protocol"""
        buffers = {}

        if self.use_falcon_tubes and falcon_tube_rack:
            # Use falcon tubes for all buffers
            pbs_falcon = falcon_tube_rack['A1']
            water_falcon = falcon_tube_rack['A2']
            buffers['pbs_sources'] = [pbs_falcon] * 8
            buffers['water_sources'] = [water_falcon] * 8
        else:
            # Use individual tubes
            buffers['pbs_sources'] = [
                tube_rack['A2'], tube_rack['B2'], tube_rack['C2'], tube_rack['D2'],
                tube_rack['A3'], tube_rack['B3'], tube_rack['C3'], tube_rack['D3']
            ]
            buffers['water_sources'] = [
                tube_rack['A4'], tube_rack['B4'], tube_rack['C4'], tube_rack['D4'],
                tube_rack['A5'], tube_rack['B5'], tube_rack['C5'], tube_rack['D5']
            ]

        self.buffer_positions = buffers
        return buffers

    def _dispense_initial_calibrants(self, protocol, pipette, plate) -> None:
        """Dispense all RGB calibrants to starting wells"""
        mix_vol = 100
        mix_reps = 3

        calibrants_wells = [
            ('fluorescein_1x', ['A1', 'B1']),
            ('sulforhodamine_1x', ['C1', 'D1']),
            ('cascade_blue_1x', ['E1', 'F1']),
            ('microspheres_1x', ['G1', 'H1'])
        ]

        for calibrant, well_names in calibrants_wells:
            for well_name in well_names:
                self.smart_pipette.liquid_transfer(
                    volume=200, source=self.calibrant_positions[calibrant],
                    destination=plate[well_name], asp_rate=self.aspiration_rate,
                    disp_rate=self.dispense_rate, mix_before=mix_vol, mix_reps=mix_reps
                )

    def _perform_serial_dilutions(self, protocol, pipette, plate) -> None:
        """Perform 1:2 serial dilutions with waste disposal"""
        layout = self._get_calibrant_layout()
        mix_vol = 100
        mix_reps = 3
        binit = self.calibrant_positions['binit']

        for start_idx, end_idx in layout['dilution_series']:
            pipette.pick_up_tip()

            # Serial dilutions
            for i in range(start_idx, end_idx):
                source_well = plate.wells()[i]
                dest_well = plate.wells()[i + 1]
                self.smart_pipette.liquid_transfer(
                    volume=100, source=source_well, destination=dest_well,
                    asp_rate=self.aspiration_rate, disp_rate=self.dispense_rate,
                    mix_before=mix_vol, mix_reps=mix_reps, new_tip=False, drop_tip=False
                )

            # Discard final dilution to binit
            final_well = plate.wells()[end_idx]
            self.smart_pipette.liquid_transfer(
                volume=100, source=final_well, destination=binit,
                asp_rate=self.aspiration_rate, disp_rate=self.dispense_rate,
                mix_before=mix_vol, mix_reps=mix_reps, new_tip=False, drop_tip=False
            )
            pipette.drop_tip()

        # Fill all wells to 200 µL with appropriate buffers
        self._fill_wells_to_200ul(protocol, pipette, plate)

    def _fill_wells_to_200ul(self, protocol, pipette, plate) -> None:
        """Add additional 100 µL to all wells to reach 200 µL final volume"""
        layout = self._get_calibrant_layout()
        buffers = self.buffer_positions
        use_conical = self.use_falcon_tubes  # Enable conical tube handling for falcon tubes

        # Add PBS to calibrant wells
        pipette.pick_up_tip()
        for wells_range, source_idx in layout['pbs']:
            target_wells = plate.wells()[wells_range[0]:wells_range[1]]
            source = buffers['pbs_sources'][source_idx]
            for well in target_wells:
                self.smart_pipette.liquid_transfer(
                    protocol, pipette, 100, source, well,
                    new_tip=False, drop_tip=False, use=use_conical
                )
        pipette.drop_tip()

        # Add water to blank wells
        pipette.pick_up_tip()
        for wells_range, source_idx in layout['water']:
            target_wells = plate.wells()[wells_range[0]:wells_range[1]]
            source = buffers['water_sources'][source_idx]
            for well in target_wells:
                self.smart_pipette.liquid_transfer(
                    protocol, pipette, 100, source, well,
                    new_tip=False, drop_tip=False, use=use_conical
                )
        pipette.drop_tip()