// Globale Faktoren:
let material_factor = 1,
    labor_factor    = 1,
    co2_factor      = 1;

// Globale Variablen (Charts + Faktoren)
let costChart = null, co2Chart = null;
let chartInitialized = false;


window.materialData = [];
let currentTaktRow  = null;
let currentMachineRow = null;
let currentLohnRow = null;
/**
 * initCharts() – erstellt costChart + co2Chart,
 * falls noch nicht vorhanden.
 */
// Falls wir GPT-Anfragen starten:
let isGPTSessionCreated = false;

// Hilfsfunktion
function parseFloatAllowZero(inputStr, fallbackVal) {
  console.log("DEBUG: Entering parseFloatAllowZero() with inputStr =", inputStr, "fallbackVal =", fallbackVal);
  let val = parseFloat(inputStr);
  console.log("DEBUG: parseFloat() result =", val);
  if (isNaN(val)) {
    console.log("DEBUG: isNaN(val) => returning fallbackVal =", fallbackVal);
    console.log("DEBUG: Exiting parseFloatAllowZero() - returning fallbackVal");
    return fallbackVal;
  }
  console.log("DEBUG: Exiting parseFloatAllowZero() - returning val =", val);
  return val;
}
// 1. Opening modals
function openParametrikModal() {
  console.log("DEBUG: Entering openParametrikModal()");
  const myModal = new bootstrap.Modal(document.getElementById('modalParametrik'));
  myModal.show();
  console.log("DEBUG: Exiting openParametrikModal()");
}

function openTaktzeitModal() {
  console.log("DEBUG: Entering openTaktzeitModal()");
  const myModal = new bootstrap.Modal(document.getElementById('modalTaktzeit'));
  myModal.show();
  console.log("DEBUG: Exiting openTaktzeitModal()");
}

// 2. AJAX to Parametrik
function calcParamFeinguss() {
  console.log("DEBUG: Entering calcParamFeinguss()");
  const csrftoken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
  console.log("DEBUG: fetch(/mycalc/feinguss) - about to POST {someParam:123}");
  fetch('/mycalc/feinguss', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrftoken
    },
    body: JSON.stringify({ someParam: 123 })
  })
  .then(res => {
    console.log("DEBUG: fetch(/mycalc/feinguss) response status =", res.status);
    return res.json();
  })
  .then(data => {
    console.log("DEBUG: fetch(/mycalc/feinguss) response data =", data);
    document.getElementById('paramResult').innerText = data.result;
    console.log("DEBUG: Exiting calcParamFeinguss() after fetch result");
  });
}

function calcParamKaltflies() {
  console.log("DEBUG: Entering calcParamKaltflies()");
  const csrftoken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
  console.log("DEBUG: fetch(/mycalc/kaltfliess) - about to POST {someParam:456}");
  fetch('/mycalc/kaltfliess', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrftoken
    },
    body: JSON.stringify({ someParam: 456 }) // Beispiel-Parameter
  })
  .then(res => {
    console.log("DEBUG: fetch(/mycalc/kaltfliess) response status =", res.status);
    return res.json();
  })
  .then(data => {
    console.log("DEBUG: fetch(/mycalc/kaltfliess) response data =", data);
    document.getElementById('paramResult').innerText = data.result;
    console.log("DEBUG: Exiting calcParamKaltflies() after fetch result");
  });
}

function calcParamSchmieden() {
  console.log("DEBUG: Entering calcParamSchmieden()");
  const csrftoken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
  console.log("DEBUG: fetch(/mycalc/schmieden) - about to POST {someParam:789}");
  fetch('/mycalc/schmieden', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrftoken
    },
    body: JSON.stringify({ someParam: 789 }) // Beispiel-Parameter
  })
  .then(res => {
    console.log("DEBUG: fetch(/mycalc/schmieden) response status =", res.status);
    return res.json();
  })
  .then(data => {
    console.log("DEBUG: fetch(/mycalc/schmieden) response data =", data);
    document.getElementById('paramResult').innerText = data.result;
    console.log("DEBUG: Exiting calcParamSchmieden() after fetch result");
  });
}

function calcParamPcb() {
  console.log("DEBUG: Entering calcParamPcb()");
  const csrftoken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
  console.log("DEBUG: fetch(/mycalc/pcb) - about to POST {someParam:999}");
  fetch('/mycalc/pcb', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrftoken
    },
    body: JSON.stringify({ someParam: 999 }) // Beispiel-Parameter
  })
  .then(res => {
    console.log("DEBUG: fetch(/mycalc/pcb) response status =", res.status);
    return res.json();
  })
  .then(data => {
    console.log("DEBUG: fetch(/mycalc/pcb) response data =", data);
    document.getElementById('paramResult').innerText = data.result;
    console.log("DEBUG: Exiting calcParamPcb() after fetch result");
  });
}

// 3. Taktzeit
function calcTaktSpritzguss() {
  console.log("DEBUG: Entering calcTaktSpritzguss()");
  const csrftoken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
  console.log("DEBUG: fetch(/mycalc/spritzguss) - about to POST {paramA:'example'}");
  fetch('/mycalc/spritzguss', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrftoken
    },
    body: JSON.stringify({ paramA: 'example' })
  })
  .then(res => {
    console.log("DEBUG: fetch(/mycalc/spritzguss) response status =", res.status);
    return res.json();
  })
  .then(data => {
    console.log("Spritzguss:", data.result);
    console.log("DEBUG: Exiting calcTaktSpritzguss() after fetch result");
  });
}

/**
 * Taktzeit: Druckguss
 * Alte Route: '/calc/takt/druckguss'
 * Neue Route: '/takt_calc/druckguss'
 */
function calcTaktDruckguss() {
  console.log("DEBUG: Entering calcTaktDruckguss()");
  const csrftoken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || "";
  console.log("DEBUG: fetch(/mycalc/druckguss) - about to POST {paramA:'example'}");
  fetch('/mycalc/druckguss', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrftoken
    },
    body: JSON.stringify({ paramA: 'example' })
  })
  .then(res => {
    console.log("DEBUG: fetch(/mycalc/druckguss) response status =", res.status);
    return res.json();
  })
  .then(data => {
    console.log("Druckguss:", data.result);
    console.log("DEBUG: Exiting calcTaktDruckguss() after fetch result");
  })
  .catch(err => console.error("Druckguss error:", err));
}


/**
 * Taktzeit: Zerspanung (Milling)
 * Alte Route: '/calc/takt/milling'
 * Neue Route: '/takt_calc/milling'
 */
function calcTaktZerspanung() {
  console.log("DEBUG: Entering calcTaktZerspanung()");
  const csrftoken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || "";
  console.log("DEBUG: fetch(/mycalc/milling) - about to POST {paramA:'example'}");
  fetch('/mycalc/milling', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrftoken
    },
    body: JSON.stringify({ paramA: 'example' })
  })
  .then(res => {
    console.log("DEBUG: fetch(/mycalc/milling) response status =", res.status);
    return res.json();
  })
  .then(data => {
    console.log("Zerspanung (milling):", data.result);
    console.log("DEBUG: Exiting calcTaktZerspanung() after fetch result");
  })
  .catch(err => console.error("Zerspanung error:", err));
}


/**
 * Taktzeit: Stanzen (Stamping)
 * Alte Route: '/calc/takt/stamping'
 * Neue Route: '/takt_calc/stamping'
 */
function calcTaktStanzen() {
  console.log("DEBUG: Entering calcTaktStanzen()");
  const csrftoken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || "";
  console.log("DEBUG: fetch(/mycalc/stamping) - about to POST {paramA:'example'}");
  fetch('/mycalc/stamping', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrftoken
    },
    body: JSON.stringify({ paramA: 'example' })
  })
  .then(res => {
    console.log("DEBUG: fetch(/mycalc/stamping) response status =", res.status);
    return res.json();
  })
  .then(data => {
    console.log("Stanzen (stamping):", data.result);
    console.log("DEBUG: Exiting calcTaktStanzen() after fetch result");
  })
  .catch(err => console.error("Stanzen error:", err));
}

// 4. Hauptberechnung
function triggerMainCalc() {
  console.log("DEBUG: Entering triggerMainCalc()");
  const csrftoken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
  // Sammle Formdaten (z. B. stückzahl, gewinn, etc.)
  const stueck = document.getElementById('inputJahresStueck').value;
  const gewinn = document.getElementById('inputGewinn').value;

  console.log("DEBUG: fetch(/mycalc/calc) - about to POST stueckzahl =", stueck, "gewinn =", gewinn);
  fetch('/mycalc/calc', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrftoken
    },
    body: JSON.stringify({
      stueckzahl: stueck,
      gewinn: gewinn
      // usw...
    })
  })
  .then(res => {
    console.log("DEBUG: fetch(/mycalc/calc) response status =", res.status);
    return res.json();
  })
  .then(data => {
    console.log("MainCalc result:", data);
    console.log("DEBUG: Exiting triggerMainCalc() after fetch result");
    // Bsp: document.getElementById('spanTotalCosts').innerText = data.total_costs;
  });
}

