//----------------------------------------------------
// spritzguss_calculator.js – Backend-AJAX Version
//----------------------------------------------------

// Globale Chart-Objekt
let sgChart = null;

// Bei DOM-Load binden wir Event-Listener (z. B. autoEstimateRunner)
document.addEventListener("DOMContentLoaded", () => {
  const runnerChk = document.getElementById("sgRunnerAutoChk");
  if (runnerChk) {
    runnerChk.addEventListener("change", () => {
      if (runnerChk.checked) {
        autoEstimateRunner();
      }
    });
  }

  // Button "Übernehmen"
  const btnUebernehmen = document.getElementById("btnSpritzgussUebernehmen");
  if (btnUebernehmen) {
    btnUebernehmen.addEventListener("click", applySpritzgussResult);
  }
});

/**
 * Anguss auto-Logik (lokal)
 */
function autoEstimateRunner() {
  const wSpin = document.getElementById("sgPartWeight");
  const cSpin = document.getElementById("sgCavities");
  const rSpin = document.getElementById("sgRunnerWeight");
  if (!wSpin || !cSpin || !rSpin) return;

  const partW = parseFloat(wSpin.value) || 50;
  const cav   = parseInt(cSpin.value)   || 4;
  const guess = (0.1 * partW) + (2 * cav);
  rSpin.value = guess.toFixed(1);
}

/**
 * Spritzguss-Berechnung via Backend.
 * Sammelt alle Felder aus dem Modal und macht POST /calc/takt/spritzguss
 */
function calculateSpritzguss() {
  console.log("Spritzguss => Sende Eingaben an Backend.");

  // 1) Eingaben
  const material   = document.getElementById("sgMaterialSelect")?.value || "PP";
  const cavities   = parseInt(document.getElementById("sgCavities")?.value) || 4;
  const partWeight = parseFloat(document.getElementById("sgPartWeight")?.value) || 50;
  const runnerWeight = parseFloat(document.getElementById("sgRunnerWeight")?.value) || 10;
  const length_mm  = parseFloat(document.getElementById("sgLength")?.value) || 100;
  const width_mm   = parseFloat(document.getElementById("sgWidth")?.value) || 80;
  const wall_mm    = parseFloat(document.getElementById("sgWallThickness")?.value) || 2;

  const machineKey   = document.getElementById("sgMachineCombo")?.value || "50t Standard";
  const isMachineAuto= !!document.getElementById("sgMachineAutoChk")?.checked;
  const safe_pct     = parseFloat(document.getElementById("sgSafetyFactor")?.value) || 30;
  const press_bar    = parseFloat(document.getElementById("sgPressureSelect")?.value) || 300;
  const isAutomotive = !!document.getElementById("sgAutomotiveChk")?.checked;
  const hasRobot     = !!document.getElementById("sgRobotChk")?.checked;
  const hasSlider    = !!document.getElementById("sgSliderChk")?.checked;
  const hold_s       = parseFloat(document.getElementById("sgHoldPressure")?.value) || 2.0;
  const util_pct     = parseFloat(document.getElementById("sgUtilPct")?.value) || 85.0;
  const min_cool_s   = parseFloat(document.getElementById("sgMinCool")?.value) || 1.5;
  const hasContour   = !!document.getElementById("sgContourCoolChk")?.checked;

  const payload = {
    material,
    cavities,
    partWeight,
    runnerWeight,
    length_mm,
    width_mm,
    wall_mm,
    machineKey,
    isMachineAuto,
    safe_pct,
    press_bar,
    isAutomotive,
    hasRobot,
    hasSlider,
    hold_s,
    util_pct,
    min_cool_s,
    hasContour
  };

  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || "";
  fetch("/calc/takt/spritzguss", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrfToken
    },
    body: JSON.stringify(payload)
  })
    .then(res => {
      if (!res.ok) throw new Error("HTTP " + res.status);
      return res.json();
    })
    .then(data => {
      console.log("Spritzguss => Backend-Ergebnis:", data);
      if (data.error) {
        alert("Fehler: " + data.error);
        return;
      }
      if (!data.ok) {
        alert("Spritzguss-Berechnung unvollständig oder abgelehnt.");
        return;
      }
      // Fülle UI
      fillSpritzgussUI(data);
    })
    .catch(err => {
      console.error("Spritzguss-Request Error:", err);
      alert("Spritzguss-Anfrage fehlgeschlagen: "+ err);
    });
}

/**
 * Schreibt das Backend-Ergebnis in die Felder (sgClosureForce etc.)
 */
function fillSpritzgussUI(data) {
  // z. B. data={
  //   ok:true,
  //   closure_tons: 75.3,
  //   rawCycleShot: 12.4,
  //   cyclePart_s: 3.1,
  //   tph: 720,
  //   costEach: 0.078,
  //   chosenMachine: "100t Standard",
  //   msg: ...
  // }
  document.getElementById("sgClosureForce").textContent  = data.closure_tons?.toFixed(1) ?? "--";
  document.getElementById("sgChosenMachine").textContent = data.chosenMachine ?? "--";
  document.getElementById("sgCycleShot").textContent     = data.rawCycleShot?.toFixed(2) ?? "--";
  document.getElementById("sgCyclePart").textContent     = data.cyclePart_s?.toFixed(2) ?? "--";
  document.getElementById("sgThroughput").textContent    = data.tph?.toFixed(0) ?? "--";
  document.getElementById("sgCostEach").textContent      = data.costEach?.toFixed(3) ?? "--";

  // Donut-Chart (falls du Zeitsegmente einzeln hast)
  // Hier nur Demo
  drawSpritzgussChart([data.rawCycleShot ?? 12, 1, 2, 3]);
}

/**
 * Donut-Chart: Demo
 */
function drawSpritzgussChart(segmentVals) {
  const ctx = document.getElementById("sgCycleChart");
  if (!ctx) return;
  if (!sgChart) {
    sgChart = new Chart(ctx, {
      type: "doughnut",
      data: {
        labels: ["Open/Close", "Inj+Hold", "Cooling", "Handling"],
        datasets: [{
          data: segmentVals,
          backgroundColor: ["#007bff","#28a745","#ffc107","#17a2b8"]
        }]
      },
      options: { responsive:false, cutout:"40%" }
    });
  } else {
    sgChart.data.datasets[0].data = segmentVals;
    sgChart.update();
  }
}

/**
 * "Übernehmen"-Button
 */
function applySpritzgussResult() {
  const cycText = document.getElementById("sgCyclePart").textContent;
  const cycVal  = parseFloat(cycText) || 0;

  // Tab3 => #fertTable?
  // Example:
  // const fertRows = document.querySelectorAll("#fertTable tbody tr");
  // if (fertRows.length > 0) {
  //   fertRows[0].cells[1].querySelector("input").value = cycVal.toFixed(1);
  // }

  // Modal schließen
  const modalEl = document.getElementById("modalSpritzguss");
  if (modalEl) {
    const bsModal = bootstrap.Modal.getInstance(modalEl);
    bsModal?.hide();
  }
  console.log("applySpritzgussResult => Zyklus pro Teil: ", cycVal);
}