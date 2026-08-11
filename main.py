from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from wound_logic import assess_wound


app = FastAPI(
    title="CDSS-Wound",
    description="Clinical Decision Support System for Wound Dressing Selection",
    version="1.0.0"
)


# Templates
templates = Jinja2Templates(directory="templates")


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
        name="assessment.html"
    )


# =========================
# Process assessment
# =========================

@app.post("/assess")
def assess(
    request: Request,

    wound_type: str = Form(...),
    depth: str = Form(...),
    exudate: str = Form(...),
    wound_bed: str = Form(...),
    infection: str = Form(...),
    periwound: str = Form(...),
    location: str = Form(...)
):

    result = assess_wound(
        wound_type=wound_type,
        depth=depth,
        exudate=exudate,
        wound_bed=wound_bed,
        infection=infection,
        periwound=periwound,
        location=location
    )

    return templates.TemplateResponse(
        request=request,
        name="result.html",
        context={
            "result": result
        }
    )