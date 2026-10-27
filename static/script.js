const form = document.querySelector("#assessment-form");

if (form) {
    const steps = Array.from(form.querySelectorAll(".wizard-step"));
    const previousButton = form.querySelector("#previous-step");
    const nextButton = form.querySelector("#next-step");
    const submitButton = form.querySelector("#submit-assessment");
    const stepLabel = document.querySelector("#step-label");
    const stepCount = document.querySelector("#step-count");
    const progressTrack = document.querySelector(".progress-track");
    const progressValue = document.querySelector("#progress-value");
    const stepNames = ["คัดกรองอันตราย", "ข้อมูลผู้ป่วยและชนิดแผล", "ประเมินลักษณะแผล", "บริบทการใช้งาน"];
    let activeStep = 0;

    function showStep(index) {
        activeStep = index;
        steps.forEach((step, stepIndex) => {
            const isVisible = stepIndex === activeStep;
            step.hidden = !isVisible;
            step.querySelectorAll("[data-required]").forEach((field) => {
                field.required = isVisible;
            });
        });

        previousButton.hidden = activeStep === 0;
        nextButton.hidden = activeStep === steps.length - 1;
        submitButton.hidden = activeStep !== steps.length - 1;
        stepLabel.textContent = `ขั้นที่ ${activeStep + 1}: ${stepNames[activeStep]}`;
        stepCount.textContent = `${activeStep + 1} / ${steps.length}`;
        progressTrack.setAttribute("aria-valuenow", String(activeStep + 1));
        progressValue.style.width = `${((activeStep + 1) / steps.length) * 100}%`;
        steps[activeStep].querySelector("select")?.focus();
    }

    nextButton.addEventListener("click", () => {
        if (!form.reportValidity()) {
            return;
        }
        showStep(activeStep + 1);
        window.scrollTo({ top: 0, behavior: "smooth" });
    });

    previousButton.addEventListener("click", () => {
        showStep(activeStep - 1);
        window.scrollTo({ top: 0, behavior: "smooth" });
    });

    showStep(0);
}
