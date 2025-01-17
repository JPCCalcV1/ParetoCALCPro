/******************************************************
 * spritzguss_calculator_v2.js
 *
 * Dies ist die "reduzierte" JavaScript-Version für V2,
 * bei der die gesamte Rechenlogik im Backend liegt.
 * Alle UI-Funktionen, Profile-Logik, Flag-Verwaltung,
 * Chart-Update etc. bleiben wie in der finalen Version.
 *
 * Wichtig:
 *  - "calculateSpritzguss()" ruft jetzt nur noch per
 *    Fetch/AJAX das Backend auf (/calc/takt/spritzguss).
 *  - Die Rückgabe wird in "fillSpritzgussUI(data)"
 *    geschrieben.
 *  - CSRF-Token wird aus <meta name="csrf-token"> genutzt,
 *    falls dein Projekt das verlangt.
 ******************************************************/

"use strict";

// Globale Referenz auf Doughnut-Chart
let sgChart = null;

/********************************************************
 * FLAGs, um manuell geänderte Felder zu erkennen
 ********************************************************/
let isWallEdited   = false;
let isCavEdited    = false;
let isRobotEdited  = false;  // Für Automotive => Roboter soll true bleiben, falls nicht manuell entfernt

/********************************************************
 * fieldLabels => Mapping von ID => Lesbares Label
 ********************************************************/
const fieldLabels = {
  sgMachineCombo:   "Maschine",
  sgPressureSelect: "Formen-Innendruck (bar)",
  sgSafetyFactor:   "Sicherheitszuschlag (%)",
  sgMinCool:        "Min. Kühlzeit (s)",
  sgWallThickness:  "Wandstärke (mm)",
  sgCavities:       "Kavitäten",
  sgAutomotiveChk:  "Automotive?",
  sgRobotChk:       "Roboter?",
  sgSliderChk:      "Schieber?",
  sgHoldPressure:   "Nachdruck (s)"
};

/********************************************************
 * KONFIGURATION (für autoEstimateRunner etc.)
 * => Hier bleiben z.B. runnerFactorBase, runnerFactorCav,
 *    robotTime etc. bestehen, falls wir sie teils
 *    frontseitig brauchen.
 ********************************************************/
const sgConfig = {
  runnerFactorBase: 0.1,   // 10% vom Bauteilgewicht
  runnerFactorCav:  2.0,   // +2g je Kavität
  contourCoolRed:   0.8,   // -20% Kühlzeit
  robotTime:        2.0,
  manualTime:       0.5,
  sliderTime:       1.5,
  injBaseTime:      1.0,
  defaultHoldTime:  2.0,
  minWall:          0.3,
  maxWall:          8.0,
  minCav:           1,
  maxCav:           64,
  automotiveExtra:  1.2,
  safetyDefault:    30
};

/********************************************************
 * INIT-EVENTS
 ********************************************************/
window.addEventListener("DOMContentLoaded", () => {
  initSpritzgussModal();
});

/********************************************************
 * initSpritzgussModal => Setup von Buttons/Checks/Flags
 ********************************************************/
function initSpritzgussModal() {
  // Runner-Auto
  const runnerChk = document.getElementById("sgRunnerAutoChk");
  if (runnerChk) {
    runnerChk.addEventListener("change", () => {
      if (runnerChk.checked) {
        autoEstimateRunner();
      }
    });
  }

  // Übernehmen-Button
  const btnUebernehmen = document.getElementById("btnSpritzgussUebernehmen");
  if (btnUebernehmen) {
    btnUebernehmen.addEventListener("click", applySpritzgussResult);
  }

  // Flags: Wandstärke / Kavitäten / Robot
  const wallEl = document.getElementById("sgWallThickness");
  if (wallEl) {
    wallEl.addEventListener("change", () => {
      isWallEdited = true;
    });
  }
  const cavEl = document.getElementById("sgCavities");
  if (cavEl) {
    cavEl.addEventListener("change", () => {
      isCavEdited = true;
    });
  }
  const robotChk = document.getElementById("sgRobotChk");
  if (robotChk) {
    robotChk.addEventListener("change", () => {
      isRobotEdited = true;
    });
  }
}