function calcAll() {
  console.log("DEBUG: Entering calcAll()");

  // -------------------------
  // 1. Projekt-Inputs
  // -------------------------
  console.log("DEBUG: Collecting Projekt-Inputs...");
  const projectName = document.getElementById("txtProjectName")?.value || "";
  const partName    = document.getElementById("txtPartName")?.value    || "";

  // Beispiel: annualQty, lotSize, ...
  const annualQty = parseFloatAllowZero(
    document.getElementById("annualQty")?.value,
    1000
  );
  const lotSize   = parseFloatAllowZero(
    document.getElementById("lotSize")?.value,
    100
  );
  const scrapPct  = parseFloatAllowZero(
    document.getElementById("scrapPct")?.value,
    5
  );
  const sgaPct    = parseFloatAllowZero(
    document.getElementById("sgaPct")?.value,
    10
  );
  const profitPct = parseFloatAllowZero(
    document.getElementById("profitPct")?.value,
    5
  );
  const zielPrice = parseFloatAllowZero(
    document.getElementById("zielPrice")?.value,
    200
  );

  // -------------------------
  // 2. Material-Inputs
  // -------------------------
  console.log("DEBUG: Collecting Material-Inputs...");
  const matName   = document.getElementById("matName")?.value || "";
  let matPrice    = parseFloatAllowZero(document.getElementById("matPrice")?.value,  2);
  let matCo2      = parseFloatAllowZero(document.getElementById("matCo2")?.value,    2);
  let matGK       = parseFloatAllowZero(document.getElementById("matGK")?.value,     5);
  let matWeight   = parseFloatAllowZero(document.getElementById("matWeight")?.value, 0.2);
  let fremdVal    = parseFloatAllowZero(document.getElementById("fremdValue")?.value,0);

  // -------------------------
  // 3. Fertigungstabelle => steps
  // -------------------------
  console.log("DEBUG: Collecting Fertigungs-Steps...");
  const fertRows = document.querySelectorAll("#fertTable tbody tr");
  let steps = [];
  fertRows.forEach((row, idx) => {
    console.log("DEBUG: In fertRows forEach index =", idx, "row =", row);
    const cells = row.cells;
    let stepName = cells[0].querySelector("input")?.value || "";

    let cycTime  = parseFloatAllowZero(cells[1].querySelector("input")?.value, 0);
    let msRate   = parseFloatAllowZero(cells[2].querySelector("input")?.value, 0);
    let lohnRate = parseFloatAllowZero(cells[3].querySelector("input")?.value, 0);
    let ruestVal = parseFloatAllowZero(cells[4].querySelector("input")?.value, 0);
    let toolingVal = parseFloatAllowZero(cells[5].querySelector("input")?.value, 0);
    let fgkPct   = parseFloatAllowZero(cells[6].querySelector("input")?.value, 0);
    let co2Hour  = parseFloatAllowZero(cells[7].querySelector("input")?.value, 0);

    steps.push({
      stepName,
      cycTime,
      msRate,
      lohnRate,
      ruestVal,
      tooling100: toolingVal,
      fgkPct,
      co2Hour
    });
  });

  // -------------------------
  // 4. Globale Faktoren anwenden
  // -------------------------
  console.log("DEBUG: Applying globale Faktoren to matPrice and steps...");
  matPrice = matPrice * material_factor;
  // MsRate / lohnRate / co2Hour mit labor_factor / co2_factor anreichern
  steps = steps.map(st => {
    return {
      ...st,
      msRate:   st.msRate   * labor_factor,
      lohnRate: st.lohnRate * labor_factor,
      co2Hour:  st.co2Hour  * co2_factor
    };
  });

  // -------------------------
  // 5. Finales Payload bauen
  // -------------------------
  console.log("DEBUG: Building payload for /mycalc/calc...");
  const payload = {
    projectName,
    partName,
    annualQty,
    lotSize,
    scrapPct,
    sgaPct,
    profitPct,
    zielPrice,

    mat_factor:   material_factor,
    labor_factor: labor_factor,
    co2_factor:   co2_factor,

    material: {
      name:    matName,
      price:   matPrice,
      co2:     matCo2,
      gk:      matGK,
      weight:  matWeight,
      fremdValue: fremdVal
    },
    steps
  };

  console.log("calcAll() => POST /mycalc/calc, payload:", payload);

  // -------------------------
  // 6. Per fetch() ans Backend
  // -------------------------
  console.log("DEBUG: fetch(/mycalc/calc) - about to POST payload...");
  const csrftoken = document.querySelector('meta[name="csrf-token"]')?.content || "";
  fetch("/mycalc/calc", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrftoken
    },
    body: JSON.stringify(payload)
  })
    .then((res) => {
      console.log("DEBUG: fetch(/mycalc/calc) response status =", res.status);
      if (!res.ok) {
        console.log("DEBUG: !res.ok => throwing error");
        throw new Error("Server error: " + res.status);
      }
      return res.json();
    })
    .then((data) => {
      console.log("Response from /mycalc/calc:", data);
      if (data.error) {
        console.log("DEBUG: data.error =", data.error);
        alert("Fehler: " + data.error);
        return;
      }

      // (a) Ergebnis-Tabelle / Felder füllen
      updateResultTable(data);

      // z. B. top area "Kosten/100" und "CO2/100"
      let cost_100 = data.totalAll100 ?? 0;
      let co2_100  = (data.co2Mat100 ?? 0) + (data.co2Proc100 ?? 0);

      document.getElementById("txtCosts100").value  = cost_100.toFixed(2);
      document.getElementById("txtCo2Per100").value = co2_100.toFixed(2);

      // (b) Charts erzeugen (einmalig) & aktualisieren
      if (!chartInitialized) {
        console.log("DEBUG: chartInitialized == false => calling initCharts()");
        initCharts();  // Neue Funktion: hier nur 1x new Chart(...)
      }
      console.log("DEBUG: calling updateCharts(data)...");
      updateCharts(data);
      console.log("DEBUG: Exiting calcAll() after successful fetch & chart update");
    })
    .catch((err) => {
      console.error("Fehler in calcAll():", err);
      alert("calcAll() error: " + err);
    });
}

/************************************************************
 * initCharts() – erstellt costChart & co2Chart falls nicht
 * vorhanden (oder zerstört alte, wenn chartInitialized=true).
 ************************************************************/
function initCharts() {
  console.log("DEBUG: Entering initCharts()");
  // Falls wir alten Chart haben, zerstören:
  if (chartInitialized && costChart) {
    console.log("DEBUG: chartInitialized && costChart => costChart.destroy()");
    costChart.destroy();
  }
  if (chartInitialized && co2Chart) {
    console.log("DEBUG: chartInitialized && co2Chart => co2Chart.destroy()");
    co2Chart.destroy();
  }

  // costChart
  const costCtx = document.getElementById("costChart");
  costChart = new Chart(costCtx, {
    type: "bar",
    data: {
      labels: ["Material", "Fertigung", "Rest"],
      datasets: [
        {
          label: "Kosten pro 100 Stk",
          data: [0, 0, 0],
          backgroundColor: ["#007bff", "#28a745", "#ffc107"]
        }
      ]
    },
    options: {
      responsive: false,
      scales: {
        y: { beginAtZero: true }
      }
    }
  });

  // co2Chart
  const co2Ctx = document.getElementById("co2Chart");
  co2Chart = new Chart(co2Ctx, {
    type: "bar",
    data: {
      labels: ["Material-CO₂", "Prozess-CO₂"],
      datasets: [
        {
          label: "CO₂ pro 100 Stk",
          data: [0, 0],
          backgroundColor: ["#9CCC65", "#FF7043"]
        }
      ]
    },
    options: {
      responsive: false,
      scales: {
        y: { beginAtZero: true }
      }
    }
  });

  chartInitialized = true;
  console.log("DEBUG: Exiting initCharts() => chartInitialized set to", chartInitialized);
}

/************************************************************
 * updateCharts(data) – übernimmt neue Daten vom Server und
 * aktualisiert costChart & co2Chart
 ************************************************************/

function updateCharts(resultData) {
  console.log("DEBUG: Entering updateCharts() with resultData =", resultData);
  if (!chartInitialized) {
    console.log("DEBUG: chartInitialized is false -> calling initCharts() as fallback");
    // Sicherheitshalber
    initCharts();
  }

  // Beispiel:
  //   - Material = matEinzel100 + matGemein100
  //   - Fertigung = mach100 + lohn100 + fgk100
  //   - Rest = sga100 + profit100 + fremd100
  console.log("DEBUG: Calculating matVal, fertVal, restVal ...");
  const matVal  = (resultData.matEinzel100 ?? 0) + (resultData.matGemein100 ?? 0);
  const fertVal = (resultData.mach100 ?? 0) + (resultData.lohn100 ?? 0) + (resultData.fgk100 ?? 0);
  const restVal = (resultData.sga100 ?? 0) + (resultData.profit100 ?? 0) + (resultData.fremd100 ?? 0);
  console.log("DEBUG: matVal =", matVal, "fertVal =", fertVal, "restVal =", restVal);

  // costChart aktualisieren
  console.log("DEBUG: Updating costChart.data.datasets[0].data with [matVal, fertVal, restVal]");
  costChart.data.datasets[0].data = [matVal, fertVal, restVal];
  costChart.update();
  console.log("DEBUG: costChart updated");

  // CO2:
  console.log("DEBUG: Calculating co2Mat, co2Proc ...");
  const co2Mat  = resultData.co2Mat100  ?? 0;
  const co2Proc = resultData.co2Proc100 ?? 0;
  console.log("DEBUG: co2Mat =", co2Mat, "co2Proc =", co2Proc);

  console.log("DEBUG: Updating co2Chart.data.datasets[0].data with [co2Mat, co2Proc]");
  co2Chart.data.datasets[0].data = [co2Mat, co2Proc];
  co2Chart.update();
  console.log("DEBUG: co2Chart updated");

  console.log("DEBUG: Exiting updateCharts()");
}

