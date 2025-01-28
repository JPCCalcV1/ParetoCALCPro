/******************************************************
 * spritzguss_calculator_merged.js
 *
 * V1-Basis + erweiterte Logik optional:
 *  - "isAdvanced" => wenn angehakt, ruft das Backend
 *    "calculate_advanced_cycle" auf.
 *  - "parallelPlast" => schaltet paralleles Plastifizieren.
 ******************************************************/
"use strict";

let sgChart = null;
let currentTaktRow = null;


// NEU: Globale Variable, um die geklickte Zeile zu speichern:

// Flag-Variablen
let isWallEdited   = false;
let isCavEdited    = false;
let isRobotEdited  = false;

// Labels ohne Fragezeichen
const fieldLabels = {
  sgMachineCombo:   "Maschine",
  sgPressureSelect: "Formen-Innendruck (bar)",
  sgSafetyFactor:   "Sicherheitszuschlag (%)",
  sgMinCool:        "Min. Kühlzeit (s)",
  sgWallThickness:  "Wandstärke (mm)",
  sgCavities:       "Kavitäten",
  sgAutomotiveChk:  "Automotive-Profil",
  sgRobotChk:       "Roboter",
  sgSliderChk:      "Schieber",
  sgHoldPressure:   "Nachdruck (s)",
  // NEU:
  sgAdvModeChk:     "Erweiterte Logik",
  sgParallelPlastChk: "Paralleles Plastifizieren"
};

const sgConfig = {
  runnerFactorBase: 0.1,
  runnerFactorCav:  2.0,
  minWall:          0.3,
  maxWall:          8.0,
  minCav:           1,
  maxCav:           64,
  safetyDefault:    30,
  defaultHoldTime:  2.0
};

window.addEventListener("DOMContentLoaded", () => {
  initSpritzgussModal();
});

/********************************************************
 * INIT / EVENTLISTENER
 ********************************************************/
function initSpritzgussModal() {
  const runnerChk = document.getElementById("sgRunnerAutoChk");
  if (runnerChk) {
    runnerChk.addEventListener("change", () => {
      if (runnerChk.checked) {
        autoEstimateRunner();
      }
    });
  }

  const btnUebernehmen = document.getElementById("btnSpritzgussUebernehmen");
  if (btnUebernehmen) {
    btnUebernehmen.addEventListener("click", applySpritzgussResult);
  }

  // Flags
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
 * RUNNER-AUTO
 ********************************************************/
function autoEstimateRunner() {
  const wSpin = document.getElementById("sgPartWeight");
  const cSpin = document.getElementById("sgCavities");
  const rSpin = document.getElementById("sgRunnerWeight");
  if (!wSpin || !cSpin || !rSpin) return;

  const partW = parseFloat(wSpin.value) || 50;
  const cav   = parseInt(cSpin.value)   || 4;
  const guess = (sgConfig.runnerFactorBase * partW) + (sgConfig.runnerFactorCav * cav);
  rSpin.value = guess.toFixed(1);
}

/********************************************************
 * BERECHNUNG (AJAX POST)
 ********************************************************/
function calculateSpritzguss() {
  console.log("calculateSpritzguss() => Backend-Request");
  const payload = buildSpritzgussPayload();

  if (!validateSpritzgussInputs(payload.wall_mm, payload.cavities)) {
    return;
  }
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
      console.log("Backend => ", data);
      if (data.error) {
        alert("Fehler: " + data.error);
        return;
      }
      if (!data.ok) {
        alert("Spritzguss-Berechnung unvollständig oder abgelehnt.");
        return;
      }
      fillSpritzgussUI(data);
    })
    .catch(err => {
      console.error("Spritzguss-Request Error:", err);
      alert("Spritzguss-Anfrage fehlgeschlagen: " + err);
    });
}

/********************************************************
 * INPUTS SAMMELN
 ********************************************************/
function buildSpritzgussPayload() {
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

  // NEU:
  const advModeChk   = document.getElementById("sgAdvModeChk");
  const plastChk     = document.getElementById("sgParallelPlastChk");

  return {
    material:       matSel?.value || "PP",
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
    hasContour:     !!contChk?.checked,

    // NEU:
    isAdvanced:     !!advModeChk?.checked,
    parallelPlast:  !!plastChk?.checked
  };
}

/********************************************************
 * PLAUSI
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
 * AUSGABE IN UI
 ********************************************************/
function fillSpritzgussUI(data) {
  document.getElementById("sgClosureForce").textContent =
    data.closure_tons?.toFixed(1) ?? "--";

  // Dropdown aktualisieren => echte Maschine
  const machineDropdown = document.getElementById("sgMachineCombo");
  if (machineDropdown && data.chosenMachine) {
    machineDropdown.value = data.chosenMachine;
  }

  document.getElementById("sgChosenMachine").textContent =
    data.chosenMachine ?? "--";

  document.getElementById("sgCycleShot").textContent =
    data.rawCycleShot?.toFixed(2) ?? "--";

  document.getElementById("sgCyclePart").textContent =
    data.cyclePart_s?.toFixed(2) ?? "--";

  const explainEl = document.getElementById("sgMachineExplain");
  if (explainEl) {
    explainEl.textContent = data.machineExplain || "";
  }

  const tputEl = document.getElementById("sgThroughput");
  if (tputEl) tputEl.textContent = (data.throughput === null) ? "--" : data.throughput;
  const costEl = document.getElementById("sgCostEach");
  if (costEl) costEl.textContent = (data.costEach === null) ? "--" : data.costEach;

  if (Array.isArray(data.rawSegmentVals)) {
    drawSpritzgussChart(data.rawSegmentVals);
  }
}