/********************************************************
 * autoEstimateRunner => Schätzt den Anguss (Runner)
 ********************************************************/
function autoEstimateRunner() {
  const wSpin = document.getElementById("sgPartWeight");
  const cSpin = document.getElementById("sgCavities");
  const rSpin = document.getElementById("sgRunnerWeight");
  if (!wSpin || !cSpin || !rSpin) return;

  const partW = parseFloat(wSpin.value) || 50;
  const cav   = parseInt(cSpin.value)   || 4;
  const guess = (sgConfig.runnerFactorBase * partW)
              + (sgConfig.runnerFactorCav * cav);
  rSpin.value = guess.toFixed(1);
}

/********************************************************
 * calculateSpritzguss => V2 => nur noch AJAX zum Backend
 ********************************************************/
function calculateSpritzguss() {
  console.log("calculateSpritzguss() => Sende Daten an Backend (V2).");

  // 1) DOM-Referenzen
  const matSel   = document.getElementById("sgMaterialSelect");
  const cavEl    = document.getElementById("sgCavities");
  const partWEl  = document.getElementById("sgPartWeight");
  const runWEl   = document.getElementById("sgRunnerWeight");
  const lenEl    = document.getElementById("sgLength");
  const widEl    = document.getElementById("sgWidth");
  const wallEl   = document.getElementById("sgWallThickness");

  const machSel  = document.getElementById("sgMachineCombo");
  const machChk  = document.getElementById("sgMachineAutoChk");
  const safeEl   = document.getElementById("sgSafetyFactor");
  const pressEl  = document.getElementById("sgPressureSelect");
  const autoChk  = document.getElementById("sgAutomotiveChk");
  const robotChk = document.getElementById("sgRobotChk");
  const slidChk  = document.getElementById("sgSliderChk");
  const holdEl   = document.getElementById("sgHoldPressure");
  const minCoolEl= document.getElementById("sgMinCool");
  const contChk  = document.getElementById("sgContourCoolChk");

  // 2) Payload-Aufbau
  const payload = {
    material:       matSel?.value            || "PP",
    cavities:       parseInt(cavEl?.value)   || 4,
    partWeight:     parseFloat(partWEl?.value) || 50,
    runnerWeight:   parseFloat(runWEl?.value)  || 10,
    length_mm:      parseFloat(lenEl?.value) || 100,
    width_mm:       parseFloat(widEl?.value) || 80,
    wall_mm:        parseFloat(wallEl?.value)|| 2.0,

    machineKey:     machSel?.value           || "80t HighSpeed",
    isMachineAuto:  !!machChk?.checked,
    safe_pct:       parseFloat(safeEl?.value) || sgConfig.safetyDefault,
    press_bar:      parseInt(pressEl?.value)  || 300,
    isAutomotive:   !!autoChk?.checked,
    hasRobot:       !!robotChk?.checked,
    hasSlider:      !!slidChk?.checked,
    hold_s:         parseFloat(holdEl?.value) || sgConfig.defaultHoldTime,
    min_cool_s:     parseFloat(minCoolEl?.value) || 1.5,
    hasContour:     !!contChk?.checked
  };

  // 3) Vorab: simple Validation (optional)
  if (!validateSpritzgussInputs(payload.wall_mm, payload.cavities)) {
    return; // => Falls ungültig
  }

  // 4) Request an Backend
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
      console.log("Backend (V2) => ", data);
      if (data.error) {
        alert("Fehler: " + data.error);
        return;
      }
      if (!data.ok) {
        alert("Spritzguss-Berechnung unvollständig oder abgelehnt.");
        return;
      }
      // => UI befüllen
      fillSpritzgussUI(data);
    })
    .catch(err => {
      console.error("Spritzguss-Request Error (V2):", err);
      alert("Spritzguss-Anfrage fehlgeschlagen: " + err);
    });
}

/********************************************************
 * validateSpritzgussInputs => Plausibilitätscheck
 ********************************************************/
