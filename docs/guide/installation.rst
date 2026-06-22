Installation
============

Computer (development / simulation)
-------------------------------------

Install PUDU from PyPI::

    pip install pudupy

To run simulations on your laptop without a physical robot::

    opentrons_simulate your_protocol.py

OT-2 robot
-----------

SSH into the OT-2 (first-time setup: `Opentrons SSH guide
<https://support.opentrons.com/s/article/Setting-up-SSH-access-to-your-OT-2>`_),
then install::

    pip install pudupy

The robot and your laptop must be on the same local network so the Opentrons
App can detect the robot.

Dependencies
------------

PUDU depends on:

* ``opentrons >= 8.4.1``
* ``xlsxwriter >= 3.2.5``

For building this documentation locally::

    pip install sphinx sphinx-rtd-theme

Developer install
-----------------

Clone the repository and install in editable mode::

    git clone https://github.com/MyersResearchGroup/PUDU.git
    cd PUDU
    pip install -e ".[test]"

Run the test suite::

    pytest tests/
