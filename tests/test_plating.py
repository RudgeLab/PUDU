"""
Unit tests for Plating validation logic and parameter handling.

Tests are split into:
  - TestPlatingInit         : __init__ / basic attribute wiring
  - TestPlatingValidation   : hard limits (colonies, replicates, dilutions, well volume)
  - TestDilutionFactor      : dilution_factor parameter and derived volume_lb_transfer
  - TestMergeParams         : param hierarchy (plating_data → json_params → kwargs)
  - TestPlateLayout         : calculate_plate_layout single/double plate logic
"""

import json
import unittest
from unittest.mock import MagicMock
from pudu.plating import Plating


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

def make_plating(bacterium_locations=None, **kwargs):
    """Convenience wrapper — instantiate Plating with a default single construct."""
    if bacterium_locations is None:
        bacterium_locations = SINGLE_CONSTRUCT
    return Plating(bacterium_locations=bacterium_locations, **kwargs)


class MockPlate:
    """Minimal stand-in for a labware plate in calculate_plate_layout."""
    def __init__(self, num_wells=96):
        # Plain integers serve as stand-in well objects; calculate_plate_layout only slices them.
        self._wells = list(range(num_wells))

    def wells(self):
        return self._wells


SINGLE_CONSTRUCT = {'A1': ['DH5alpha', 'plasmid_1']}

THREE_CONSTRUCTS = {
    'A1': ['DH5alpha', 'plasmid_1'],
    'B1': ['DH5alpha', 'plasmid_2'],
    'C1': ['DH5alpha', 'plasmid_3'],
}


# ---------------------------------------------------------------------------
# 1. Init / basic attribute wiring
# ---------------------------------------------------------------------------

class TestPlatingInit(unittest.TestCase):

    def test_no_bacterium_locations_raises(self):
        """Omitting bacterium_locations entirely must raise immediately."""
        with self.assertRaises(ValueError) as ctx:
            Plating()
        self.assertIn('Must input', str(ctx.exception))

    def test_valid_minimal_construction(self):
        """Minimal valid call must succeed."""
        p = make_plating()
        self.assertIsNotNone(p)

    def test_number_constructs_computed_from_locations(self):
        p = make_plating(THREE_CONSTRUCTS)
        self.assertEqual(p.number_constructs, 3)

    def test_total_colonies_computed(self):
        """total_colonies == number_constructs × number_dilutions × replicates."""
        p = make_plating(THREE_CONSTRUCTS, replicates=2, number_dilutions=2)
        self.assertEqual(p.total_colonies, 3 * 2 * 2)

    def test_volume_lb_transfer_derived_from_default_factor(self):
        """Default dilution_factor=10, bacteria=2 → volume_lb_transfer = 2×9 = 18."""
        p = make_plating()
        self.assertAlmostEqual(p.volume_lb_transfer, 18.0)

    def test_volume_lb_transfer_updates_with_custom_factor(self):
        """dilution_factor=5, bacteria=2 → volume_lb_transfer = 2×4 = 8."""
        p = make_plating(dilution_factor=5)
        self.assertAlmostEqual(p.volume_lb_transfer, 8.0)


# ---------------------------------------------------------------------------
# 2. Hard limit validations (all checked in __init__)
# ---------------------------------------------------------------------------

