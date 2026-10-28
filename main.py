import hashlib
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError

from models import RedFlagScreening, WoundAssessment
from wound_logic import assess_red_flags, assess_wound
from wound_rules import MULTI_SELECT_CHOICES, RED_FLAG_QUESTIONS


app = FastAPI(
    title="CDSS-Wound",
    description="Clinical Decision Support System for Wound Dressing Selection",
    version="1.0.0"
)

# Templates
templates = Jinja2Templates(directory="templates")
static_content = Path("static/style.css").read_bytes() + Path("static/script.js").read_bytes()
templates.env.globals["static_version"] = hashlib.sha256(static_content).hexdigest()[:12]


# Static files
app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)


# =========================
# Home page
# =========================

@app.get("/")
def home(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )


# =========================
# Assessment page
# =========================

@app.get("/assessment")
def assessment(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="assessment.html",
        context={"red_flags": RED_FLAG_QUESTIONS},
    )


# =========================
# Process assessment
# =========================

@app.post("/assess")
async def assess(request: Request):
    form = await request.form()
    red_flags = {code: form.get(code, "") for code in RED_FLAG_QUESTIONS}
    try:
        RedFlagScreening(red_flags=red_flags)
    except ValidationError as error:
        messages = "; ".join(item["msg"] for item in error.errors())
        raise HTTPException(status_code=422, detail=messages) from error

    if any(answer in {"yes", "unable"} for answer in red_flags.values()):
        return templates.TemplateResponse(
            request=request,
            name="result.html",
            context={"result": assess_red_flags(red_flags)},
        )

    payload = {"red_flags": red_flags}
    for field in WoundAssessment.model_fields:
        if field == "red_flags":
            continue
        if field in MULTI_SELECT_CHOICES:
            payload[field] = form.getlist(field)
        else:
            payload[field] = form.get(field, "")

    try:
        assessment_data = WoundAssessment.model_validate(payload)
    except ValidationError as error:
        messages = "; ".join(item["msg"] for item in error.errors())
        raise HTTPException(status_code=422, detail=messages) from error

    result = assess_wound(assessment_data)

    return templates.TemplateResponse(
        request=request,
        name="result.html",
        context={
            "result": result
        }
    )