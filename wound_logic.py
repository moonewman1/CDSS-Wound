from models import WoundAssessment
from wound_rules import (
    CHOICE_LABELS,
    PRODUCT_CLASSES,
    REFERENCES,
    RESTRICTED_PRODUCT_CLASSES,
    RED_FLAG_QUESTIONS,
)


ANTIMICROBIAL_CLASSES = ("silver", "iodine", "honey", "phmb_dacc")
RESTRICTED_PRODUCTS = {
    "silver": RESTRICTED_PRODUCT_CLASSES[0],
    "iodine": RESTRICTED_PRODUCT_CLASSES[1],
    "honey": RESTRICTED_PRODUCT_CLASSES[2],
    "phmb_dacc": RESTRICTED_PRODUCT_CLASSES[3],
    "charcoal": RESTRICTED_PRODUCT_CLASSES[4],
}
ANTIMICROBIAL_WEAR = {
    "silver": "1–7 วัน ตามฉลาก",
    "iodine": "ตามฉลาก",
    "honey": "1–3 วัน",
    "phmb_dacc": "ตามฉลาก",
    "charcoal": "ตามชนิดและฉลาก",
}
HIGH_RISK_COMORBIDITIES = {"diabetes", "pad", "immunosuppressed"}
HIGH_RISK_MEDICATIONS = {"steroid", "chemotherapy", "anticoagulant"}
HIGH_RISK_SITES = {
    "face_head", "hand", "foot", "joint", "heel_bony", "weight_bearing_foot",
    "genital", "perianal", "contaminated",
}


def _referral(code: str, reason: str) -> dict[str, str]:
    return {"code": code, "reason": reason}


def assess_red_flags(red_flags: dict[str, str]) -> dict:
    referrals = [
        _referral(code.upper(), RED_FLAG_QUESTIONS[code])
        for code, answer in red_flags.items()
        if answer in {"yes", "unable"}
    ]
    return {
        "triage": {"level": "refer", "label": "ส่งต่อแพทย์"},
        "referrals": referrals,
        "recommendations": [],
        "reasons": [item["reason"] for item in referrals],
        "advice": [
            "ส่งต่อแพทย์ตามข้อที่พบ โดยไม่ประเมินหรือเลือกผลิตภัณฑ์ต่อ",
            "กรณีแผลไหม้ ให้ลดความร้อนด้วยน้ำก๊อกไหลผ่าน 20 นาที โดยไม่ใช้น้ำแข็ง และไม่ชะลอการส่งต่อ",
        ],
        "follow_up": [],
        "clinical_status": "ระบบสนับสนุนการตัดสินใจเบื้องต้น ไม่ทดแทนการวินิจฉัยหรือคำแนะนำจากบุคลากรทางการแพทย์",
        "references": REFERENCES,
    }


def _risk_factors(assessment: WoundAssessment) -> bool:
    return bool(
        HIGH_RISK_COMORBIDITIES.intersection(assessment.comorbidities)
        or HIGH_RISK_MEDICATIONS.intersection(assessment.medications)
        or assessment.age_group == "under_1"
        or assessment.pregnancy == "yes"
    )


def _product_detail(product_class: str) -> dict:
    product = PRODUCT_CLASSES.get(product_class)
    if product is None:
        product = RESTRICTED_PRODUCTS.get(product_class)
    if product is None:
        raise ValueError(f"Unknown dressing class: {product_class}")
    return product


