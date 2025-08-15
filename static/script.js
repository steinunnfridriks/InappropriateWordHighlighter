// script.js

console.log("Script loaded!");

const textInput = document.getElementById("text-input");
const submitBtn = document.getElementById("submit-btn");
const loadingIndicator = document.getElementById("loading");
const resultDiv = document.getElementById("result");

submitBtn.addEventListener("click", async () => {
  console.log("Button clicked");
  const text = textInput.value.trim();
  if (!text) {
    resultDiv.innerHTML = "<p style='color: #d32f2f; font-weight: bold;'>Please enter some text to check.</p>";
    return;
  }

  loadingIndicator.classList.remove("hidden");
  resultDiv.innerHTML = "";

  try {
    const res = await fetch("/process", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });

    const data = await res.json();
    resultDiv.innerHTML = data.html;
  } catch (err) {
    resultDiv.innerHTML = "<p style='color: red;'>Error processing text.</p>";
  } finally {
    loadingIndicator.classList.add("hidden");
    textInput.value = ""; // Optional: clear input after submit
  }
});

window.addEventListener("DOMContentLoaded", () => {
  document.getElementById("text-input").value = "";
});

// Show tooltip text on tap for legend items (mobile-friendly)
document.querySelectorAll('.legend-item').forEach(item => {
  item.addEventListener('click', function (e) {
    e.stopPropagation();
    // Remove any existing tooltips
    document.querySelectorAll('.legend-tooltip').forEach(tip => tip.remove());

    // Create tooltip
    const tooltip = document.createElement('div');
    tooltip.className = 'legend-tooltip';
    tooltip.textContent = item.getAttribute('title');
    item.appendChild(tooltip);

    // Remove tooltip on next tap anywhere
    setTimeout(() => {
      const removeTooltip = () => {
        tooltip.remove();
        document.removeEventListener('click', removeTooltip, true);
      };
      document.addEventListener('click', removeTooltip, true);
    }, 10);
  });
});

