import unittest

from pydantic import ValidationError

from models import WoundAssessment
from wound_logic import assess_wound
from wound_rules import RED_FLAG_QUESTIONS


def assessment(**updates):
    data = {
        "red_flags": {code: "no" for code in RED_FLAG_QUESTIONS},
        "age_group": "13_64",
        "comorbidities": [],
        "medications": [],
        "allergies": [],
        "pregnancy": "no",
        "thyroid_condition": "no",
        "fragile_skin": "no",
        "self_care": "independent",
        "wound_type": "abrasion",
        "duration": "1_7d",
        "leg_profile": "not_applicable",
        "pressure_stage": "not_applicable",
        "burn_depth": "not_applicable",
        "skin_tear_type": "not_applicable",
        "tissue": "granulation",
        "depth": "superficial",
        "infection_signs": [],
        "exudate": "low",
        "exudate_character": "clear",
        "wound_edge": "normal",
        "wound_size": "small",
        "pain": "0_3",
        "location": "extremity",
        "previous_care": [],
        "clinician_plan": "no",
        "waterproof": "no",
        "dressing_frequency": "2_3_days",
        "budget": "low",
    }
    data.update(updates)
    return WoundAssessment.model_validate(data)


class WoundLogicTests(unittest.TestCase):
    def test_minor_clean_wound_shows_classes_and_unverified_brand_examples(self):
        result = assess_wound(assessment())

        self.assertEqual(result["triage"]["level"], "care")
        self.assertEqual(result["severity"]["level"], "low")
        self.assertTrue(result["recommendations"])
        self.assertIn("ยังไม่ยืนยัน", result["recommendations"][0]["verification"])
        self.assertTrue(result["follow_up"])

    def test_emergency_red_flag_stops_product_recommendations(self):
        flags = {code: "no" for code in RED_FLAG_QUESTIONS}
        flags["a6"] = "yes"

        result = assess_wound(assessment(red_flags=flags))

        self.assertEqual(result["triage"]["level"], "emergency")
        self.assertEqual(result["referrals"][0]["code"], "a6")
        self.assertEqual(result["recommendations"], [])

    def test_diabetic_foot_is_referred_even_if_red_flag_was_missed(self):
        result = assess_wound(assessment(
            wound_type="foot_ulcer",
            comorbidities=["diabetes"],
        ))

        self.assertEqual(result["triage"]["level"], "refer")
        self.assertTrue(any("เบาหวาน" in item["reason"] for item in result["referrals"]))
        self.assertEqual(result["recommendations"], [])

    def test_local_infection_signs_refer_instead_of_suggesting_antimicrobials(self):
        result = assess_wound(assessment(infection_signs=["pus"]))

        self.assertEqual(result["triage"]["level"], "refer")
        self.assertEqual(result["recommendations"], [])
        self.assertTrue(any("antimicrobial dressing" in warning for warning in result["warnings"]))

    def test_cavity_and_unstageable_pressure_injury_are_referred(self):
        cavity_result = assess_wound(assessment(depth="cavity"))
        pressure_result = assess_wound(assessment(
            wound_type="pressure",
            pressure_stage="unstageable",
        ))

        self.assertEqual(cavity_result["triage"]["level"], "refer")
        self.assertEqual(pressure_result["triage"]["level"], "refer")

    def test_allergy_and_exudate_filters_remove_inappropriate_classes(self):
        result = assess_wound(assessment(
            exudate="high",
            allergies=["alginate"],
        ))

        classes = [item["name"] for item in result["recommendations"]]
        excluded = {item["name"]: item["reason"] for item in result["excluded_products"]}
        self.assertTrue(any("โฟม" in name for name in classes))
        self.assertFalse(any("อัลจิเนต" in name for name in classes))
        self.assertIn("อัลจิเนต", next(name for name in excluded if "อัลจิเนต" in name))

    def test_invalid_or_incomplete_red_flag_answers_are_rejected(self):
        flags = {code: "no" for code in RED_FLAG_QUESTIONS}
        flags["a2"] = "maybe"

        with self.assertRaises(ValidationError):
            assessment(red_flags=flags)

        with self.assertRaises(ValidationError):
            assessment(red_flags={"a1": "no"})


if __name__ == "__main__":
    unittest.main()