def _infection_gate(assessment: WoundAssessment) -> tuple[str, list[str]]:
    sign_count = len(assessment.infection_signs)
    if (
        not sign_count
        and assessment.purulence == "no"
        and assessment.erythema_extent != "over_2cm"
    ):
        return "none", []

    referrals = []
    reasons = []
    if assessment.erythema_extent == "over_2cm":
        reasons.append("รอยแดงลามจากขอบแผลมากกว่า 2 ซม. (D3a/A7)")
    if assessment.purulence == "yes":
        reasons.append("มีหนองมากหรือฝี")
    if sign_count >= 4:
        reasons.append("พบสัญญาณติดเชื้อเฉพาะที่ตั้งแต่ 4 ข้อ")
    if _risk_factors(assessment):
        reasons.append("มีโรคร่วมหรือยาที่เพิ่มความเสี่ยงต่อการติดเชื้อ")
    if assessment.duration == "gt4w":
        reasons.append("แผลเรื้อรังนานกว่า 4 สัปดาห์")
    if assessment.depth in {"moderate", "cavity_deep"}:
        reasons.append("แผลลึกกว่าชั้นตื้นหรือเป็นโพรงลึก")
    if assessment.location in HIGH_RISK_SITES:
        reasons.append("แผลอยู่ในตำแหน่งเสี่ยง")

    if reasons:
        referrals.extend(_referral("D3", reason) for reason in reasons)
        return "refer", referrals

    mild_infection_eligible = (
        assessment.duration in {"lt24h", "1_7d", "1_3w"}
        and assessment.depth == "superficial"
        and assessment.wound_size in {"small", "medium"}
        and 1 <= sign_count <= 3
        and assessment.erythema_extent in {"none", "up_to_2cm"}
        and assessment.purulence == "no"
    )
    if mild_infection_eligible:
        return "mild_local", []

    return "refer", [
        _referral(
            "D3",
            "ไม่ครบเกณฑ์แผลติดเชื้อเฉพาะที่ระดับเบาที่ร้านยาแนะนำได้",
        )
    ]


def _get_referrals(
    assessment: WoundAssessment,
) -> list[dict[str, str]]:
    referrals = []
    for code, answer in assessment.red_flags.items():
        if answer in {"yes", "unable"}:
            referrals.append(_referral(code.upper(), RED_FLAG_QUESTIONS[code]))

    comorbidities = set(assessment.comorbidities)
    if assessment.wound_type == "foot_ulcer" and (
        "diabetes" in comorbidities or "pad" in comorbidities
    ):
        referrals.append(_referral("C1/A8", "แผลที่เท้าร่วมกับเบาหวานหรือ PAD อยู่นอกขอบเขตร้านยา"))
    if assessment.wound_type == "leg_ulcer":
        if assessment.leg_profile in {"arterial", "mixed", "uncertain"}:
            referrals.append(_referral("C3", "สงสัยแผลหลอดเลือดแดง/ชนิดผสม/ไม่แน่ใจ; ห้ามใช้ compression"))
        elif assessment.leg_profile != "venous":
            referrals.append(_referral("C3", "ไม่ทราบสาเหตุของแผลที่ขา"))
        elif assessment.clinician_plan == "no":
            referrals.append(_referral("C3", "แผลหลอดเลือดดำต้องได้รับการวินิจฉัยและมีแผนจากแพทย์"))
    if assessment.wound_type == "leg_ulcer" and "pad" in comorbidities:
        referrals.append(_referral("A8/B2", "แผลที่ขาร่วมกับ PAD"))
    if assessment.wound_type == "pressure":
        if assessment.pressure_stage in {"stage3", "stage4", "dtpi", "unstageable"}:
            referrals.append(_referral("C4", "แผลกดทับ Stage 3–4, DTPI หรือจัดระยะไม่ได้"))
        elif assessment.pressure_stage == "stage2" and assessment.clinician_plan == "no":
            referrals.append(_referral("C4", "แผลกดทับ Stage 2 ต้องส่งต่อประเมินรอบแรก"))
    if assessment.wound_type == "burn" and assessment.burn_depth in {"deep_partial", "full_thickness"}:
        referrals.append(_referral("C5", "แผลไหม้ลึกเกินขอบเขตร้านยา"))
    if assessment.wound_type == "skin_tear":
        if assessment.skin_tear_type == "type3":
            referrals.append(_referral("C6", "ผิวหนังฉีก ISTAP Type 3"))
        elif "anticoagulant" in assessment.medications:
            referrals.append(_referral("C6/B3", "ผิวหนังฉีกในผู้ใช้ยากันเลือดแข็ง"))
    if assessment.wound_type == "other":
        referrals.append(_referral("C1", "ไม่ทราบสาเหตุของแผล"))
    if assessment.wound_type == "surgical" and assessment.clinician_plan == "no":
        referrals.append(_referral("C1/E4", "แผลผ่าตัดต้องดูแลตามแผนศัลยแพทย์"))
    if assessment.depth == "moderate":
        referrals.append(_referral("D2", "แผลลึกปานกลางอยู่นอกเกณฑ์ความรุนแรงที่ดูแลได้"))
    if assessment.depth == "cavity_deep":
        referrals.append(_referral("D2", "โพรงลึก/tunnel/undermining ต้องส่งต่อแพทย์"))
    if assessment.tissue == "eschar" and (
        assessment.location in {"heel_bony", "weight_bearing_foot"}
        or "pad" in comorbidities
    ):
        referrals.append(_referral("D1", "eschar ที่ส้นเท้า/นิ้วหรือมี PAD; ห้าม debride เอง"))
    if assessment.wound_size == "large" and assessment.duration == "gt4w":
        referrals.append(_referral("D7/C2", "แผลขนาดใหญ่และเป็นมานานกว่า 4 สัปดาห์"))
    if _risk_factors(assessment) and assessment.depth != "superficial":
        referrals.append(_referral("B2/B3/D2", "มีปัจจัยเสี่ยงร่วมกับแผลที่ไม่ตื้น"))
    return referrals


