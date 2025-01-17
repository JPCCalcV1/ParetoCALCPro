/************************************************************
 * druckguss_calculator.js – AJAX-Variante
 *
 * Hier nur Felder sammeln & fetch('/calc/takt/druckguss',...).
 * Das Ergebnis (JSON) füllt wir ins Modal (#dgClosureForce, etc.).
 ************************************************************/

let dgChart = null; // Donut-Chart

document.addEventListener("DOMContentLoaded", () => {
  initDruckgussModal();
});

function initDruckgussModal() {
  const btnUebernehmen = document.getElementById("btnDruckgussUebernehmen");
  if (btnUebernehmen) {
    btnUebernehmen.addEventListener("click", applyDruckgussResult);
  }
}

/**
 * Sammelt Eingaben und ruft /calc/takt/druckguss auf.
 */
function calculateDruckguss() {
  console.log("Druckguss => AJAX an /calc/takt/druckguss.");

  const matSel     = document.getElementById("dgMaterialSelect");
  const partWEl    = document.getElementById("dgPartWeight");
  const areaEl     = document.getElementById("dgAreaCm2");
  const cavEl      = document.getElementById("dgCavities");
  const dickChk    = document.getElementById("dgDickwandChk");
  const entgChk    = document.getElementById("dgEntgratenChk");
  const ovfEl      = document.getElementById("dgOverflowPct");

  const autoMachChk= document.getElementById("dgAutoMachineChk");
  const machSel    = document.getElementById("dgMachineSelect");
  const abgChk     = document.getElementById("dgAbgeschrChk");
  const safeEl     = document.getElementById("dgSafetyFactor");
  const squeezeChk = document.getElementById("dgSqueezeChk");

  const wallEl     = document.getElementById("dgWallThickness");
  const sprayEl    = document.getElementById("dgSprayTime");
  const holdEl     = document.getElementById("dgHoldTime");
  const automSel   = document.getElementById("dgAutomationSelect");
  const utilEl     = document.getElementById("dgUtilPct");

  // Payload
  const payload = {
    matName: matSel.value || "AlSi9Cu3",
    partW_g: parseFloat(partWEl.value)|| 500,
    area_cm2: parseFloat(areaEl.value)|| 80,
    cav: parseInt(cavEl.value)|| 1,
    isDickwand: !!dickChk.checked,
    isEntgraten: !!entgChk.checked,
    overflow_pct: (parseFloat(ovfEl.value)||50)/ 100.0,

    isMachAuto: !!autoMachChk.checked,
    machKey: machSel.value || "200t",
    isAbgeschr: !!abgChk.checked,
    sf_val: parseFloat(safeEl.value)|| 2.0,
    isSqueeze: !!squeezeChk.checked,

    wall_mm: parseFloat(wallEl.value)|| 6.0,
    spray_s: parseFloat(sprayEl.value)|| 5.0,
    hold_s: parseFloat(holdEl.value)|| 5.0,
    automLevel: automSel.value|| "Manuell",
    util_pct: (parseFloat(utilEl.value)|| 85)/ 100.0
  };

  console.log("Druckguss => Sende Payload:", payload);

  fetch("/mycalc/druckguss", {
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
        alert("Druckguss-Backend: Kalkulation unvollständig.");
        return;
      }
      console.log("Druckguss => Ergebnis:", data);
      updateDruckgussUI(data);
    })
    .catch(err => {
      console.error("Druckguss AJAX Error:", err);
      alert("Druckguss-Anfrage fehlgeschlagen: " + err);
    });
}

/**
 * Schreibt das JSON-Ergebnis (Backend) in die UI-Felder.
 */
function updateDruckgussUI(data) {
  // data => {
  //   ok:true,
  //   force_t: 345.6,
  //   chosenMachine: "400t",
  //   cycle_shot: 18.0,
  //   cycle_part: 9.0,
  //   tph: 200.0,
  //   costEach: 0.27,
  //   co2Each: 0.09
  // }
  document.getElementById("dgClosureForce").textContent  = data.force_t?.toFixed(1) ?? "--";
  document.getElementById("dgChosenMachine").textContent = data.chosenMachine ?? "--";
  document.getElementById("dgCycleShot").textContent     = data.cycle_shot?.toFixed(2) ?? "--";
  document.getElementById("dgCyclePart").textContent     = data.cycle_part?.toFixed(2) ?? "--";
  document.getElementById("dgThroughput").textContent    = data.tph?.toFixed(1) ?? "--";
  document.getElementById("dgCostEach").textContent      = data.costEach?.toFixed(2) ?? "--";
  document.getElementById("dgCo2Each").textContent       = data.co2Each?.toFixed(2) ?? "--";

  // Donut-Chart:
  // Wir haben hier nur Summen (cycle_shot, costEach, co2Each).
  // Für Demo -> Verteilen wir cycle_shot "grob" auf 4 Segmente.
  // => Bsp.: [openclose, spray, fill+hold, cool+others].
  let seg1 = 2.0;
  let seg2 = 5.0;
  let seg3 = data.cycle_shot ? (data.cycle_shot - (seg1+seg2+5.0)) : 3.0;
  let seg4 = 5.0;
  drawDruckgussChart([seg1, seg2, seg3, seg4], data.cycle_shot?? 12);
}

/**
 * Donut-Chart
 */
function drawDruckgussChart(segmentVals, cycle_shot) {
  const ctx = document.getElementById("dgCycleChart");
  if (!ctx) {
    console.warn("drawDruckgussChart => #dgCycleChart not found!");
    return;
  }
  if (!dgChart) {
    dgChart = new Chart(ctx, {
      type: "doughnut",
      data: {
        labels: ["Open/Close","Spray","F+Hold","Cool+Rest"],
        datasets: [{
          data: segmentVals,
          backgroundColor: ["#007bff","#28a745","#ffc107","#17a2b8"]
        }]
      },
      options: {
        responsive: false,
        maintainAspectRatio: false,
        cutout: "40%",
        plugins: {
          title: {
            display: true,
            text: cycle_shot.toFixed(1)+" s/Schuss",
            font: { size:14 }
          }
        }
      }
    });
  } else {
    dgChart.data.datasets[0].data = segmentVals;
    dgChart.options.plugins.title.text = cycle_shot.toFixed(1)+" s/Schuss";
    dgChart.update();
  }
}

/**
 * Übernehmen => Zyklus in #fertTable (Beispiel).
 */
function applyDruckgussResult() {
  const cycText = document.getElementById("dgCyclePart").textContent;
  const cycVal  = parseFloat(cycText) || 0;

  // z. B. Tab3 => row(0), col(1)
  const fertRows = document.querySelectorAll("#fertTable tbody tr");
  if (fertRows.length > 0) {
    fertRows[0].cells[1].querySelector("input").value = cycVal.toFixed(1);
  }

  // Modal schließen
  const modalEl = document.getElementById("modalDruckguss");
  if (modalEl) {
    const bsModal = bootstrap.Modal.getInstance(modalEl);
    bsModal?.hide();
  }
  console.log("applyDruckgussResult => Zyklus (s)", cycVal, "eingetragen.");
}