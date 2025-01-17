/******************************************************
 * milling_calculator.js – AJAX-Version
 *
 * - DOM => Felder wie #millMatSelect, #millLenMm, etc.
 * - fetch('/calc/takt/milling', { ... })
 * - updateMillingUI()
 ******************************************************/

let millChart = null;

document.addEventListener("DOMContentLoaded", () => {
  initMillingModal();
});

function initMillingModal() {
  const btnUebernehmen = document.getElementById("btnMillingUebernehmen");
  if (btnUebernehmen) {
    btnUebernehmen.addEventListener("click", applyMillingResult);
  }

  const autoChk = document.getElementById("millAutoMachChk");
  if (autoChk) {
    autoChk.addEventListener("change", () => {
      const sel = document.getElementById("millMachineSelect");
      if (sel) sel.disabled = autoChk.checked;
    });
  }
}

/**
 * Sammelt Eingaben, ruft das Backend /calc/takt/milling
 */
function calculateMilling() {
  console.log("calculateMilling() => AJAX /calc/takt/milling");

  const matSel   = document.getElementById("millMatSelect");
  const autoChk  = document.getElementById("millAutoMachChk");
  const machSel  = document.getElementById("millMachineSelect");

  const lenEl    = document.getElementById("millLenMm");
  const widEl    = document.getElementById("millWidMm");
  const heiEl    = document.getElementById("millHeiMm");
  const finEl    = document.getElementById("millFinishHeight");
  const feedEl   = document.getElementById("millFeedRate");
  const cutdEl   = document.getElementById("millCutDepth");
  const toolEl   = document.getElementById("millToolChange");
  const lotEl    = document.getElementById("millLotSize");
  const ruestEl  = document.getElementById("millRuestMin");

  // Payload
  const payload = {
    matName:  matSel.value || "Stahl S235",
    isAuto:   !!autoChk.checked,
    machKey:  machSel.value || "3-Achs Standard",

    L_mm:     parseFloat(lenEl.value)|| 100,
    W_mm:     parseFloat(widEl.value)|| 80,
    H_mm:     parseFloat(heiEl.value)|| 30,
    Hfin:     parseFloat(finEl.value)|| 28,

    feed_mmmin:   parseFloat(feedEl.value)|| 1500,
    cutDepth:     parseFloat(cutdEl.value)|| 3.0,
    toolChange_s: parseFloat(toolEl.value)|| 20,

    lot:      parseInt(lotEl.value)|| 100,
    ruest_min: parseFloat(ruestEl.value)|| 30
  };

  console.log("Milling => Payload:", payload);

  fetch("/mycalc/milling", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
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
        alert("Milling-Backend: unvollständig oder abgelehnt.");
        return;
      }
      console.log("Milling => Ergebnis:", data);
      updateMillingUI(data);
    })
    .catch(err => {
      console.error("Milling AJAX Error:", err);
      alert("Milling-Anfrage fehlgeschlagen: " + err);
    });
}

/**
 * Nimmt JSON vom Backend und schreibt es in #millResultsArea
 */
function updateMillingUI(data) {
  // data => {
  //   ok:true,
  //   chosenMachine: "5-Achs Standard",
  //   cycle_s: 180.0,
  //   partsPerHour: 20.0,
  //   costEach: 2.37,
  //   co2Each: 0.84
  // }

  document.getElementById("millChosenMachine").textContent = data.chosenMachine ?? "--";
  document.getElementById("millCycleTime").textContent     = data.cycle_s?.toFixed(2) ?? "--";
  document.getElementById("millPartPerHour").textContent   = data.partsPerHour?.toFixed(1) ?? "--";
  document.getElementById("millCostEach").textContent      = data.costEach?.toFixed(2) ?? "--";
  document.getElementById("millCo2Each").textContent       = data.co2Each?.toFixed(2) ?? "--";

  // Donut-Chart => 3 Segment (Material, Maschine, Rüst)
  // Da das Backend nur Summen liefert, wir machen Demo-Split:
  let matCost  = data.costEach ? data.costEach*0.40 : 0.0;
  let machCost = data.costEach ? data.costEach*0.50 : 0.0;
  let ruestCost= data.costEach ? data.costEach*0.10 : 0.0;
  drawMillingChart([matCost, machCost, ruestCost], data.costEach?? 0);
}

/**
 * Donut
 */
function drawMillingChart(segmentVals, totalCost) {
  const ctx = document.getElementById("millCostChart");
  if (!ctx) return;
  if (!millChart) {
    millChart = new Chart(ctx, {
      type: "doughnut",
      data: {
        labels:["Material","Maschine","Rüst"],
        datasets:[{
          data: segmentVals,
          backgroundColor:["#007bff","#28a745","#ffc107"]
        }]
      },
      options: {
        responsive: false,
        maintainAspectRatio: false,
        cutout: "40%",
        plugins: {
          title: {
            display:true,
            text: totalCost.toFixed(2)+" €/Teil",
            font:{size:14}
          }
        }
      }
    });
  } else {
    millChart.data.datasets[0].data = segmentVals;
    millChart.options.plugins.title.text = totalCost.toFixed(2)+" €/Teil";
    millChart.update();
  }
}

/**
 * Übernehmen => Zyklus in #fertTable (Beispiel)
 */
function applyMillingResult() {
  const cycTxt = document.getElementById("millCycleTime").textContent;
  const cycVal = parseFloat(cycTxt) || 0;

  // row(0), col(1)
  const fertRows = document.querySelectorAll("#fertTable tbody tr");
  if (fertRows.length>0) {
    fertRows[0].cells[1].querySelector("input").value = cycVal.toFixed(1);
  }
  // Modal schließen
  const modalEl = document.getElementById("modalMilling");
  if (modalEl) {
    const bsModal = bootstrap.Modal.getInstance(modalEl);
    bsModal?.hide();
  }
  console.log("applyMillingResult => Takt (s)", cycVal,"eingetragen.");
}
