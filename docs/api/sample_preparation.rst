pudu.sample_preparation
========================

Classes for distributing samples and creating inducer gradients on 96-well
plates for characterisation experiments.

* :class:`~pudu.sample_preparation.PlateSamples` — distributes a list of
  samples into replicate wells across a plate.
* :class:`~pudu.sample_preparation.PlateWithGradient` — creates a serial
  inducer-concentration gradient (e.g. IPTG dose-response) across replicate
  rows on a 96-well plate.

Both subclass :class:`~pudu.sample_preparation.SamplePreparation`, which
provides shared labware loading and well-slot management.

.. autoclass:: pudu.sample_preparation.SamplePreparation
   :members:
   :special-members: __init__

.. autoclass:: pudu.sample_preparation.PlateSamples
   :members:
   :special-members: __init__
   :show-inheritance:

.. autoclass:: pudu.sample_preparation.PlateWithGradient
   :members:
   :special-members: __init__
   :show-inheritance:
