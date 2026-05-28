pudu.calibration
================

Classes for automated plate-reader calibration following the iGEM 2022
InterLab calibration protocol.

Two protocols are provided:

* :class:`~pudu.calibration.GFPODCalibration` — two calibrants (fluorescein
  and silica microspheres), two replicates each; for GFP fluorescence and
  OD600 calibration.
* :class:`~pudu.calibration.RGBODCalibration` — four calibrants (fluorescein,
  sulforhodamine 101, cascade blue, microspheres), two replicates each; for
  RGB fluorescence and OD600 calibration.

Both subclass :class:`~pudu.calibration.BaseCalibration` and use the
template-method pattern: ``run()`` is implemented in the base class and calls
abstract methods for the calibrant-specific steps.

Reference protocol:
`iGEM 2022 InterLab Calibration Protocol <https://old.igem.org/wiki/images/a/a4/InterLab_2022_-_Calibration_Protocol_v2.pdf>`_

.. autoclass:: pudu.calibration.BaseCalibration
   :members:
   :special-members: __init__

.. autoclass:: pudu.calibration.GFPODCalibration
   :members:
   :show-inheritance:

.. autoclass:: pudu.calibration.RGBODCalibration
   :members:
   :show-inheritance:
