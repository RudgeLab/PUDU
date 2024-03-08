# PUDU
Welcome to the PUDU (Protocol Unified Design Unit) repository, our Python package for liquid handling robot control on Synthetic Biology workflows.


<img src="https://github.com/RudgeLab/PUDU/blob/main/images/PUDU_Logo.png#gh-light-mode-only" alt="PUDU logo" width="250"/>
<img src="https://github.com/RudgeLab/PUDU/blob/main/images/PUDU_Logo.png#gh-dark-mode-only" alt="PUDU night logo" width="250"/>

## *The art of automated liquid handling*

As you may have noticed, our logo features a beautiful pudu _[(Pudu puda)](https://en.wikipedia.org/wiki/Pudu)_; a deer native to the southern forests of Chile and Argentina known for being the smallest deer of the world[.](https://youtu.be/xRQnJyP77tY)
This package intends to make the code to program liquid handling robots as small and simple as possible.

## No Installation required

Some scripts have "libre" in their name, this means that users can modify these scripts and use them to run protocols whithout the need to install PUDU.

### Calibrate your plate reader using PUDU script libre

[Human protocol](https://github.com/RudgeLab/PUDU/blob/main/protocols/Multicolor_fluorescence_per_particle_calibration_protocol_igem/Automated_protocol_user_instructions.xlsx) (Excel to set the OT2 deck)

[Robot protocol](https://github.com/RudgeLab/PUDU/blob/main/scripts/run_iGEM2022_rgb_od_libre.py) (Python script to run the OT2)

Reference: [Original protocol](https://old.igem.org/wiki/images/a/a4/InterLab_2022_-_Calibration_Protocol_v2.pdf) (2022 iGEM InterLab study)


## Installation

### Computer installation

Installing PUDU is way easier than pronuncing it! 

Run:

`pip install pudupy`

This code can be executed in the terminal and in jupyter notebooks.

For more details please refer to our Wiki (TODO) for installation instructions and developer guides.

### OT-2 installation

To install it on an OT2 you first need to SSH into it.

Only the first time you need to set the SSH connection [[instructions](https://support.opentrons.com/s/article/Setting-up-SSH-access-to-your-OT-2)]

Afterwards you can just SSH into the OT2 [[instructions](https://support.opentrons.com/s/article/Connecting-to-your-OT-2-with-SSH)]

then in the OT-2 terminal run:

`pip install pudupy`

## Recommended workflow

- Install PUDU in your computer
- Install PUDU in the OT2 that will perform the automation
- Develop protocols in your computer
- To simulate your protocols you can open the PUDU folder in your terminal and run `opentrons_simulate ./scripts/run_Loop_assembly.py ` for example [[instructions](https://support.opentrons.com/s/article/Simulating-OT-2-protocols-on-your-computer?)]
- Transfer the script file (.py) to the computer used to run the protocol on the OT2 (if its the same, omit)
- Load the script file (.py) on the Opentrons App
- Follow Oppentrons App instruction
- Set the OT2 deck with the information provided by the Opentrons App and PUDU human readable dictionaries at the top of the simulation output.
- Run your protocol and enjoy automation (Now you have more time to design your next experiment! :wink: )

## Documentation

 Please visit our documentation with API reference at Read the Docs (TODO)

## Tutorials

TODO
