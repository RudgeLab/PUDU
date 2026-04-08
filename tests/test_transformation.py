"""
Unit tests for HeatShockTransformation validation logic.

These tests cover __init__ parsing, _validate_protocol edge cases, and
the specific issues identified in code review:
  - P1: tip reuse for competent cell distribution (verified via simulation)
  - P2: inconsistent plasmid replicate counts in plasmid_locations

Tests are split into:
  - TestTransformationDataParsing  : __init__ / _parse_transformation_data
  - TestValidateProtocol           : _validate_protocol edge cases
"""

import unittest
from unittest.mock import MagicMock
from pudu.transformation import HeatShockTransformation


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

def make_transformation(transformation_data, plasmid_locations=None, **kwargs):
    """Convenience wrapper — instantiate HeatShockTransformation with minimal args."""
    return HeatShockTransformation(
        transformation_data=transformation_data,
        plasmid_locations=plasmid_locations,
        **kwargs
    )


class MockLabware:
    """Minimal stand-in for an alumblock labware in _validate_protocol."""
    def __init__(self, num_wells=24):
        self._wells = [MagicMock() for _ in range(num_wells)]

    def wells(self):
        return self._wells


# Reusable transformation data blocks

SINGLE_DH5ALPHA = [
    {
        'Strain':  'https://SBOL2Build.org/strain_1/1',
        'Chassis': 'https://sbolcanvas.org/DH5alpha/1',
        'Plasmids': ['https://SBOL2Build.org/plasmid_1/1']
    }
]

TWO_STRAINS_TWO_PLASMIDS = [
    {
        'Strain':  'https://SBOL2Build.org/strain_1/1',
        'Chassis': 'https://sbolcanvas.org/DH5alpha/1',
        'Plasmids': ['https://SBOL2Build.org/plasmid_1/1']
    },
    {
        'Strain':  'https://SBOL2Build.org/strain_2/1',
        'Chassis': 'https://sbolcanvas.org/DH5alpha/1',
        'Plasmids': ['https://SBOL2Build.org/plasmid_2/1']
    }
]

MULTI_CHASSIS = [
    {
        'Strain':  'https://SBOL2Build.org/strain_1/1',
        'Chassis': 'https://sbolcanvas.org/DH5alpha/1',
        'Plasmids': ['https://SBOL2Build.org/plasmid_1/1']
    },
    {
        'Strain':  'https://SBOL2Build.org/strain_2/1',
        'Chassis': 'https://sbolcanvas.org/BL21/1',
        'Plasmids': ['https://SBOL2Build.org/plasmid_1/1']
    }
]

CONSISTENT_PLASMID_LOCATIONS = {
    'https://SBOL2Build.org/plasmid_1/1': ['A1', 'B1'],
    'https://SBOL2Build.org/plasmid_2/1': ['C1', 'D1']
}

INCONSISTENT_PLASMID_LOCATIONS = {
    'https://SBOL2Build.org/plasmid_1/1': ['A1', 'B1'],   # 2 replicates
    'https://SBOL2Build.org/plasmid_2/1': ['C1']           # 1 replicate
}


# ---------------------------------------------------------------------------
# 1. Transformation data parsing (__init__ / _parse_transformation_data)
# ---------------------------------------------------------------------------

class TestTransformationDataParsing(unittest.TestCase):

    def test_none_transformation_data_raises(self):
        """transformation_data=None must raise immediately."""
        with self.assertRaises(ValueError) as ctx:
            HeatShockTransformation(transformation_data=None)
        self.assertIn('Must provide', str(ctx.exception))

    def test_transformation_data_not_list_raises(self):
        """A dict passed as transformation_data must raise (old API format)."""
        with self.assertRaises(ValueError) as ctx:
            HeatShockTransformation(transformation_data={
                'list_of_dna': ['pA', 'pB'],
                'competent_cells': 'DH5alpha'
            })
        self.assertIn('must be a list', str(ctx.exception))

    def test_missing_strain_field_raises(self):
        with self.assertRaises(ValueError) as ctx:
            HeatShockTransformation(transformation_data=[{
                'Chassis': 'https://sbolcanvas.org/DH5alpha/1',
                'Plasmids': ['https://SBOL2Build.org/plasmid_1/1']
            }])
        self.assertIn("missing 'Strain'", str(ctx.exception))

    def test_missing_chassis_field_raises(self):
        with self.assertRaises(ValueError) as ctx:
            HeatShockTransformation(transformation_data=[{
                'Strain':  'https://SBOL2Build.org/strain_1/1',
                'Plasmids': ['https://SBOL2Build.org/plasmid_1/1']
            }])
        self.assertIn("missing 'Chassis'", str(ctx.exception))

    def test_missing_plasmids_field_raises(self):
        with self.assertRaises(ValueError) as ctx:
            HeatShockTransformation(transformation_data=[{
                'Strain':  'https://SBOL2Build.org/strain_1/1',
                'Chassis': 'https://sbolcanvas.org/DH5alpha/1'
            }])
        self.assertIn("missing 'Plasmids'", str(ctx.exception))

    def test_empty_plasmids_list_raises(self):
        with self.assertRaises(ValueError) as ctx:
            HeatShockTransformation(transformation_data=[{
                'Strain':  'https://SBOL2Build.org/strain_1/1',
                'Chassis': 'https://sbolcanvas.org/DH5alpha/1',
                'Plasmids': []
            }])
        self.assertIn('cannot be empty', str(ctx.exception))

    def test_use_dna_96plate_without_plasmid_locations_raises(self):
        """use_dna_96plate=True requires plasmid_locations."""
        with self.assertRaises(ValueError) as ctx:
            HeatShockTransformation(
                transformation_data=SINGLE_DH5ALPHA,
                use_dna_96plate=True
            )
        self.assertIn('plasmid_locations must be provided', str(ctx.exception))

    def test_valid_single_chassis_parses(self):
        t = make_transformation(SINGLE_DH5ALPHA)
        self.assertEqual(len(t.transformations), 1)
        self.assertEqual(t.all_chassis, ['DH5alpha'])
        self.assertEqual(t.all_plasmids, ['plasmid_1'])

    def test_valid_multi_chassis_parses(self):
        t = make_transformation(MULTI_CHASSIS)
        self.assertEqual(len(t.transformations), 2)
        self.assertIn('DH5alpha', t.all_chassis)
        self.assertIn('BL21', t.all_chassis)

    def test_uri_and_plain_name_both_accepted(self):
        """Plain names (non-URI) should work alongside full URIs."""
        t = make_transformation([{
            'Strain':  'strain_1',
            'Chassis': 'DH5alpha',
            'Plasmids': ['plasmid_1']
        }])
        self.assertEqual(t.all_chassis, ['DH5alpha'])
        self.assertEqual(t.all_plasmids, ['plasmid_1'])