/************************************************************
 * "Dritter Teil": Fertigungs-Tabelle-Funktionen + Material-
 * und Maschinen-/Lohn-Funktionen (CSRF-ready).
 ************************************************************/

/** Globale Variable zum Speichern der Daten */


/** ============ TABS (Prev/Next) ============ */
function goPrevTab() {
  console.log("DEBUG: Entering goPrevTab()");
  const allBtns = document.querySelectorAll("#calcTab button");
  const idx = Array.from(allBtns).findIndex((btn) => btn.classList.contains("active"));
  console.log("DEBUG: Current active tab index =", idx);
  if (idx > 0) {
    console.log("DEBUG: Clicking previous tab button");
    allBtns[idx - 1].click();
  } else {
    console.log("DEBUG: Already at the first tab, no action taken");
  }
  console.log("DEBUG: Exiting goPrevTab()");
}
function goNextTab() {
  console.log("DEBUG: Entering goNextTab()");
  const allBtns = document.querySelectorAll("#calcTab button");
  const idx = Array.from(allBtns).findIndex((btn) => btn.classList.contains("active"));
  console.log("DEBUG: Current active tab index =", idx);
  if (idx < allBtns.length - 1) {
    console.log("DEBUG: Clicking next tab button");
    allBtns[idx + 1].click();
  } else {
    console.log("DEBUG: Already at the last tab, no action taken");
  }
  console.log("DEBUG: Exiting goNextTab()");
}

/** ============ Fertigungs-Tabelle: init, addRow, attachRowEvents ============ */
function initFertRows(rowCount) {
  console.log("DEBUG: Entering initFertRows() with rowCount =", rowCount);
  const tbody = document.querySelector("#fertTable tbody");
  if (!tbody) {
    console.log("DEBUG: tbody not found => returning");
    return;
  }

  tbody.innerHTML = "";
  for (let i = 0; i < rowCount; i++) {
    console.log("DEBUG: Creating row i =", i);
    const tr = document.createElement("tr");

    // step:
    const tdStep = document.createElement("td");
    tdStep.innerHTML = `<input type="text" class="form-control" placeholder="Step ${i + 1}" />`;
    tr.appendChild(tdStep);

    // Zyklus + T-Button
    const tdZyklus = document.createElement("td");
    tdZyklus.innerHTML = `
      <div class="flex-container">
        <input type="number" class="form-control" step="0.1" value="" />
        <button class="btn btn-sm btn-outline-secondary" onclick="openZyklusModalWithTakt(${i})">T</button>
      </div>
    `;
    tr.appendChild(tdZyklus);

    // Maschinen + M-Button
    const tdMachine = document.createElement("td");
    tdMachine.innerHTML = `
      <div class="flex-container">
        <input type="number" class="form-control" step="0.1" value="" />
        <button class="btn btn-sm btn-outline-primary" onclick="openMachineModal(${i})">M</button>
      </div>
    `;
    tr.appendChild(tdMachine);

    // Lohn + L-Button
    const tdLohn = document.createElement("td");
    tdLohn.innerHTML = `
      <div class="flex-container">
        <input type="number" class="form-control" step="0.1" value="" />
        <button class="btn btn-sm btn-outline-info" onclick="openLohnModal(${i})">L</button>
      </div>
    `;
    tr.appendChild(tdLohn);

    // Restliche Spalten (Rüst, Tooling, FGK, CO2/h, Kosten/100, CO2/100, …)
    const tdRuest = document.createElement("td");
    tdRuest.innerHTML = `<input type="number" class="form-control" step="0.1" value="" />`;
    tr.appendChild(tdRuest);

    const tdTool = document.createElement("td");
    tdTool.innerHTML = `<input type="number" class="form-control" step="0.1" value="" />`;
    tr.appendChild(tdTool);

    const tdFGK = document.createElement("td");
    tdFGK.innerHTML = `<input type="number" class="form-control" step="0.1" value="" />`;
    tr.appendChild(tdFGK);

    const tdCo2H = document.createElement("td");
    tdCo2H.innerHTML = `<input type="number" class="form-control" step="0.1" value="" />`;
    tr.appendChild(tdCo2H);

    const tdKosten100 = document.createElement("td");
    tdKosten100.innerHTML = `<span class="fw-bold">0.00</span>`;
    tr.appendChild(tdKosten100);

    const tdCo2100 = document.createElement("td");
    tdCo2100.innerHTML = `<span class="fw-bold">0.00</span>`;
    tr.appendChild(tdCo2100);

    tbody.appendChild(tr);
  }
  console.log("DEBUG: Finished creating rows, now calling attachRowEvents()");
  attachRowEvents();
  console.log("DEBUG: Exiting initFertRows()");
}

/** Neue Zeile in FertTable hinzufügen */
function addFertRow() {
  console.log("DEBUG: Entering addFertRow()");
  const tbody = document.querySelector("#fertTable tbody");
  if (!tbody) {
    console.log("DEBUG: tbody not found => returning");
    return;
  }

  const rowIdx = tbody.rows.length;
  console.log("DEBUG: Creating new row with index =", rowIdx);
  const tr = document.createElement("tr");
  tr.innerHTML = `
    <!-- step -->
    <td><input type="text" class="form-control" placeholder="Step ${rowIdx + 1}" /></td>
    <!-- Zyklus + T-Button -->
    <td class="d-flex">
      <input type="number" class="form-control" step="0.1" value="" />
      <button class="btn btn-sm btn-outline-secondary ms-1" onclick="openZyklusModalWithTakt(${rowIdx})">T</button>
    </td>
    <!-- Maschinen + M-Button -->
    <td class="d-flex">
      <input type="number" class="form-control" step="0.1" value="" />
      <button class="btn btn-sm btn-outline-primary ms-1" onclick="openMachineModal(${rowIdx})">M</button>
    </td>
    <!-- Lohn + L-Button -->
    <td class="d-flex">
      <input type="number" class="form-control" step="0.1" value="30" />
      <button class="btn btn-sm btn-outline-primary ms-1" onclick="openLohnModal(${rowIdx})">L</button>
    </td>
    <!-- Weitere Spalten -->
    <td><input type="number" class="form-control" step="0.1" value="" /></td>
    <td><input type="number" class="form-control" step="0.1" value="" /></td>
    <td><input type="number" class="form-control" step="0.1" value="" /></td>
    <td><input type="number" class="form-control" step="0.1" value="" /></td>
    <td><span>0.00</span></td>
    <td><span>0.00</span></td>
  `;
  tbody.appendChild(tr);
  console.log("DEBUG: New row appended to tbody");
  console.log("DEBUG: Exiting addFertRow()");
}

/** attachRowEvents(): z. B. wenn Input-Felder sich ändern => updateRowCalc */
function attachRowEvents() {
  console.log("DEBUG: Entering attachRowEvents()");
  const rows = document.querySelectorAll("#fertTable tbody tr");
  rows.forEach((row, rowIdx) => {
    console.log("DEBUG: In attachRowEvents() forEach - rowIdx =", rowIdx);
    row.querySelectorAll("input").forEach((inp) => {
      inp.addEventListener("change", () => {
        console.log("DEBUG: onChange event for rowIdx =", rowIdx, "input element =", inp);
        const lotVal = parseFloat(document.getElementById("lotSize")?.value) || 100;
        updateRowCalc(rowIdx, lotVal);
      });
    });
  });
  console.log("DEBUG: Exiting attachRowEvents()");
}

/** updateRowCalc(rowIdx, lotSize): rechnet die Zeile neu (dummy) */
function updateRowCalc(rowIdx, lotSize) {
  console.log("DEBUG: Entering updateRowCalc() with rowIdx =", rowIdx, "lotSize =", lotSize);
  const rows = document.querySelectorAll("#fertTable tbody tr");
  if (rowIdx < 0 || rowIdx >= rows.length) {
    console.log("DEBUG: rowIdx out of range => returning");
    return;
  }
  const row = rows[rowIdx];

  // Bsp:
  const cycTime = parseFloat(row.cells[1].querySelector("input").value) || 0;
  const msRate  = parseFloat(row.cells[2].querySelector("input").value) || 0;
  console.log("DEBUG: cycTime =", cycTime, "msRate =", msRate);

  let cost100 = 0;
  if (lotSize > 0) {
    console.log("DEBUG: lotSize > 0 => calculating cost100");
    cost100 = (cycTime * msRate) / 3600.0 * 100;
  }
  row.cells[8].querySelector("span").textContent = cost100.toFixed(2);

  const co2Val = parseFloat(row.cells[7].querySelector("input").value) || 0;
  console.log("DEBUG: co2Val =", co2Val, " -> setting co2/100 field");
  // Bsp: co2 pro stück * 100
  row.cells[9].querySelector("span").textContent = (co2Val * 100).toFixed(2);

  console.log("DEBUG: Exiting updateRowCalc()");
}

/** ============== Material-Funktionen ============== */

/**
 * openMaterialModal() – ruft /auth/whoami => check license => /mycalc/material_list
 * => Füllt Tabelle => Öffnet Modal
 */
