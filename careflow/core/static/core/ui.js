(() => {
  "use strict";
  const dateMessage = "Enter a complete date in YYYY-MM-DD format with a four-digit year (0001–9999).";
  document.querySelectorAll('input[type="date"]').forEach((input, index) => {
    const id = `${input.id || `date-${index}`}-guide`;
    const guide = document.createElement("small");
    guide.id = id;
    guide.className = "muted date-guide";
    guide.textContent = "Use YYYY-MM-DD with a four-digit year.";
    input.insertAdjacentElement("afterend", guide);
    input.setAttribute("aria-describedby", `${input.getAttribute("aria-describedby") || ""} ${id}`.trim());
    if (!input.min) input.min = "0001-01-01";
    if (!input.max) input.max = "9999-12-31";
    const validate = () => {
      input.setCustomValidity("");
      if (input.validity.badInput || (input.value && !/^\d{4}-\d{2}-\d{2}$/.test(input.value))) {
        input.setCustomValidity(dateMessage);
      } else if (input.validity.rangeOverflow) {
        input.setCustomValidity(`Choose a date on or before ${input.max}.`);
      } else if (input.validity.rangeUnderflow) {
        input.setCustomValidity(`Choose a date on or after ${input.min}.`);
      }
    };
    input.addEventListener("input", validate);
    input.addEventListener("change", validate);
    validate();
  });

  document.querySelectorAll(".table-scroll").forEach((region, index) => {
    const hint = document.createElement("p");
    hint.className = "small muted scroll-hint";
    hint.id = `table-scroll-hint-${index}`;
    hint.textContent = "Scroll horizontally to view all columns. Keyboard: focus the table area and use the arrow keys.";
    region.insertAdjacentElement("beforebegin", hint);
    const update = () => {
      const overflow = region.scrollWidth > region.clientWidth + 1;
      hint.hidden = !overflow;
      region.classList.toggle("has-overflow", overflow);
      if (overflow) {
        region.setAttribute("tabindex", "0");
        region.setAttribute("role", "region");
        if (!region.hasAttribute("aria-label")) {
          const heading = region.closest("section")?.querySelector("h2,h3");
          region.setAttribute("aria-label", heading ? `${heading.textContent.trim()} table` : "Scrollable clinical table");
        }
        region.setAttribute("aria-describedby", hint.id);
      }
    };
    new ResizeObserver(update).observe(region);
    update();
  });

  document.querySelectorAll("form").forEach(form => {
    form.addEventListener("submit", event => {
      if (form.dataset.submitting === "true") {
        event.preventDefault();
        return;
      }
      form.dataset.submitting = "true";
      // aria-disabled keeps named submit-button values in the submitted payload.
      form.querySelectorAll('button[type="submit"],button:not([type])').forEach(button => button.setAttribute("aria-disabled", "true"));
    });
  });
  window.addEventListener("pageshow", () => {
    document.querySelectorAll("form[data-submitting]").forEach(form => {
      delete form.dataset.submitting;
      form.querySelectorAll('[aria-disabled="true"]').forEach(button => button.removeAttribute("aria-disabled"));
    });
  });
})();
