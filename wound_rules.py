import json
from pathlib import Path


RED_FLAG_QUESTIONS = {
    "a1": "แผลมีเลือดออกไม่หยุดหลังกดห้ามเลือดต่อเนื่อง 10 นาที",
    "a2": "แผลลึกถึงไขมัน/กล้ามเนื้อ/เส้นเอ็น/กระดูก หรือเห็นกระดูก/เอ็น",
    "a3": "แผลถูกสัตว์/คนกัด แผลถูกแทง มีสิ่งแปลกปลอมฝังอยู่ หรือสกปรกมากล้างไม่ออก",
    "a4": "ขอบแผลถ่างเกิน/ต้องเย็บ เช่น ยาว >1.5–2 ซม. ลึก ขอบไม่ชิด โดยเฉพาะใบหน้า/ข้อพับ",
    "a5": "แผลไหม้ใหญ่กว่าฝ่ามือ อยู่ตำแหน่งหน้า/มือ/เท้า/อวัยวะเพศ/ข้อพับ/รอบวง เป็นแผลไฟฟ้า/สารเคมี สูดควัน หรือผิวขาว/ดำแข็งไม่เจ็บ",
    "a6": "มีอาการทั้งตัว เช่น ไข้ หนาวสั่น ซึม สับสน ใจสั่น หรือความดันต่ำ",
    "a7": "รอยแดงลามจากขอบแผล >2 ซม. เส้นแดงตามทางน้ำเหลือง บวมร้อนมาก มีเสียงกรอบใต้ผิว หรือผิวหนังม่วง/ดำ",
    "a8": "มีแผลที่เท้าร่วมกับเบาหวาน หรือแผลที่เท้า/ขาร่วมกับโรคหลอดเลือดแดงส่วนปลาย (PAD)",
    "a9": "ปลายนิ้ว/เท้าซีด เย็น ดำ หรือปวดรุนแรงผิดสัดส่วนกับแผล",
    "a10": "เป็นแผลนานกว่า 4 สัปดาห์ไม่ดีขึ้น หรือกลับเป็นซ้ำที่เดิม",
    "a11": "กลุ่มเสี่ยงสูง: เด็ก <1 ปี ตั้งครรภ์ ภูมิคุ้มกันบกพร่อง/เคมีบำบัด/สเตียรอยด์ขนาดสูง หรือใช้ยากันเลือดแข็ง",
}

RED_FLAG_CHOICES = {
    code: ({"yes", "no", "unable"} if code == "a2" else {"yes", "no"})
    for code in RED_FLAG_QUESTIONS
}

ASSESSMENT_CHOICES = {
    "age_group": {"under_1", "1_12", "13_64", "65_plus"},
    "pregnancy": {"yes", "no"},
    "thyroid_condition": {"yes", "no", "unknown"},
    "fragile_skin": {"yes", "no"},
    "self_care": {"independent", "assistance", "bedbound"},
    "wound_type": {
        "abrasion", "laceration", "skin_tear", "burn", "blister",
        "pressure", "leg_ulcer", "foot_ulcer", "surgical", "other",
    },
    "duration": {"lt24h", "1_7d", "1_3w", "4w", "gt4w"},
    "leg_profile": {"not_applicable", "venous", "arterial", "mixed", "uncertain"},
    "pressure_stage": {"not_applicable", "stage1", "stage2", "stage3", "stage4", "dtpi", "unstageable"},
    "burn_depth": {"not_applicable", "superficial", "superficial_partial", "deep_partial", "full_thickness"},
    "skin_tear_type": {"not_applicable", "type1", "type2", "type3"},
    "tissue": {"granulation", "epithelial", "slough", "eschar", "mixed"},
    "depth": {"superficial", "moderate", "cavity_shallow", "cavity_deep"},
    "erythema_extent": {"none", "up_to_2cm", "over_2cm"},
    "purulence": {"yes", "no"},
    "exudate": {"dry", "low", "moderate", "high"},
    "exudate_character": {"clear", "cloudy", "green", "bloody", "unknown"},
    "wound_edge": {"advancing", "rolled", "macerated", "irritated", "normal"},
    "wound_size": {"small", "medium", "large"},
    "pain": {"0_3", "4_6", "7_10"},
    "location": {
        "face_head", "hand", "foot", "joint", "heel_bony", "extremity",
        "torso", "genital", "perianal", "weight_bearing_foot", "contaminated",
    },
    "clinician_plan": {"yes", "no"},
    "waterproof": {"yes", "no"},
    "dressing_frequency": {"daily", "2_3_days", "weekly"},
    "budget": {"low", "medium", "unlimited"},
}

