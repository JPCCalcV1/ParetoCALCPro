/******************************************************
 * stamping_calculator.js – AJAX-Version
 *
 * - calculateStamping() => holt Felder aus #modalStamping,
 *   sendet POST /calc/takt/stamping
 * - updateStampingUI() => füllt Felder + Chart
 * - applyStampingResult() => Zyklus in Tab3
 ******************************************************/

// NEU: Speichert die aktuell geklickte Tabellenzeile
let currentStampingRow = null;

let stChart = null;

// Wenn DOM fertig
document.addEventListener("DOMContentLoaded", () => {
  initStampingModal();
});

function initStampingModal() {
  const btnUebernehmen = document.getElementById("btnStampingUebernehmen");
  if (btnUebernehmen) {
    btnUebernehmen.addEventListener("click", applyStampingResult);
  }

  const autoChk = document.getElementById("stAutoMachChk");
  if (autoChk) {
    autoChk.addEventListener("change", () => {
      const pressSel = document.getElementById("stPressSelect");
      if (!pressSel) return;
      pressSel.disabled = autoChk.checked;
    });
  }
}

/**
 * NEU: Öffnet das Stamping-Modal für eine bestimmte Tabellenzeile.
 * @param {number} rowIndex – Index der Zeile, auf die geklickt wurde
 */
function openStampingModalWithTakt(rowIndex) {
  // 1) Zeilenindex merken
  currentStampingRow = rowIndex;
  console.log("openStampingModalWithTakt => rowIndex =", rowIndex);

  // 2) Modal #modalStamping anzeigen
  const modalEl = document.getElementById("modalStamping");
  if (!modalEl) {
    console.error("modalStamping not found!");
    return;
  }
  const bsModal = new bootstrap.Modal(modalEl);
  bsModal.show();
  console.log("Stamping-Modal geöffnet (Zeile:", rowIndex, ")");
}

/**
 * Sammelt Eingaben, ruft /calc/takt/stamping und zeigt Ergebnis an.
 */
function calculateStamping() {
  console.log("Stamping => fetch('/calc/takt/stamping')...");

  // Felder
  const matSel     = document.getElementById("stMatSelect");
  const thickEl    = document.getElementById("stThickMm");
  const areaEl     = document.getElementById("stAreaCm2");
  const scrapEl    = document.getElementById("stScrapPct");
  const losEl      = document.getElementById("stLos");
  const ruestEl    = document.getElementById("stRuestMin");
  const dickChk    = document.getElementById("stDickBlechChk");

  const autoChk    = document.getElementById("stAutoMachChk");
  const pressSel   = document.getElementById("stPressSelect");

  // Parsen
  const matName    = matSel.value || "Stahl DC01";
  const thick_mm   = parseFloat(thickEl.value) || 1.0;
  const area_cm2   = parseFloat(areaEl.value) || 150.0;
  const scrap_pct  = (parseFloat(scrapEl.value)||15)/100.0;
  const los        = parseInt(losEl.value)||10000;
  const ruest_min  = parseFloat(ruestEl.value)||60;
  const isDick     = !!dickChk.checked;

  const isAuto     = !!autoChk.checked;
  const pressKey   = pressSel.value || "100";

  const payload = {
    matName,
    thick_mm,
    area_cm2,
    scrap_pct,
    los,
    ruest_min,
    isDick,
    isAuto,
    pressKey
  };

  console.log("Stamping => Payload:", payload);

  fetch("/calc/takt/stamping", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
      // ggf. "X-CSRFToken": ...
    },
    body: JSON.stringify(payload)
  })
    .then(res => {
      if (!res.ok) {
        throw new Error("HTTP " + res.status);
      }
      return res.json();
    })
    .then(data => {
      if (data.error) {
        alert("Fehler: " + data.error);
        return;
      }
      if (!data.ok) {
        alert("Stamping-Backend: Kalkulation fehlgeschlagen.");
        return;
      }
      console.log("Stamping => Backend-Ergebnis:", data);
      updateStampingUI(data);
    })
    .catch(err => {
      console.error("Stamping AJAX Error:", err);
      alert("Stamping-Request fehlgeschlagen: " + err);
    });
}

/**
 * Nimmt JSON vom Backend und schreibt es ins Modal
 */
function updateStampingUI(data) {
  // data => {
  //   ok: true,
  //   pressForce_t: 123.4,
  //   chosenPress: "200 t",
  //   cycle_s: 3.5,
  //   partsPerHour: 1028.6,
  //   costEach: 0.17,
  //   co2Each: 0.05
  // }
  document.getElementById("stPressForce").textContent = data.pressForce_t?.toFixed(1) ?? "--";
  document.getElementById("stChosenPress").textContent = data.chosenPress ?? "--";
  document.getElementById("stCycleTime").textContent   = data.cycle_s?.toFixed(2) ?? "--";
  document.getElementById("stPartPerHour").textContent = data.partsPerHour?.toFixed(1) ?? "--";
  document.getElementById("stCostEach").textContent    = data.costEach?.toFixed(2) ?? "--";
  document.getElementById("stCo2Each").textContent     = data.co2Each?.toFixed(2) ?? "--";

  drawStampingChart([
    data.costEach ? data.costEach*0.50 : 0.1, // Demo breakdown
    data.costEach ? data.costEach*0.40 : 0.1,
    data.costEach ? data.costEach*0.10 : 0.1
  ], data.costEach ?? 0);
}

/**
 * Zeichnet Donut-Chart (kosten-breakdown).
 * Da das Backend nur Gesamtkosten liefert,
 * trennen wir hier demohaft in 50/40/10%.
 */
function drawStampingChart(segmentVals, totalCost) {
  const ctx = document.getElementById("stCycleChart");
  if (!ctx) {
    console.warn("drawStampingChart => #stCycleChart not found!");
    return;
  }
  if (!stChart) {
    stChart = new Chart(ctx, {
      type: "doughnut",
      data: {
        labels: ["Material","Maschine","Rüst"],
        datasets: [{
          data: segmentVals,
          backgroundColor: ["#007bff","#28a745","#ffc107"]
        }]
      },
      options: {
        responsive: false,
        maintainAspectRatio: false,
        cutout: "40%",
        plugins: {
          title: {
            display: true,
            text: totalCost.toFixed(2) + " €/Teil",
            font: { size: 14 }
          }
        }
      }
    });
  } else {
    stChart.data.datasets[0].data = segmentVals;
    stChart.options.plugins.title.text = totalCost.toFixed(2) + " €/Teil";
    stChart.update();
  }
}

/**
 * applyStampingResult => Zyklus in #fertTable (Beispiel)
 */
function applyStampingResult() {
  const cycText= document.getElementById("stCycleTime").textContent;
  const cycVal= parseFloat(cycText) || 0;

  // NEU: statt immer fertRows[0] => currentStampingRow beachten
  const fertRows= document.querySelectorAll("#fertTable tbody tr");
  if (
    currentStampingRow !== null &&
    currentStampingRow >= 0 &&
    currentStampingRow < fertRows.length
  ) {
    fertRows[currentStampingRow]
      .cells[1]
      .querySelector("input").value = cycVal.toFixed(1);
  }

  // Modal schließen
  const modalEl = document.getElementById("modalStamping");
  if (modalEl) {
    const bsModal = bootstrap.Modal.getInstance(modalEl);
    bsModal?.hide();
  }
  console.log("applyStampingResult => Zyklus", cycVal,"in Zeile", currentStampingRow,"eingetragen.");
}
