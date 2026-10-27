from models import WoundAssessment
from wound_rules import (
    CHOICE_LABELS,
    FIELD_LABELS,
    MULTI_SELECT_LABELS,
    PRODUCT_CLASSES,
    PRODUCT_CATALOG_NOTE,
    RED_FLAG_QUESTIONS,
    REFERENCES,
    RESTRICTED_PRODUCT_CLASSES,
)


EMERGENCY_FLAGS = {"a6", "a7", "a9"}
URGENT_FLAGS = {"a1", "a2", "a3", "a4", "a5", "a8"}


def _label(field: str, value: str) -> str:
    return CHOICE_LABELS.get(field, {}).get(value, value)


def _referral(code: str, reason: str, timeframe: str) -> dict[str, str]:
    return {"code": code, "reason": reason, "timeframe": timeframe}


def _get_referrals(assessment: WoundAssessment) -> list[dict[str, str]]:
    referrals = []
    for code, answer in assessment.red_flags.items():
        if answer == "no" or (code == "a11" and answer == "no"):
            continue
        if code == "a11" and answer == "unknown":
            referrals.append(_referral(code, RED_FLAG_QUESTIONS[code], "ปรึกษาบุคลากรทางการแพทย์โดยเร็ว"))
        elif code in EMERGENCY_FLAGS:
            referrals.append(_referral(code, RED_FLAG_QUESTIONS[code], "ฉุกเฉิน: ส่งห้องฉุกเฉิน/โทร 1669 ทันที"))
        elif code == "a10":
            referrals.append(_referral(code, RED_FLAG_QUESTIONS[code], "นัดพบแพทย์ภายใน 1 สัปดาห์"))
        elif code == "a12":
            referrals.append(_referral(code, RED_FLAG_QUESTIONS.get(code, "ผู้ป่วยอยู่ในกลุ่มเสี่ยงสูง"), "ปรึกษาแพทย์โดยเร็ว"))
        else:
            timeframe = "ส่งต่อภายในวันเดียวกัน" if code == "a8" else "ประเมินและส่งต่อโดยเร็ว"
            referrals.append(_referral(code, RED_FLAG_QUESTIONS[code], timeframe))

    comorbidities = set(assessment.comorbidities)
    if "diabetes" in comorbidities and assessment.wound_type == "foot_ulcer":
        referrals.append(_referral("B2", "แผลที่เท้าร่วมกับเบาหวาน", "ส่งต่อภายในวันเดียวกัน"))
    if "pad" in comorbidities and assessment.wound_type in {"foot_ulcer", "leg_ulcer"}:
        referrals.append(_referral("B2", "แผลที่เท้าหรือขาร่วมกับ PAD", "ส่งต่อภายในวันเดียวกัน"))
    if assessment.wound_type == "leg_ulcer" and assessment.leg_profile in {"arterial", "mixed", "uncertain"}:
        referrals.append(_referral("C3", "แผลที่ขาสงสัยหลอดเลือดแดง/ชนิดผสม/ไม่แน่ใจ; ห้ามใช้ compression", "ส่งต่อแพทย์โดยเร็ว"))
    if assessment.wound_type == "leg_ulcer" and assessment.leg_profile == "venous" and assessment.clinician_plan == "no":
        referrals.append(_referral("C3", "แผลหลอดเลือดดำต้องได้รับการยืนยันและมีแผนจากแพทย์ก่อนดูแลต่อ", "ส่งต่อแพทย์โดยเร็ว"))
    if assessment.wound_type == "pressure" and assessment.pressure_stage in {
        "stage3", "stage4", "dtpi", "unstageable",
    }:
        referrals.append(_referral("C4", "แผลกดทับ Stage 3–4, DTPI หรือจัดระยะไม่ได้", "ส่งต่อแพทย์โดยเร็ว"))
    if assessment.wound_type == "burn" and assessment.burn_depth in {"deep_partial", "full_thickness"}:
        referrals.append(_referral("C5", "แผลไหม้สงสัยลึก (deep partial/full thickness)", "ส่งต่อฉุกเฉิน/โดยเร็ว"))
    if assessment.wound_type == "skin_tear" and assessment.skin_tear_type == "type3":
        referrals.append(_referral("C6", "ผิวหนังฉีก ISTAP Type 3", "ส่งต่อแพทย์โดยเร็ว"))
    if assessment.wound_type == "surgical" and assessment.clinician_plan == "no":
        referrals.append(_referral("C1", "แผลผ่าตัดควรดูแลตามแผนศัลยแพทย์", "ติดต่อทีมรักษา"))
    if assessment.duration == "gt4w":
        referrals.append(_referral("C2", "แผลเป็นมานานกว่า 4 สัปดาห์", "นัดพบแพทย์ภายใน 1 สัปดาห์"))
    if assessment.depth in {"moderate", "cavity"}:
        referrals.append(_referral("D2", "แผลลึกปานกลางหรือมีโพรง/ร่อง", "ส่งต่อแพทย์โดยเร็ว"))
    if assessment.tissue == "eschar" and assessment.location in {"heel_bony", "weight_bearing_foot"}:
        referrals.append(_referral("D1", "พบ eschar บริเวณส้นเท้าหรือเท้า; ห้ามตัด/ทำ debridement เอง", "ส่งต่อแพทย์โดยเร็ว"))
    if assessment.tissue == "eschar" and "pad" in comorbidities:
        referrals.append(_referral("D1", "พบ eschar ร่วมกับ PAD; ห้ามตัด/ทำ debridement เอง", "ส่งต่อแพทย์โดยเร็ว"))

    if assessment.infection_signs:
        timeframe = "ฉุกเฉิน: ส่งห้องฉุกเฉิน/โทร 1669 ทันที" if len(assessment.infection_signs) > 3 else "ให้แพทย์ประเมินภายในวันเดียวกัน"
        referrals.append(_referral("D3", "พบสัญญาณติดเชื้อเฉพาะที่; ห้ามเลือก antimicrobial dressing หรือรักษาแทนแพทย์", timeframe))

    is_high_risk = (
        assessment.age_group == "under_1"
        or assessment.pregnancy == "yes"
        or "immunosuppressed" in comorbidities
        or bool({"chemotherapy", "steroid", "anticoagulant"} & set(assessment.medications))
    )
    if is_high_risk:
        referrals.append(_referral("A12", "ผู้ป่วยอยู่ในกลุ่มเสี่ยงสูง", "ปรึกษาแพทย์/เภสัชกรผู้เชี่ยวชาญโดยเร็ว"))
    return referrals


def _candidate_classes(assessment: WoundAssessment) -> tuple[list[str], list[str]]:
    reasons = []
    if assessment.wound_type == "pressure" and assessment.pressure_stage == "stage1":
        return ["foam"], ["แผลกดทับ Stage 1: ใช้โฟมเพื่อป้องกันและลดแรงเสียดสี; การลดแรงกดสำคัญที่สุด"]
    if assessment.wound_type == "pressure" and assessment.pressure_stage == "stage2":
        classes = ["foam", "hydrocolloid"] if assessment.exudate in {"low", "moderate"} else ["foam"]
        return classes, ["แผลกดทับ Stage 2 ตื้น: พิจารณาโฟมหรือไฮโดรคอลลอยด์เมื่อไม่มีข้อห้าม"]
    if assessment.wound_type == "blister":
        return ["hydrocolloid", "foam"], ["ตุ่มพองจากเสียดสี: ปกป้องแผลและลดแรงเสียดสี; ไม่เจาะตุ่ม"]
    if assessment.wound_type == "skin_tear":
        return ["silicone_contact", "foam", "non_adherent"], ["ผิวหนังฉีก Type 1–2: ลดแรงดึงและการบาดเจ็บตอนเปลี่ยนแผล"]
    if assessment.wound_type == "burn":
        return ["silicone_contact", "non_adherent", "hydrogel"], ["แผลไหม้ตื้นขนาดเล็ก: ใช้แผ่นไม่ติดแผล; ให้ความเย็นด้วยน้ำไหลก่อนปิดแผล"]
    if assessment.wound_type == "pressure":
        return ["foam"], ["เลือกวัสดุปิดแผลไม่ติดแผลและให้ความสำคัญกับการลดแรงกด"]
    if assessment.tissue == "eschar":
        return ["non_adherent"], ["หลีกเลี่ยงการทำให้ eschar แห้งเสียหายเพิ่ม; ห้ามตัดเนื้อตายเอง"]
    if assessment.tissue == "slough" and assessment.exudate in {"dry", "low"}:
        return ["hydrogel", "non_adherent"], ["พบ slough และสารคัดหลั่งน้อย: พิจารณารักษาความชุ่มชื้นหลังประเมินการติดเชื้อ"]
    if assessment.exudate == "high":
        return ["foam", "hydrofiber", "alginate"], ["สารคัดหลั่งมาก: เลือกวัสดุดูดซับสูงและติดตามผิวหนังรอบแผล"]
    if assessment.exudate == "moderate":
        return ["foam", "hydrofiber"], ["สารคัดหลั่งปานกลาง: เลือกวัสดุดูดซับให้เหมาะกับแผล"]
    if assessment.exudate == "dry":
        return ["hydrogel", "silicone_contact", "non_adherent"], ["แผลแห้ง: รักษาความชุ่มชื้นพอเหมาะและหลีกเลี่ยงวัสดุดูดซับสูง"]
    if assessment.wound_edge == "macerated":
        return ["foam", "hydrofiber"], ["ผิวรอบแผลเปื่อยยุ่ย: ลดความชื้นส่วนเกินและปกป้องผิวรอบแผล"]
    if assessment.wound_type in {"abrasion", "laceration"} and assessment.exudate in {"low", "moderate"}:
        return ["non_adherent", "hydrocolloid", "film"], ["แผลตื้นสะอาด: ล้างแผลและใช้วัสดุปิดแผลที่ไม่ติดแผล"]
    return ["non_adherent", "silicone_contact", "film"], ["แผลตื้นและมีสารคัดหลั่งน้อย: ปกป้องแผลโดยลดการติดแผล"]


def _filter_classes(
    assessment: WoundAssessment,
    candidates: list[str],
) -> tuple[list[str], list[dict[str, str]]]:
    allergies = set(assessment.allergies)
    excluded = []
    kept = []
    for product_class in candidates:
        reason = None
        if assessment.exudate == "dry" and product_class in {"alginate", "hydrofiber"}:
            reason = "แผลแห้ง: เสี่ยงทำให้แผลแห้ง/ติดแผล"
        elif assessment.exudate == "high" and product_class in {"hydrogel", "hydrocolloid", "film"}:
            reason = "สารคัดหลั่งมากเกินข้อบ่งใช้"
        elif "adhesive" in allergies and product_class in {"film", "hydrocolloid"}:
            reason = "มีประวัติแพ้กาว/พลาสเตอร์"
        elif "silicone" in allergies and product_class in {"silicone_contact", "foam"}:
            reason = "มีประวัติแพ้ซิลิโคน; ต้องให้ผู้เชี่ยวชาญตรวจส่วนประกอบ"
        elif "alginate" in allergies and product_class == "alginate":
            reason = "มีประวัติแพ้อัลจิเนต/สาหร่าย"
        elif assessment.wound_edge == "macerated" and product_class in {"film", "hydrocolloid"}:
            reason = "ผิวรอบแผลเปื่อยยุ่ย"
        if reason:
            excluded.append({"name": PRODUCT_CLASSES[product_class]["name"], "reason": reason})
        else:
            kept.append(product_class)
    return kept, excluded


def _rank_classes(assessment: WoundAssessment, candidates: list[str]) -> list[str]:
    scores = {product_class: 0 for product_class in candidates}
    moisture_matches = {
        "high": {"foam", "hydrofiber", "alginate"},
        "moderate": {"foam", "hydrofiber", "alginate", "hydrocolloid"},
        "low": {"film", "hydrocolloid", "non_adherent", "silicone_contact"},
        "dry": {"hydrogel", "silicone_contact", "non_adherent"},
    }
    tissue_matches = {
        "granulation": {"foam", "hydrofiber", "alginate"},
        "epithelial": {"film", "non_adherent", "silicone_contact"},
        "slough": {"hydrogel", "hydrofiber"},
        "eschar": {"non_adherent"},
        "mixed": {"foam", "hydrofiber"},
    }
    for product_class in candidates:
        if product_class in moisture_matches[assessment.exudate]:
            scores[product_class] += 3
        if product_class in tissue_matches[assessment.tissue]:
            scores[product_class] += 2
        if assessment.location in {"heel_bony", "joint"} and product_class == "foam":
            scores[product_class] += 2
        if assessment.waterproof == "yes" and product_class in {"film", "hydrocolloid"}:
            scores[product_class] += 1
        if assessment.dressing_frequency == "weekly" and product_class in {"hydrofiber", "hydrocolloid", "foam"}:
            scores[product_class] += 1
        if assessment.self_care != "independent" and product_class in {"hydrofiber", "hydrocolloid", "foam"}:
            scores[product_class] += 1
    return sorted(candidates, key=lambda product_class: (-scores[product_class], candidates.index(product_class)))[:3]


def _patient_advice(assessment: WoundAssessment, referred: bool) -> list[str]:
    if referred:
        advice = [
            "ให้ไปพบแพทย์ตามระดับความเร่งด่วนที่แสดง และอย่ารอผลจากระบบนี้ก่อนส่งต่อ",
            "หากมีเลือดออก ให้ใช้ผ้าสะอาดกดตรงแผลต่อเนื่อง; หากมีอาการฉุกเฉินให้โทร 1669",
            "อย่าตัดเนื้อตาย เจาะตุ่ม หรือใส่ยาพื้นบ้าน/ยาฆ่าเชื้อเข้มข้นลงบนแผล",
        ]
        if assessment.wound_type == "burn":
            advice.insert(0, "แผลไหม้: ลดความร้อนด้วยน้ำก๊อกไหลผ่าน 20 นาที (ไม่ใช้น้ำแข็ง) โดยไม่ชะลอการส่งต่อ")
        return advice

    advice = [
        "ล้างมือก่อนและหลังทำแผล; ล้างแผลด้วยน้ำสะอาดไหลผ่านหรือน้ำเกลือ โดยไม่ถูแรง",
        "หลีกเลี่ยงแอลกอฮอล์ ไฮโดรเจนเปอร์ออกไซด์ น้ำยาฆ่าเชื้อเข้มข้น และของพื้นบ้าน เว้นแต่แพทย์สั่ง",
        "เปลี่ยนแผ่นปิดเมื่อเปียก สกปรก หลุด หรือชุ่มสารคัดหลั่ง; ลอกอย่างช้า ๆ ขนานกับผิว",
        "กลับมาประเมินหากแผลไม่ดีขึ้น; หากไม่ดีขึ้นภายใน 2 สัปดาห์หรือขนาดไม่ลดลง ให้พบแพทย์",
    ]
    if assessment.wound_type == "burn":
        advice.insert(0, "แผลไหม้ตื้นขนาดเล็ก: ลดความร้อนด้วยน้ำก๊อกไหลผ่าน 20 นาที; ไม่ใช้น้ำแข็ง ไม่เจาะตุ่ม และไม่ทายาสีฟัน/เนย")
    elif assessment.wound_type == "pressure":
        advice.insert(0, "ลดแรงกดและการเสียดสี เปลี่ยนท่าตามความเหมาะสม; ห้ามนวดบริเวณที่แดง")
    elif assessment.wound_type == "skin_tear":
        advice.insert(0, "หลีกเลี่ยงพลาสเตอร์ที่ติดผิวโดยตรง และลอกวัสดุปิดแผลตามแนวผิวอย่างระมัดระวัง")
    elif assessment.wound_type == "blister":
        advice.insert(0, "ลดแรงเสียดสีและปรับรองเท้าหรืออุปกรณ์; อย่าเจาะตุ่มพอง")
    if assessment.wound_edge == "macerated":
        advice.append("ปกป้องผิวรอบแผลที่เปื่อยยุ่ยและประเมินความชื้น/การซึมของแผลซ้ำ")
    if assessment.comorbidities:
        advice.append("โรคร่วมอาจมีผลต่อการหายของแผล; ปรึกษาแพทย์เรื่องการควบคุมโรคและยาที่ใช้อยู่")
    return advice


def assess_wound(assessment: WoundAssessment) -> dict:
    referrals = _get_referrals(assessment)
    is_emergency = any(
        item["code"] in EMERGENCY_FLAGS or (
            item["code"] == "D3" and len(assessment.infection_signs) > 3
        )
        for item in referrals
    )
    is_urgent = bool(referrals)
    if is_emergency:
        triage = {"level": "emergency", "label": "ส่งต่อฉุกเฉิน", "timeframe": "ทันที"}
    elif is_urgent:
        triage = {"level": "refer", "label": "ควรส่งต่อ/ปรึกษาแพทย์", "timeframe": "ตามเหตุผลในรายการส่งต่อ"}
    else:
        triage = {"level": "care", "label": "ประเมินเพื่อดูแลเบื้องต้น", "timeframe": "ติดตามอาการใกล้ชิด"}

    comorbidities = set(assessment.comorbidities)
    risk_factors = bool(
        comorbidities
        or assessment.age_group in {"under_1", "65_plus"}
        or assessment.fragile_skin == "yes"
        or assessment.pregnancy == "yes"
        or assessment.medications
    )
    if is_urgent or assessment.depth != "superficial" or assessment.infection_signs:
        severity = {"level": "high", "label": "สูง"}
    elif risk_factors or assessment.exudate in {"moderate", "high"} or assessment.duration == "1_4w":
        severity = {"level": "moderate", "label": "ปานกลาง"}
    else:
        severity = {"level": "low", "label": "ต่ำ"}

    raw_recommendations = []
    reasons = []
    excluded = []
    if not is_urgent:
        candidates, reasons = _candidate_classes(assessment)
        candidates, excluded = _filter_classes(assessment, candidates)
        candidates = _rank_classes(assessment, candidates)
        for product_class in candidates:
            item = PRODUCT_CLASSES[product_class]
            raw_recommendations.append({
                "name": item["name"],
                "use": item["use"],
                "wear": item["wear"],
                "caution": item["caution"],
                "brands": item["brands"],
                "verification": "ตัวอย่างจากเอกสารแนบ; ยังไม่ยืนยันทะเบียน อย. หรือการจำหน่ายในไทย และไม่ใช่รายชื่อครบถ้วน",
                "cost_note": "เอกสารแนบไม่มีข้อมูลราคา จึงไม่จัดอันดับตามงบประมาณ",
                "secondary": product_class in {"alginate", "hydrofiber", "silicone_contact"},
            })
        if not raw_recommendations:
            reasons.append("ไม่พบชนิดผลิตภัณฑ์ที่ผ่านตัวกรองข้อห้าม; ควรประเมินโดยผู้เชี่ยวชาญ")

    assessment_summary = []
    for code, answer in assessment.red_flags.items():
        assessment_summary.append({
            "label": f"{code.upper()} · {RED_FLAG_QUESTIONS[code]}",
            "value": {"yes": "ใช่", "no": "ไม่ใช่", "unable": "ประเมินไม่ได้", "unknown": "ไม่ทราบ"}[answer],
        })
    for field in WoundAssessment.model_fields:
        if field == "red_flags":
            continue
        value = getattr(assessment, field)
        if isinstance(value, list):
            labels = [MULTI_SELECT_LABELS[field][item] for item in value]
            display = "ไม่มี/ไม่ได้เลือก" if not labels else ", ".join(labels)
        else:
            display = _label(field, value)
        assessment_summary.append({"label": FIELD_LABELS[field], "value": display})

    infection_status = "พบสัญญาณที่ต้องให้แพทย์ประเมิน" if assessment.infection_signs else "ไม่พบสัญญาณติดเชื้อที่เลือก"
    warnings = [
        "NICE ไม่ได้หมายถึงการรับรองผลิตภัณฑ์ปิดแผลรายแบรนด์; เอกสารแนบระบุให้เลือกตามการประเมินทางคลินิก",
        PRODUCT_CATALOG_NOTE,
    ]
    if is_urgent:
        warnings.append("พบข้อมูลที่ต้องส่งต่อหรือปรึกษาแพทย์ ระบบจึงหยุดการแนะนำผลิตภัณฑ์")
    if assessment.infection_signs:
        warnings.append("ไม่แนะนำให้เริ่ม antimicrobial dressing จากระบบนี้; การใช้ต้องเป็นไปตามแผนแพทย์และประเมินซ้ำ")
    if raw_recommendations:
        warnings.append("ชื่อแบรนด์เป็นเพียงตัวอย่างในเอกสารแนบ ไม่ได้ยืนยันการขึ้นทะเบียน อย. การวางจำหน่ายปัจจุบัน หรือความครบถ้วนในประเทศไทย")
        warnings.append("ข้อมูลต้นทางไม่มีราคาและระดับราคา ระบบจึงไม่เปรียบเทียบต้นทุน")

    return {
        "assessment": assessment_summary,
        "wound_type": _label("wound_type", assessment.wound_type),
        "severity": severity,
        "triage": triage,
        "infection_status": infection_status,
        "time_profile": {
            "tissue": _label("tissue", assessment.tissue),
            "infection": infection_status,
            "moisture": _label("exudate", assessment.exudate),
            "edge": _label("wound_edge", assessment.wound_edge),
            "depth": _label("depth", assessment.depth),
            "size": _label("wound_size", assessment.wound_size),
            "location": _label("location", assessment.location),
        },
        "referrals": referrals,
        "recommendations": raw_recommendations,
        "restricted_products": RESTRICTED_PRODUCT_CLASSES,
        "reasons": reasons,
        "excluded_products": excluded,
        "warnings": warnings,
        "advice": _patient_advice(assessment, is_urgent),
        "follow_up": [
            "ประเมินแนวโน้มการหายภายใน 2 สัปดาห์; หากไม่ดีขึ้น/ขนาดไม่ลดลง ให้ส่งต่อแพทย์",
            "ส่งต่อทันทีหากมีไข้ แดงบวมร้อนมากขึ้น หนอง กลิ่นเหม็นเพิ่ม ปวดมากขึ้น เลือดออกไม่หยุด หรือแผลขยาย",
        ],
        "references": REFERENCES,
        "clinical_status": "ข้อมูลตั้งต้นจากเอกสารร่าง ต้องให้ผู้เชี่ยวชาญตรวจสอบและยืนยันทะเบียน/การจำหน่ายก่อนใช้จริง",
    }
