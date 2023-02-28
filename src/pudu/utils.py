

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