function openMaterialModal() {
  console.log("DEBUG: Entering openMaterialModal()");
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || "";

  console.log("DEBUG: fetch(/auth/whoami) => checking license");
  // Lizenzstatus abfragen
  fetch("/auth/whoami", {
    headers:{ "X-CSRFToken": csrfToken }
  })
    .then(res => {
      console.log("DEBUG: /auth/whoami response status =", res.status);
      return res.json();
    })
    .then(data => {
      console.log("DEBUG: /auth/whoami data =", data);
      if (data.license === "extended") {
        console.log("DEBUG: License is extended => fetching /mycalc/material_list");
        // Materialliste laden
        return fetch("/mycalc/material_list", {
          method: "GET",
          headers:{ "X-CSRFToken": csrfToken }
        });
      } else {
        console.log("DEBUG: License not extended => throwing error");
        throw new Error("Lizenz nicht ausreichend.");
      }
    })
    .then(res => {
      console.log("DEBUG: /mycalc/material_list response status =", res.status);
      if (res.ok) {
        return res.json();
      } else {
        throw new Error("HTTP Error " + res.status);
      }
    })
    .then(data => {
      console.log("DEBUG: /mycalc/material_list => data received =", data);
      // fülle Tabelle
      fillMaterialTable(data);

      // Modal anzeigen
      let modalEl = document.getElementById("modalMaterial");
      let bsModal = new bootstrap.Modal(modalEl);
      bsModal.show();
      console.log("DEBUG: material modal shown");
    })
    .catch(err => {
      console.error("openMaterialModal error:", err);
      alert(
        err.message === "Lizenz nicht ausreichend."
          ? "Ihre Lizenz reicht nicht aus, um die Materialliste zu öffnen."
          : "Fehler beim Laden der Materialliste."
      );
    });
  console.log("DEBUG: Exiting openMaterialModal()");
}