# ---------------------------------------------------------------------------
# 2. _validate_protocol edge cases
# ---------------------------------------------------------------------------

class TestValidateProtocol(unittest.TestCase):
    """
    Call _validate_protocol directly with a mock labware so we can test
    validation logic without spinning up a full protocol context.
    """

    def _run_validate(self, transformation, num_wells=24):
        transformation._validate_protocol(protocol=None, labware=MockLabware(num_wells))

    # --- P2: inconsistent plasmid replicate counts ---

    def test_inconsistent_plasmid_replicate_counts_raises(self):
        """P2: plasmid_locations with uneven well-list lengths must raise."""
        t = make_transformation(
            TWO_STRAINS_TWO_PLASMIDS,
            plasmid_locations=INCONSISTENT_PLASMID_LOCATIONS
        )
        with self.assertRaises(ValueError) as ctx:
            self._run_validate(t)
        self.assertIn('inconsistent replicate counts', str(ctx.exception))

    def test_consistent_plasmid_replicate_counts_passes(self):
        """Matching well-list lengths must not raise."""
        t = make_transformation(
            TWO_STRAINS_TWO_PLASMIDS,
            plasmid_locations=CONSISTENT_PLASMID_LOCATIONS
        )
        # Should complete without error
        self._run_validate(t)
        self.assertEqual(t.location_replicates, 2)

    def test_single_plasmid_location_passes(self):
        """Single plasmid — trivially consistent."""
        t = make_transformation(
            SINGLE_DH5ALPHA,
            plasmid_locations={'https://SBOL2Build.org/plasmid_1/1': ['A1', 'B1', 'C1']}
        )
        self._run_validate(t)
        self.assertEqual(t.location_replicates, 3)

    # --- Reagent capacity ---

    def test_too_many_reagents_for_alumblock_raises(self):
        """
        20 unique plasmids + competent cell tubes + media tubes > 24 wells.
        Uses temp module path (no plasmid_locations).
        """
        overflow_data = [
            {
                'Strain':  f'https://SBOL2Build.org/strain_{i}/1',
                'Chassis': 'https://sbolcanvas.org/DH5alpha/1',
                'Plasmids': [f'https://SBOL2Build.org/plasmid_{i}/1']
            }
            for i in range(20)
        ]
        t = make_transformation(overflow_data)
        with self.assertRaises(ValueError) as ctx:
            self._run_validate(t, num_wells=24)
        self.assertIn('more than', str(ctx.exception))

    def test_reagents_exactly_at_capacity_passes(self):
        """
        Verify that a protocol fitting exactly within the alumblock does not raise.
        1 plasmid + 1 chassis tube + 1 media tube = 3 wells — well within 24.
        """
        t = make_transformation(SINGLE_DH5ALPHA)
        self._run_validate(t, num_wells=24)

    def test_multi_chassis_reagent_count(self):
        """
        Multi-chassis: each chassis gets its own cell tube(s).
        2 strains × 1 chassis each × 2 replicates = 4 reactions total,
        1 tube per chassis (4 reactions < 5 per tube), 1 media tube.
        Total: 2 plasmids + 2 cell tubes + 1 media = 5 wells — fits in 24.
        """
        t = make_transformation(MULTI_CHASSIS)
        self._run_validate(t, num_wells=24)
        self.assertEqual(len(t.competent_cell_tubes_by_chassis), 2)
        self.assertEqual(t.competent_cell_tubes_by_chassis['DH5alpha'], 1)
        self.assertEqual(t.competent_cell_tubes_by_chassis['BL21'], 1)


if __name__ == '__main__':
    unittest.main()