function validateSpritzgussInputs(wall_mm, cav) {
  const errs = [];
  if (wall_mm < sgConfig.minWall || wall_mm > sgConfig.maxWall) {
    errs.push(`Wandstärke außerhalb (${sgConfig.minWall}–${sgConfig.maxWall} mm)`);
  }
  if (cav < sgConfig.minCav || cav > sgConfig.maxCav) {
    errs.push(`Kavitätenanzahl außerhalb (${sgConfig.minCav}–${sgConfig.maxCav})`);
  }

  if (errs.length > 0) {
    alert("Bitte prüfen:\n - " + errs.join("\n - "));
    return false;
  }
  return true;
}

/********************************************************
 * fillSpritzgussUI => Daten ins UI schreiben
 ********************************************************/
function fillSpritzgussUI(data) {
  // Erwartete Felder: data={
  //   ok: true,
  //   closure_tons: 120.0,
  //   chosenMachine: "150t Automotive",
  //   rawCycleShot: 7.5,
  //   cyclePart_s: 1.88,
  //   rawSegmentVals: [...],
  //   machineExplain: "Maschine '150t Automotive' gewählt ...",
  //   costEach: null,
  //   throughput: null,
  //   msg: "..."
  // }

  document.getElementById("sgClosureForce").textContent  =
    data.closure_tons?.toFixed(1) ?? "--";

  document.getElementById("sgChosenMachine").textContent =
    data.chosenMachine ?? "--";

  document.getElementById("sgCycleShot").textContent     =
    data.rawCycleShot?.toFixed(2) ?? "--";

  document.getElementById("sgCyclePart").textContent     =
    data.cyclePart_s?.toFixed(2) ?? "--";

  // Zusätzliche Erklärung
  const explainEl = document.getElementById("sgMachineExplain");
  if (explainEl) {
    explainEl.textContent = data.machineExplain || "";
  }

  // costEach & throughput in V2 = null => UI zeigt "--"
  const tputEl = document.getElementById("sgThroughput");
  if (tputEl) {
    tputEl.textContent = (data.throughput === null) ? "--" : data.throughput;
  }
  const costEl = document.getElementById("sgCostEach");
  if (costEl) {
    costEl.textContent = (data.costEach === null) ? "--" : data.costEach;
  }

  // Donut-Chart
  if (Array.isArray(data.rawSegmentVals)) {
    drawSpritzgussChart(data.rawSegmentVals);
  }
}

/********************************************************
 * drawSpritzgussChart => Donut-Chart
 ********************************************************/
function drawSpritzgussChart(segmentVals) {
  const ctx = document.getElementById("sgCycleChart");
  if (!ctx) {
    console.warn("drawSpritzgussChart => #sgCycleChart not found!");
    return;
  }
  if (!sgChart) {
    sgChart = new Chart(ctx, {
      type: "doughnut",
      data: {
        labels: ["Open/Close","Inj+Hold","Cooling","Handling"],
        datasets: [
          {
            data: segmentVals,
            backgroundColor: ["#007bff","#28a745","#ffc107","#17a2b8"]
          }
        ]
      },
      options: {
        responsive: false,
        maintainAspectRatio: false,
        cutout: "40%"
      }
    });
  } else {
    sgChart.data.datasets[0].data = segmentVals;
    sgChart.update();
  }
}

/********************************************************
 * applySpritzgussResult => Zykluswert ins Hauptprogramm
 ********************************************************/
function applySpritzgussResult() {
  const cycText = document.getElementById("sgCyclePart")?.textContent || "0";
  const cycVal  = parseFloat(cycText) || 0;

  // Bsp: Tab3 => #fertTable => Zeile 0 => Spalte[1]
  const fertRows = document.querySelectorAll("#fertTable tbody tr");
  if (fertRows.length > 0) {
    fertRows[0].cells[1].querySelector("input").value = cycVal.toFixed(1);
  }

  // Modal schließen
  const modalEl = document.getElementById("modalSpritzguss");
  if (modalEl) {
    const bsModal = bootstrap.Modal.getInstance(modalEl);
    bsModal?.hide();
  }
  console.log("applySpritzgussResult => Zyklus", cycVal, "s übertragen.");
}