def _candidate_classes(
    assessment: WoundAssessment,
    infection_status: str,
) -> tuple[list[str], list[str]]:
    reasons = []
    if infection_status == "mild_local":
        if assessment.exudate == "high":
            candidates = ["silver", "phmb_dacc"]
            reason = "ติดเชื้อเฉพาะที่ระดับเบา: เลือก antimicrobial ระยะสั้นและ carrier ที่ดูดซับสูง"
        else:
            candidates = list(ANTIMICROBIAL_CLASSES)
            reason = "ติดเชื้อเฉพาะที่ระดับเบา: เลือก antimicrobial dressing ระยะสั้น"
        if "increasing_odor" in assessment.infection_signs:
            candidates.append("charcoal")
        return candidates, [reason]

    if assessment.wound_type == "blister":
        return ["hydrocolloid", "foam"], ["ตุ่มพอง: ไม่เจาะตุ่ม"]
    if assessment.wound_type == "burn":
        return ["silicone_contact", "foam", "hydrogel"], ["แผลไหม้ตื้น: ลดความร้อนด้วยน้ำก๊อก 20 นาที"]
    if assessment.wound_type == "skin_tear":
        return ["silicone_contact", "foam"], ["Skin tear Type 1–2: จัด flap กลับโดยไม่ยืด และหลีกเลี่ยง adhesive strip"]
    if assessment.wound_type == "pressure" and assessment.pressure_stage == "stage1":
        return ["foam"], ["แผลกดทับ Stage 1: silicone foam border; offloading/เปลี่ยนท่าสำคัญที่สุด"]
    if assessment.wound_type == "pressure" and assessment.pressure_stage == "stage2":
        return ["foam", "hydrocolloid"], ["แผลกดทับ Stage 2 ตื้น: เลือกตามสารคัดหลั่งและข้อห้าม"]
    if assessment.wound_type == "leg_ulcer":
        return ["foam", "non_adherent"], ["VLU ที่แพทย์ยืนยัน: ใช้ dressing สนับสนุนแผน compression ของแพทย์"]
    if assessment.depth == "cavity_shallow":
        return ["alginate", "hydrofiber"], ["โพรงตื้น: ใช้ rope/ribbon ร่วมกับ secondary dressing; ห้ามอัดแน่น"]
    if assessment.tissue == "eschar":
        return ["non_adherent"], ["Eschar: ห้าม hydrogel/debride เอง; รักษา eschar ให้แห้งและปรึกษาแพทย์"]
    if assessment.tissue == "slough":
        if assessment.exudate in {"dry", "low"}:
            return ["hydrogel", "hydrocolloid"], ["Slough และสารคัดหลั่งน้อย: hydrogel หรือ hydrocolloid"]
        return ["foam", "hydrofiber"], ["Slough: เลือกตามระดับสารคัดหลั่ง"]
    if assessment.tissue == "epithelial":
        return ["silicone_contact", "film", "foam", "hydrocolloid"], ["ขอบแผลกำลังสร้างผิวใหม่: ปกป้องผิวและลดแรงดึง"]
    if assessment.wound_edge == "macerated":
        return ["foam", "hydrofiber"], ["ผิวรอบแผลเปื่อย: เพิ่มการดูดซับและใช้ skin barrier"]
    if assessment.exudate == "high":
        return ["foam", "alginate", "hydrofiber"], ["สารคัดหลั่งมาก: เลือกวัสดุดูดซับสูงและ secondary dressing ตามชนิด"]
    if assessment.exudate == "moderate":
        return ["foam", "hydrofiber"], ["สารคัดหลั่งปานกลาง: เลือก dressing ตาม tissue และข้อห้าม"]
    if assessment.exudate == "dry":
        return ["hydrogel", "silicone_contact", "non_adherent"], ["แผลแห้ง: รักษาความชุ่มชื้นพอเหมาะ"]
    if assessment.wound_type in {"abrasion", "laceration"}:
        return ["non_adherent", "silicone_contact", "hydrocolloid", "film"], ["แผลตื้นสะอาด: ล้างแผลและเลือกวัสดุไม่ติดแผล"]
    return ["non_adherent", "silicone_contact", "foam"], ["เลือกตามสภาพ tissue และสารคัดหลั่ง"]


def _filter_classes(
    assessment: WoundAssessment,
    candidates: list[str],
    infection_status: str,
) -> tuple[list[str], list[dict[str, str]]]:
    allergies = set(assessment.allergies)
    excluded = []
    kept = []
    for product_class in candidates:
        reason = None
        if infection_status == "mild_local" and product_class in {"film", "hydrocolloid"}:
            reason = "ติดเชื้อเฉพาะที่ระดับเบา: ห้ามใช้ film/hydrocolloid"
        elif assessment.exudate == "dry" and product_class in {"alginate", "hydrofiber", "foam"}:
            reason = "แผลแห้ง: dressing กลุ่มนี้ไม่เหมาะกับระดับสารคัดหลั่ง"
        elif assessment.exudate == "high" and product_class in {"hydrogel", "film", "hydrocolloid"}:
            reason = "สารคัดหลั่งมากเกินข้อบ่งใช้"
        elif "adhesive" in allergies and product_class in {"film", "hydrocolloid"}:
            reason = "มีประวัติแพ้กาว/พลาสเตอร์"
        elif "silicone" in allergies and product_class in {"silicone_contact", "foam"}:
            reason = "มีประวัติแพ้ซิลิโคน"
        elif "alginate" in allergies and product_class == "alginate":
            reason = "มีประวัติแพ้อัลจิเนต/สาหร่าย"
        elif "silver" in allergies and product_class == "silver":
            reason = "มีประวัติแพ้เงิน"
        elif "iodine" in allergies and product_class == "iodine":
            reason = "มีประวัติแพ้ไอโอดีน"
        elif "honey" in allergies and product_class == "honey":
            reason = "มีประวัติแพ้น้ำผึ้ง"
        elif product_class == "iodine" and (
            assessment.pregnancy == "yes"
            or assessment.thyroid_condition != "no"
            or assessment.age_group == "under_1"
        ):
            reason = "ข้อห้าม/ข้อควรระวังของ iodine: ไทรอยด์ ตั้งครรภ์/ให้นม หรือทารก"
        elif assessment.fragile_skin == "yes" and product_class in {"film", "hydrocolloid"}:
            reason = "ผิวบอบบาง: หลีกเลี่ยง adhesive แรงสูง"
        elif assessment.wound_edge == "macerated" and product_class in {"film", "hydrocolloid"}:
            reason = "ผิวรอบแผลเปื่อยยุ่ย"
        if reason:
            excluded.append({"name": _product_detail(product_class)["name"], "reason": reason})
        else:
            kept.append(product_class)
    return kept, excluded