/** fillMaterialTable(matArray) – füllt #tblMaterialList */
function fillMaterialTable(matArray) {
  console.log("DEBUG: Entering fillMaterialTable() with matArray length =", matArray.length);
  const tbody = document.querySelector("#tblMaterialList tbody");
  if (!tbody) {
    console.log("DEBUG: #tblMaterialList tbody not found => returning");
    return;
  }

  // Tabelle leeren
  tbody.innerHTML = "";
  window.materialData = matArray; // optional

  matArray.forEach((m, idx) => {
    console.log("DEBUG: In fillMaterialTable() forEach - idx =", idx, "material =", m.material);
    const matName   = m.material       || "Unbekannt";
    const verfahren = m.verfahrensTyp  || "";
    const priceKg   = m.gesamtPreisEURkg?.toFixed?.(2) || "";
    const co2Kg     = m.co2EmissionenKG?.toFixed?.(2)  || "";
    const comm      = m.kommentar      || "";

    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${matName}</td>
      <td>${verfahren}</td>
      <td>${priceKg}</td>
      <td>${co2Kg}</td>
      <td>${comm}</td>
      <td>
        <button class="btn btn-sm btn-primary" onclick="selectMaterial(${idx})">
          Übernehmen
        </button>
      </td>
    `;
    // data-Attrs
    tr.dataset.index   = idx;
    tr.dataset.matName = matName;
    tr.dataset.matPrice= priceKg;
    tr.dataset.matCo2  = co2Kg;

    tbody.appendChild(tr);
  });
  console.log("DEBUG: Exiting fillMaterialTable()");
}

/** selectMaterial(idx): schreibt in #matName, #matPrice, #matCo2 */
function selectMaterial(idx) {
  console.log("DEBUG: Entering selectMaterial() with idx =", idx);
  const row = document.querySelector(`#tblMaterialList tbody tr[data-index="${idx}"]`);
  if (!row) {
    console.log("DEBUG: Row not found => returning");
    return;
  }

  document.getElementById("matName").value  = row.dataset.matName || "";
  document.getElementById("matPrice").value = row.dataset.matPrice||"0.00";
  document.getElementById("matCo2").value   = row.dataset.matCo2  ||"0.00";

  // Modal schließen
  const modalEl = document.getElementById("modalMaterial");
  const bsModal = bootstrap.Modal.getInstance(modalEl);
  bsModal.hide();
  console.log("DEBUG: Material selected, modal hidden");
  console.log("DEBUG: Exiting selectMaterial()");
}

/** filterMaterialList(): optionaler Filter auf window.materialData */
function filterMaterialList() {
  console.log("DEBUG: Entering filterMaterialList()");
  const filterVal = document.getElementById("matFilterInput")?.value.toLowerCase() || "";
  if (!window.materialData) {
    console.log("DEBUG: No window.materialData => returning");
    return;
  }

  console.log("DEBUG: filterVal =", filterVal);
  const filtered = window.materialData.filter(m => {
    const matN = (m.material || "").toLowerCase();
    const verF= (m.verfahrensTyp||"").toLowerCase();
    return matN.includes(filterVal) || verF.includes(filterVal);
  });
  console.log("DEBUG: filtered material count =", filtered.length);

  fillMaterialTable(filtered);
  console.log("DEBUG: Exiting filterMaterialList()");
}

/** openZyklusModalWithTakt(rowIndex) => #modalZyklusBild öffnen */
function openZyklusModalWithTakt(rowIndex) {
  console.log("DEBUG: Entering openZyklusModalWithTakt() with rowIndex =", rowIndex);
  currentTaktRow = rowIndex;
  const modalEl = document.getElementById("modalZyklusBild");
  if (!modalEl) {
    console.log("DEBUG: #modalZyklusBild not found => returning");
    return;
  }
  const bsModal= new bootstrap.Modal(modalEl);
  bsModal.show();
  console.log("DEBUG: ZyklusModal shown for rowIndex =", rowIndex);
  console.log("DEBUG: Exiting openZyklusModalWithTakt()");
}

/** =========== Maschinen-Funktionen =========== */

function openMachineModal(rowIdx) {
  console.log("DEBUG: Entering openMachineModal() with rowIdx =", rowIdx);
  currentMachineRow = rowIdx;
  const modalEl = document.getElementById("modalMachine");
  if (!modalEl) {
    console.log("DEBUG: #modalMachine not found => returning");
    return;
  }
  new bootstrap.Modal(modalEl).show();
  console.log("DEBUG: Machine modal shown");
  console.log("DEBUG: Exiting openMachineModal()");
}

/** openMachineListModal() => holt /mycalc/machine_list */
function openMachineListModal() {
  console.log("DEBUG: Entering openMachineListModal()");
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || "";

  console.log("DEBUG: fetch(/mycalc/machine_list) => GET");
  fetch("/mycalc/machine_list", {
    method: "GET",
    headers:{ "X-CSRFToken": csrfToken }
  })
    .then((res) => {
      console.log("DEBUG: /mycalc/machine_list response status =", res.status);
      if (!res.ok) {
        if (res.status === 403) {
          console.log("DEBUG: 403 => License not sufficient");
          throw new Error("Lizenz nicht ausreichend. Bitte upgraden!");
        }
        throw new Error("Fehler beim Laden der Maschinenliste: " + res.status);
      }
      return res.json();
    })
    .then((data) => {
      console.log("DEBUG: /mycalc/machine_list => data received, length =", data.length);
      fillMachineTable(data);

      const modalEl= document.getElementById("modalMachineList");
      new bootstrap.Modal(modalEl).show();
      console.log("DEBUG: modalMachineList shown");
    })
    .catch((err) => {
      console.error("Maschinenliste Fehler:", err);
      alert(err.message || "Maschinenliste nicht verfügbar.");
    });
  console.log("DEBUG: Exiting openMachineListModal()");
}

/** fillMachineTable(machArr) => #tblMachineList */
function fillMachineTable(machArr) {
  console.log("DEBUG: Entering fillMachineTable() with machArr length =", machArr.length);
  const tbody = document.querySelector("#tblMachineList tbody");
  if (!tbody) {
    console.log("DEBUG: #tblMachineList tbody not found => returning");
    return;
  }

  tbody.innerHTML= "";
  machArr.forEach((m, idx) => {
    console.log("DEBUG: In fillMachineTable() forEach - idx =", idx, "machineName =", m.machineName);
    const mName= m.machineName || "Unbekannt";
    const verf = m.verfahren   || m.type || "";
    const kauf = m.kaufpreis   || 0;
    const pw   = m.power_kW    || 0;
    const comm = m.comment     || "";

    const tr = document.createElement("tr");
    tr.innerHTML=`
      <td>${mName}</td>
      <td>${verf}</td>
      <td>${kauf}</td>
      <td>${pw}</td>
      <td>${comm}</td>
      <td>
        <button class="btn btn-sm btn-primary" onclick="selectMachine(${idx})">
          Übernehmen
        </button>
      </td>
    `;
    tr.dataset.index= idx;
    tr.dataset.kauf = kauf;
    tr.dataset.power= pw;

    tbody.appendChild(tr);
  });
  console.log("DEBUG: Exiting fillMachineTable()");
}

/** selectMachine(idx): schreibt in #machKaufpreis, #machKW */
function selectMachine(idx) {
  console.log("DEBUG: Entering selectMachine() with idx =", idx);
  const row = document.querySelector(`#tblMachineList tbody tr[data-index="${idx}"]`);
  if (!row) {
    console.log("DEBUG: Row not found => returning");
    return;
  }

  const kaufVal  = parseFloat(row.dataset.kauf)  || 0;
  const powerVal = parseFloat(row.dataset.power) || 0;
  console.log("DEBUG: kaufVal =", kaufVal, "powerVal =", powerVal);

  document.getElementById("machKaufpreis").value = kaufVal.toFixed(0);
  document.getElementById("machKW").value        = powerVal.toFixed(1);

  // Modal schließen
  const modalEl= document.getElementById("modalMachineList");
  const bsModal= bootstrap.Modal.getInstance(modalEl);
  bsModal.hide();
  console.log("DEBUG: Machine selected, modal hidden");
  console.log("DEBUG: Exiting selectMachine()");
}

/** =========== Lohn-Funktionen =========== */
function openLohnModal(rowIndex) {
  console.log("DEBUG: Entering openLohnModal() with rowIndex =", rowIndex);
  currentLohnRow = rowIndex;
  const csrfToken= document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || "";

  console.log("DEBUG: fetch(/mycalc/lohn_list) => GET");
  fetch("/mycalc/lohn_list", {
    method: "GET",
    headers:{ "X-CSRFToken": csrfToken }
  })
    .then((res) => {
      console.log("DEBUG: /mycalc/lohn_list response status =", res.status);
      if (!res.ok) {
        if (res.status===403) {
          console.log("DEBUG: 403 => License not sufficient");
          throw new Error("Lizenz nicht ausreichend. Bitte upgraden!");
        }
        throw new Error("Fehler beim Laden der Lohnliste: "+ res.status);
      }
      return res.json();
    })
    .then((lohnData) => {
      console.log("DEBUG: /mycalc/lohn_list => data received, length =", lohnData.length);
      fillLohnTable(lohnData);

      const modalEl= document.getElementById("modalLohn");
      new bootstrap.Modal(modalEl).show();
      console.log("DEBUG: modalLohn shown");
    })
    .catch((err) => {
      console.error("Lohnliste Fehler:", err);
      alert(err.message || "Lohnliste nicht verfügbar.");
    });
  console.log("DEBUG: Exiting openLohnModal()");
}

/** fillLohnTable(lohnArr) => #tblLohnList */
function fillLohnTable(lohnArr) {
  console.log("DEBUG: Entering fillLohnTable() with lohnArr length =", lohnArr.length);
  const tbody = document.querySelector("#tblLohnList tbody");
  if (!tbody) {
    console.log("DEBUG: #tblLohnList tbody not found => returning");
    return;
  }

  tbody.innerHTML= "";
  lohnArr.forEach((item, idx) => {
    console.log("DEBUG: In fillLohnTable() forEach - idx =", idx, "country =", item.country);
    const countryStr= item.country     || "Unbekannt";
    const shiftMod  = item.shiftModel  || "N/A";
    const allIn     = parseFloat(item.allInEURh||0).toFixed(2);
    const comm      = item.comment     || "";

    const tr = document.createElement("tr");
    tr.innerHTML=`
      <td>${countryStr}</td>
      <td>${shiftMod}</td>
      <td>${allIn}</td>
      <td>${comm}</td>
      <td>
        <button class="btn btn-sm btn-primary" onclick="selectLohn(${idx})">
          Übernehmen
        </button>
      </td>
    `;
    tr.dataset.index    = idx;
    tr.dataset.allIneurh= allIn;
    tbody.appendChild(tr);
  });
  console.log("DEBUG: Exiting fillLohnTable()");
}


function selectLohn(idx) {
  console.log("DEBUG: Entering selectLohn() with idx =", idx);
  const row = document.querySelector(`#tblLohnList tbody tr[data-index="${idx}"]`);
  if (!row) {
    console.log("DEBUG: Row not found => returning");
    return;
  }

  const rate = parseFloat(row.dataset.allIneurh) || 0;
  const ops  = parseFloat(document.getElementById("operatorsPerMachine")?.value) || 0.5;
  const lohnGesc = rate * ops; // Gesamtlohn
  console.log("DEBUG: Calculated lohnGesc =", lohnGesc, "(rate =", rate, ", ops =", ops, ")");

  const fertRows = document.querySelectorAll("#fertTable tbody tr");
  console.log("DEBUG: fertRows.length =", fertRows.length);
  if (currentLohnRow >= 0 && currentLohnRow < fertRows.length) {
    console.log("DEBUG: Valid currentLohnRow => setting cell[3] input.value =", lohnGesc.toFixed(2));
    fertRows[currentLohnRow].cells[3].querySelector("input").value = lohnGesc.toFixed(2);
  } else {
    console.log("DEBUG: currentLohnRow out of range => no action");
  }

  // Modal schließen
  const modalEl = document.getElementById("modalLohn");
  console.log("DEBUG: Attempting to close modalLohn");
  const bsModal = bootstrap.Modal.getInstance(modalEl);
  bsModal.hide();

  console.log("DEBUG: Exiting selectLohn()");
}

// ---------------------------------------------
// calcExtendedMachineRate()
//  - Liest Input-Felder (#machKaufpreis, #machNutzdauer, #machAuslast, ...)
//  - Rechnet Jahreskosten + €/h
//  - Speichert Ergebnisse in globale (oder gibt sie zurück)
// ---------------------------------------------
function calcExtendedMachineRate() {
  console.log("DEBUG: Entering calcExtendedMachineRate()");
  // 1) Hole Felder
  const kaufpreis = parseFloat(document.getElementById("machKaufpreis").value) || 100000;
  const jahre     = parseFloat(document.getElementById("machNutzdauer").value) || 5;
  const auslast   = parseFloat(document.getElementById("machAuslast").value)   || 6000;
  const kw        = parseFloat(document.getElementById("machKW").value)        || 100.0;
  const stromPct  = parseFloat(document.getElementById("machStromPct").value) || 80.0;
  const stromCost = parseFloat(document.getElementById("machStromCost").value)|| 0.20;

  // Neu: Flächenbedarf (m²) und Flächenkosten (€/m²/Monat)
  // => Du kannst es wahlweise in 2 Felder oder 1 Feld packen.
  const flaecheBedarf = parseFloat(document.getElementById("machFlaecheBedarf").value) || 20.0;
  const flaecheCost   = parseFloat(document.getElementById("machFlaechenkost").value)  || 7.0;

  const instPct   = parseFloat(document.getElementById("machInstandPct").value) || 3.0;
  const betrPct   = parseFloat(document.getElementById("machBetriebPct").value) || 2.0;
  const availPct  = parseFloat(document.getElementById("machAvailPct").value)   || 85.0;

  console.log("DEBUG: Input values =>", {
    kaufpreis, jahre, auslast, kw, stromPct, stromCost, flaecheBedarf, flaecheCost,
    instPct, betrPct, availPct
  });

  // (A) Abschreibung pro Jahr (lineare)
  const depreciationYear = kaufpreis / jahre;
  console.log("DEBUG: depreciationYear =", depreciationYear);

  const zinssatz = 0.03;
  const interestYear = kaufpreis * 0.5 * zinssatz;
  console.log("DEBUG: interestYear =", interestYear);

  // (C) Instandhaltung pro Jahr
  const instYear = kaufpreis * (instPct / 100.0);
  console.log("DEBUG: instYear =", instYear);

  // (D) Betriebskosten pro Jahr
  const betrYear = kaufpreis * (betrPct / 100.0);
  console.log("DEBUG: betrYear =", betrYear);

  // (E) Flächenkosten pro Jahr
  const flaecheYear = flaecheBedarf * flaecheCost * 12;
  console.log("DEBUG: flaecheYear =", flaecheYear);

  // (F) Strom
  const usedKW = kw * (stromPct / 100.0);
  console.log("DEBUG: usedKW =", usedKW);
  const stromHour = usedKW * stromCost;  // € pro Betriebsstunde
  console.log("DEBUG: stromHour =", stromHour);
  const stromYear = stromHour * auslast;
  console.log("DEBUG: stromYear =", stromYear);

  // (G) Summe pro Jahr
  const sumYear =
      depreciationYear
    + interestYear
    + instYear
    + betrYear
    + flaecheYear
    + stromYear
    // + (lohnRate * operators * auslast) => Nur wenn du Lohn hier einrechnen willst
    ;
  console.log("DEBUG: sumYear =", sumYear);

  // (H) Eff. Stunden => auslast*(availPct/100)
  const effHours = auslast * (availPct / 100.0);
  console.log("DEBUG: effHours =", effHours);

  let costPerHour = 0;
  if (effHours > 0) {
    console.log("DEBUG: effHours > 0 => calculating costPerHour");
    costPerHour = sumYear / effHours;
  } else {
    console.log("DEBUG: effHours <= 0 => costPerHour remains 0");
  }

  // (I) CO2 - optional
  const co2_per_hour = usedKW * 0.38; // dummy => 0.38 kg CO2/kWh
  console.log("DEBUG: co2_per_hour =", co2_per_hour);

  // 3) Zwischenergebnisse in globalem Objekt speichern (o.ä.)
  window.extMachCalc = {
    depYear: depreciationYear,
    interestYear,
    instYear,
    betrYear,
    flaecheYear,
    stromYear,
    sumYear,
    effHours,
    costPerHour,
    co2_per_hour
  };
  console.log("DEBUG: window.extMachCalc =", window.extMachCalc);

  document.getElementById("machKaufpreisHr").value = (effHours > 0 ? depreciationYear / effHours : 0).toFixed(2);
  document.getElementById("machZinsHr").value      = (effHours > 0 ? interestYear     / effHours : 0).toFixed(2);
  document.getElementById("machInstandHr").value   = (effHours > 0 ? instYear        / effHours : 0).toFixed(2);
  document.getElementById("machBetriebHr").value   = (effHours > 0 ? betrYear        / effHours : 0).toFixed(2);
  document.getElementById("machFlaechenkostHr").value = (effHours > 0 ? flaecheYear / effHours : 0).toFixed(2);
  document.getElementById("machStromCostHr").value = (effHours > 0 ? stromYear      / effHours : 0).toFixed(2);
  document.getElementById("machAvailHr").value     = effHours.toFixed(1) + " h eff.";
  document.getElementById("machCo2Hr").value       = co2_per_hour.toFixed(2);
  document.getElementById("machResult").textContent= costPerHour.toFixed(2);

  console.log("DEBUG: Exiting calcExtendedMachineRate()");
}

function acceptMachine() {
  console.log("DEBUG: Entering acceptMachine() => currentMachineRow:", currentMachineRow);
  console.log("DEBUG: Checking if window.extMachCalc is defined");
  // 1) Prüfen, ob calcExtendedMachineRate() schon aufgerufen wurde => extMachCalc existiert
  if (!window.extMachCalc) {
    console.log("DEBUG: window.extMachCalc is falsy => alerting user");
    alert("Bitte zuerst 'Berechnen' klicken!");
    return;
  }
  const rows = document.querySelectorAll("#fertTable tbody tr");
  console.log("DEBUG: rows.length =", rows.length);
  if (currentMachineRow < 0 || currentMachineRow >= rows.length) {
    console.error("Ungültige Zeilen-ID:", currentMachineRow);
    alert("Es wurde keine gültige Zeile ausgewählt oder currentMachineRow ist -1.");
    return;
  }

  const {
    depYear, interestYear, instYear, betrYear,
    flaecheYear, stromYear, sumYear, effHours,
    costPerHour, co2_per_hour
  } = window.extMachCalc;
  console.log("DEBUG: destructured extMachCalc =", {
    depYear, interestYear, instYear, betrYear, flaecheYear, stromYear, sumYear, effHours, costPerHour, co2_per_hour
  });

  // 2) Einzelwerte pro Stunde
  const depHour   = effHours > 0 ? depYear      / effHours : 0;
  const intHour   = effHours > 0 ? interestYear / effHours : 0;
  const instHour  = effHours > 0 ? instYear     / effHours : 0;
  const betrHour  = effHours > 0 ? betrYear     / effHours : 0;
  const flaechHour= effHours > 0 ? flaecheYear  / effHours : 0;
  const stromHour = effHours > 0 ? stromYear    / effHours : 0;
  console.log("DEBUG: calcHourly =>", { depHour, intHour, instHour, betrHour, flaechHour, stromHour });

  // 3) In die Textfelder
  document.getElementById("machKaufpreisHr").value  = depHour.toFixed(2);
  document.getElementById("machZinsHr").value       = intHour.toFixed(2);
  document.getElementById("machInstandHr").value    = instHour.toFixed(2);
  document.getElementById("machBetriebHr").value    = betrHour.toFixed(2);
  document.getElementById("machFlaechenkostHr").value = flaechHour.toFixed(2);
  document.getElementById("machStromCostHr").value  = stromHour.toFixed(2);
  document.getElementById("machAvailHr").value      = effHours.toFixed(1) + " h eff.";
  document.getElementById("machResult").textContent = costPerHour.toFixed(2);
  document.getElementById("machCo2Hr").value        = co2_per_hour.toFixed(2);

  // 4) Endsumme = costPerHour
  // => in #machResult (z. B. <span id="machResult">)
  // (bereits gesetzt oben)

  // 6) In Tab3 die Zeile => cells[2] = msRate, etc.
  const row = rows[currentMachineRow];
  console.log("DEBUG: Setting row.cells[2].querySelector(input).value =", costPerHour.toFixed(2));
  row.cells[2].querySelector("input").value = costPerHour.toFixed(2);   // msRate
  console.log("DEBUG: Setting row.cells[7].querySelector(input).value =", co2_per_hour.toFixed(2));
  row.cells[7].querySelector("input").value = co2_per_hour.toFixed(2); // co2/h

  // => Modal schließen?
  const modalEl = document.getElementById("modalMachine");
  console.log("DEBUG: Attempting to close modalMachine");
  let bsModal = bootstrap.Modal.getInstance(modalEl);
  bsModal.hide();

  console.log("DEBUG: Exiting acceptMachine()");
}

function updateResultTable(e) {
  console.log("DEBUG: Entering updateResultTable() with object e =", e);
  document.getElementById("tdMatEinzel").textContent  = (e.matEinzel100 ?? 0).toFixed(2),
  document.getElementById("tdMatGemein").textContent  = (e.matGemein100 ?? 0).toFixed(2),
  document.getElementById("tdFremd").textContent      = (e.fremd100     ?? 0).toFixed(2),
  document.getElementById("tdMach").textContent       = (e.mach100      ?? 0).toFixed(2),
  document.getElementById("tdLohn").textContent       = (e.lohn100      ?? 0).toFixed(2),
  document.getElementById("tdFGK").textContent        = (e.fgk100       ?? 0).toFixed(2),
  document.getElementById("tdHerstell").textContent   = (e.herstell100  ?? 0).toFixed(2),
  document.getElementById("tdSGA").textContent        = (e.sga100       ?? 0).toFixed(2),
  document.getElementById("tdProfit").textContent     = (e.profit100    ?? 0).toFixed(2),
  document.getElementById("tdTotal").textContent      = (e.totalAll100  ?? 0).toFixed(2);
  console.log("DEBUG: Exiting updateResultTable()");
}

function onSliderMaterialChange(e) {
  console.log("DEBUG: Entering onSliderMaterialChange() with e =", e);
  // e = int % (z.B. -30..+30)
  material_factor = 1 + e / 100;
  console.log("DEBUG: material_factor =", material_factor, "=> calling calcAll()");
  calcAll(); // Deine lokale Rechenfunktion
  console.log("DEBUG: Exiting onSliderMaterialChange()");
}

/**
 * onSliderLaborChange(e)
 */
function onSliderLaborChange(e) {
  console.log("DEBUG: Entering onSliderLaborChange() with e =", e);
  labor_factor = 1 + e / 100;
  console.log("DEBUG: labor_factor =", labor_factor, "=> calling calcAll()");
  calcAll();
  console.log("DEBUG: Exiting onSliderLaborChange()");
}

/**
 * onSliderCO2Change(e)
 */
function onSliderCO2Change(e) {
  console.log("DEBUG: Entering onSliderCO2Change() with e =", e);
  co2_factor = 1 + e / 100;
  console.log("DEBUG: co2_factor =", co2_factor, "=> calling calcAll()");
  calcAll();
  console.log("DEBUG: Exiting onSliderCO2Change()");
}

function exampleFetchChartsData() {
  console.log("DEBUG: Entering exampleFetchChartsData()");
  const csrftoken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || "";
  console.log("DEBUG: fetch(/calc/chartsData) - about to POST with { someParam: 123 }");
  fetch("/calc/chartsData", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrftoken
    },
    body: JSON.stringify({ someParam: 123 })
  })
    .then(res => {
      console.log("DEBUG: fetch(/calc/chartsData) response status =", res.status);
      return res.json();
    })
    .then(data => {
      console.log("DEBUG: /calc/chartsData response data =", data);
      // data enthält z. B. { matVal, fertVal, restVal, co2Mat, co2Proc }
      costChart.data.datasets[0].data = [data.matVal, data.fertVal, data.restVal];
      costChart.update();

      co2Chart.data.datasets[0].data = [data.co2Mat, data.co2Proc];
      co2Chart.update();
      console.log("DEBUG: Charts updated from exampleFetchChartsData()");
    })
    .catch(err => {
      console.error("chartsData fetch error:", err);
    });
  console.log("DEBUG: Exiting exampleFetchChartsData()");
}

