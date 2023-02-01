from opentrons import protocol_api
from utils import thermo_wells, temp_wells

class igem_gfp_od():
    '''
    Creates a ptopocol to calibrate GFP using fluorescein (MEFL) and OD600 using nanoparticles.
    Refer to: https://old.igem.org/wiki/images/a/a4/InterLab_2022_-_Calibration_Protocol_v2.pdf

    Attributes
    ----------   
    fluorescein_concentration: float
        Concentration of fluorescein in uM. By default 10 micro molar (uM).
    aspiration_rate: float
        Aspiration rate in micro liters per second (uL/s). By default 0.5 uL/s.
    '''
    def __init__(self, 
                aspiration_rate:float=0.5,
                tiprack_labware:str='opentrons_96_tiprack_300ul',
                tiprack_position:int=9,
                pipette:str='p300_single_gen2',
                pipette_position:str='left',
                calibration_plate_labware:str='corning_96_wellplate_360ul_flat',
                calibration_plate_position:int=7,
                use_temperature_module:bool=True,
                tube_rack_labware:str='opentrons_24_aluminumblock_nest_1.5ml_snapcap',
                tube_rack_position:int=1,
                use_falcon_tubes:bool=False,
                falcon_tube_rack_labware:str='opentrons_6_tuberack_falcon_50ml_conical',
                falcon_tube_rack_position:int=2,


                ):
        self.aspiration_rate = aspiration_rate
        self.tiprack_labware = tiprack_labware
        self.tiprack_position = tiprack_position
        self.pipette = pipette
        self.pipette_position = pipette_position
        self.calibration_plate_labware = calibration_plate_labware
        self.calibration_plate_position = calibration_plate_position
        self.use_temperature_module = use_temperature_module
        self.tube_rack_labware = tube_rack_labware
        self.tube_rack_position = tube_rack_position
        self.use_falcon_tubes = use_falcon_tubes
        self.falcon_tube_rack_labware = falcon_tube_rack_labware
        self.falcon_tube_rack_position = falcon_tube_rack_position





        metadata = {
        'protocolName': 'iGEM GFP OD600 calibration',
        'author': 'Gonzalo Vidal <gsvidal@uc.cl>',
        'description': 'Protocol to perform serial dilutions of fluorescein and nanoparticles for calibration',
        'apiLevel': '2.13'}

    def run(self, protocol: protocol_api.ProtocolContext):

        #Labware
        tiprack = protocol.load_labware(self.tiprack_labware, f'{self.tiprack_position}')
        pipette = protocol.load_instrument(self.pipette, self.pipette_position, tip_racks=[tiprack])
        plate = protocol.load_labware(self.calibration_plate_labware, self.calibration_plate_position)
        if self.use_temperature_module:
            temperature_module = protocol.load_module('Temperature Module', self.tube_rack_position)
            tube_rack = temperature_module.load_labware(self.tube_rack_labware)
        else:
            tube_rack = protocol.load_labware(self.tube_rack_labware, self.tube_rack_position)
        if self.use_falcon_tubes:
            falcon_tube_rack = protocol.load_labware(self.falcon_tube_rack_labware, self.falcon_tube_rack_position)
        #Protocol
        #dispense PBS
        #dispense water
        #dispense fluorescein
        #dispense nanoparticles
        #fluorescein serial dilutions
        #nanoparticles serial dilutions

        #END