def _rank_classes(
    assessment: WoundAssessment,
    candidates: list[str],
) -> list[str]:
    moisture_matches = {
        "high": {"foam", "hydrofiber", "alginate", "silver", "phmb_dacc"},
        "moderate": {"foam", "hydrofiber", "alginate", "hydrocolloid", "silver", "iodine", "honey", "phmb_dacc"},
        "low": {"film", "hydrocolloid", "non_adherent", "silicone_contact", "hydrogel", "silver", "iodine", "honey", "phmb_dacc"},
        "dry": {"hydrogel", "silicone_contact", "non_adherent", "honey"},
    }
    tissue_matches = {
        "granulation": {"foam", "hydrofiber", "alginate", "silver", "phmb_dacc"},
        "epithelial": {"film", "non_adherent", "silicone_contact", "foam"},
        "slough": {"hydrogel", "hydrofiber", "honey", "iodine"},
        "eschar": {"non_adherent"},
        "mixed": {"foam", "hydrofiber", "alginate", "silver", "phmb_dacc"},
    }
    scores = {}
    for product_class in candidates:
        score = 0
        if product_class in moisture_matches[assessment.exudate]:
            score += 3
        if product_class in tissue_matches[assessment.tissue] or product_class in {"alginate", "hydrofiber"} and assessment.depth == "cavity_shallow":
            score += 2
        if assessment.location in {"heel_bony", "joint"} and product_class in {"foam", "silicone_contact"}:
            score += 2
        product = _product_detail(product_class)
        if assessment.waterproof == "yes" and product.get("waterproof") is True:
            score += 1
        if assessment.dressing_frequency == "weekly" and product_class in {"hydrofiber", "hydrocolloid", "foam"}:
            score += 1
        cost_tier = product.get("cost_tier")
        budget_ceiling = {"low": 1, "medium": 2, "unlimited": None}[assessment.budget]
        if cost_tier is not None and (budget_ceiling is None or cost_tier <= budget_ceiling):
            score += 1
        if assessment.self_care != "independent" and product_class in {"hydrofiber", "hydrocolloid", "foam"}:
            score += 1
        scores[product_class] = score
    return sorted(candidates, key=lambda item: (-scores[item], candidates.index(item)))[:3]


def _refer_result(referrals: list[dict[str, str]]) -> dict:
    return {
        "triage": {"level": "refer", "label": "ส่งต่อแพทย์"},
        "referrals": referrals,
        "recommendations": [],
        "reasons": [item["reason"] for item in referrals],
        "advice": [
            "ส่งต่อแพทย์ตามเหตุผลที่ระบุ โดยไม่เลือกผลิตภัณฑ์ต่อ",
            "ห้ามตัดเนื้อตายหรือทำ debridement เอง",
        ],
        "follow_up": [],
        "clinical_status": "ระบบสนับสนุนการตัดสินใจเบื้องต้น ไม่ทดแทนการวินิจฉัยหรือคำแนะนำจากบุคลากรทางการแพทย์",
        "references": REFERENCES,
    }


def _severity(assessment: WoundAssessment, infection_status: str) -> str:
    if (
        infection_status == "mild_local"
        or assessment.age_group == "65_plus"
        or assessment.fragile_skin == "yes"
        or assessment.exudate in {"moderate", "high"}
        or assessment.duration == "gt4w" and assessment.clinician_plan == "yes"
    ):
        return "ปานกลาง"
    return "ต่ำ"


