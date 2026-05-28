pudu.plating
============

Classes for automated and manual serial-dilution spot plating.

* :class:`~pudu.plating.Plating` — OT-2 protocol that takes transformed
  bacteria from a thermocycler plate, performs up to two serial dilutions,
  and spots each dilution onto agar plates with replicates.
* :class:`~pudu.plating.ManualPlating` — generates a human-readable Markdown
  bench protocol.

On simulation, :class:`~pudu.plating.Plating` writes:

* ``{protocol_name}.json`` — machine-readable agar plate map
* ``{protocol_name}.xlsx`` — colour-coded Excel grid (blue = dilution 1, orange = dilution 2)

.. autoclass:: pudu.plating.Plating
   :members:
   :special-members: __init__

.. autoclass:: pudu.plating.ManualPlating
   :members:
   :special-members: __init__
   :show-inheritance:

.. autoclass:: pudu.plating.ManualPlatingRecord
   :members:
