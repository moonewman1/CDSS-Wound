from wound_rules import DRESSING_RULES, REFERRAL_CRITERIA


def assess_wound(
    wound_type,
    depth,
    exudate,
    wound_bed,
    infection,
    periwound,
    location
):

    recommendations = []
    reasons = []
    warnings = []

    # ==========================================
    # 1. Basic information
    # ==========================================

    assessment = {
        "wound_type": wound_type,
        "depth": depth,
        "exudate": exudate,
        "wound_bed": wound_bed,
        "infection": infection,
        "periwound": periwound,
        "location": location
    }


    # ==========================================
    # 2. Check referral criteria
    # ==========================================

    if infection == "yes":

        warnings.append(
            "พบลักษณะที่สงสัยการติดเชื้อ ควรประเมินผู้ป่วยเพิ่มเติมและพิจารณาส่งต่อ"
        )


    if depth == "deep":

        warnings.append(
            "แผลมีความลึก ควรได้รับการประเมินเพิ่มเติมโดยบุคลากรทางการแพทย์"
        )


    # ==========================================
    # 3. Dressing recommendation
    # ==========================================

    for rule in DRESSING_RULES:

        condition = rule["condition"]

        matched = True

        for key, value in condition.items():

            if assessment.get(key) != value:

                matched = False
                break

        if matched:

            recommendations.extend(
                rule["recommendation"]
            )

            reasons.append(
                rule["reason"]
            )


    # ==========================================
    # 4. If no rule matched
    # ==========================================

    if not recommendations:

        recommendations.append(
            "ไม่พบคำแนะนำที่ตรงกับข้อมูลทั้งหมด ควรประเมินแผลเพิ่มเติม"
        )


    # ==========================================
    # 5. Return result
    # ==========================================

    return {

        "assessment": assessment,

        "recommendations": recommendations,

        "reasons": reasons,

        "warnings": warnings

    }