def assess_wound(assessment: WoundAssessment) -> dict:
    infection_status, infection_referrals = _infection_gate(assessment)
    referrals = _get_referrals(assessment)
    if infection_referrals:
        referrals.extend(infection_referrals)
    if referrals:
        return _refer_result(referrals)

    candidates, reasons = _candidate_classes(assessment, infection_status)
    candidates, excluded = _filter_classes(assessment, candidates, infection_status)
    candidates = _rank_classes(assessment, candidates)
    recommendations = []
    for product_class in candidates:
        product = _product_detail(product_class)
        recommendations.append({
            "id": product_class,
            "name": product["name"],
            "use": product["use"],
            "wear": product["wear"] if product_class in PRODUCT_CLASSES else ANTIMICROBIAL_WEAR[product_class],
            "caution": product["caution"],
            "secondary": product_class in {"alginate", "hydrofiber", "silicone_contact"},
        })

    if not recommendations:
        reasons.append("ไม่พบผลิตภัณฑ์ที่ผ่านตัวกรองข้อห้าม; ควรส่งต่อให้แพทย์ประเมิน")
        return _refer_result([_referral("ENGINE 2", reasons[-1])])

    advice = [
        "ล้างมือก่อนและหลังทำแผล และล้างแผลด้วยน้ำสะอาดไหลผ่านหรือน้ำเกลือ (NSS) โดยไม่ถูแรง",
        "หลีกเลี่ยงแอลกอฮอล์ น้ำยาฆ่าเชื้อเข้มข้น หรือไฮโดรเจนเปอร์ออกไซด์ซ้ำ ๆ บนเนื้อแผล เว้นแต่แพทย์สั่ง",
        "ห้ามตัดเนื้อตายเอง เจาะตุ่มพอง หรือใช้น้ำปลา ยาสีฟัน น้ำแข็ง หรือเนยกับแผลไหม้",
    ]
    if infection_status == "mild_local":
        advice.extend([
            "ประเมินแผลซ้ำภายใน 48–72 ชั่วโมง และเมื่อครบ 2 สัปดาห์",
            "หากไม่มีสัญญาณติดเชื้อแล้ว ให้หยุด antimicrobial และกลับไปใช้ dressing ตามชนิดแผล",
        ])
        follow_up = [
            "ประเมินซ้ำใน 48–72 ชั่วโมง และครบ 2 สัปดาห์",
            "หากไม่ดีขึ้น แย่ลง หรือมีสัญญาณใหม่ ให้ส่งต่อแพทย์",
        ]
    else:
        follow_up = [
            "ประเมินแนวโน้มการหายภายใน 2 สัปดาห์; หากไม่ดีขึ้นหรือขนาดลดลงน้อยกว่า 20–30% ให้ส่งต่อแพทย์",
        ]
    follow_up.append("ส่งต่อทันทีหากมีไข้ แดงบวมร้อนมากขึ้น หนอง กลิ่นเหม็นเพิ่ม ปวดเพิ่ม เลือดออกไม่หยุด หรือแผลขยาย")

    severity = _severity(assessment, infection_status)
    return {
        "triage": {"level": "care", "label": "ผลิตภัณฑ์ปิดแผลที่แนะนำ"},
        "referrals": [],
        "recommendations": recommendations,
        "reasons": reasons,
        "excluded_products": excluded,
        "advice": advice,
        "follow_up": follow_up,
        "is_infected": infection_status == "mild_local",
        "infection_status": infection_status,
        "wound_type": CHOICE_LABELS["wound_type"][assessment.wound_type],
        "severity": severity,
        "time_profile": {
            "tissue": CHOICE_LABELS["tissue"][assessment.tissue],
            "infection": "ติดเชื้อเฉพาะที่ระดับเบา" if infection_status == "mild_local" else "ไม่ติดเชื้อ",
            "moisture": CHOICE_LABELS["exudate"][assessment.exudate],
            "edge": CHOICE_LABELS["wound_edge"][assessment.wound_edge],
            "depth": CHOICE_LABELS["depth"][assessment.depth],
            "size": CHOICE_LABELS["wound_size"][assessment.wound_size],
            "location": CHOICE_LABELS["location"][assessment.location],
        },
        "assessment": [
            {"label": label, "value": value}
            for label, value in (
                ("ชนิดแผล", CHOICE_LABELS["wound_type"][assessment.wound_type]),
                ("ความรุนแรง", severity),
                ("สถานะติดเชื้อ", "ติดเชื้อเฉพาะที่ระดับเบา" if infection_status == "mild_local" else "ไม่ติดเชื้อ"),
            )
        ],
        "warnings": [
            "ข้อมูลเป็นข้อเสนอเชิงออกแบบ ต้องให้ผู้เชี่ยวชาญด้านแผลตรวจสอบก่อนใช้งานจริง",
            "รายชื่อแบรนด์/เลขทะเบียน อย. และระดับราคาในฐานข้อมูลยังไม่ผ่านการยืนยัน จึงไม่แสดงแบรนด์หรือจัดอันดับตามราคา",
        ],
        "references": REFERENCES,
        "clinical_status": "ระบบสนับสนุนการตัดสินใจเบื้องต้น ไม่ทดแทนการวินิจฉัยหรือคำแนะนำจากบุคลากรทางการแพทย์",
    }