class TestPlatingValidation(unittest.TestCase):

    def test_too_many_colonies_raises(self):
        """total_colonies > max_colonies must raise."""
        with self.assertRaises(ValueError):
            make_plating(THREE_CONSTRUCTS, replicates=2, number_dilutions=2, max_colonies=5)
        # 3 × 2 × 2 = 12 > 5

    def test_too_many_replicates_raises(self):
        """replicates > 8 must raise."""
        with self.assertRaises(ValueError) as ctx:
            make_plating(replicates=9)
        self.assertIn('8', str(ctx.exception))

    def test_number_dilutions_above_2_raises(self):
        """number_dilutions > 2 must raise — only 1 or 2 dilution steps are supported."""
        with self.assertRaises(ValueError) as ctx:
            make_plating(number_dilutions=3)
        self.assertIn('2', str(ctx.exception))

    def test_volume_sufficiency_raises_when_well_too_small(self):
        """
        dilution_factor=2, bacteria=2 → well = 4 µL.
        2 replicates × 4 µL + 2 µL seed = 10 µL > 4 µL → must raise.
        """
        with self.assertRaises(ValueError) as ctx:
            make_plating(dilution_factor=2, replicates=2, number_dilutions=2)
        self.assertIn('insufficient', str(ctx.exception))

    def test_volume_sufficiency_passes_at_exact_boundary(self):
        """
        Default: factor=10, bacteria=2, colony=4, dilutions=2.
        4 replicates × 4 µL + 2 µL seed = 18 µL ≤ 20 µL → must not raise.
        """
        make_plating(replicates=4, dilution_factor=10, number_dilutions=2)

    def test_volume_sufficiency_raises_one_replicate_above_boundary(self):
        """
        5 replicates × 4 µL + 2 µL seed = 22 µL > 20 µL → must raise.
        """
        with self.assertRaises(ValueError) as ctx:
            make_plating(replicates=5, dilution_factor=10, number_dilutions=2)
        self.assertIn('insufficient', str(ctx.exception))

    def test_single_dilution_relaxes_volume_constraint(self):
        """
        With number_dilutions=1 there is no seed volume to reserve.
        factor=4, bacteria=2 → well = 8 µL.
        2 replicates × 4 µL = 8 µL ≤ 8 µL → passes for 1 dilution.
        The same config would fail with 2 dilutions (8 + 2 = 10 > 8).
        """
        with self.assertRaises(ValueError):
            make_plating(dilution_factor=4, replicates=2, number_dilutions=2)

        # Must not raise with 1 dilution
        make_plating(dilution_factor=4, replicates=2, number_dilutions=1)

    def test_volume_sufficiency_error_message_is_informative(self):
        """Error message must mention the well volume, the need, and a suggested fix."""
        with self.assertRaises(ValueError) as ctx:
            make_plating(dilution_factor=2, replicates=2, number_dilutions=2)
        msg = str(ctx.exception)
        self.assertIn('µL', msg)
        self.assertIn('dilution_factor', msg)


# ---------------------------------------------------------------------------
# 3. dilution_factor parameter
# ---------------------------------------------------------------------------

class TestDilutionFactor(unittest.TestCase):

    def test_default_dilution_factor_is_ten(self):
        p = make_plating()
        self.assertEqual(p.dilution_factor, 10)

    def test_custom_dilution_factor_stored(self):
        p = make_plating(dilution_factor=5)
        self.assertEqual(p.dilution_factor, 5)

    def test_dilution_factor_via_json_params(self):
        """dilution_factor must be settable via the json_params hierarchy."""
        p = make_plating(json_params={'dilution_factor': 20})
        self.assertEqual(p.dilution_factor, 20)
        self.assertAlmostEqual(p.volume_lb_transfer, 38.0)  # 2 × (20-1) = 38

    def test_volume_lb_transfer_rejected_as_direct_param(self):
        """
        volume_lb_transfer is no longer a valid parameter — it is derived.
        Passing it via json_params must raise an unknown-parameter error.
        """
        with self.assertRaises(ValueError) as ctx:
            make_plating(json_params={'volume_lb_transfer': 18})
        self.assertIn('volume_lb_transfer', str(ctx.exception))

    def test_dilution_factor_kwargs_overrides_json_params(self):
        """A kwarg dilution_factor must take precedence over json_params."""
        p = make_plating(json_params={'dilution_factor': 5}, dilution_factor=20)
        self.assertEqual(p.dilution_factor, 20)

    def test_large_dilution_factor_allowed_when_volume_fits(self):
        """A large factor is fine as long as volumes stay within limits."""
        # factor=20, bacteria=2 → well=40 µL; 1 replicate × 4 + 2 seed = 6 ≤ 40
        p = make_plating(dilution_factor=20, replicates=1, number_dilutions=2)
        self.assertAlmostEqual(p.volume_lb_transfer, 38.0)

    def test_mix_volume_capped_at_19_for_default_factor(self):
        """Default factor=10 → well=20 µL → mix_volume = min(19, 20-1) = 19."""
        p = make_plating()
        self.assertEqual(p.mix_volume, 19)

    def test_mix_volume_capped_below_well_volume_for_small_factor(self):
        """
        factor=5, bacteria=2 → well=10 µL → mix_volume = min(19, 10-1) = 9.
        Without this cap the mix step would try to aspirate 19 µL from a 10 µL well.
        """
        p = make_plating(dilution_factor=5)
        self.assertEqual(p.mix_volume, 9)

    def test_mix_volume_never_exceeds_19(self):
        """Large factor → well volume > 20, but mix_volume is still capped at 19."""
        p = make_plating(dilution_factor=20)  # well = 40 µL
        self.assertEqual(p.mix_volume, 19)


# ---------------------------------------------------------------------------
# 4. Parameter merge hierarchy
# ---------------------------------------------------------------------------

class TestMergeParams(unittest.TestCase):

    def test_bacterium_locations_via_plating_data(self):
        """plating_data is the primary way to pass bacterium_locations."""
        p = Plating(plating_data={'bacterium_locations': SINGLE_CONSTRUCT})
        self.assertEqual(p.bacterium_locations, SINGLE_CONSTRUCT)

    def test_json_params_overrides_plating_data(self):
        """json_params must take precedence over plating_data for shared keys."""
        p = Plating(
            plating_data={'bacterium_locations': SINGLE_CONSTRUCT, 'replicates': 1},
            json_params={'replicates': 3}
        )
        self.assertEqual(p.replicates, 3)

    def test_kwargs_override_json_params(self):
        """An explicit kwarg must override json_params."""
        p = make_plating(json_params={'dilution_factor': 5}, dilution_factor=15)
        self.assertEqual(p.dilution_factor, 15)

    def test_unknown_param_in_json_params_raises(self):
        """An unrecognised key in json_params must raise a descriptive error."""
        with self.assertRaises(ValueError) as ctx:
            make_plating(json_params={'not_a_valid_param': 99})
        self.assertIn('not_a_valid_param', str(ctx.exception))

    def test_unknown_param_in_plating_data_raises(self):
        """An unrecognised key in plating_data must also raise."""
        with self.assertRaises(ValueError) as ctx:
            Plating(plating_data={
                'bacterium_locations': SINGLE_CONSTRUCT,
                'bad_param': 1
            })
        self.assertIn('bad_param', str(ctx.exception))

    def test_defaults_used_when_nothing_overrides(self):
        """Check a sample of defaults are applied when nothing is provided."""
        p = make_plating()
        self.assertEqual(p.replicates, 1)
        self.assertEqual(p.number_dilutions, 2)
        self.assertEqual(p.dilution_factor, 10)
        self.assertAlmostEqual(p.volume_colony, 4.0)


# ---------------------------------------------------------------------------
# 5. calculate_plate_layout
# ---------------------------------------------------------------------------

class TestPlateLayout(unittest.TestCase):
    """
    Call calculate_plate_layout directly with MockPlate objects so we can test
    the slicing and two-plate expansion logic without a full protocol context.
    """

    def _make_layout(self, plating, wells_per_dilution, plate2=None):
        plate1 = MockPlate()
        return plating.calculate_plate_layout(
            MagicMock(), plate1, plate2, wells_per_dilution=wells_per_dilution
        ), plate1

    def test_single_dilution_populates_only_dilution_1(self):
        """number_dilutions=1 → dilution_2 key must be None."""
        p = make_plating(THREE_CONSTRUCTS, number_dilutions=1)
        layout, plate1 = self._make_layout(p, wells_per_dilution=3)
        self.assertIsNone(layout['dilution_2'])
        self.assertEqual(layout['dilution_1']['wells'], plate1.wells()[:3])

    def test_two_dilutions_fit_on_one_plate(self):
        """
        3 constructs (≤ 48) → both dilution steps fit in halves of a single plate.
        dilution_1 occupies wells [0:3], dilution_2 occupies wells [48:51].
        """
        p = make_plating(THREE_CONSTRUCTS, number_dilutions=2)
        layout, plate1 = self._make_layout(p, wells_per_dilution=3)
        self.assertEqual(layout['dilution_1']['plate'], 1)
        self.assertEqual(layout['dilution_2']['plate'], 1)
        self.assertEqual(layout['dilution_1']['wells'], plate1.wells()[:3])
        self.assertEqual(layout['dilution_2']['wells'], plate1.wells()[48:51])

    def test_two_dilutions_overflow_to_two_plates(self):
        """
        50 wells per dilution > 48 → each dilution step gets its own plate.
        """
        p = make_plating(THREE_CONSTRUCTS, number_dilutions=2)
        plate1 = MockPlate()
        plate2 = MockPlate()
        layout = p.calculate_plate_layout(MagicMock(), plate1, plate2, wells_per_dilution=50)
        self.assertEqual(layout['dilution_1']['plate'], 1)
        self.assertEqual(layout['dilution_2']['plate'], 2)
        self.assertEqual(len(layout['dilution_1']['wells']), 50)
        self.assertEqual(len(layout['dilution_2']['wells']), 50)
        self.assertEqual(layout['dilution_1']['wells'], plate1.wells()[:50])
        self.assertEqual(layout['dilution_2']['wells'], plate2.wells()[:50])

    def test_two_dilutions_overflow_without_plate2_raises(self):
        """Overflow without a second plate object provided must raise."""
        p = make_plating(THREE_CONSTRUCTS, number_dilutions=2)
        with self.assertRaises(ValueError) as ctx:
            p.calculate_plate_layout(MagicMock(), MockPlate(), wells_per_dilution=50)
        self.assertIn('plate2', str(ctx.exception))

    def test_exactly_48_wells_fits_on_one_plate(self):
        """
        48 wells per dilution step is the boundary — both steps must share one plate.
        """
        p = make_plating(THREE_CONSTRUCTS, number_dilutions=2)
        layout, _ = self._make_layout(p, wells_per_dilution=48)
        self.assertEqual(layout['dilution_1']['plate'], 1)
        self.assertEqual(layout['dilution_2']['plate'], 1)

    def test_different_wells_per_dilution_for_dilution_and_agar(self):
        """
        Dilution plates use number_constructs wells; agar plates use
        number_constructs × replicates wells. Both must be sliced correctly.
        """
        p = make_plating(THREE_CONSTRUCTS, replicates=4, number_dilutions=2)
        dil_layout, dil_plate = self._make_layout(p, wells_per_dilution=3)   # constructs only
        agar_layout, agar_plate = self._make_layout(p, wells_per_dilution=12)  # constructs × replicates

        self.assertEqual(len(dil_layout['dilution_1']['wells']), 3)
        self.assertEqual(len(agar_layout['dilution_1']['wells']), 12)


# ---------------------------------------------------------------------------
# 6. Plating JSON outputs
# ---------------------------------------------------------------------------

class TestPlatingOutputs(unittest.TestCase):

    def test_well_name_from_index_column_major(self):
        from pudu.plating import Plating
        self.assertEqual(Plating._well_name_from_index(0), 'A1')
        self.assertEqual(Plating._well_name_from_index(1), 'B1')
        self.assertEqual(Plating._well_name_from_index(7), 'H1')
        self.assertEqual(Plating._well_name_from_index(8), 'A2')
        self.assertEqual(Plating._well_name_from_index(48), 'A7')

    def test_format_construct_name_list(self):
        from pudu.plating import Plating
        self.assertEqual(Plating._format_construct_name(['DH5alpha', 'plasmid_1']), 'DH5alpha, plasmid_1')

    def test_format_construct_name_string(self):
        from pudu.plating import Plating
        self.assertEqual(Plating._format_construct_name('construct'), 'construct')

    def test_dilution_ratio_label(self):
        p = make_plating(dilution_factor=10)
        self.assertEqual(p._dilution_ratio_label(1), '1/10')
        self.assertEqual(p._dilution_ratio_label(2), '1/100')

    def test_dilution_ratio_label_factor_5(self):
        p = make_plating(dilution_factor=5)
        self.assertEqual(p._dilution_ratio_label(1), '1/5')
        self.assertEqual(p._dilution_ratio_label(2), '1/25')

    def test_build_agar_plate_map_structure(self):
        p = make_plating(THREE_CONSTRUCTS, replicates=2, number_dilutions=2)
        plates = p.build_agar_plate_map()
        self.assertIn('plate_1', plates)
        self.assertIn('dilution_1', plates['plate_1'])
        self.assertIn('dilution_2', plates['plate_1'])
        self.assertIn('ratio', plates['plate_1']['dilution_1'])
        self.assertIn('wells', plates['plate_1']['dilution_1'])

    def test_build_agar_plate_map_ratio_labels(self):
        p = make_plating(THREE_CONSTRUCTS, number_dilutions=2, dilution_factor=10)
        plates = p.build_agar_plate_map()
        self.assertEqual(plates['plate_1']['dilution_1']['ratio'], '1/10')
        self.assertEqual(plates['plate_1']['dilution_2']['ratio'], '1/100')

    def test_build_agar_plate_map_well_positions(self):
        """
        3 constructs, 2 replicates: dilution_1 wells are A1-F1 (indices 0-5),
        dilution_2 wells start at index 48 (A7).
        """
        p = make_plating(THREE_CONSTRUCTS, replicates=2, number_dilutions=2)
        plates = p.build_agar_plate_map()
        dil1_wells = plates['plate_1']['dilution_1']['wells']
        dil2_wells = plates['plate_1']['dilution_2']['wells']
        self.assertIn('A1', dil1_wells)
        self.assertIn('B1', dil1_wells)
        self.assertEqual(len(dil1_wells), 6)  # 3 constructs × 2 replicates
        self.assertIn('A7', dil2_wells)

    def test_build_agar_plate_map_replicate_numbering(self):
        p = make_plating(THREE_CONSTRUCTS, replicates=2, number_dilutions=1)
        plates = p.build_agar_plate_map()
        wells = plates['plate_1']['dilution_1']['wells']
        # construct 0 → A1 (rep 1), B1 (rep 2)
        self.assertEqual(wells['A1']['replicate'], 1)
        self.assertEqual(wells['B1']['replicate'], 2)
        self.assertEqual(wells['A1']['source_well'], 'A1')

    def test_build_agar_plate_map_construct_name(self):
        p = make_plating(SINGLE_CONSTRUCT, number_dilutions=1)
        plates = p.build_agar_plate_map()
        well = plates['plate_1']['dilution_1']['wells']['A1']
        self.assertEqual(well['construct'], 'DH5alpha, plasmid_1')

    def test_build_agar_plate_map_two_plates_when_overflow(self):
        """
        When number_constructs * replicates > 48 with 2 dilutions, each
        dilution step gets its own plate.
        """
        locs = {f'A{i+1}': [f'construct_{i}'] for i in range(25)}
        p = make_plating(locs, replicates=2, number_dilutions=2)
        # 25 * 2 = 50 wells per dilution > 48 → two plates
        plates = p.build_agar_plate_map()
        self.assertIn('plate_1', plates)
        self.assertIn('plate_2', plates)
        self.assertIn('dilution_1', plates['plate_1'])
        self.assertIn('dilution_2', plates['plate_2'])

    def test_build_agar_plate_map_single_dilution_overflow(self):
        """
        When number_dilutions == 1 and number_constructs * replicates > 96,
        wells should spill onto plate_2 rather than generating invalid well names.
        """
        locs = {f'W{i}': f'construct_{i}' for i in range(97)}
        p = make_plating(locs, number_dilutions=1)
        plates = p.build_agar_plate_map()
        self.assertIn('plate_1', plates)
        self.assertIn('plate_2', plates)
        self.assertEqual(len(plates['plate_1']['dilution_1']['wells']), 96)
        self.assertEqual(len(plates['plate_2']['dilution_1']['wells']), 1)
        # overflow starts fresh at A1 on plate_2
        self.assertIn('A1', plates['plate_2']['dilution_1']['wells'])
        # no well name should exceed column 12
        for plate in plates.values():
            for dil in plate.values():
                for well in dil['wells']:
                    self.assertLessEqual(int(well[1:]), 12)

    def test_get_plates_json_top_level_key(self):
        p = make_plating(THREE_CONSTRUCTS, number_dilutions=2)
        data = p.get_plates_json()
        self.assertIn('agar_plates', data)
        self.assertIsInstance(data['agar_plates'], dict)

    def test_write_plates_json_creates_valid_file(self):
        import tempfile, os
        p = make_plating(THREE_CONSTRUCTS, replicates=2, number_dilutions=2)
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, 'plating_layout.json')
            returned = p.write_plates_json(path)
            self.assertTrue(os.path.exists(path))
            with open(path) as f:
                loaded = json.load(f)
            self.assertEqual(loaded, returned)
            self.assertIn('agar_plates', loaded)

    def test_write_plates_excel_creates_valid_file(self):
        import tempfile, os, zipfile
        p = make_plating(THREE_CONSTRUCTS, replicates=2, number_dilutions=2)
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, 'plating_layout.xlsx')
            p.write_plates_excel(path)
            self.assertTrue(os.path.exists(path))
            self.assertGreater(os.path.getsize(path), 0)
            self.assertTrue(zipfile.is_zipfile(path))

    def test_write_plates_excel_two_plates(self):
        import tempfile, os, zipfile
        locs = {f'A{i+1}': [f'construct_{i}'] for i in range(25)}
        p = make_plating(locs, replicates=2, number_dilutions=2)
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, 'plating_layout.xlsx')
            p.write_plates_excel(path)
            self.assertTrue(os.path.exists(path))
            self.assertTrue(zipfile.is_zipfile(path))

    def test_write_plates_excel_single_dilution(self):
        import tempfile, os, zipfile
        p = make_plating(THREE_CONSTRUCTS, number_dilutions=1)
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, 'plating_layout.xlsx')
            p.write_plates_excel(path)
            self.assertTrue(os.path.exists(path))
            self.assertTrue(zipfile.is_zipfile(path))


if __name__ == '__main__':
    unittest.main()