window.baugruppenItems = window.baugruppenItems || [];

function renderBaugruppeItems() {
  console.log("DEBUG: Entering renderBaugruppeItems()");
  const tb = document.querySelector("#baugruppeTable tbody");
  if (!tb) {
    console.log("DEBUG: #baugruppeTable tbody not found => returning");
    return;
  }
  tb.innerHTML = ""; // Tabelle leeren

  for (let i = 0; i < baugruppenItems.length; i++) {
    console.log("DEBUG: In for loop => i =", i, " item =", baugruppenItems[i]);
    const it = baugruppenItems[i];
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>
        <input 
          type="text" 
          class="form-control form-control-sm"
          value="${it.name ?? ''}"
          style="width: 120px;"
          oninput="baugruppenItems[${i}].name = this.value" 
        />
      </td>
      <td>${it.verfahren ?? ''}</td>
      <td>${(it.matEinzel ?? 0).toFixed(2)}</td>
      <td>${(it.matGemein ?? 0).toFixed(2)}</td>
      <td>${(it.fremd ?? 0).toFixed(2)}</td>
      <td>${(it.mach ?? 0).toFixed(2)}</td>
      <td>${(it.lohn ?? 0).toFixed(2)}</td>
      <td>${(it.fgk ?? 0).toFixed(2)}</td>
      <td>${(it.herstell ?? 0).toFixed(2)}</td>
      <td>${(it.sga ?? 0).toFixed(2)}</td>
      <td>${(it.profit ?? 0).toFixed(2)}</td>
      <td>${(it.total ?? 0).toFixed(2)}</td>
      <td>${(it.co2_100 ?? 0).toFixed(2)}</td>
    `;
    tb.appendChild(tr);
  }
  console.log("DEBUG: Exiting renderBaugruppeItems()");
}

/**
 * Summiert alle Baugruppenwerte und zeigt sie im Fuß (tfoot)
 */
function calcBaugruppeSum() {
  let sumMatEinz = 0, sumMatGem = 0, sumFremd = 0, sumMach = 0,
      sumLohn = 0, sumFGK = 0, sumHerstell = 0, sumSGA = 0,
      sumProfit = 0, sumTotal = 0, sumCo2 = 0;

  // Werte summieren
  for (const it of baugruppenItems) {
    sumMatEinz  += (it.matEinzel  ?? 0);
    sumMatGem   += (it.matGemein  ?? 0);
    sumFremd    += (it.fremd      ?? 0);
    sumMach     += (it.mach       ?? 0);
    sumLohn     += (it.lohn       ?? 0);
    sumFGK      += (it.fgk        ?? 0);
    sumHerstell += (it.herstell   ?? 0);
    sumSGA      += (it.sga        ?? 0);
    sumProfit   += (it.profit     ?? 0);
    sumTotal    += (it.total      ?? 0);
    sumCo2      += (it.co2_100    ?? 0);
  }

  // Summen in <tfoot> Felder schreiben
  document.getElementById("bgSumMatEinzel").textContent  = sumMatEinz.toFixed(2);
  document.getElementById("bgSumMatGemein").textContent  = sumMatGem.toFixed(2);
  document.getElementById("bgSumFremd").textContent      = sumFremd.toFixed(2);
  document.getElementById("bgSumMach").textContent       = sumMach.toFixed(2);
  document.getElementById("bgSumLohn").textContent       = sumLohn.toFixed(2);
  document.getElementById("bgSumFGK").textContent        = sumFGK.toFixed(2);
  document.getElementById("bgSumHerstell").textContent   = sumHerstell.toFixed(2);
  document.getElementById("bgSumSGA").textContent        = sumSGA.toFixed(2);
  document.getElementById("bgSumProfit").textContent     = sumProfit.toFixed(2);
  document.getElementById("bgSumTotal").textContent      = sumTotal.toFixed(2);
  document.getElementById("bgSumCO2").textContent        = sumCo2.toFixed(2);
}

/**
 * Liest die Daten aus Tab 4 und überträgt sie in baugruppenItems
 */
function addResultToBaugruppeFromTab4() {
  // Hole Bauteilname (z. B. aus #txtPartName)
  const name = document.getElementById("txtPartName")?.value || "Bauteil X";
  // Optional: Verfahren
  const verfahren = "---"; // oder: document.getElementById(...) ?

  // Lese Zahlen aus Tab 4 Feldern
  const matEinzel  = parseFloat(document.getElementById("tdMatEinzel")?.textContent || "0");
  const matGemein  = parseFloat(document.getElementById("tdMatGemein")?.textContent || "0");
  const fremd      = parseFloat(document.getElementById("tdFremd")?.textContent     || "0");
  const mach       = parseFloat(document.getElementById("tdMach")?.textContent      || "0");
  const lohn       = parseFloat(document.getElementById("tdLohn")?.textContent      || "0");
  const fgk        = parseFloat(document.getElementById("tdFGK")?.textContent       || "0");
  const herstell   = parseFloat(document.getElementById("tdHerstell")?.textContent  || "0");
  const sga        = parseFloat(document.getElementById("tdSGA")?.textContent       || "0");
  const profit     = parseFloat(document.getElementById("tdProfit")?.textContent    || "0");
  const total      = parseFloat(document.getElementById("tdTotal")?.textContent     || "0");
  const co2_100    = parseFloat(document.getElementById("txtCo2Per100")?.value      || "0");

  // Neues Objekt
  const newItem = {
    name,
    verfahren,
    matEinzel,
    matGemein,
    fremd,
    mach,
    lohn,
    fgk: fgk,
    herstell,
    sga,
    profit,
    total,
    co2_100
  };
  baugruppenItems.push(newItem);

  // Neu rendern + Summieren
  renderBaugruppeItems();
  calcBaugruppeSum();
}

/**
 * Liste zurücksetzen
 */
function resetBaugruppenListe() {
  baugruppenItems = [];
  renderBaugruppeItems();
  calcBaugruppeSum();
}

/**
 * Manuelles Hinzufügen
 */
function addManualBaugruppe() {
  const name       = prompt("Bauteilname:")          || "Manuelles Bauteil";
  const verfahren  = prompt("Verfahren:")            || "---";
  const matEinzel  = parseFloat(prompt("MatEinzel (€/100):")   || 0);
  const matGemein  = parseFloat(prompt("MatGemein (€/100):")   || 0);
  const fremd      = parseFloat(prompt("Fremdzukauf (€/100):") || 0);
  const mach       = parseFloat(prompt("Maschinenkosten (€/100):") || 0);
  const lohn       = parseFloat(prompt("Lohnkosten (€/100):")   || 0);
  const fgk        = parseFloat(prompt("FGK (€/100):")          || 0);
  const herstell   = parseFloat(prompt("Herstellkosten (€/100):")|| 0);
  const sga        = parseFloat(prompt("SG&A (€/100):")         || 0);
  const profit     = parseFloat(prompt("Profit (€/100):")       || 0);
  const total      = parseFloat(prompt("Total (€/100):")        || 0);
  const co2_100    = parseFloat(prompt("CO₂/100 (kg):")         || 0);

  const newItem = {
    name,
    verfahren,
    matEinzel,
    matGemein,
    fremd,
    mach,
    lohn,
    fgk,
    herstell,
    sga,
    profit,
    total,
    co2_100
  };
  baugruppenItems.push(newItem);
  renderBaugruppeItems();
  calcBaugruppeSum();
}

/**
 * Export als CSV
 */
function exportBaugruppenAsCSV() {
  if (!baugruppenItems.length) {
    alert("Keine Einträge in der Baugruppenliste.");
    return;
  }
  let csvStr = "Bauteilname;Verfahren;MatEinzel;MatGemein;Fremd;Mach;Lohn;FGK;Herstell;SGA;Profit;Total;CO2_100\n";
  for (const it of baugruppenItems) {
    csvStr += [
      it.name,
      it.verfahren,
      (it.matEinzel  ?? 0).toFixed(2),
      (it.matGemein  ?? 0).toFixed(2),
      (it.fremd      ?? 0).toFixed(2),
      (it.mach       ?? 0).toFixed(2),
      (it.lohn       ?? 0).toFixed(2),
      (it.fgk        ?? 0).toFixed(2),
      (it.herstell   ?? 0).toFixed(2),
      (it.sga        ?? 0).toFixed(2),
      (it.profit     ?? 0).toFixed(2),
      (it.total      ?? 0).toFixed(2),
      (it.co2_100    ?? 0).toFixed(2),
    ].join(";") + "\n";
  }
  const blob = new Blob([csvStr], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);

  const link = document.createElement("a");
  link.href = url;
  link.download = "baugruppe_export.csv";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

/**
 * (Falls wir später AJAX-Calls für Baugruppen-POST an Server machen wollen)
 * => hier ein Beispiel, wie wir CSRF konform abwickeln
 */
function exampleBaugruppeAjax() {
  // Beachte: DU hast aktuell KEINE fetch in diesem Baugruppen-Code.
  // Dies ist nur eine Vorlage, falls du später Daten per AJAX speichern willst.
  const csrftoken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || "";
  fetch('/some/baugruppe/api', {
    method:'POST',
    headers:{
      'Content-Type':'application/json',
      'X-CSRFToken': csrftoken
    },
    body: JSON.stringify({ items: baugruppenItems })
  })
    .then(res=>res.json())
    .then(data=>{
      console.log("Saved baugruppenItems:", data);
    })
    .catch(err=>console.error("Error saving baugruppen:", err));
}

// Beim Laden einmal initial rendern + summieren
document.addEventListener("DOMContentLoaded", () => {
  renderBaugruppeItems();
  calcBaugruppeSum();
});






//----------------------------------------------------------
// mycalc.js – Haupt-JavaScript-Datei
//----------------------------------------------------------



function openZyklusModalwithtakt() {
  const zyklusModalEl = document.getElementById("modalZyklusBild");
  if (!zyklusModalEl) {
    console.error("modalZyklusBild not found!");
    return;
  }
  const bsModal = new bootstrap.Modal(zyklusModalEl);
  bsModal.show();
}

function closeZyklusModal() {
  const zyklusModalEl = document.getElementById("modalZyklusBild");
  if (!zyklusModalEl) return;
  const bsModal = bootstrap.Modal.getInstance(zyklusModalEl);
  bsModal?.hide();
}

/**
 * Parametric Tools Modal
 */
function openParamToolsModal() {
  const paramEl = document.getElementById("modalParamTools");
  if (!paramEl) {
    console.error("modalParamTools not found!");
    return;
  }
  const bsModal = new bootstrap.Modal(paramEl);
  bsModal.show();
}

/**
 * Schließt Parametric Tools (falls offen).
 */
function closeParamToolsModal() {
  const paramEl = document.getElementById("modalParamTools");
  if (!paramEl) return;
  const bsModal = bootstrap.Modal.getInstance(paramEl);
  bsModal?.hide();
}

/**
 * Spritzguss
 */
function openSpritzgussModal() {
  closeZyklusModal();
  const sgModalEl = document.getElementById("modalSpritzguss");
  if (!sgModalEl) {
    console.error("Modal 'modalSpritzguss' nicht gefunden!");
    return;
  }
  const bsModal = new bootstrap.Modal(sgModalEl);
  bsModal.show();
}




function openDruckgussModal() {
  // Optional: Zyklus-Modal schließen, falls offen
  // closeZyklusModal();

  const dgModalEl = document.getElementById("modalDruckguss");
  if (!dgModalEl) {
    console.error("modalDruckguss not found!");
    return;
  }
  const bsModal = new bootstrap.Modal(dgModalEl);
  bsModal.show();
}

function openMillingModal() {
  // Optional: Zykluszeit-Modal schließen, etc.
  // closeZyklusModal();

  const millModalEl = document.getElementById("modalMilling");
  if (!millModalEl) {
    console.error("modalMilling not found!");
    return;
  }
  const bsModal = new bootstrap.Modal(millModalEl);
  bsModal.show();
}


function openStampingModal() {
  // Evtl. vorher "Zykluszeit-Modal" schließen oder ParamTools schließen ...
  // closeZyklusModal();

  const stModalEl = document.getElementById("modalStamping");
  if (!stModalEl) {
    console.error("modalStamping not found!");
    return;
  }
  const bsModal = new bootstrap.Modal(stModalEl);
  bsModal.show();
}


function openFeingussModal() {
  closeParamToolsModal();
  const modalEl = document.getElementById("feingussModal");
  if (!modalEl) return;
  const bsModal = new bootstrap.Modal(modalEl);
  bsModal.show();
}


function openSchmiedenModal() {
  closeParamToolsModal();
  alert("Schmieden-Modal not implemented.");
}


function openKaltfliessModal() {
  // Schließt ggf. das ParamTools-Modal
  closeParamToolsModal();

  const modalEl = document.getElementById("kaltfliessModal");
  if (!modalEl) {
    console.error("kaltfliessModal not found!");
    return;
  }
  const bsModal = new bootstrap.Modal(modalEl);
  bsModal.show();
}


function openPcbModal() {
  // Falls du vorher ein Tools-Modal schließen willst (z. B. closeParamToolsModal()),
  // kannst du das hier tun, z. B.:
  // closeParamToolsModal();

  const pcbEl = document.getElementById("pcbModal");
  if (!pcbEl) {
    console.error("pcbModal not found!");
    return;
  }
  const bsModal = new bootstrap.Modal(pcbEl);
  bsModal.show();
}
/**
 * onAskGPT(inputId, outputId):
 *  - Liest question aus inputId,
 *  - ruft askCustomGPT(question),
 *  - schreibt Antwort in outputId.
 */
function onAskGPT(inputId, outputId) {
  const inp = document.getElementById(inputId);
  const out = document.getElementById(outputId);
  if (!inp || !out) return;

  const question = inp.value.trim();
  if (!question) {
    out.textContent = "Bitte frage etwas...";
    return;
  }

  out.textContent = "Ich frage die KI...";
  askCustomGPT(question)
    .then((reply) => {
      out.textContent = reply;
    })
    .catch((err) => {
      out.textContent = "Fehler: " + err.message;
      console.error("onAskGPT error:", err);
    });
}

/**
 * askCustomGPT(userQuestion):
 *  - Ruft /mycalc/gpt_ask auf, schickt {question}, holt {answer}
 *  - Session-Cookie via credentials:"include"
 *  - Neu: X-CSRFToken.
 */
function askCustomGPT(userQuestion) {
  const csrftoken = document.querySelector('meta[name="csrf-token"]')?.content || "";
  return fetch("/mycalc/gpt_ask", {
    method: "POST",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrftoken
    },
    body: JSON.stringify({ question: userQuestion })
  })
    .then((res) => {
      if (!res.ok) {
        throw new Error("GPT request error: " + res.status);
      }
      return res.json();
    })
    .then((data) => {
      if (data.error) {
        throw new Error("GPT error: " + data.error);
      }
      return data.answer || "Keine Antwort gefunden.";
    });
}

/** ================= Login/Logout/Session ================ */

/**
 * doLogin(): Schickt email+password an /auth/login (POST)
 */
function doLogin() {
  const email = document.getElementById("txtEmail")?.value || "";
  const password = document.getElementById("txtPass")?.value || "";

  const csrftoken = document.querySelector('meta[name="csrf-token"]')?.content || "";
  fetch("/auth/login", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrftoken
    },
    body: JSON.stringify({ email, password })
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.error) {
        alert(data.error);
        return;
      }
      // Verstecke LoginPanel, zeige userInfo
      document.getElementById("loginPanel").style.display = "none";
      document.getElementById("userInfo").style.display = "block";
      document.getElementById("spanUserEmail").textContent = email;

      // Lizenzstatus prüfen
      checkLicense();
    })
    .catch((err) => {
      alert("Login fehlgeschlagen: " + err);
    });
}

/**
 * doLogout():
 *  - POST /auth/logout
 *  - leitet ggf. auf /auth/login weiter
 */
function doLogout() {
  const csrftoken = document.querySelector('meta[name="csrf-token"]')?.content || "";
  fetch("/auth/logout", {
    method: "POST",
    headers: { "X-CSRFToken": csrftoken }
  })
    .then((res) => res.json())
    .then(() => {
      window.location.href = "/auth/login";
    })
    .catch((err) => {
      alert("Logout fehlgeschlagen: " + err);
    });
}

/**
 * doRegister(): email+password => /auth/register
 */
function doRegister() {
  const email = document.getElementById("txtEmail")?.value || "";
  const password = document.getElementById("txtPass")?.value || "";

  const csrftoken = document.querySelector('meta[name="csrf-token"]')?.content || "";
  fetch("/auth/register", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrftoken
    },
    body: JSON.stringify({ email, password })
  })
    .then((res) => res.json())
    .then((data) => {
      console.log("DEBUG: Server-Antwort:", data);
      if (data.error) {
        alert(data.error);
        return;
      }
      alert("Registrierung erfolgreich. Jetzt einloggen.");
    })
    .catch((err) => {
      alert("Registrierung fehlgeschlagen: " + err);
    });
}

/** ===================== Lizenz / whoami ===================== */

/**
 * checkLicense():
 *  - Ruft /auth/whoami => ermittelt logged_in, license
 *  - Zeigt/hide #userInfo, #loginPanel
 */
function checkLicense() {
  const csrftoken = document.querySelector('meta[name="csrf-token"]')?.content || "";
  fetch("/auth/whoami", {
    method: "GET",
    headers: { "X-CSRFToken": csrftoken }
  })
    .then((res) => res.json())
    .then((data) => {
      console.log("DEBUG: Lizenzprüfung/whoami:", data);
      if (data.logged_in) {
        // Benutzerinfos
        document.getElementById("userInfo").style.display = "block";
        document.getElementById("spanUserEmail").textContent = data.email || "Unbekannt";
        // Weitere UI-Anpassungen je nach data.license
      } else {
        // Nicht eingeloggt => userInfo verstecken
        document.getElementById("userInfo").style.display = "none";
      }
    })
    .catch((err) => {
      console.error("Lizenzstatus konnte nicht abgerufen werden:", err);
    });
}

/**
 * buyExtended():
 *  - POST /pay/create-checkout-session => { checkout_url }
 *  - Weiterleitung
 */
function buyExtended() {
  const csrftoken = document.querySelector('meta[name="csrf-token"]')?.content || "";
  fetch("/pay/create-checkout-session", {
    method: "POST",
    headers:{ "X-CSRFToken": csrftoken }
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.error) {
        alert(data.error);
        return;
      }
      window.location = data.checkout_url;
    })
    .catch((err) => {
      alert("Fehler beim Start des Lizenzkaufs: " + err);
    });
}

/**
 * checkMaterialAccess():
 *  - Ruft /auth/whoami => prüft license
 *  - Wenn license===extended => openMaterialModal()
 */
function checkMaterialAccess() {
  const csrftoken = document.querySelector('meta[name="csrf-token"]')?.content || "";
  fetch("/auth/whoami", {
    method: "GET",
    headers:{ "X-CSRFToken": csrftoken }
  })
    .then((res) => res.json())
    .then((data) => {
      console.log("DEBUG: Lizenzprüfung Material:", data);
      if (data.logged_in && data.license === "extended") {
        openMaterialModal();
      } else {
        alert("Materialliste nur in Extended-Version verfügbar. Bitte upgraden!");
      }
    })
    .catch((err) => {
      console.error("Fehler checkMaterialAccess:", err);
      alert("Ein Fehler ist aufgetreten. Bitte später erneut versuchen.");
    });
}

/**
 * checkLoanAccess():
 *  - Ruft /auth/whoami => prüft license
 *  - wenn extended => openLohnModal()
 */
function checkLoanAccess() {
  const csrftoken = document.querySelector('meta[name="csrf-token"]')?.content || "";
  fetch("/auth/whoami", {
    method: "GET",
    headers:{ "X-CSRFToken": csrftoken }
  })
    .then((res) => res.json())
    .then((data) => {
      console.log("DEBUG: Lizenzprüfung Lohnliste:", data);
      if (data.logged_in && data.license === "extended") {
        openLohnModal();
      } else {
        alert("Lohnliste nur in Extended-Version verfügbar. Bitte upgraden!");
      }
    })
    .catch((err) => {
      console.error("Fehler checkLoanAccess:", err);
      alert("Ein Fehler ist aufgetreten. Bitte später erneut versuchen.");
    });
}

/**
 * DOMContentLoaded => checkLicense() aufrufen
 */
document.addEventListener("DOMContentLoaded", () => {
  checkLicense();
});

// Exporte, falls nötig
window.onAskGPT     = onAskGPT;
window.doLogin      = doLogin;
window.doLogout     = doLogout;
window.doRegister   = doRegister;
window.checkLicense = checkLicense;
window.buyExtended  = buyExtended;
window.checkMaterialAccess = checkMaterialAccess;
window.checkLoanAccess = checkLoanAccess;

document.addEventListener("DOMContentLoaded", () => {
  initFertRows(DEFAULT_ROW_COUNT);
  initCharts();
});