/********************************************************
 * DONUT-CHART
 ********************************************************/
function drawSpritzgussChart(segmentVals) {
  const ctx = document.getElementById("sgCycleChart");
  if (!ctx) {
    console.warn("drawSpritzgussChart => Canvas fehlt!");
    return;
  }
  if (!sgChart) {
    sgChart = new Chart(ctx, {
      type: "doughnut",
      data: {
        labels: ["Open/Close","Inj+Hold","Cooling","Handling"],
        datasets: [{
          data: segmentVals,
          backgroundColor: ["#007bff","#28a745","#ffc107","#17a2b8"]
        }]
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
 * WERT ÜBERNEHMEN => Z.B. IN TABELLE
 ********************************************************/
function applySpritzgussResult() {
  // HIER die Änderung: Nutze die globale Variable currentSpritzgussRow
  // statt immer Zeile 0 zu beschreiben.
  const cycText = document.getElementById("sgCyclePart")?.textContent || "0";
  const cycVal  = parseFloat(cycText) || 0;

  const fertRows = document.querySelectorAll("#fertTable tbody tr");
  if (
    currentTaktRow !== null &&
    currentTaktRow >= 0 &&
    currentTaktRow < fertRows.length
  ) {
    fertRows[currentTaktRow]
      .cells[1]
      .querySelector("input").value = cycVal.toFixed(1);
  }

  // Modal schließen
  const modalEl = document.getElementById("modalSpritzguss");
  if (modalEl) {
    const bsModal = bootstrap.Modal.getInstance(modalEl);
    if (bsModal) {
      bsModal.hide();
    }
  }
  console.log("applySpritzgussResult => Zyklus", cycVal, "Sekunden in Zeile", currentTaktRow, "übertragen.");
}

/********************************************************
 * PROFILE LADEN => Marketingfreundliche Meldungen
 ********************************************************/
function loadProfile(profileType) {
  console.log("loadProfile:", profileType);
  const changes = [];
  let sgProfileMsg = `Profil '${profileType}' wurde geladen:\n`;

  function getLabelFor(id) {
    return fieldLabels[id] || id;
  }
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
    const wasChecked = el.checked;
    el.checked = boolVal;
    if (wasChecked !== boolVal) {
      changes.push(boolVal
        ? `${getLabelFor(id)} aktiviert`
        : `${getLabelFor(id)} deaktiviert`
      );
    }
  }
  function setCheckboxIfNotEdited(id, boolVal, flagEdited) {
    if (flagEdited) return; // vom User manuell verändert
    setCheckbox(id, boolVal);
  }

  // Profile-spezifische Einstellungen (Standard/Packaging/Automotive)
  if (profileType === "standard") {
    setFormValue("sgMachineCombo", "100t Standard");
    setCheckbox("sgAutomotiveChk", false);
    setCheckboxIfNotEdited("sgRobotChk", false, isRobotEdited);
    setCheckbox("sgSliderChk", false);
    setFormValue("sgSafetyFactor", 30);
    setFormValue("sgPressureSelect", 300);
    setFormValue("sgMinCool", 1.5);

  } else if (profileType === "packaging") {
    setFormValue("sgMachineCombo", "80t HighSpeed");
    setCheckbox("sgAutomotiveChk", false);
    setCheckboxIfNotEdited("sgRobotChk", true, isRobotEdited);
    setCheckbox("sgSliderChk", false);
    setFormValue("sgSafetyFactor", 25);
    setFormValue("sgPressureSelect", 300);
    setFormValue("sgMinCool", 1.0);

    if (!isWallEdited) {
      setFormValue("sgWallThickness", 1.0);
    }
    if (!isCavEdited) {
      setFormValue("sgCavities", 16);
    }

  } else if (profileType === "automotive") {
    setFormValue("sgMachineCombo", "150t Automotive");
    setCheckbox("sgAutomotiveChk", true);
    setCheckboxIfNotEdited("sgRobotChk", true, isRobotEdited);
    setCheckbox("sgSliderChk", true);
    setFormValue("sgSafetyFactor", 35);
    setFormValue("sgPressureSelect", 600);
    setFormValue("sgMinCool", 2.0);

    if (!isWallEdited) {
      setFormValue("sgWallThickness", 3.0);
    }
    if (!isCavEdited) {
      setFormValue("sgCavities", 2);
    }
  }

  if (changes.length === 0) {
    sgProfileMsg += "Keine relevanten Felder verändert.";
  } else {
    sgProfileMsg += changes.map(ch => " - " + ch).join("\n");
  }
  console.log(sgProfileMsg);

  const profChgDiv = document.getElementById("sgProfileChanges");
  if (profChgDiv) {
    profChgDiv.innerText = sgProfileMsg;
  }
}


