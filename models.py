from pydantic import BaseModel, ConfigDict, Field, model_validator

from wound_rules import (
    ASSESSMENT_CHOICES,
    MULTI_SELECT_CHOICES,
    RED_FLAG_CHOICES,
    RED_FLAG_QUESTIONS,
)


class RedFlagScreening(BaseModel):
    model_config = ConfigDict(extra="forbid")

    red_flags: dict[str, str]

    @model_validator(mode="after")
    def validate_red_flags(self):
        if set(self.red_flags) != set(RED_FLAG_QUESTIONS):
            raise ValueError("ต้องตอบคำถามคัดกรองอันตรายให้ครบทุกข้อ")
        for key, value in self.red_flags.items():
            if value not in RED_FLAG_CHOICES[key]:
                raise ValueError(f"คำตอบคัดกรอง {key} ไม่ถูกต้อง")
        return self


class WoundAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    red_flags: dict[str, str]
    age_group: str
    comorbidities: list[str] = Field(default_factory=list)
    healing_factors: list[str] = Field(default_factory=list)
    medications: list[str] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)
    pregnancy: str
    thyroid_condition: str
    fragile_skin: str
    self_care: str
    wound_type: str
    duration: str
    leg_profile: str
    pressure_stage: str
    burn_depth: str
    skin_tear_type: str
    tissue: str
    depth: str
    infection_signs: list[str] = Field(default_factory=list)
    erythema_extent: str
    purulence: str
    exudate: str
    exudate_character: str
    wound_edge: str
    wound_size: str
    pain: str
    location: str
    previous_care: list[str] = Field(default_factory=list)
    clinician_plan: str
    waterproof: str
    dressing_frequency: str
    budget: str

    @model_validator(mode="after")
    def validate_answer_choices(self):
        RedFlagScreening(red_flags=self.red_flags)

        for field, allowed in ASSESSMENT_CHOICES.items():
            if getattr(self, field) not in allowed:
                raise ValueError(f"คำตอบ {field} ไม่ถูกต้อง")
        for field, allowed in MULTI_SELECT_CHOICES.items():
            values = getattr(self, field)
            if len(values) != len(set(values)) or not set(values).issubset(allowed):
                raise ValueError(f"คำตอบ {field} ไม่ถูกต้อง")
        return self
