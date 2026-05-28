pudu.assembly
=============

Classes for automated Golden Gate DNA assembly on the Opentrons OT-2.

The module exposes four concrete classes and one factory:

* :class:`~pudu.assembly.Domestication` — assembles individual parts into a universal acceptor backbone, one part at a time.
* :class:`~pudu.assembly.ManualLoopAssembly` — combinatorial Loop Assembly from role-based part lists; detects Odd/Even receivers and selects the correct enzyme automatically.
* :class:`~pudu.assembly.SBOLLoopAssembly` — explicit Loop Assembly from SBOL-format input; each assembly dict specifies parts, backbone, and enzyme directly.
* :class:`~pudu.assembly.ManualAssembly` — generates a human-readable Markdown bench protocol (no OT-2 commands).
* :class:`~pudu.assembly.LoopAssembly` — factory that auto-detects input format and returns the appropriate subclass.

All OT-2 classes inherit from :class:`~pudu.assembly.BaseAssembly`, which
implements shared hardware setup, tip management, and liquid transfer.

.. autoclass:: pudu.assembly.BaseAssembly
   :members:
   :special-members: __init__

.. autoclass:: pudu.assembly.Domestication
   :members:
   :special-members: __init__
   :show-inheritance:

.. autoclass:: pudu.assembly.ManualLoopAssembly
   :members:
   :special-members: __init__
   :show-inheritance:

.. autoclass:: pudu.assembly.SBOLLoopAssembly
   :members:
   :special-members: __init__
   :show-inheritance:

.. autoclass:: pudu.assembly.ManualAssembly
   :members:
   :special-members: __init__
   :show-inheritance:

.. autoclass:: pudu.assembly.LoopAssembly
   :members:
   :show-inheritance:

.. autoclass:: pudu.assembly.ManualReactionRecord
   :members:
