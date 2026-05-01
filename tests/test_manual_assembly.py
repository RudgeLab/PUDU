import unittest

from pudu.assembly import ManualAssembly


class TestManualAssembly(unittest.TestCase):
    def setUp(self):
        self.assemblies = [
            {
                "Product": "https://SBOL2Build.org/composite_1/1",
                "Backbone": "https://sbolcanvas.org/pSB1C3/1",
                "PartsList": [
                    "https://sbolcanvas.org/J23101/1",
                    "https://sbolcanvas.org/B0034/1",
                    "https://sbolcanvas.org/GFP/1",
                    "https://sbolcanvas.org/B0015/1",
                ],
                "Restriction Enzyme": "https://SBOL2Build.org/BsaI/1",
            }
        ]

    def test_extract_name_from_uri(self):
        assembly = ManualAssembly(assemblies=self.assemblies)
        self.assertEqual(assembly._extract_name_from_uri("https://sbolcanvas.org/GFP/1"), "GFP")
        self.assertEqual(assembly._extract_name_from_uri("https://SBOL2Build.org/composite_1/1"), "composite_1")

    def test_volume_calculation(self):
        assembly = ManualAssembly(assemblies=self.assemblies)
        volumes = assembly._calculate_reaction_volumes(number_of_dna_components=5)
        self.assertEqual(volumes["water_volume"], 2)
        self.assertEqual(volumes["fixed_reagent_volume"], 8)
        self.assertEqual(volumes["total_dna_volume"], 10)

    def test_invalid_overfilled_reaction(self):
        assembly = ManualAssembly(
            assemblies=self.assemblies,
            volume_total_reaction=10,
            volume_part=2,
            volume_restriction_enzyme=2,
            volume_t4_dna_ligase=4,
            volume_t4_dna_ligase_buffer=2,
        )
        with self.assertRaises(ValueError) as error:
            assembly._calculate_reaction_volumes(number_of_dna_components=5)
        self.assertIn("Cannot fit", str(error.exception))

    def test_markdown_rendering_contains_sections_and_parts(self):
        assembly = ManualAssembly(assemblies=self.assemblies)
        markdown = assembly.render_markdown()

        self.assertIn("# Manual Golden Gate Assembly Protocol", markdown)
        self.assertIn("## Reaction Setup", markdown)
        self.assertIn("## Assembly 1: composite_1", markdown)
        self.assertIn("| [J23101](https://sbolcanvas.org/J23101/1) | 2 |", markdown)
        self.assertIn("## Thermocycler Program", markdown)
        self.assertIn("| Digest | 37 C | 2 min | 25 |", markdown)

    def test_markdown_rendering_supports_legacy_thermocycling_profile(self):
        legacy_profile = [
            {"temperature": 37, "hold_time_minutes": 2},
            {"temperature": 16, "hold_time_minutes": 5},
            {"temperature": 80, "hold_time_minutes": 10},
            {"temperature": 4, "hold_time_minutes": "indefinite"},
        ]
        assembly = ManualAssembly(
            assemblies=self.assemblies,
            thermocycling_profile=legacy_profile,
            thermocycling_cycles=30,
        )

        markdown = assembly.render_markdown()

        self.assertIn("| Step 1 | 37 C | 2 min | 30 |", markdown)
        self.assertIn("| Step 2 | 16 C | 5 min | 30 |", markdown)
        self.assertIn("| Step 3 | 80 C | 10 min | 1 |", markdown)
        self.assertIn("| Step 4 | 4 C | indefinite | 1 |", markdown)


if __name__ == "__main__":
    unittest.main()
