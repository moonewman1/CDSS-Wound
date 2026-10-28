import unittest

from pydantic import ValidationError

from models import RedFlagScreening, WoundAssessment
from wound_logic import assess_red_flags, assess_wound
from wound_rules import RED_FLAG_QUESTIONS


def assessment(**updates):
    data = {
        "red_flags": {code: "no" for code in RED_FLAG_QUESTIONS},
        "age_group": "13_64",
        "comorbidities": [],
        "healing_factors": [],
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
        "erythema_extent": "none",
        "purulence": "no",
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
    def test_clean_minor_wound_recommends_dressing_classes(self):
        result = assess_wound(assessment())

        self.assertEqual(result["triage"]["level"], "care")
        self.assertTrue(result["recommendations"])
        self.assertLessEqual(len(result["recommendations"]), 3)
        self.assertNotIn("brands", result["recommendations"][0])

    def test_any_red_flag_stops_assessment(self):
        flags = {code: "no" for code in RED_FLAG_QUESTIONS}
        flags["a6"] = "yes"

        result = assess_red_flags(flags)

        self.assertEqual(result["triage"]["level"], "refer")
        self.assertEqual(result["referrals"][0]["code"], "A6")
        self.assertEqual(result["recommendations"], [])

    def test_unable_to_assess_depth_is_referred(self):
        flags = {code: "no" for code in RED_FLAG_QUESTIONS}
        flags["a2"] = "unable"

        result = assess_red_flags(flags)

        self.assertEqual(result["referrals"][0]["code"], "A2")
        self.assertEqual(result["recommendations"], [])

    def test_diabetic_foot_is_referred(self):
        result = assess_wound(assessment(
            wound_type="foot_ulcer",
            comorbidities=["diabetes"],
        ))

        self.assertEqual(result["triage"]["level"], "refer")
        self.assertTrue(any("เบาหวาน" in item["reason"] for item in result["referrals"]))
        self.assertEqual(result["recommendations"], [])

    def test_mild_local_infection_allows_short_term_antimicrobial_classes(self):
        result = assess_wound(assessment(infection_signs=["increasing_pain"]))

        classes = [item["id"] for item in result["recommendations"]]
        self.assertEqual(result["infection_status"], "mild_local")
        self.assertTrue(classes)
        self.assertFalse({"film", "hydrocolloid"} & set(classes))
        self.assertIn("48–72", result["follow_up"][0])

    def test_infection_gate_refers_major_purulence_and_high_risk_hosts(self):
        purulent = assess_wound(assessment(
            purulence="yes",
        ))
        high_risk = assess_wound(assessment(
            infection_signs=["redness"],
            comorbidities=["diabetes"],
        ))

        self.assertEqual(purulent["triage"]["level"], "refer")
        self.assertEqual(high_risk["triage"]["level"], "refer")

    def test_infection_at_four_weeks_does_not_pass_under_four_week_gate(self):
        result = assess_wound(assessment(
            infection_signs=["increasing_pain"],
            duration="4w",
        ))

        self.assertEqual(result["triage"]["level"], "refer")

    def test_infection_gate_refers_more_than_two_centimeters_or_four_signs(self):
        erythema = assess_wound(assessment(
            erythema_extent="over_2cm",
        ))
        many_signs = assess_wound(assessment(
            infection_signs=[
                "redness", "increasing_pain", "increasing_exudate", "increasing_odor",
            ],
        ))

        self.assertEqual(erythema["triage"]["level"], "refer")
        self.assertEqual(many_signs["triage"]["level"], "refer")

    def test_cavity_depth_selects_shallow_cavity_dressing_and_refers_deep(self):
        shallow = assess_wound(assessment(depth="cavity_shallow"))
        deep = assess_wound(assessment(depth="cavity_deep"))

        self.assertIn("alginate", {item["id"] for item in shallow["recommendations"]})
        self.assertEqual(deep["triage"]["level"], "refer")

    def test_hard_exclusions_remove_allergy_and_iodine_classes(self):
        result = assess_wound(assessment(
            infection_signs=["increasing_pain"],
            allergies=["iodine"],
        ))

        classes = {item["id"] for item in result["recommendations"]}
        excluded = {item["name"] for item in result["excluded_products"]}
        self.assertNotIn("iodine", classes)
        self.assertTrue(any("ไอโอดีน" in name for name in excluded))

    def test_invalid_or_incomplete_red_flag_answers_are_rejected(self):
        flags = {code: "no" for code in RED_FLAG_QUESTIONS}
        flags["a2"] = "maybe"

        with self.assertRaises(ValidationError):
            RedFlagScreening(red_flags=flags)

        with self.assertRaises(ValidationError):
            RedFlagScreening(red_flags={"a1": "no"})


if __name__ == "__main__":
    unittest.main()
