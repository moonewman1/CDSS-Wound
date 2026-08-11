from pydantic import BaseModel


class WoundAssessment(BaseModel):

    wound_type: str
    depth: str
    exudate: str
    wound_bed: str
    infection: str
    periwound: str
    location: str