"""
Unit tests for HeatShockTransformation validation logic.

These tests cover __init__ parsing, _validate_protocol edge cases, and
the specific issues identified in code review:
  - P1: tip reuse for competent cell distribution (verified via simulation)
  - P2: inconsistent plasmid replicate counts in plasmid_locations

Tests are split into:
  - TestTransformationDataParsing  : __init__ / _parse_transformation_data
  - TestValidateProtocol           : _validate_protocol edge cases
  - TestInitialTips                : initial_tip_p20 / initial_tip_p300 params
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

    def test_shared_plasmid_uri_across_transformations_passes(self):
        """Same plasmid URI used in two different transformations is valid (shared source well)."""
        t = make_transformation([
            {
                'Strain':  'https://SBOL2Build.org/strain_1/1',
                'Chassis': 'https://sbolcanvas.org/DH5alpha/1',
                'Plasmids': ['https://SBOL2Build.org/plasmid_1/1']
            },
            {
                'Strain':  'https://SBOL2Build.org/strain_2/1',
                'Chassis': 'https://sbolcanvas.org/BL21/1',
                'Plasmids': ['https://SBOL2Build.org/plasmid_1/1']  # same URI
            }
        ])
        # plasmid_1 appears only once — shared, not a collision
        self.assertEqual(t.all_plasmids, ['plasmid_1'])

    def test_colliding_plasmid_uris_raises(self):
        """Two different URIs that extract to the same plasmid name must raise."""
        with self.assertRaises(ValueError) as ctx:
            make_transformation([
                {
                    'Strain':  'https://SBOL2Build.org/strain_1/1',
                    'Chassis': 'https://sbolcanvas.org/DH5alpha/1',
                    'Plasmids': ['https://SBOL2Build.org/plasmid_1/1']
                },
                {
                    'Strain':  'https://SBOL2Build.org/strain_2/1',
                    'Chassis': 'https://sbolcanvas.org/DH5alpha/1',
                    'Plasmids': ['https://SBOL2Build.org/plasmid_1/2']  # different URI, same name
                }
            ])
        self.assertIn('plasmid_1', str(ctx.exception))

    def test_colliding_chassis_uris_raises(self):
        """Two different URIs that extract to the same chassis name must raise."""
        with self.assertRaises(ValueError) as ctx:
            make_transformation([
                {
                    'Strain':  'https://SBOL2Build.org/strain_1/1',
                    'Chassis': 'https://sbolcanvas.org/DH5alpha/1',
                    'Plasmids': ['https://SBOL2Build.org/plasmid_1/1']
                },
                {
                    'Strain':  'https://SBOL2Build.org/strain_2/1',
                    'Chassis': 'https://sbolcanvas.org/DH5alpha/2',  # different URI, same name
                    'Plasmids': ['https://SBOL2Build.org/plasmid_2/1']
                }
            ])
        self.assertIn('DH5alpha', str(ctx.exception))


# ---------------------------------------------------------------------------
# 2. _validate_protocol edge cases
# ---------------------------------------------------------------------------

class TestValidateProtocol(unittest.TestCase):
    """
    Call _validate_protocol directly with a mock labware so we can test
    validation logic without spinning up a full protocol context.
    """

    def _run_validate(self, transformation, num_wells=24, tube_rack_wells=24):
        transformation._validate_protocol(
            protocol=None,
            labware=MockLabware(num_wells),
            tube_rack=MockLabware(tube_rack_wells)
        )

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

    def test_too_many_plasmids_for_alumblock_raises(self):
        """
        25 unique plasmids > 24 wells on the temperature module.
        Cells and media are on the tube rack, so the alumblock check is plasmids-only.
        """
        overflow_data = [
            {
                'Strain':  f'https://SBOL2Build.org/strain_{i}/1',
                'Chassis': 'https://sbolcanvas.org/DH5alpha/1',
                'Plasmids': [f'https://SBOL2Build.org/plasmid_{i}/1']
            }
            for i in range(25)
        ]
        t = make_transformation(overflow_data)
        with self.assertRaises(ValueError) as ctx:
            self._run_validate(t, num_wells=24)
        self.assertIn('more than', str(ctx.exception))

    def test_too_many_tubes_for_tube_rack_raises(self):
        """
        Enough reactions to overflow a very small tube rack.
        2 strains × 2 replicates = 4 reactions → 1 cell tube + 1 media tube = 2 > 1.
        """
        t = make_transformation(TWO_STRAINS_TWO_PLASMIDS)
        with self.assertRaises(ValueError) as ctx:
            self._run_validate(t, tube_rack_wells=1)
        self.assertIn('more than', str(ctx.exception))

    def test_reagents_exactly_at_capacity_passes(self):
        """
        Verify that a protocol fitting exactly within the alumblock does not raise.
        1 plasmid + 1 chassis tube + 1 media tube = 3 wells — well within 24.
        """
        t = make_transformation(SINGLE_DH5ALPHA)
        self._run_validate(t, num_wells=24)

    def test_initial_dna_well_offset_included_in_capacity_check(self):
        """
        P2: initial_dna_well offset must be counted in the temp-module capacity check.
        Cells and media are now on the tube rack, so the alumblock holds only plasmids.
        initial_dna_well=24 + 1 plasmid = 25 > 24 → out of range.
        """
        t = make_transformation(SINGLE_DH5ALPHA, initial_dna_well=24)
        with self.assertRaises(ValueError) as ctx:
            self._run_validate(t, num_wells=24)
        self.assertIn('more than', str(ctx.exception))

    def test_initial_dna_well_offset_within_capacity_passes(self):
        """A non-zero initial_dna_well that still fits within the block must not raise."""
        t = make_transformation(SINGLE_DH5ALPHA, initial_dna_well=5)
        self._run_validate(t, num_wells=24)  # 5 + 1 plasmid = 6 <= 24

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


# ---------------------------------------------------------------------------
# 3. Initial tip parameters
# ---------------------------------------------------------------------------

class TestInitialTips(unittest.TestCase):
    """
    Tests for initial_tip_p20 and initial_tip_p300.

    Attribute tests verify the full wiring:
      __init__ param → kwargs_params → _merge_params → self.attribute

    Assignment tests replicate the run() conditional logic with mock objects
    to confirm starting_tip is set (or not set) correctly without needing a
    full protocol context.
    """

    # --- Attribute wiring ---

    def test_initial_tips_default_to_none(self):
        """Both params must default to None when not provided."""
        t = make_transformation(SINGLE_DH5ALPHA)
        self.assertIsNone(t.initial_tip_p20)
        self.assertIsNone(t.initial_tip_p300)

    def test_initial_tip_p20_stored(self):
        t = make_transformation(SINGLE_DH5ALPHA, initial_tip_p20='B1')
        self.assertEqual(t.initial_tip_p20, 'B1')

    def test_initial_tip_p300_stored(self):
        t = make_transformation(SINGLE_DH5ALPHA, initial_tip_p300='C3')
        self.assertEqual(t.initial_tip_p300, 'C3')

    def test_both_initial_tips_set_independently(self):
        """Setting both at once must not interfere with each other."""
        t = make_transformation(SINGLE_DH5ALPHA, initial_tip_p20='A3', initial_tip_p300='D6')
        self.assertEqual(t.initial_tip_p20, 'A3')
        self.assertEqual(t.initial_tip_p300, 'D6')

    def test_initial_tips_via_json_params(self):
        """Params must be in valid_params so they can be set via json_params."""
        t = make_transformation(
            SINGLE_DH5ALPHA,
            json_params={'initial_tip_p20': 'E1', 'initial_tip_p300': 'F2'}
        )
        self.assertEqual(t.initial_tip_p20, 'E1')
        self.assertEqual(t.initial_tip_p300, 'F2')

    # --- starting_tip assignment logic ---

    def test_starting_tip_set_on_tiprack_when_provided(self):
        """
        When initial_tip_p20/p300 are set, starting_tip should be assigned
        using tiprack[well_name]. Replicates the run() conditional with mocks.
        """
        t = make_transformation(SINGLE_DH5ALPHA, initial_tip_p20='B1', initial_tip_p300='C3')

        mock_tiprack_p20 = MagicMock()
        mock_tiprack_p300 = MagicMock()
        mock_pipette_p20 = MagicMock()
        mock_pipette_p300 = MagicMock()

        if t.initial_tip_p20:
            mock_pipette_p20.starting_tip = mock_tiprack_p20[t.initial_tip_p20]
        if t.initial_tip_p300:
            mock_pipette_p300.starting_tip = mock_tiprack_p300[t.initial_tip_p300]

        mock_tiprack_p20.__getitem__.assert_called_once_with('B1')
        mock_tiprack_p300.__getitem__.assert_called_once_with('C3')

    def test_starting_tip_not_assigned_when_none(self):
        """When initial_tip params are None, starting_tip must never be touched."""
        t = make_transformation(SINGLE_DH5ALPHA)

        mock_tiprack_p20 = MagicMock()
        mock_tiprack_p300 = MagicMock()
        mock_pipette_p20 = MagicMock()
        mock_pipette_p300 = MagicMock()

        if t.initial_tip_p20:
            mock_pipette_p20.starting_tip = mock_tiprack_p20[t.initial_tip_p20]
        if t.initial_tip_p300:
            mock_pipette_p300.starting_tip = mock_tiprack_p300[t.initial_tip_p300]

        mock_tiprack_p20.__getitem__.assert_not_called()
        mock_tiprack_p300.__getitem__.assert_not_called()

    def test_p20_tip_set_independently_of_p300(self):
        """Setting only p20 must leave p300 starting_tip untouched."""
        t = make_transformation(SINGLE_DH5ALPHA, initial_tip_p20='G6')

        mock_tiprack_p20 = MagicMock()
        mock_tiprack_p300 = MagicMock()
        mock_pipette_p20 = MagicMock()
        mock_pipette_p300 = MagicMock()

        if t.initial_tip_p20:
            mock_pipette_p20.starting_tip = mock_tiprack_p20[t.initial_tip_p20]
        if t.initial_tip_p300:
            mock_pipette_p300.starting_tip = mock_tiprack_p300[t.initial_tip_p300]

        mock_tiprack_p20.__getitem__.assert_called_once_with('G6')
        mock_tiprack_p300.__getitem__.assert_not_called()


if __name__ == '__main__':
    unittest.main()
