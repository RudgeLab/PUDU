pudu.transformation
===================

Classes for automated and manual bacterial heat-shock transformation.

* :class:`~pudu.transformation.HeatShockTransformation` — OT-2 protocol that
  loads DNA and competent cells into a thermocycler plate, runs the heat-shock
  cycle, adds recovery media, and exports a plating map.
* :class:`~pudu.transformation.ManualTransformation` — generates a
  human-readable Markdown bench protocol.

Both classes accept SBOL-style transformation data of the form::

    [
        {
            "Strain":   "https://SBOL2Build.org/strain_GFP/1",
            "Chassis":  "https://sbolcanvas.org/DH5alpha/1",
            "Plasmids": ["https://SBOL2Build.org/composite_1/1"]
        }
    ]

.. autoclass:: pudu.transformation.Transformation
   :members:
   :special-members: __init__

.. autoclass:: pudu.transformation.HeatShockTransformation
   :members:
   :special-members: __init__
   :show-inheritance:

.. autoclass:: pudu.transformation.ManualTransformation
   :members:
   :special-members: __init__
   :show-inheritance:

.. autoclass:: pudu.transformation.ManualTransformationRecord
   :members:
