# PUDU
Welcome to the PUDU (Protocol Unified Design Unit) repository, our Python package for liquid handling robot control on Synthetic Biology workflows.


<img src="https://github.com/RudgeLab/PUDU/blob/main/images/PUDU_Monet.jpeg#gh-light-mode-only" alt="PUDU logo" width="250"/>
<img src="https://github.com/RudgeLab/PUDU/blob/main/images/PUDU_Ukiyo_e.jpeg#gh-dark-mode-only" alt="PUDU night logo" width="250"/>

## *The art of automated liquid handling*

As you may have noticed, our logo features a beautiful pudu _[(Pudu puda)](https://en.wikipedia.org/wiki/Pudu)_; a deer native to the southern forests of Chile and Argentina known for being the smallest deer of the world[.](https://youtu.be/xRQnJyP77tY)

## Multicolor fluorescence per particle calibration automated protocol iGEM

[Human protocol](https://github.com/RudgeLab/PUDU/blob/main/protocols/Multicolor_fluorescence_per_particle_calibration_protocol_igem/Automated_protocol_user_instructions.xlsx) (Excel to set the OT2 deck)

[Robot protocol](https://github.com/RudgeLab/PUDU/blob/main/scripts/run_iGEM2022_rgb_od_libre.py) (Python script to run the OT2)

[Original protocol](https://old.igem.org/wiki/images/a/a4/InterLab_2022_-_Calibration_Protocol_v2.pdf) (2022 iGEM InterLab study)

## Installation

Installing PUDU is way easier than pronuncing it! 

Do:

`pip install pudupy`

For more details please refer to our Wiki (TODO) for installation instructions and developer guides.

This counts with a libre version (does not require any package installation)

To install it on an OT2 you first need to SSH into it.

Only the first time you need to set the SSH connection [[instructions](https://support.opentrons.com/s/article/Setting-up-SSH-access-to-your-OT-2)]

Afterwards you can just SSH into the OT2 [[instructions](https://support.opentrons.com/s/article/Connecting-to-your-OT-2-with-SSH)]

## PUDU facilitates the creation of OT2 liquid handling robot protocols to automate:

- DNA assembly using SBOL as input [[script](https://github.com/RudgeLab/PUDU/blob/main/scripts/run_Loop_assembly.py)]
- Protocol metadata capture and storage in SBOL
- Domestication of gBlocks into plasmids from lists of parts [[script](https://github.com/RudgeLab/PUDU/blob/main/scripts/run_Domestication.py)]
- Loop DNA assembly using dictionaries of parts per role [[script](https://github.com/RudgeLab/PUDU/blob/main/scripts/run_Loop_assembly.py)]
- Chemical transformation
- [Multicolor fluorescence per particle calibration protocol](https://old.igem.org/wiki/images/a/a4/InterLab_2022_-_Calibration_Protocol_v2.pdf) plate setup [[script](https://github.com/RudgeLab/PUDU/blob/main/scripts/run_iGEM2022_rgb_od_libre.py)]
- Design Of Experiments 96 well plate test setup with supplement gradients

## Recommended workflow

- Install PUDU in your computer
- Install PUDU in the OT2 that will perform the automation
- Develop protocols in your computer
- To simulate your protocols you can open the PUDU folder in your terminal and run `opentrons_simulate ./scripts/run_Loop_assembly.py ` for example [[instructions](https://support.opentrons.com/s/article/Simulating-OT-2-protocols-on-your-computer?)]
- Transfer the script file (.py) to the computer used to run the protocol on the OT2 (if its the same, omit)
- Load the script file (.py) on the Opentrons App
- Follow Oppentrons App instruction
- Set the OT2 deck with the information provided by the Opentrons App and PUDU human readable output (.xlsx)
- Run your protocol and enjoy automation (Now you have more time to design your next experiment! :wink: )

## Documentation

 Please visit our documentation with API reference at Read the Docs (TODO)

## Tutorials

TODO