MULTI_SELECT_CHOICES = {
    "comorbidities": {
        "diabetes", "pad", "venous_disease", "heart_failure", "kidney_disease",
        "liver_disease", "immunosuppressed", "chronic_dermatitis",
    },
    "healing_factors": {"smoking", "malnutrition", "heavy_alcohol"},
    "medications": {"steroid", "anticoagulant", "antiplatelet", "chemotherapy", "long_term_nsaid"},
    "allergies": {"adhesive", "silicone", "iodine", "silver", "honey", "latex", "alginate"},
    "infection_signs": {
        "redness", "increasing_pain", "increasing_exudate", "increasing_odor",
        "friable_granulation", "delayed_healing",
    },
    "previous_care": {"not_treated", "cleaned", "antiseptic", "existing_dressing"},
}

CHOICE_LABELS = {
    "age_group": {"under_1": "<1 ปี", "1_12": "1–12 ปี", "13_64": "13–64 ปี", "65_plus": "≥65 ปี"},
    "pregnancy": {"yes": "ใช่", "no": "ไม่ใช่"},
    "thyroid_condition": {"yes": "มี", "no": "ไม่มี", "unknown": "ไม่ทราบ"},
    "fragile_skin": {"yes": "ใช่", "no": "ไม่ใช่"},
    "self_care": {"independent": "ดูแลเองได้", "assistance": "ต้องมีผู้ช่วย", "bedbound": "ติดเตียง"},
    "wound_type": {
        "abrasion": "แผลบาด/ถลอก", "laceration": "แผลฉีกขาด", "skin_tear": "ผิวหนังฉีก (skin tear)",
        "burn": "แผลไหม้/น้ำร้อนลวก", "blister": "ตุ่มพองจากเสียดสี", "pressure": "แผลกดทับ",
        "leg_ulcer": "แผลที่ขา", "foot_ulcer": "แผลที่เท้า", "surgical": "แผลผ่าตัด", "other": "อื่น ๆ",
    },
    "duration": {
        "lt24h": "<24 ชั่วโมง",
        "1_7d": "1–7 วัน",
        "1_3w": "1–3 สัปดาห์",
        "4w": "4 สัปดาห์",
        "gt4w": ">4 สัปดาห์",
    },
    "leg_profile": {
        "not_applicable": "ไม่เกี่ยวข้อง", "venous": "เข้าได้กับแผลหลอดเลือดดำ",
        "arterial": "เข้าได้กับแผลหลอดเลือดแดง", "mixed": "ลักษณะผสม", "uncertain": "ไม่แน่ใจ",
    },
    "pressure_stage": {
        "not_applicable": "ไม่เกี่ยวข้อง", "stage1": "Stage 1", "stage2": "Stage 2",
        "stage3": "Stage 3", "stage4": "Stage 4", "dtpi": "DTPI", "unstageable": "จัดระยะไม่ได้",
    },
    "burn_depth": {
        "not_applicable": "ไม่เกี่ยวข้อง", "superficial": "ผิวแดง ไม่มีตุ่ม (superficial)",
        "superficial_partial": "มีตุ่ม/ชมพูแดง เจ็บ (superficial partial)",
        "deep_partial": "สงสัย deep partial", "full_thickness": "สงสัย full thickness",
    },
    "skin_tear_type": {
        "not_applicable": "ไม่เกี่ยวข้อง", "type1": "ISTAP Type 1", "type2": "ISTAP Type 2", "type3": "ISTAP Type 3",
    },
    "tissue": {
        "granulation": "เนื้อแดง (granulation)", "epithelial": "ผิวใหม่ (epithelial)",
        "slough": "เนื้อเหลือง/ขาว (slough)", "eschar": "เนื้อตายแห้ง (eschar)", "mixed": "ผสม",
    },
    "depth": {
        "superficial": "ตื้น",
        "moderate": "ลึกปานกลาง",
        "cavity_shallow": "โพรงตื้น",
        "cavity_deep": "โพรงลึก/อุโมงค์/undermining",
    },
    "erythema_extent": {
        "none": "ไม่มีรอยแดง",
        "up_to_2cm": "รอยแดงไม่เกิน 2 ซม.",
        "over_2cm": "รอยแดงมากกว่า 2 ซม.",
    },
    "purulence": {"yes": "มีหนองมาก/ฝี", "no": "ไม่มีหนองมาก/ฝี"},
    "exudate": {"dry": "แห้ง", "low": "น้อย", "moderate": "ปานกลาง", "high": "มาก"},
    "exudate_character": {
        "clear": "ใส/เหลืองจาง", "cloudy": "ขุ่น/เหลืองข้น", "green": "เขียว",
        "bloody": "มีเลือดปน", "unknown": "ไม่ทราบ",
    },
    "wound_edge": {
        "advancing": "ขอบมีผิวใหม่", "rolled": "ขอบม้วน/แข็ง/ไม่เคลื่อน",
        "macerated": "ผิวรอบแผลเปื่อยยุ่ย", "irritated": "ผิวแดง/ลอก/ผื่น", "normal": "ปกติ",
    },
    "wound_size": {"small": "เล็ก (<2×2 ซม.)", "medium": "ปานกลาง (2–5 ซม.)", "large": "ใหญ่ (>5 ซม.)"},
    "pain": {"0_3": "0–3", "4_6": "4–6", "7_10": "7–10"},
    "location": {
        "face_head": "ใบหน้า/ศีรษะ", "hand": "มือ", "foot": "เท้า",
        "joint": "ข้อ/ข้อพับ", "heel_bony": "ส้นเท้า/ปุ่มกระดูก",
        "extremity": "แขนขาทั่วไป", "torso": "ลำตัว", "weight_bearing_foot": "ฝ่าเท้ารับน้ำหนัก",
        "genital": "อวัยวะเพศ", "perianal": "ใกล้ทวารหนัก",
        "contaminated": "ใกล้ทวาร/ปัสสาวะ (เสี่ยงปนเปื้อน)",
    },
    "clinician_plan": {"yes": "มีแผนจากแพทย์", "no": "ไม่มีแผนจากแพทย์"},
    "waterproof": {"yes": "ต้องการ", "no": "ไม่จำเป็น"},
    "dressing_frequency": {"daily": "ทุกวัน", "2_3_days": "ทุก 2–3 วัน", "weekly": "สัปดาห์ละครั้ง"},
    "budget": {"low": "ประหยัด", "medium": "ปานกลาง", "unlimited": "ไม่จำกัด"},
}

