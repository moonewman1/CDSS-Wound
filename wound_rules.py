# ==========================================
# Wound type
# ==========================================

WOUND_TYPES = {
    "abrasion": "แผลถลอก",
    "laceration": "แผลฉีกขาด",
    "burn": "แผลไหม้",
    "pressure": "แผลกดทับ",
    "other": "อื่น ๆ"
}


# ==========================================
# Exudate
# ==========================================

EXUDATE_LEVEL = {
    "none": "ไม่มี",
    "low": "น้อย",
    "moderate": "ปานกลาง",
    "high": "มาก"
}


# ==========================================
# Clinical rules
# ==========================================

DRESSING_RULES = [

    {
        "condition": {
            "exudate": "high"
        },

        "recommendation": [
            "พิจารณา dressing ที่มีความสามารถในการดูดซับสารคัดหลั่งสูง"
        ],

        "reason": "มีสารคัดหลั่งปริมาณมาก"
    },

    {
        "condition": {
            "exudate": "moderate"
        },

        "recommendation": [
            "พิจารณา absorbent dressing ที่เหมาะสมกับ wound bed"
        ],

        "reason": "มีสารคัดหลั่งปริมาณปานกลาง"
    },

    {
        "condition": {
            "exudate": "low"
        },

        "recommendation": [
            "พิจารณา dressing ที่ช่วยรักษาสภาพแวดล้อมของแผลให้เหมาะสม"
        ],

        "reason": "มีสารคัดหลั่งปริมาณน้อย"
    },

    {
        "condition": {
            "exudate": "none"
        },

        "recommendation": [
            "พิจารณา non-adherent หรือ protective dressing ตามลักษณะแผล"
        ],

        "reason": "ไม่มีสารคัดหลั่ง"
    }
]


# ==========================================
# Referral criteria
# ==========================================

REFERRAL_CRITERIA = {

    "infection": {
        "yes": True
    },

    "depth": {
        "deep": True
    }
}