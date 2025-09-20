import React, { useState } from "react";
import "./Stepper.css";

const Stepper = ({ onComplete }) => {
  const [step, setStep] = useState(0);
  const [formData, setFormData] = useState({
    Skillset: "",
    Stipend: "",
    Experience: "",
    JobTitle: "",
    Mode: "",
    Location: "",
  });

  const steps = [
    { label: "Skillset", key: "Skillset", placeholder: "e.g. Python, Data Analysis" },
    { label: "Stipend", key: "Stipend", placeholder: "e.g. ₹10,000/month" },
    { label: "Experience", key: "Experience", placeholder: "e.g. 2 years" },
    { label: "Job Title", key: "JobTitle", placeholder: "e.g. CIVIL ENGINEER (INTERN)" },
    { label: "Mode", key: "Mode", placeholder: "e.g. Full Time / Part Time / Virtual Internship" },
    { label: "Location", key: "Location", placeholder: "e.g. New Delhi" },
  ];

  const handleChange = (e) => {
    setFormData({ ...formData, [steps[step].key]: e.target.value });
  };

  const nextStep = () => {
    if (step < steps.length - 1) {
      setStep(step + 1);
    } else {
      const payload = {
        JobTitle: formData.JobTitle,
        Mode: formData.Mode,
        Location: formData.Location,
      };
      onComplete(payload);
    }
  };

  const prevStep = () => {
    if (step > 0) setStep(step - 1);
  };

  return (
    <div className="stepper-container">
      {/* Indicators */}
      <div className="step-indicators">
        {steps.map((s, i) => (
          <div key={s.key} className="step-wrapper">
            <div
              className={`step-circle ${i === step ? "active" : i < step ? "completed" : ""}`}
            >
              {i < step ? "✓" : i + 1}
            </div>
            {i < steps.length - 1 && (
              <div className={`step-line ${i < step ? "filled" : ""}`} />
            )}
          </div>
        ))}
      </div>

      {/* Current step with fade */}
      <div className="step-content">
        <div key={step} className="step-fade">
          <h2 style={{ color: "white" }}>{steps[step].label}</h2>
          <input
            type="text"
            value={formData[steps[step].key]}
            onChange={handleChange}
            placeholder={steps[step].placeholder}
          />
        </div>
      </div>

      {/* Footer */}
      <div className="stepper-footer">
        <button className="step-btn back" onClick={prevStep} disabled={step === 0}>
          Back
        </button>
        <button className="step-btn next" onClick={nextStep}>
          {step < steps.length - 1 ? "Next" : "Submit"}
        </button>
      </div>
    </div>
  );
};

export default Stepper;