MULTI_SELECT_LABELS = {
    "comorbidities": {
        "diabetes": "เบาหวาน", "pad": "โรคหลอดเลือดแดงส่วนปลาย (PAD)",
        "venous_disease": "หลอดเลือดดำเสื่อม (CVI)", "heart_failure": "หัวใจล้มเหลว/บวม",
        "kidney_disease": "โรคไต", "liver_disease": "โรคตับ",
        "immunosuppressed": "ภูมิคุ้มกันบกพร่อง", "chronic_dermatitis": "ผิวหนังอักเสบเรื้อรัง",
    },
    "healing_factors": {
        "smoking": "สูบบุหรี่",
        "malnutrition": "ขาดสารอาหาร",
        "heavy_alcohol": "ดื่มสุรามาก",
    },
    "medications": {
        "steroid": "สเตียรอยด์", "anticoagulant": "ยาต้านการแข็งตัวของเลือด",
        "antiplatelet": "ยาต้านเกล็ดเลือด", "chemotherapy": "เคมีบำบัด",
        "long_term_nsaid": "NSAIDs ระยะยาว",
    },
    "allergies": {
        "adhesive": "กาว/พลาสเตอร์", "silicone": "ซิลิโคน", "iodine": "ไอโอดีน",
        "silver": "เงิน", "honey": "น้ำผึ้ง", "latex": "ลาเทกซ์", "alginate": "อัลจิเนต/สาหร่าย",
    },
    "infection_signs": {
        "redness": "แดง/ร้อน/บวมรอบแผล",
        "increasing_exudate": "สารคัดหลั่งเพิ่ม",
        "increasing_odor": "กลิ่นเหม็นเพิ่มขึ้น", "increasing_pain": "ปวดเพิ่มหรือเกิดใหม่",
        "friable_granulation": "เนื้อแดงเปราะ/เลือดออกง่าย", "delayed_healing": "แผลไม่หายหรือขยาย",
    },
    "previous_care": {
        "not_treated": "ยังไม่เคยทำแผล", "cleaned": "ล้างด้วย NSS/น้ำสะอาด",
        "antiseptic": "ใช้น้ำยาฆ่าเชื้อ/ยาทา", "existing_dressing": "ปิด dressing เดิม",
    },
}