/********************************************************
 * loadProfile => Überschreibt Felder, wenn user sie
 *               nicht manuell geändert hat.
 ********************************************************/
function loadProfile(profileType) {
  console.log("loadProfile called with:", profileType);
  let sgProfileMsg = "Profil '" + profileType + "' hat geändert:\n";
  const changes = [];

  function getLabelFor(id) {
    return fieldLabels[id] || id;
  }

  // Nur überschreiben, falls 'flag' nicht true
  function setIfNotEdited(id, val, flag) {
    const el = document.getElementById(id);
    if (!el) return;
    if (!flag) {
      const oldVal = el.value;
      el.value = val;
      if (oldVal != val) {
        changes.push(`${getLabelFor(id)}: ${oldVal} => ${val}`);
      }
    }
  }

  // Nur überschreiben, falls 'flag' nicht true (Checkbox)
  function setCheckboxIfNotEdited(id, boolVal, flag) {
    const el = document.getElementById(id);
    if (!el) return;
    if (!flag) {
      const oldVal = el.checked;
      el.checked = boolVal;
      if (oldVal !== boolVal) {
        changes.push(`${getLabelFor(id)}: ${oldVal} => ${boolVal}`);
      }
    }
  }

  // Harte Überschreib-Funktion (immer)
  function setFormValue(id, val) {
    const el = document.getElementById(id);
    if (!el) return;
    const oldVal = el.value;
    el.value = val;
    if (oldVal != val) {
      changes.push(`${getLabelFor(id)}: ${oldVal} => ${val}`);
    }
  }
  function setCheckbox(id, boolVal) {
    const el = document.getElementById(id);
    if (!el) return;
    const oldVal = el.checked;
    el.checked = boolVal;
    if (oldVal !== boolVal) {
      changes.push(`${getLabelFor(id)}: ${oldVal} => ${boolVal}`);
    }
  }

  // 1) Profil-spezifische Logik
  if (profileType === "standard") {
    setFormValue("sgMachineCombo",    "100t Standard");
    setCheckbox("sgAutomotiveChk",    false);
    setCheckboxIfNotEdited("sgRobotChk", false, isRobotEdited);
    setCheckbox("sgSliderChk",        false);
    setFormValue("sgSafetyFactor",    30);
    setFormValue("sgPressureSelect",  300);
    setFormValue("sgMinCool",         1.5);

  } else if (profileType === "packaging") {
    setFormValue("sgMachineCombo",    "80t HighSpeed");
    setCheckbox("sgAutomotiveChk",    false);
    setCheckboxIfNotEdited("sgRobotChk", true, isRobotEdited);
    setCheckbox("sgSliderChk",        false);
    setFormValue("sgSafetyFactor",    25);
    setFormValue("sgPressureSelect",  300);
    setFormValue("sgMinCool",         1.0);

    setIfNotEdited("sgWallThickness", 1.0, isWallEdited);
    setIfNotEdited("sgCavities",      16,  isCavEdited);

  } else if (profileType === "automotive") {
    setFormValue("sgMachineCombo",    "150t Automotive");
    setCheckbox("sgAutomotiveChk",    true);
    setCheckboxIfNotEdited("sgRobotChk", true, isRobotEdited);
    setCheckbox("sgSliderChk",        true);
    setFormValue("sgSafetyFactor",    35);
    setFormValue("sgPressureSelect",  600);
    setFormValue("sgMinCool",         2.0);

    setIfNotEdited("sgWallThickness", 3.0, isWallEdited);
    setIfNotEdited("sgCavities",      2,   isCavEdited);
  }

  // 2) Log ausgeben
  if (changes.length > 0) {
    sgProfileMsg += changes.map(ch => " - " + ch).join("\n");
  } else {
    sgProfileMsg += " keine relevanten Felder verändert.";
  }

  console.log(sgProfileMsg);
  const profChgDiv = document.getElementById("sgProfileChanges");
  if (profChgDiv) {
    profChgDiv.innerText = sgProfileMsg;
  }
}
