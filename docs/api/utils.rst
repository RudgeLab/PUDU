pudu.utils
==========

Shared utilities used across PUDU protocols.

* :class:`~pudu.utils.Camera` — captures images and records video via ffmpeg
  during OT-2 protocol runs.
* :class:`~pudu.utils.SmartPipette` — pipette wrapper that uses the
  Opentrons liquid-tracking API to compute safe aspiration heights for
  conical tubes, preventing tip plunging as tubes empty.
* ``colors`` — list of 24 hex colour strings used to colour-code liquids in
  the Opentrons deck visualiser.

.. autodata:: pudu.utils.colors

.. autoclass:: pudu.utils.Camera
   :members:
   :special-members: __init__

.. autoclass:: pudu.utils.SmartPipette
   :members:
   :special-members: __init__