FIELD_LABELS = {
    "age_group": "ช่วงอายุ",
    "comorbidities": "โรคร่วม",
    "healing_factors": "ภาวะที่มีผลต่อการหายของแผล",
    "medications": "ยาที่ใช้อยู่",
    "allergies": "ประวัติแพ้",
    "pregnancy": "ตั้งครรภ์/ให้นมบุตร",
    "thyroid_condition": "โรคต่อมไทรอยด์",
    "fragile_skin": "ผิวบอบบาง/ฉีกขาดง่าย",
    "self_care": "ความสามารถดูแลตนเอง",
    "wound_type": "กลไก/ชนิดแผล",
    "duration": "ระยะเวลาที่เป็นแผล",
    "leg_profile": "ลักษณะแผลที่ขา",
    "pressure_stage": "ระยะแผลกดทับ",
    "burn_depth": "ความลึกแผลไหม้",
    "skin_tear_type": "ชนิดผิวหนังฉีก",
    "tissue": "เนื้อเยื่อในแผล",
    "depth": "ความลึก",
    "infection_signs": "สัญญาณติดเชื้อเฉพาะที่",
    "erythema_extent": "ระยะรอยแดงจากขอบแผล",
    "purulence": "หนองมาก/ฝี",
    "exudate": "ปริมาณสารคัดหลั่ง",
    "exudate_character": "ลักษณะสารคัดหลั่ง",
    "wound_edge": "ขอบแผล/ผิวรอบแผล",
    "wound_size": "ขนาดแผล",
    "pain": "ระดับความเจ็บปวด",
    "location": "ตำแหน่งแผล",
    "previous_care": "สิ่งที่ทำกับแผลแล้ว",
    "clinician_plan": "มีแผนจากแพทย์",
    "waterproof": "ความต้องการกันน้ำ",
    "dressing_frequency": "ความถี่เปลี่ยน dressing ที่ทำได้",
    "budget": "งบประมาณ",
}

_catalog = json.loads((Path(__file__).parent / "data" / "products.json").read_text(encoding="utf-8"))
PRODUCT_CLASSES = {item["id"]: item for item in _catalog["classes"]}
RESTRICTED_PRODUCT_CLASSES = _catalog["clinician_managed_classes"]
PRODUCT_CATALOG_NOTE = _catalog["catalog_note"]

REFERENCES = [
    "TIME framework / WUWHS Consensus และ Wound Bed Preparation — กรอบประเมินเนื้อเยื่อ การติดเชื้อ ความชื้น และขอบแผล",
    "IWII, Wound Infection in Clinical Practice (2022) — สัญญาณติดเชื้อและการประเมินซ้ำ",
    "NPIAP/EPUAP/PPPIA International Guideline (2019; ตรวจฉบับปรับปรุงก่อนใช้) — การจัดระยะแผลกดทับ",
    "ISTAP Best Practice Recommendations — การจัดการผิวหนังฉีก",
    "NICE CKS: Burns and scalds / Pressure ulcers / Venous leg ulcer; NICE HTG751, HTG758, HTG502/MTG42 — ตามที่อ้างในเอกสารแนบ",
    "แนวทางไทยจาก Thai Wound Care Society และสมาคมโรคเบาหวานแห่งประเทศไทย — เอกสารฉบับล่าสุดยังต้องขอและตรวจสอบก่อนใช้",
]
