// Globale Faktoren:
let material_factor = 1,
    labor_factor = 1,
    co2_factor = 1;

// Globale Variablen (Charts + Faktoren)
let costChart = null, co2Chart = null;
let chartInitialized = false;

let apexCostChart = null;
let apexCo2Chart = null;
let apexInitialized = false;

window.materialData = [];
let currentTaktRow = null;
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

/**
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
 */
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
  const partName = document.getElementById("txtPartName")?.value || "";

  // Beispiel: annualQty, lotSize, ...
  const annualQty = parseFloatAllowZero(
    document.getElementById("annualQty")?.value,
    1000
  );
  const lotSize = parseFloatAllowZero(
    document.getElementById("lotSize")?.value,
    100
  );
  const scrapPct = parseFloatAllowZero(
    document.getElementById("scrapPct")?.value,
    5
  );
  const sgaPct = parseFloatAllowZero(
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
  const matName = document.getElementById("matName")?.value || "";
  let matPrice = parseFloatAllowZero(document.getElementById("matPrice")?.value, 2);
  let matCo2 = parseFloatAllowZero(document.getElementById("matCo2")?.value, 2);
  let matGK = parseFloatAllowZero(document.getElementById("matGK")?.value, 5);
  let matWeight = parseFloatAllowZero(document.getElementById("matWeight")?.value, 0.2);
  let fremdVal = parseFloatAllowZero(document.getElementById("fremdValue")?.value, 0);

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

    let cycTime = parseFloatAllowZero(cells[1].querySelector("input")?.value, 0);
    let msRate = parseFloatAllowZero(cells[2].querySelector("input")?.value, 0);
    let lohnRate = parseFloatAllowZero(cells[3].querySelector("input")?.value, 0);
    let ruestVal = parseFloatAllowZero(cells[4].querySelector("input")?.value, 0);
    let toolingVal = parseFloatAllowZero(cells[5].querySelector("input")?.value, 0);
    let fgkPct = parseFloatAllowZero(cells[6].querySelector("input")?.value, 0);
    let co2Hour = parseFloatAllowZero(cells[7].querySelector("input")?.value, 0);

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
  // Beispiel: material_factor, labor_factor, co2_factor
  // Du musst sicherstellen, dass diese Variablen global existieren!
  matPrice = matPrice * (window.material_factor || 1);
  steps = steps.map(st => {
    return {
      ...st,
      msRate: st.msRate * (window.labor_factor || 1),
      lohnRate: st.lohnRate * (window.labor_factor || 1),
      co2Hour: st.co2Hour * (window.co2_factor || 1)
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

    mat_factor: window.material_factor || 1,
    labor_factor: window.labor_factor || 1,
    co2_factor: window.co2_factor || 1,

    material: {
      name: matName,
      price: matPrice,
      co2: matCo2,
      gk: matGK,
      weight: matWeight,
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

      // top area "Kosten/100" und "CO2/100"
      let cost_100 = data.totalAll100 ?? 0;
      let co2_100 = (data.co2Mat100 ?? 0) + (data.co2Proc100 ?? 0);

        // Quick & Dirty => pro Stück
  let cost_per_piece = cost_100 / 100;
  let co2_per_piece  = co2_100  / 100;
      document.getElementById("txtCosts100").value = cost_per_piece.toFixed(4);
  document.getElementById("txtCo2Per100").value = co2_per_piece.toFixed(4);

      // (b) ApexCharts erzeugen (einmalig) & aktualisieren
      if (!apexInitialized) {
        console.log("DEBUG: apexInitialized == false => calling initApexCharts()");
        initApexCharts();
      }
      console.log("DEBUG: calling updateApexCharts(data)...");
      updateApexCharts(data);
      console.log("DEBUG: Exiting calcAll() after successful fetch & chart update");
    })
    .catch((err) => {
      console.error("Fehler in calcAll():", err);
      alert("calcAll() error: " + err);
    });
}

/************************************************************
 * initApexCharts() – Erstellt apexCostChart & apexCo2Chart
 ************************************************************/
/************************************************************
 * initApexCharts() – Kompakter & "cooler" Style
 ************************************************************/
function initApexCharts() {
  console.log("DEBUG: Entering initApexCharts()");

  // 1) Check if Dark Mode aktiv ist
  const appEl = document.getElementById('app');
  const isDarkModeActive = appEl && appEl.classList.contains('app-theme-dark-mode');

  // (A) Falls schon existieren -> destroy
  if (apexInitialized && apexCostChart) {
    apexCostChart.destroy();
  }
  if (apexInitialized && apexCo2Chart) {
    apexCo2Chart.destroy();
  }

  /********************************************************
   * (B) Kostenverteilung als "Pie" (Kuchen)
   * Wir verteilen Material, Fertigung, SG&A, Profit
   *******************************************************/
  let costPieOptions = {
    chart: {
      type: 'pie',
      height: 180,
      // Dynamische Farbe je nach Dark/Light
      foreColor: isDarkModeActive ? '#ccc' : '#000',
      background: isDarkModeActive ? '#2d2d2d' : '#f8f9fa'
    },
    series: [0, 0, 0, 0],     // [Material, Fertigung, SGA, Profit]
    labels: ['Material', 'Fertigung', 'SG&A', 'Profit'],
    colors: ['#00c3ff', '#ffc107', '#fe6f5e', '#9b59b6'], // 4 Versch. Farben
    tooltip: {
      y: {
        formatter: (val) => val.toFixed(2) + ' €'
      }
    }
  };
  apexCostChart = new ApexCharts(
    document.querySelector("#apexCostChart"),
    costPieOptions
  );
  apexCostChart.render();

  /********************************************************
   * (C) CO2 Donut (Material vs. Prozess)
   *******************************************************/
  let co2DonutOptions = {
    chart: {
      type: 'donut',
      height: 180,
      // Dynamische Farbe je nach Dark/Light
      foreColor: isDarkModeActive ? '#ccc' : '#000',
      background: isDarkModeActive ? '#2d2d2d' : '#f8f9fa'
    },
    series: [0, 0],           // [Mat-CO2, Proc-CO2]
    labels: ['Material-CO2', 'Prozess-CO2'],
    colors: ['#9CCC65', '#FF7043'],  // Grün + Orange
    plotOptions: {
      pie: {
        donut: {
          size: '55%'        // Loch-Anteil
        }
      }
    },
    tooltip: {
      y: {
        formatter: (val) => val.toFixed(2) + ' kg'
      }
    }
  };
  apexCo2Chart = new ApexCharts(
    document.querySelector("#apexCo2Chart"),
    co2DonutOptions
  );
  apexCo2Chart.render();

  apexInitialized = true;
  console.log("DEBUG: Exiting initApexCharts()");
}
/************************************************************
 * updateApexCharts(data) – Neues "data" vom Server
 ************************************************************/
function updateApexCharts(resultData) {
  console.log("DEBUG: Entering updateApexCharts() with resultData =", resultData);
  if (!apexInitialized) {
    console.log("DEBUG: apexInitialized is false -> calling initApexCharts()");
    initApexCharts();
  }

  // (1) Rechne Material & Fertigung zusammen
  let material = (resultData.matEinzel100 ?? 0) + (resultData.matGemein100 ?? 0) + (resultData.fremd100 ?? 0);
  let fertigung = (resultData.mach100 ?? 0) + (resultData.lohn100 ?? 0) + (resultData.fgk100 ?? 0);
  let sgaVal = (resultData.sga100 ?? 0);
  let profitVal = (resultData.profit100 ?? 0);

  console.log("DEBUG: cost-dist =>", material, fertigung, sgaVal, profitVal);

  // (2) Kosten-Kuchen updaten (Material, Fertigung, SGA, Profit)
  apexCostChart.updateSeries([ material, fertigung, sgaVal, profitVal ]);

  // (3) CO2-Daten
  let co2Mat = (resultData.co2Mat100 ?? 0);
  let co2Proc = (resultData.co2Proc100 ?? 0);
  console.log("DEBUG: co2-dist =>", co2Mat, co2Proc);

  apexCo2Chart.updateSeries([ co2Mat, co2Proc ]);

  console.log("DEBUG: Exiting updateApexCharts()");
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
        y: {beginAtZero: true}
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
        y: {beginAtZero: true}
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
  const matVal = (resultData.matEinzel100 ?? 0) + (resultData.matGemein100 ?? 0);
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
  const co2Mat = resultData.co2Mat100 ?? 0;
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

/**
 * updateRowCalc(rowIdx, lotSize):
 * Ersetzt die bisherige Minimal-Rechnung durch das V1-Schema.
 * cost100 = cycTime/3600 * msRate * 100 + cycTime/3600 * lohnRate * 100
 *           + (ruestVal / lotSize)*100 + toolingVal
 * co2_100 = cycTime/3600 * co2Hour * 100
 */
function updateRowCalc(rowIdx, lotSize) {
  console.log("DEBUG: Entering updateRowCalc() with rowIdx =", rowIdx, "lotSize =", lotSize);

  const rows = document.querySelectorAll("#fertTable tbody tr");
  if (rowIdx < 0 || rowIdx >= rows.length) {
    console.log("DEBUG: rowIdx out of range => returning");
    return;
  }
  const row = rows[rowIdx].cells; // bequemer Alias

  // cycTime = row.cells[1].querySelector("input")
  // msRate  = row.cells[2].querySelector("input")
  // lohnRate= row.cells[3].querySelector("input")
  // ruestVal= row.cells[4].querySelector("input")
  // toolingVal = row.cells[5].querySelector("input")
  // fgkPct  = row.cells[6].querySelector("input") // (Falls du es brauchst)
  // co2Hour = row.cells[7].querySelector("input")

  const cycTime = parseFloat(row[1].querySelector("input").value) || 0;
  const msRate = parseFloat(row[2].querySelector("input").value) || 0;
  const lohnRate = parseFloat(row[3].querySelector("input").value) || 0;
  const ruestVal = parseFloat(row[4].querySelector("input").value) || 0;
  const toolingVal = parseFloat(row[5].querySelector("input").value) || 0;
  // const fgkPct = parseFloat(row[6].querySelector("input").value) || 0; // Nur nötig, wenn du's einbeziehen willst
  const co2Hour = parseFloat(row[7].querySelector("input").value) || 0;

  console.log("DEBUG: cycTime=", cycTime, "msRate=", msRate, "lohnRate=", lohnRate,
      "ruestVal=", ruestVal, "toolingVal=", toolingVal, "co2Hour=", co2Hour);

  // Zyklus in Stunden:
  const cycTimeH = cycTime / 3600;

  // => Maschinenkosten pro 100
  const costMach100 = cycTimeH * msRate * 100;
  // => Lohnkosten pro 100
  const costLohn100 = cycTimeH * lohnRate * 100;
  // => Rüstkosten pro 100 (verteilt auf lotSize)
  const costRuest100 = (ruestVal / lotSize) * 100;
  // => Tooling (falls gewünscht 1:1 addieren, je 100)
  const costTool100 = toolingVal; // oder (toolingVal / lotSize)*100, je nach V1-Logik?

  // Summiere => spalte[8] (Kosten/100)
  const cost100 = costMach100 + costLohn100 + costRuest100 + costTool100;
  row[8].querySelector("span").textContent = cost100.toFixed(2);

  // => CO₂ pro 100 (CycTime in h * co2Hour * 100)
  // (Beispiel: cycTime=10s => cycTimeH=10/3600=0.0027h, co2Hour=3 => result=0.0081 => *100 => 0.81)
  const co2_100 = cycTimeH * co2Hour * 100;
  row[9].querySelector("span").textContent = co2_100.toFixed(2);

  const cost_per_piece = cost100 / 100;
row[8].querySelector("span").textContent = cost_per_piece.toFixed(4);

const co2_per_piece = co2_100 / 100;
row[9].querySelector("span").textContent = co2_per_piece.toFixed(4);

  console.log("DEBUG: cost100=", cost100, "co2_100=", co2_100);
  console.log("DEBUG: Exiting updateRowCalc()");
}

/** ============== Material-Funktionen ============== */

/**
 * openMaterialModal() – ruft /auth/whoami => check license => /mycalc/material_list
 * => Füllt Tabelle => Öffnet Modal
 */
function openMaterialModal() {
  console.log("DEBUG: Entering openMaterialModal()");
  const csrfToken = document.querySelector('meta[name=\"csrf-token\"]')?.content || "";

  fetch("/mycalc/material_list", {
    headers: {"X-CSRFToken": csrfToken}
  })
      .then(res => {
        if (!res.ok) {
          if (res.status === 403) {
            throw new Error("Lizenz nicht ausreichend oder abgelaufen.");
          }
          throw new Error("HTTP Error " + res.status);
        }
        return res.json();
      })
      .then(data => {
        fillMaterialTable(data);
        // Modal anzeigen
        new bootstrap.Modal(document.getElementById("modalMaterial")).show();
        console.log("DEBUG: modalMaterial shown");
      })
      .catch(err => alert(err.message));
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

  // Global speichern => Filterfunktion
  window.materialData = matArray;

  // Jede Zeile anlegen
  matArray.forEach((m, idx) => {
    const matName = m.material || "Unbekannt";
    const verfahren = m.verfahrensTyp || "";
    const priceKg = (m.gesamtPreisEURkg ?? 0).toFixed(2);
    const co2Kg = (m.co2EmissionenKG ?? 0).toFixed(2);
    const comm = m.kommentar || "";

    // TR erzeugen
    const tr = document.createElement("tr");
    tr.dataset.index = idx;           // für selectMaterial(idx)
    tr.dataset.matName = matName;
    tr.dataset.matPrice = priceKg;
    tr.dataset.matCo2 = co2Kg;

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
    tbody.appendChild(tr);
  });
  console.log("DEBUG: Exiting fillMaterialTable()");
}

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
    const verF = (m.verfahrensTyp || "").toLowerCase();
    return matN.includes(filterVal) || verF.includes(filterVal);
  });
  console.log("DEBUG: filtered material count =", filtered.length);

  fillMaterialTable(filtered);
  console.log("DEBUG: Exiting filterMaterialList()");
}

/** selectMaterial(idx): schreibt in #matName, #matPrice, #matCo2 */
function selectMaterial(idx) {
  console.log("DEBUG: Entering selectMaterial() with idx =", idx);
  const row = document.querySelector(`#tblMaterialList tbody tr[data-index="${idx}"]`);
  if (!row) {
    console.log("DEBUG: Row not found => returning");
    return;
  }

  // => Input-Felder in Tab2
  document.getElementById("matName").value = row.dataset.matName || "";
  document.getElementById("matPrice").value = row.dataset.matPrice || "0.00";
  document.getElementById("matCo2").value = row.dataset.matCo2 || "0.00";

  // Modal schließen
  const modalEl = document.getElementById("modalMaterial");
  const bsModal = bootstrap.Modal.getInstance(modalEl);
  bsModal.hide();

  console.log("DEBUG: Material selected => Exiting selectMaterial()");
}

function clearMaterialFilter() {
  console.log("DEBUG: Entering clearMaterialFilter()");
  document.getElementById("matFilterInput").value = "";
  filterMaterialList(); // => zeigt alle wieder an
  console.log("DEBUG: Exiting clearMaterialFilter()");
}

function applyLohnFilter() {
  console.log("DEBUG: Entering applyLohnFilter()");
  const filterVal = (document.getElementById("txtLohnFilter").value || "").trim().toLowerCase();
  const tbody = document.querySelector("#tblLohnList tbody");
  if (!tbody) return;

  Array.from(tbody.querySelectorAll("tr")).forEach(row => {
    const rowText = row.innerText.toLowerCase();
    if (rowText.includes(filterVal)) {
      row.style.display = "";
    } else {
      row.style.display = "none";
    }
  });
  console.log("DEBUG: Exiting applyLohnFilter()");
}

function clearLohnFilter() {
  console.log("DEBUG: Entering clearLohnFilter()");
  document.getElementById("txtLohnFilter").value = "";
  applyLohnFilter(); // Reset => zeigt alle an
  console.log("DEBUG: Exiting clearLohnFilter()");
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
    const verF = (m.verfahrensTyp || "").toLowerCase();
    return matN.includes(filterVal) || verF.includes(filterVal);
  });
  console.log("DEBUG: filtered material count =", filtered.length);

  fillMaterialTable(filtered);
  console.log("DEBUG: Exiting filterMaterialList()");
}

/********************************************************
 * NEU: MODAL ÖFFNEN FÜR EINEN BESTIMMTEN TABELLENINDEX
 ********************************************************/
function openZyklusModalWithTakt(rowIndex) {
  currentTaktRow = rowIndex;
  console.log("openZyklusModalWithTakt => rowIndex =", rowIndex);

  // Das Auswahlmodal #modalZyklusBild öffnen
  const zyModalEl = document.getElementById("modalZyklusBild");
  if (!zyModalEl) {
    console.error("Modal '#modalZyklusBild' nicht gefunden!");
    return;
  }
  const bsModal = new bootstrap.Modal(zyModalEl);
  bsModal.show();
  console.log("Zykluszeit-Modal geöffnet (Zeile:", rowIndex, ").");
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
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || "";
  fetch("/mycalc/machine_list", {
    headers: {"X-CSRFToken": csrfToken}
  })
      .then(res => {
        if (!res.ok) {
          if (res.status === 403) {
            throw new Error("Lizenz nicht ausreichend oder abgelaufen.");
          }
          throw new Error("HTTP Error " + res.status);
        }
        return res.json();
      })
      .then(data => {
        fillMachineTable(data);
        new bootstrap.Modal(document.getElementById("modalMachineList")).show();
      })
      .catch(err => alert(err.message));
}


function openLohnModal(rowIndex) {
  console.log("DEBUG: Entering openLohnModal() with rowIndex =", rowIndex);
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || "";

  // 1) check login
  fetch("/auth/whoami", {method: "GET", headers: {"X-CSRFToken": csrfToken}})
      .then(res => res.json())
      .then(data => {
        if (!data.logged_in) {
          throw new Error("Nicht eingeloggt.");
        }
        if (data.license === "no_access") {
          throw new Error("Lizenz abgelaufen.");
        }
        // 2) load /mycalc/lohn_list
        return fetch("/mycalc/lohn_list", {
          method: "GET",
          headers: {"X-CSRFToken": csrfToken}
        });
      })
      .then(res => {
        if (!res.ok) {
          throw new Error("Fehler beim Laden der Lohnliste: " + res.status);
        }
        return res.json();
      })
      .then(lohnData => {
        // 3) fill table
        LOHN_DATA = lohnData;
        fillLohnTable(lohnData);

        // 4) open modal
        currentLohnRow = rowIndex; // Speichere, für selectLohn()
        const modalEl = document.getElementById("modalLohn");
        new bootstrap.Modal(modalEl).show();
        console.log("DEBUG: modalLohn shown");
      })
      .catch(err => {
        console.error("openLohnModal error:", err);
        alert(err.message || "Lohnliste nicht verfügbar.");
      });
  console.log("DEBUG: Exiting openLohnModal()");
}

/** fillMachineTable(machArr) => #tblMachineList */
function fillMachineTable(machArr) {
  console.log("DEBUG: Entering fillMachineTable() with machArr length =", machArr.length);
  const tbody = document.querySelector("#tblMachineList tbody");
  if (!tbody) {
    console.log("DEBUG: #tblMachineList tbody not found => returning");
    return;
  }
  tbody.innerHTML = "";

  machArr.forEach((item, idx) => {
    // Beispiel: item => { "machineName": "XYZ", "process": "Drehen", "kaufpreis": 100000, ... }
    const machName = item.machineName || "Unbekannt";
    const process = item.process || "N/A";
    const kauf = parseFloat(item.kaufpreis || 0).toFixed(0);
    const power = parseFloat(item.power_kW || 0).toFixed(1);
    const comment = item.comment || "";

    const tr = document.createElement("tr");
    tr.dataset.index = idx;
    tr.dataset.kauf = kauf;
    tr.dataset.power = power;

    tr.innerHTML = `
      <td>${machName}</td>
      <td>${process}</td>
      <td>${kauf}</td>
      <td>${power}</td>
      <td>${comment}</td>
      <td>
        <button class="btn btn-sm btn-primary" onclick="selectMachine(${idx})">
          Übernehmen
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  });
  console.log("DEBUG: Exiting fillMachineTable()");
}

function applyMachineFilter() {
  console.log("DEBUG: Entering applyMachineFilter()");
  const filterVal = (document.getElementById("txtMachineFilter").value || "")
      .trim()
      .toLowerCase();

  const rows = document.querySelectorAll("#tblMachineList tbody tr");
  rows.forEach(row => {
    const rowText = row.innerText.toLowerCase();
    if (rowText.includes(filterVal)) {
      row.style.display = "";
    } else {
      row.style.display = "none";
    }
  });
  console.log("DEBUG: Exiting applyMachineFilter()");
}

function clearMachineFilter() {
  console.log("DEBUG: Entering clearMachineFilter()");
  document.getElementById("txtMachineFilter").value = "";
  applyMachineFilter(); // => zeigt alles wieder an
  console.log("DEBUG: Exiting clearMachineFilter()");
}

/** selectMachine(idx): schreibt in #machKaufpreis, #machKW */
function selectMachine(idx) {
  console.log("DEBUG: Entering selectMachine() with idx =", idx);
  const row = document.querySelector(`#tblMachineList tbody tr[data-index="${idx}"]`);
  if (!row) {
    console.log("DEBUG: Row not found => returning");
    return;
  }

  const kaufVal = parseFloat(row.dataset.kauf) || 0;
  const powerVal = parseFloat(row.dataset.power) || 0;
  console.log("DEBUG: kaufVal =", kaufVal, "powerVal =", powerVal);

  document.getElementById("machKaufpreis").value = kaufVal.toFixed(0);
  document.getElementById("machKW").value = powerVal.toFixed(1);

  // Modal schließen
  const modalEl = document.getElementById("modalMachineList");
  const bsModal = bootstrap.Modal.getInstance(modalEl);
  bsModal.hide();

  console.log("DEBUG: Machine selected => Exiting selectMachine()");
}

/** =========== Lohn-Funktionen =========== */
function openLohnModal(rowIndex) {
  console.log("DEBUG: Entering openLohnModal() with rowIndex =", rowIndex);
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || "";

  // 1) Wer bin ich?
  fetch("/auth/whoami", {
    method: "GET",
    headers: {"X-CSRFToken": csrfToken}
  })
      .then(res => res.json())
      .then(data => {
        if (!data.logged_in) {
          throw new Error("Nicht eingeloggt.");
        }
        if (data.license === "no_access") {
          throw new Error("Lizenz abgelaufen.");
        }
        // 2) Lohnliste abrufen
        return fetch("/mycalc/lohn_list", {
          method: "GET",
          headers: {"X-CSRFToken": csrfToken}
        });
      })
      .then(res => {
        if (!res.ok) {
          throw new Error("Fehler beim Laden der Lohnliste: " + res.status);
        }
        return res.json();
      })
      .then(lohnData => {
        // 3) Tabelle befüllen
        fillLohnTable(lohnData);

        // 4) Modal öffnen
        currentLohnRow = rowIndex; // falls du rowIndex irgendwo brauchst
        const modalEl = document.getElementById("modalLohn");
        new bootstrap.Modal(modalEl).show();
        console.log("DEBUG: modalLohn shown");
      })
      .catch(err => {
        console.error("openLohnModal error:", err);
        alert(err.message || "Lohnliste nicht verfügbar.");
      });
  console.log("DEBUG: Exiting openLohnModal()");
}

/** fillLohnTable(lohnArr) => #tblLohnList */
/** fillLohnTable(lohnArr) => #tblLohnList */
function fillLohnTable(lohnArr) {
  console.log("DEBUG: Entering fillLohnTable() with lohnArr length =", lohnArr.length);
  const tbody = document.querySelector("#tblLohnList tbody");
  if (!tbody) {
    console.log("DEBUG: #tblLohnList tbody not found => returning");
    return;
  }
  tbody.innerHTML = "";

  lohnArr.forEach((item, idx) => {
    const countryStr = item.country || "Unbekannt";
    const shiftMod   = item.shiftModel || "N/A";
    const allInVal   = parseFloat(item.allInEURh || 0).toFixed(2);
    const comment    = item.comment || "";

    // Jede Zeile speichert den Index und allIneurh ins dataset,
    // und ruft per Button-Klick 'selectLohn(idx)' auf:
    const tr = document.createElement("tr");
    tr.dataset.index     = idx;
    tr.dataset.allIneurh = allInVal;

    tr.innerHTML = `
      <td>${countryStr}</td>
      <td>${shiftMod}</td>
      <td>${allInVal}</td>
      <td>${comment}</td>
      <td>
        <button class="btn btn-sm btn-primary" onclick="selectLohn(${idx})">
          Übernehmen
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  });
  console.log("DEBUG: Exiting fillLohnTable()");
}

/** selectLohn(idx) => sucht anhand 'idx' das passende <tr> und trägt Wert in #fertTable ein. */
function selectLohn(idx) {
  console.log("DEBUG: Entering selectLohn() with idx =", idx);

  // 1) Tabelleneintrag per data-index suchen
  const row = document.querySelector(`#tblLohnList tbody tr[data-index="${idx}"]`);
  if (!row) {
    console.log("DEBUG: Row not found => returning");
    return;
  }

  // 2) All-In Stundensatz aus dataset
  const baseRate = parseFloat(row.dataset.allIneurh) || 0;
  const ops      = parseFloat(document.getElementById("operatorsPerMachine")?.value) || 0.5;
  const utilPct  = parseFloat(document.getElementById("lohnUtilPct")?.value) || 85.0;

  // Beispiel-Formel
  let effRate = (utilPct > 0) ? (baseRate / (utilPct / 100.0)) : baseRate;
  const lohnGesc = effRate * ops;

  console.log("DEBUG: Calculated lohnGesc =", lohnGesc);

  // 3) In #fertTable übernehmen (Benutzung von currentLohnRow)
  const fertRows = document.querySelectorAll("#fertTable tbody tr");
  if (typeof currentLohnRow !== "undefined" && currentLohnRow >= 0 && currentLohnRow < fertRows.length) {
    fertRows[currentLohnRow].cells[3].querySelector("input").value = lohnGesc.toFixed(2);
  }

  // 4) Modal schließen
  console.log("DEBUG: Attempting to close modalLohn");
  const modalEl = document.getElementById("modalLohn");
  const bsModal = bootstrap.Modal.getInstance(modalEl);
  bsModal.hide();

  console.log("DEBUG: Exiting selectLohn()");
}



// ===========================================================================
// HILFSFUNKTIONEN FÜR MASCHINENSTUNDENSATZ
// ===========================================================================
/************************************************************
 * parseFloatAllowZero() – parst eine Zahl oder gibt fallback zurück,
 *   ABER 0 bleibt 0 und führt NICHT zum fallback.
 ************************************************************/
function parseFloatAllowZero(str, fallbackVal) {
  const val = parseFloat(str);
  if (isNaN(val)) {
    return fallbackVal; // Nur bei wirklichem NaN
  }
  return val; // 0 bleibt 0
}

/************************************************************
 * formatIntCurrency(value):
 *  - Tausender-Punkte (de-DE)
 *  - Keine Nachkommastellen
 *  - " €" am Ende
 ************************************************************/
function formatIntCurrency(value) {
  return (
      value.toLocaleString("de-DE", {
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
      }) + " €"
  );
}

/************************************************************
 * formatHourCurrency(value):
 *  - Tausender-Punkte (de-DE)
 *  - 2 Nachkommastellen
 *  - " €" am Ende
 ************************************************************/
function formatHourCurrency(value) {
  return (
      value.toLocaleString("de-DE", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      }) + " €"
  );
}

/************************************************************
 * toggleDedicatedPct() – wird aufgerufen, wenn Checkbox "Dedicated?"
 *   geändert wird. Aktiviert/Deaktiviert das Eingabefeld für den
 *   Ded.-Prozentsatz.
 ************************************************************/
function toggleDedicatedPct() {
  const cb = document.getElementById("chkDedicated");
  const pctField = document.getElementById("machDedicatedPct");
  if (cb.checked) {
    pctField.disabled = false;
  } else {
    pctField.disabled = true;
    pctField.value = "100";
  }
}

// ===========================================================================
// calcExtendedMachineRate() – Hauptfunktion zur Berechnung des Maschinenstundensatzes
// ===========================================================================
function calcExtendedMachineRate() {
  console.log("DEBUG: Entering calcExtendedMachineRate()");

  // 1) Felder aus dem DOM – parseFloatAllowZero()
  const kaufpreis = parseFloatAllowZero(document.getElementById("machKaufpreis").value, 100000);
  const instCost = parseFloatAllowZero(document.getElementById("machInstCost").value, 0);
  const jahre = parseFloatAllowZero(document.getElementById("machNutzdauer").value, 5);
  const auslast = parseFloatAllowZero(document.getElementById("machAuslast").value, 6000);
  const availPct = parseFloatAllowZero(document.getElementById("machAvailPct").value, 85);

  const chkDedicated = document.getElementById("chkDedicated").checked;
  const dedicatedPct = parseFloatAllowZero(document.getElementById("machDedicatedPct").value, 100);

  const kw = parseFloatAllowZero(document.getElementById("machKW").value, 100.0);
  const stromPct = parseFloatAllowZero(document.getElementById("machStromPct").value, 80.0);
  const stromCost = parseFloatAllowZero(document.getElementById("machStromCost").value, 0.20);

  const flaecheBedarf = parseFloatAllowZero(document.getElementById("machFlaecheBedarf").value, 20.0);
  const flaecheCost = parseFloatAllowZero(document.getElementById("machFlaechenkost").value, 7.0);

  const instPct = parseFloatAllowZero(document.getElementById("machInstandPct").value, 3.0);
  const betrPct = parseFloatAllowZero(document.getElementById("machBetriebPct").value, 2.0);

  // Zinssatz (z. B. 3 => 3%)
  const inputZins = parseFloatAllowZero(document.getElementById("machZinssatz").value, 3.0);
  const zinssatz = inputZins / 100.0;

  console.log("DEBUG: Input Values =>", {
    kaufpreis, instCost, jahre, auslast, availPct, chkDedicated, dedicatedPct,
    kw, stromPct, stromCost, flaecheBedarf, flaecheCost, instPct, betrPct, zinssatz
  });

  // 2) Fixkosten pro Jahr
  const depYear = (kaufpreis + instCost) / jahre;
  const interestYear = (kaufpreis + instCost) * 0.5 * zinssatz;
  const instYear = kaufpreis * (instPct / 100.0);
  const betrYear = kaufpreis * (betrPct / 100.0);
  const flaecheYear = flaecheBedarf * flaecheCost * 12;

  // Summe fixe Jahreskosten (ohne Strom)
  let fixYear = depYear + interestYear + instYear + betrYear + flaecheYear;

  // 3) Variable Kosten (Strom) pro Jahr
  const usedKW = kw * (stromPct / 100.0); // effektive kW
  const stromHour = usedKW * stromCost;      // €/h
  const baseEffHours = auslast * (availPct / 100.0);
  let varYear = stromHour * baseEffHours;

  // 4) Dedicated-Logik
  let usageFactor = 1.0;
  if (chkDedicated) {
    usageFactor = dedicatedPct / 100.0; // z. B. 0.5, wenn 50% eingetragen
  }
  fixYear *= usageFactor;
  const effHours = baseEffHours * usageFactor;
  varYear *= usageFactor;

  console.log("DEBUG: fixYear=", fixYear, "varYear=", varYear, "effHours=", effHours);

  // 5) Jahreskosten
  const sumYear = fixYear + varYear;

  // 6) Maschinenkosten pro Stunde
  let costPerHour = 0;
  if (effHours > 0) {
    costPerHour = sumYear / effHours;
  }

  // 7) CO₂ pro Stunde (Dummy-Faktor)
  const co2_per_hour = usedKW * 0.38;

  // 8) Felder befüllen
  // Abschreibung, Zins, ...
  document.getElementById("machKaufpreisHr").value =
      effHours > 0 ? formatHourCurrency(depYear / effHours) : "0,00 €";
  document.getElementById("machZinsHr").value =
      effHours > 0 ? formatHourCurrency(interestYear / effHours) : "0,00 €";
  document.getElementById("machInstandHr").value =
      effHours > 0 ? formatHourCurrency(instYear / effHours) : "0,00 €";
  document.getElementById("machBetriebHr").value =
      effHours > 0 ? formatHourCurrency(betrYear / effHours) : "0,00 €";
  document.getElementById("machFlaechenkostHr").value =
      effHours > 0 ? formatHourCurrency(flaecheYear / effHours) : "0,00 €";
  document.getElementById("machStromCostHr").value =
      effHours > 0 ? formatHourCurrency(varYear / effHours) : "0,00 €";

  // Effektive Stunden
  document.getElementById("machAvailHr").value =
      effHours.toLocaleString("de-DE", {minimumFractionDigits: 1, maximumFractionDigits: 1}) + " h eff.";

  // CO₂ kg/h
  document.getElementById("machCo2Hr").value =
      co2_per_hour.toLocaleString("de-DE", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      });

  // Jahreskosten (falls Feld vorhanden)
  if (document.getElementById("machSumYear")) {
    document.getElementById("machSumYear").value = formatIntCurrency(sumYear);
  }

  // Summe der 6 Einzelwerte => machResult
  let sumOfSix = 0;
  if (effHours > 0) {
    sumOfSix =
        (depYear / effHours) +
        (interestYear / effHours) +
        (instYear / effHours) +
        (betrYear / effHours) +
        (flaecheYear / effHours) +
        (varYear / effHours);
  }
  document.getElementById("machResult").textContent = formatHourCurrency(sumOfSix);

  // 9) Globale Variable für acceptMachine()
  window.extMachCalc = {
    depYear,
    interestYear,
    instYear,
    betrYear,
    flaecheYear,
    fixYear,
    varYear,
    sumYear,
    effHours,
    co2_per_hour,
    usageFactor,
    costPerHour: sumOfSix
  };

  console.log("DEBUG: Exiting calcExtendedMachineRate(), costPerHour=", sumOfSix);
}

// ===========================================================================
// acceptMachine() – Übernimmt den berechneten Maschinenstundenansatz in die Tabelle
// ===========================================================================
function acceptMachine() {
  console.log("DEBUG: Entering acceptMachine() => currentMachineRow:", currentMachineRow);
  console.log("DEBUG: Checking if window.extMachCalc is defined");

  if (!window.extMachCalc) {
    console.log("DEBUG: window.extMachCalc is falsy => alerting user");
    alert("Bitte zuerst 'Berechnen' klicken!");
    return;
  }

  const rows = document.querySelectorAll("#fertTable tbody tr");
  console.log("DEBUG: rows.length =", rows.length);
  if (typeof currentMachineRow === "undefined" || currentMachineRow < 0 || currentMachineRow >= rows.length) {
    console.error("Ungültige Zeilen-ID:", currentMachineRow);
    alert("Es wurde keine gültige Zeile ausgewählt oder currentMachineRow ist -1.");
    return;
  }

  const {
    depYear, interestYear, instYear, betrYear,
    flaecheYear, varYear, sumYear, effHours,
    costPerHour, co2_per_hour
  } = window.extMachCalc;
  console.log("DEBUG: destructured extMachCalc =", {
    depYear, interestYear, instYear, betrYear, flaecheYear, varYear, sumYear, effHours, costPerHour, co2_per_hour
  });

  // Einzelwerte pro Stunde:
  const depHour = effHours > 0 ? depYear / effHours : 0;
  const intHour = effHours > 0 ? interestYear / effHours : 0;
  const instHour = effHours > 0 ? instYear / effHours : 0;
  const betrHour = effHours > 0 ? betrYear / effHours : 0;
  const flaechHour = effHours > 0 ? flaecheYear / effHours : 0;
  const stromHour = effHours > 0 ? varYear / effHours : 0;

  console.log("DEBUG: calcHourly =>", {depHour, intHour, instHour, betrHour, flaechHour, stromHour});

  // In die Textfelder (Modal)
  document.getElementById("machKaufpreisHr").value = depHour.toFixed(2);
  document.getElementById("machZinsHr").value = intHour.toFixed(2);
  document.getElementById("machInstandHr").value = instHour.toFixed(2);
  document.getElementById("machBetriebHr").value = betrHour.toFixed(2);
  document.getElementById("machFlaechenkostHr").value = flaechHour.toFixed(2);
  document.getElementById("machStromCostHr").value = stromHour.toFixed(2);
  document.getElementById("machAvailHr").value = effHours.toFixed(1) + " h eff.";
  document.getElementById("machResult").textContent = costPerHour.toFixed(2);
  document.getElementById("machCo2Hr").value = co2_per_hour.toFixed(2);

  // In #fertTable übernehmen
  const row = rows[currentMachineRow];
  console.log("DEBUG: Setting row.cells[2].querySelector(input).value =", costPerHour.toFixed(2));
  row.cells[2].querySelector("input").value = costPerHour.toFixed(2);   // Maschinen-€/h
  console.log("DEBUG: Setting row.cells[7].querySelector(input).value =", co2_per_hour.toFixed(2));
  row.cells[7].querySelector("input").value = co2_per_hour.toFixed(2); // co2/h

  // Modal schließen
  const modalEl = document.getElementById("modalMachine");
  console.log("DEBUG: Attempting to close modalMachine");
  const bsModal = bootstrap.Modal.getInstance(modalEl);
  bsModal.hide();

  console.log("DEBUG: Exiting acceptMachine()");
}

// ===========================================================================
// updateResultTable() – ggf. für andere Summen / Endergebnisse
// ===========================================================================
function updateResultTable(data) {
  console.log("DEBUG: updateResultTable()", data);

  //
  // A) Rohe "pro 100"-Werte holen
  //
  // Material
  const matEinzel_100 = data.matEinzel100 ?? 0;
  const matGemein_100 = data.matGemein100 ?? 0;
  const fremd_100     = data.fremd100 ?? 0;

  // Fertigung
  const mach_100    = data.mach100 ?? 0;
  const lohn_100    = data.lohn100 ?? 0;
  const fgk_100     = data.fgk100 ?? 0;
  const ruest_100   = data.ruest100 ?? 0;
  const tooling_100 = data.tooling100 ?? 0;

  // Summen
  const herstell_100 = data.herstell100 ?? 0;
  const sga_100      = data.sga100 ?? 0;
  const profit_100   = data.profit100 ?? 0;
  const totalAll_100 = data.totalAll100 ?? 0;

  //
  // B) Quick & Dirty: Auf "pro Stück" umrechnen (jeweils /100)
  //
  // Material (pro Stück)
  const matEinzel = matEinzel_100 / 100;
  const matGemein = matGemein_100 / 100;
  const fremd     = fremd_100     / 100;

  // Fertigung (pro Stück)
  const mach    = mach_100    / 100;
  const lohn    = lohn_100    / 100;
  const fgk     = fgk_100     / 100;
  const ruest   = ruest_100   / 100;  // Rüstkosten/100 => Rüst pro Stück
  const tooling = tooling_100 / 100;

  // Summen (pro Stück)
  const herstell = herstell_100 / 100;
  const sga      = sga_100      / 100;
  const profit   = profit_100   / 100;
  const totalAll = totalAll_100 / 100;

  //
  // C) In HTML-Felder schreiben
  //
  // Material
  document.getElementById("tdMatEinzel").textContent   = matEinzel.toFixed(2);
  document.getElementById("tdMatGemein").textContent   = matGemein.toFixed(2);
  document.getElementById("tdFremd").textContent       = fremd.toFixed(2);

  // Fertigung
  document.getElementById("tdMach").textContent        = mach.toFixed(2);
  document.getElementById("tdLohn").textContent        = lohn.toFixed(2);
  document.getElementById("tdFGK").textContent         = fgk.toFixed(2);
  document.getElementById("tdRuestDetailed").textContent  = ruest.toFixed(2);
  document.getElementById("tdToolingDetailed").textContent= tooling.toFixed(2);

  // Summen unten
  document.getElementById("tdHerstell").textContent  = herstell.toFixed(2);
  document.getElementById("tdSGA").textContent       = sga.toFixed(2);
  document.getElementById("tdProfit").textContent    = profit.toFixed(2);
  document.getElementById("tdTotal").textContent     = totalAll.toFixed(2);

  //
  // D) Weitere Detail-Summen (pro Stück)
  //
  // z.B. Material-Gesamtsumme = (matEinzel_100 + matGemein_100 + fremd_100) /100
  const matSum_100 = matEinzel_100 + matGemein_100 + fremd_100;
  const matSum     = matSum_100 / 100;
  document.getElementById("tdMatSumDetailed").textContent = matSum.toFixed(2);

  // Fertigungs-Gesamtsumme = (mach_100 + lohn_100 + fgk_100 + ruest_100 + tooling_100) /100
  const fertSum_100 = mach_100 + lohn_100 + fgk_100 + ruest_100 + tooling_100;
  const fertSum     = fertSum_100 / 100;
  document.getElementById("tdFertSumDetailed").textContent = fertSum.toFixed(2);

  //
  // E) Ausschuss-Delta-Berechnung pro Stück
  //
  const scrapPctInput = document.getElementById("scrapPct");
  let scrapPct = 0;
  if (scrapPctInput) {
    scrapPct = parseFloat(scrapPctInput.value) || 0;
  }
  const factorScrap = 1 + scrapPct / 100;

  // (1) Material-Ausschuss
  //   - matEinzel_100 enthält schon Ausschuss
  //   - Basis ohne Ausschuss = (matEinzel_100 / factorScrap) / 100 => pro Stück
  const basisMatEinzel_100 = matEinzel_100 / factorScrap;
  const basisMatEinzel     = basisMatEinzel_100 / 100;
  const matScrapDelta      = matEinzel - basisMatEinzel;
  document.getElementById("tdMatScrapDelta").textContent = matScrapDelta.toFixed(2);

  // (2) Fertigungs-Ausschuss
  //   - (mach_100, lohn_100, tooling_100, fgk_100) wurden mit Ausschuss multipliziert,
  //     nur ruest_100 nicht
  //   - Also baseline = (mach_100/factorScrap + lohn_100/factorScrap + tooling_100/factorScrap + fgk_100/factorScrap + ruest_100)
  //   - Dann /100 => pro Stück
  const basisMach_100   = mach_100    / factorScrap;
  const basisLohn_100   = lohn_100    / factorScrap;
  const basisTooling_100= tooling_100 / factorScrap;
  const basisFgk_100    = fgk_100     / factorScrap;
  // ruest_100 bleibt gleich
  const basisFertSum_100 = basisMach_100 + basisLohn_100 + basisTooling_100 + basisFgk_100 + ruest_100;
  const basisFertSum     = basisFertSum_100 / 100;
  const fertScrapDelta   = fertSum - basisFertSum;
  document.getElementById("tdFertScrapDelta").textContent = fertScrapDelta.toFixed(2);

  //
  // F) Debug-Log
  //
  console.log("DEBUG: updateResultTable() => matSum=", matSum, "fertSum=", fertSum);
  console.log("DEBUG: matScrapDelta=", matScrapDelta, "fertScrapDelta=", fertScrapDelta);
  console.log("DEBUG: Exiting updateResultTable()");
}


function onSliderMaterialChange(e) {
  console.log("DEBUG: Entering onSliderMaterialChange() with e =", e);
  // e = int % (z.B. -30..+30)
  window.material_factor = 1 + e / 100;
  console.log("DEBUG: material_factor =", material_factor, "=> calling calcAll()");
  calcAll(); // Deine lokale Rechenfunktion
  console.log("DEBUG: Exiting onSliderMaterialChange()");
}

/**
 * onSliderLaborChange(e)
 */
function onSliderLaborChange(e) {
  console.log("DEBUG: Entering onSliderLaborChange() with e =", e);
  window.labor_factor = 1 + e / 100;
  console.log("DEBUG: labor_factor =", labor_factor, "=> calling calcAll()");
  calcAll();
  console.log("DEBUG: Exiting onSliderLaborChange()");
}

/**
 * onSliderCO2Change(e)
 */
function onSliderCO2Change(e) {
  console.log("DEBUG: Entering onSliderCO2Change() with e =", e);
  window.co2_factor = 1 + e / 100;
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
    body: JSON.stringify({someParam: 123})
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
    sumMatEinz += (it.matEinzel ?? 0);
    sumMatGem += (it.matGemein ?? 0);
    sumFremd += (it.fremd ?? 0);
    sumMach += (it.mach ?? 0);
    sumLohn += (it.lohn ?? 0);
    sumFGK += (it.fgk ?? 0);
    sumHerstell += (it.herstell ?? 0);
    sumSGA += (it.sga ?? 0);
    sumProfit += (it.profit ?? 0);
    sumTotal += (it.total ?? 0);
    sumCo2 += (it.co2_100 ?? 0);
  }

  // Summen in <tfoot> Felder schreiben
  document.getElementById("bgSumMatEinzel").textContent = sumMatEinz.toFixed(2);
  document.getElementById("bgSumMatGemein").textContent = sumMatGem.toFixed(2);
  document.getElementById("bgSumFremd").textContent = sumFremd.toFixed(2);
  document.getElementById("bgSumMach").textContent = sumMach.toFixed(2);
  document.getElementById("bgSumLohn").textContent = sumLohn.toFixed(2);
  document.getElementById("bgSumFGK").textContent = sumFGK.toFixed(2);
  document.getElementById("bgSumHerstell").textContent = sumHerstell.toFixed(2);
  document.getElementById("bgSumSGA").textContent = sumSGA.toFixed(2);
  document.getElementById("bgSumProfit").textContent = sumProfit.toFixed(2);
  document.getElementById("bgSumTotal").textContent = sumTotal.toFixed(2);
  document.getElementById("bgSumCO2").textContent = sumCo2.toFixed(2);
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
  const matEinzel = parseFloat(document.getElementById("tdMatEinzel")?.textContent || "0");
  const matGemein = parseFloat(document.getElementById("tdMatGemein")?.textContent || "0");
  const fremd = parseFloat(document.getElementById("tdFremd")?.textContent || "0");
  const mach = parseFloat(document.getElementById("tdMach")?.textContent || "0");
  const lohn = parseFloat(document.getElementById("tdLohn")?.textContent || "0");
  const fgk = parseFloat(document.getElementById("tdFGK")?.textContent || "0");
  const herstell = parseFloat(document.getElementById("tdHerstell")?.textContent || "0");
  const sga = parseFloat(document.getElementById("tdSGA")?.textContent || "0");
  const profit = parseFloat(document.getElementById("tdProfit")?.textContent || "0");
  const total = parseFloat(document.getElementById("tdTotal")?.textContent || "0");
  const co2_100 = parseFloat(document.getElementById("txtCo2Per100")?.value || "0");

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
  const name = prompt("Bauteilname:") || "Manuelles Bauteil";
  const verfahren = prompt("Verfahren:") || "---";
  const matEinzel = parseFloat(prompt("MatEinzel (€/100):") || 0);
  const matGemein = parseFloat(prompt("MatGemein (€/100):") || 0);
  const fremd = parseFloat(prompt("Fremdzukauf (€/100):") || 0);
  const mach = parseFloat(prompt("Maschinenkosten (€/100):") || 0);
  const lohn = parseFloat(prompt("Lohnkosten (€/100):") || 0);
  const fgk = parseFloat(prompt("FGK (€/100):") || 0);
  const herstell = parseFloat(prompt("Herstellkosten (€/100):") || 0);
  const sga = parseFloat(prompt("SG&A (€/100):") || 0);
  const profit = parseFloat(prompt("Profit (€/100):") || 0);
  const total = parseFloat(prompt("Total (€/100):") || 0);
  const co2_100 = parseFloat(prompt("CO₂/100 (kg):") || 0);

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

  // Lizenz abfragen
  const lic = window.currentUser?.license || "unknown";
  if (lic === "plus" || lic === "test") {
    alert("Dein aktuelles Abo erlaubt keinen CSV-Export. Bitte upgrade auf Premium oder Extended.");
    return;
  }

  // CSV-String aufbauen
  let csvStr = "Bauteilname;Verfahren;MatEinzel;MatGemein;Fremd;Mach;Lohn;FGK;Herstell;SGA;Profit;Total;CO2_100\n";
  for (const it of baugruppenItems) {
    csvStr += [
      it.name,
      it.verfahren,
      (it.matEinzel ?? 0).toFixed(2),
      (it.matGemein ?? 0).toFixed(2),
      (it.fremd ?? 0).toFixed(2),
      (it.mach ?? 0).toFixed(2),
      (it.lohn ?? 0).toFixed(2),
      (it.fgk ?? 0).toFixed(2),
      (it.herstell ?? 0).toFixed(2),
      (it.sga ?? 0).toFixed(2),
      (it.profit ?? 0).toFixed(2),
      (it.total ?? 0).toFixed(2),
      (it.co2_100 ?? 0).toFixed(2),
    ].join(";") + "\n";
  }

  // Blob erzeugen und Download-Link klicken
  const blob = new Blob([csvStr], {type: "text/csv;charset=utf-8;"});
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
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrftoken
    },
    body: JSON.stringify({items: baugruppenItems})
  })
      .then(res => res.json())
      .then(data => {
        console.log("Saved baugruppenItems:", data);
      })
      .catch(err => console.error("Error saving baugruppen:", err));
}

// Beim Laden einmal initial rendern + summieren
document.addEventListener("DOMContentLoaded", () => {
  renderBaugruppeItems();
  calcBaugruppeSum();
});


//----------------------------------------------------------
// mycalc.js – Haupt-JavaScript-Datei
//----------------------------------------------------------




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
  closeZyklusModal();
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
  closeZyklusModal();
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
  closeZyklusModal();
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
  closeParamToolsModal();
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
        if (err.message === "GPT usage limit exceeded") {
          alert("Dein GPT-Kontingent ist aufgebraucht. Bitte upgrade dein Abo!");
        } else {
          console.error("onAskGPT error:", err);
          out.textContent = "Fehler: " + err.message;
        }
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
          // Hier können wir zusätzlich checken:
          if (res.status === 403) {
            throw new Error("GPT usage limit exceeded");
          }
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

function togglePcbChatWindow() {
  const wnd = document.getElementById("pcbChatWindow");
  if (!wnd) return;
  if (wnd.style.display === "none" || !wnd.style.display) {
    wnd.style.display = "block";
  } else {
    wnd.style.display = "none";
  }
}

/**
 * sendPcbChat()
 *  - Liest den Wert aus #pcbChatInput,
 *  - postet "Du: ..." ins Chat-Fenster,
 *  - ruft askCustomGPT(...) auf => Antwort => "KI: ..." in Chat.
 *  - Falls GPT usage exceeded => alert(...), Fehlermeldung in Chat.
 */
function sendPcbChat() {
  const inputEl = document.getElementById("pcbChatInput");
  const chatBody = document.querySelector("#pcbChatWindow .body");
  if (!inputEl || !chatBody) return;

  const userText = inputEl.value.trim();
  if (!userText) return;

  // 1) User-Text in den Chat schreiben
  const userP = document.createElement("p");
  userP.innerHTML = `<strong>Du:</strong> ${userText}`;
  chatBody.appendChild(userP);
  chatBody.scrollTop = chatBody.scrollHeight;

  // 2) GPT anfragen
  askCustomGPT(userText)
    .then((reply) => {
      const aiP = document.createElement("p");
      aiP.innerHTML = `<strong>KI:</strong> ${reply}`;
      chatBody.appendChild(aiP);
      chatBody.scrollTop = chatBody.scrollHeight;
    })
    .catch((err) => {
      console.error("sendPcbChat error:", err);
      const errP = document.createElement("p");
      errP.style.color = "red";
      errP.innerHTML = `Fehler: ${err.message}`;
      chatBody.appendChild(errP);

      if (err.message === "GPT usage limit exceeded") {
        alert("Dein GPT-Kontingent ist aufgebraucht. Bitte upgrade dein Abo!");
      }
      chatBody.scrollTop = chatBody.scrollHeight;
    });

  // Eingabefeld leeren
  inputEl.value = "";
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
    body: JSON.stringify({email, password})
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
    headers: {"X-CSRFToken": csrftoken}
  })
      .then((res) => res.json())
      .then(() => {
        window.location.href = "/";
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
    body: JSON.stringify({email, password})
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
    headers: {"X-CSRFToken": csrftoken}
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

/**
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
 */
/**
 * checkMaterialAccess():
 *  - Ruft /auth/whoami => prüft license
 *  - Wenn license===extended => openMaterialModal()
 */
function checkMaterialAccess() {
  const csrftoken = document.querySelector('meta[name="csrf-token"]')?.content || "";
  fetch("/auth/whoami", {
    method: "GET",
    headers: {"X-CSRFToken": csrftoken}
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

// Exporte, falls nötig
window.onAskGPT = onAskGPT;
window.doLogin = doLogin;
window.doLogout = doLogout;
window.doRegister = doRegister;
window.checkLicense = checkLicense;


document.addEventListener("DOMContentLoaded", () => {
  console.log("V2 => DOMContentLoaded => combined with old V1 stuff");

  // 1) (Aus V1:) Tab 1 aktivieren
  console.log("DEBUG: Activating Tab #tab1 (like in V1)...");
  const tab1El = document.querySelector("#tab1");
  // V1 hat per classList.add("active", "show") Tab 1 sichtbar gemacht
  if (tab1El) {
    tab1El.classList.add("active", "show");
    console.log("DEBUG: Tab #tab1 found => .active .show added");
  } else {
    console.warn("DEBUG: #tab1 not found in DOM => can't set active");
  }

  // 2) (Aus V1:) Baugruppen-Daten aus localStorage laden
  //    Nur falls du das wirklich noch brauchst:
  const saved = localStorage.getItem("baugruppe");
  if (saved) {
    console.log("DEBUG: Found 'baugruppe' in localStorage => parsing JSON");
    baugruppenItems = JSON.parse(saved);
    renderBaugruppeItems(); // V2-Funktion, sollte identisch sein
  }

  // 3) (Aus V1:) Input-Felder default 0.00, falls du das willst
  // (Kannst du optional machen, wenn's in V1 war)
  // document.getElementById("txtCosts100").value = "0.00";
  // document.getElementById("txtCo2Per100").value = "0.00";

  // 4) (Aus V2, vorhandenes):
  console.log("DEBUG: initFertRows(8)");
  initFertRows(8);
  //
  // In V1 war: initFertRows(DEFAULT_ROW_COUNT);

  // 5) (Aus V1:) initCharts()
  console.log("DEBUG: initCharts()");
  initCharts();

  console.log("DEBUG: DOMContentLoaded end (fusion done).");
});

async function checkLicenseThen(fnIfOk) {
  try {
    const res = await fetch("/auth/whoami", {method: "GET"});
    const data = await res.json();

    // Falls nicht eingeloggt => Umleiten zum Login
    if (!data.logged_in) {
      alert("Bitte einloggen (Upgrade-Feature).");
      window.location.href = "/auth/login";
      return;
    }

    // Lizenzprüfung: Nur "premium" oder "extended" erlaubt
    if (!["premium", "extended"].includes(data.license)) {
      alert("Dieses Feature erfordert Premium oder Extended. Bitte Upgrade!");
      return;
    }

    // Falls alles OK => eigentliche Funktion ausführen
    fnIfOk();

  } catch (err) {
    console.error(err);
    alert("Lizenzprüfung fehlgeschlagen. Bitte erneut versuchen.");
  }
}

/* ========================
   3) "Safe"-Funktionen für Modal-Öffner
   ======================== */
function openDruckgussModalSafe() {
  checkLicenseThen(() => {
    openDruckgussModal();
  });
}

function openMillingModalSafe() {
  checkLicenseThen(() => {
    openMillingModal();
  });
}

function openStampingModalSafe() {
  checkLicenseThen(() => {
    openStampingModal();
  });
}

function openFeingussModalSafe() {
  checkLicenseThen(() => {
    openFeingussModal();
  });
}

function openSchmiedenModalSafe() {
  checkLicenseThen(() => {
    openSchmiedenModal();
  });
}

function openKaltfliessModalSafe() {
  checkLicenseThen(() => {
    openKaltfliessModal();
  });
}

function openPcbModalSafe() {
  checkLicenseThen(() => {
    openPcbModal();
  });
}




  async function exportBaugruppenExcel() {
  // 1) Bauteile aus globaler Liste:
  if(!window.baugruppenItems || !window.baugruppenItems.length){
  alert("Keine Einträge in der Baugruppenliste.");
  return;
}
  // 2) POST an /exports/baugruppe/excel
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || "";
  const resp = await fetch("/exports/baugruppe/excel", {
  method: "POST",
  headers: {
  "Content-Type": "application/json",
  "X-CSRFToken": csrfToken
},
  body: JSON.stringify({baugruppenItems: window.baugruppenItems})
});
  if(!resp.ok){
  let data = null;
  try {data = await resp.json();} catch(e){}
  if(data?.error) alert("Fehler: " + data.error);
  else alert("Fehler: " + resp.status);
  return;
}
  // 3) Download
  // Da wir "send_file", fetch => Blobs
  const blob = await resp.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "baugruppe_export.xlsx";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

  async function exportBaugruppenPdf(){
  if(!window.baugruppenItems || !window.baugruppenItems.length){
  alert("Keine Einträge in der Baugruppenliste.");
  return;
}
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || "";
  const resp = await fetch("/exports/baugruppe/pdf", {
  method:"POST",
  headers: {
  "Content-Type":"application/json",
  "X-CSRFToken": csrfToken
},
  body: JSON.stringify({baugruppenItems: window.baugruppenItems})
});
  if(!resp.ok){
  let data = null;
  try {data = await resp.json();} catch(e){}
  if(data?.error) alert("Fehler: " + data.error);
  else alert("Fehler: " + resp.status);
  return;
}
  const blob = await resp.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "baugruppe_export.pdf";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}


/* ------------------------------------------------------
   Beispielhafter JS-Code für Comparison-Excel-Export
   ------------------------------------------------------ */

/**
 * Sammelt Daten aus Tab1-4 und ruft /exports/baugruppe/excel_comparison auf.
 * Erwartet, dass du die Daten vorher in globalen Variablen oder per DOM ausgelesen hast.
 */
async function exportComparisonExcel() {
  // Beispielhaft: Hier holst du dir die Werte aus dem DOM (Tab1):
  const tab1 = {
    projectName: document.getElementById("txtProjectName")?.value || "",
    partName: document.getElementById("txtPartName")?.value || "",
    annualQty: parseFloat(document.getElementById("annualQty")?.value) || 0,
    lotSize: parseFloat(document.getElementById("lotSize")?.value) || 0,
    scrapPct: parseFloat(document.getElementById("scrapPct")?.value) || 0,
    sgaPct: parseFloat(document.getElementById("sgaPct")?.value) || 0,
    profitPct: parseFloat(document.getElementById("profitPct")?.value) || 0
  };

  // Tab2:
  const tab2 = {
    matName: document.getElementById("matName")?.value || "",
    matPrice: parseFloat(document.getElementById("matPrice")?.value) || 0,
    matCo2: parseFloat(document.getElementById("matCo2")?.value) || 0,
    matGK: parseFloat(document.getElementById("matGK")?.value) || 0,
    matWeight: parseFloat(document.getElementById("matWeight")?.value) || 0,
    fremdValue: parseFloat(document.getElementById("fremdValue")?.value) || 0
  };

  // Tab3: bis zu 8 Schritte
  // Hier ein rudimentäres Beispiel. Du müsstest ggf. die DOM-Struktur deines
  // "fertTable" durchlaufen und Daten extrahieren.
  const rows = document.querySelectorAll("#fertTable tbody tr");
  const tab3 = [];
  rows.forEach((tr, idx) => {
    if(idx < 8) { // Max 8
      const tds = tr.querySelectorAll("td");
      // Columns (Annahme: StepName, Zyklus, MS/h, Lohn/h, Rüst/Los, Tooling, FGK, CO2/h, etc.)
      // Hier exemplarisch, du musst es an deine Felder anpassen
      const stepName = tds[0]?.querySelector("input")?.value || `Step ${idx+1}`;
      const zyklus_s = parseFloat(tds[1]?.querySelector("input")?.value) || 0;
      const ms_eur_h = parseFloat(tds[2]?.querySelector("input")?.value) || 0;
      const lohn_eur_h = parseFloat(tds[3]?.querySelector("input")?.value) || 0;
      const ruest_eur_los = parseFloat(tds[4]?.querySelector("input")?.value) || 0;
      const tooling_eur_100 = parseFloat(tds[5]?.querySelector("input")?.value) || 0;
      const fgk_pct = parseFloat(tds[6]?.querySelector("input")?.value) || 0;
      const co2_kg_h = parseFloat(tds[7]?.querySelector("input")?.value) || 0;
      // Die berechneten Spalten 8/9 in Tab3 (#kosten/100, #co2/100) sind Spans?
      const kosten_100 = parseFloat(tds[8]?.querySelector("span")?.innerText) || 0;
      const co2_100 = parseFloat(tds[9]?.querySelector("span")?.innerText) || 0;

      tab3.push({
        stepName,
        zyklus_s,
        ms_eur_h,
        lohn_eur_h,
        ruest_eur_los,
        tooling_eur_100,
        fgk_pct,
        co2_kg_h,
        kosten_100,
        co2_100
      });
    }
  });

  // Tab4: Summary
  const tab4 = {
    matEinzel: parseFloat(document.getElementById("tdMatEinzel")?.innerText) || 0,
    matGemein: parseFloat(document.getElementById("tdMatGemein")?.innerText) || 0,
    fremd: parseFloat(document.getElementById("tdFremd")?.innerText) || 0,
    mach: parseFloat(document.getElementById("tdMach")?.innerText) || 0,
    lohn: parseFloat(document.getElementById("tdLohn")?.innerText) || 0,
    fgk: parseFloat(document.getElementById("tdFGK")?.innerText) || 0,
    herstell: parseFloat(document.getElementById("tdHerstell")?.innerText) || 0,
    sga: parseFloat(document.getElementById("tdSGA")?.innerText) || 0,
    profit: parseFloat(document.getElementById("tdProfit")?.innerText) || 0,
    total: parseFloat(document.getElementById("tdTotal")?.innerText) || 0,
    co2_100: parseFloat(document.getElementById("tdCo2Total")?.innerText) || 0
  };

  // Jetzt POST an /exports/baugruppe/excel_comparison
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || "";
  const resp = await fetch("/exports/baugruppe/excel_comparison", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrfToken
    },
    body: JSON.stringify({
      tab1,
      tab2,
      tab3,
      tab4
    })
  });

  if (!resp.ok) {
    let data = null;
    try { data = await resp.json(); } catch(e){}
    if(data?.error) alert("Fehler: " + data.error);
    else alert("Fehler: " + resp.status);
    return;
  }

  // Download (ähnlich wie in deinem bestehenden code)
  const blob = await resp.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "ParetoKalk_Comparison.xlsx";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

// ------------------------------------------------------
// Ende JS
// ------------------------------------------------------

async function exportBaugruppenPowerPoint() {
  // 1) Einsammeln der Tab1-4 Daten (genau wie bei Excel)
  const tab1 = {
    projectName: document.getElementById("txtProjectName")?.value || "",
    partName: document.getElementById("txtPartName")?.value || "",
    sgaPct: parseFloat(document.getElementById("sgaPct")?.value) || 0,
    profitPct: parseFloat(document.getElementById("profitPct")?.value) || 0,
    // etc...
  };
  const tab2 = {
    matName: document.getElementById("matName")?.value || "",
    matPrice: parseFloat(document.getElementById("matPrice")?.value) || 0,
    matWeight: parseFloat(document.getElementById("matWeight")?.value) || 0,
    fremdValue: parseFloat(document.getElementById("fremdValue")?.value) || 0,
    // ...
  };
  // Tab3 => bis zu 8 steps
  const rows = document.querySelectorAll("#fertTable tbody tr");
  const tab3 = [];
  rows.forEach((row, idx) => {
    if (idx < 8) {
      const cells = row.querySelectorAll("td");
      tab3.push({
        stepName: cells[0].querySelector("input")?.value || `Step ${idx+1}`,
        cycTime: parseFloat(cells[1].querySelector("input")?.value) || 0,
        kosten_100: parseFloat(cells[8].querySelector("span")?.innerText) || 0,
        co2_100: parseFloat(cells[9].querySelector("span")?.innerText) || 0
      });
    }
  });
  // Tab4 => Summary
  const tab4 = {
    matEinzel: parseFloat(document.getElementById("tdMatEinzel")?.innerText) || 0,
    fremd: parseFloat(document.getElementById("tdFremd")?.innerText) || 0,
    herstell: parseFloat(document.getElementById("tdHerstell")?.innerText) || 0,
    sga: parseFloat(document.getElementById("tdSGA")?.innerText) || 0,
    profit: parseFloat(document.getElementById("tdProfit")?.innerText) || 0,
    total: parseFloat(document.getElementById("tdTotal")?.innerText) || 0,
    co2_100: parseFloat(document.getElementById("tdCo2Total")?.innerText) || 0
  };

  // 2) POST an /exports/baugruppe/ppt
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || "";
  const resp = await fetch("/exports/baugruppe/ppt", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrfToken
    },
    body: JSON.stringify({ tab1, tab2, tab3, tab4 })
  });

  if (!resp.ok) {
    let errData = null;
    try { errData = await resp.json(); } catch(e){}
    if (errData?.error) alert("Fehler: " + errData.error);
    else alert("Fehler: " + resp.status);
    return;
  }

  // 3) Download
  const blob = await resp.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "ParetoKalk_Presentation.pptx";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

async function export8StepsExcel() {
  // 1) Daten aus Tab1..Tab4 sammeln
  const tab1 = {
    scrapPct: parseFloat(document.getElementById("scrapPct")?.value) || 5,
    sgaPct: parseFloat(document.getElementById("sgaPct")?.value) || 10,
    profitPct: parseFloat(document.getElementById("profitPct")?.value) || 5,
    // ...
  };
  const tab2 = {
    matPrice: parseFloat(document.getElementById("matPrice")?.value) || 2.0,
    matWeight: parseFloat(document.getElementById("matWeight")?.value) || 0.2,
    fremdValue: parseFloat(document.getElementById("fremdValue")?.value) || 0,
    // ...
  };
  // tab3 => 8 Steps
  const rows = document.querySelectorAll("#fertTable tbody tr");
  const tab3 = [];
  rows.forEach((tr, idx) => {
    if(idx<8){
      const cells = tr.querySelectorAll("td");
      tab3.push({
        stepName: cells[0].querySelector("input")?.value || "",
        kosten_100: parseFloat(cells[8].querySelector("span")?.innerText) || 0,
        co2_100: parseFloat(cells[9].querySelector("span")?.innerText) || 0
      });
    }
  });
  const tab4 = {
    matEinzel: parseFloat(document.getElementById("tdMatEinzel")?.innerText) || 0,
    matGemein: parseFloat(document.getElementById("tdMatGemein")?.innerText) || 0,
    fremd: parseFloat(document.getElementById("tdFremd")?.innerText) || 0,
    ruest: parseFloat(document.getElementById("tdRuest")?.innerText) || 0,
    tooling: parseFloat(document.getElementById("tdTooling")?.innerText) || 0,
    herstell: parseFloat(document.getElementById("tdHerstell")?.innerText) || 0,
    sga: parseFloat(document.getElementById("tdSGA")?.innerText) || 0,
    profit: parseFloat(document.getElementById("tdProfit")?.innerText) || 0,
    total: parseFloat(document.getElementById("tdTotal")?.innerText) || 0,
    co2_100: parseFloat(document.getElementById("tdCo2Total")?.innerText) || 0
  };

  // 2) Post => /exports/baugruppe/excel_8steps
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || "";
  const resp = await fetch("/exports/baugruppe/excel_8steps", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrfToken
    },
    body: JSON.stringify({ tab1, tab2, tab3, tab4 })
  });

  if(!resp.ok){
    let errData = null;
    try {errData = await resp.json();} catch(e){}
    if(errData?.error) alert("Fehler: " + errData.error);
    else alert("Fehler: " + resp.status);
    return;
  }

  // 3) Download
  const blob = await resp.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "ParetoKalk_OnePager_8Steps.xlsx";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
async function exportEpicExcel() {
  // 1) Daten aus Tabs sammeln
  const tab1 = {
    projectName: document.getElementById("txtProjectName")?.value || "",
    partName: document.getElementById("txtPartName")?.value || "",
    annualQty: parseFloat(document.getElementById("annualQty")?.value) || 0,
    lotSize: parseFloat(document.getElementById("lotSize")?.value) || 0,
    scrapPct: parseFloat(document.getElementById("scrapPct")?.value) || 0,
    sgaPct: parseFloat(document.getElementById("sgaPct")?.value) || 0,
    profitPct: parseFloat(document.getElementById("profitPct")?.value) || 0
  };
  const tab2 = {
    matName: document.getElementById("matName")?.value || "Aluminium",
    matWeight: parseFloat(document.getElementById("matWeight")?.value) || 0,
    matPrice: parseFloat(document.getElementById("matPrice")?.value) || 0,
    fremdValue: parseFloat(document.getElementById("fremdValue")?.value) || 0,
    matGK: parseFloat(document.getElementById("matGK")?.value) || 0
  };

  // Tab3 => 8 steps
  const rows = document.querySelectorAll("#fertTable tbody tr");
  const tab3 = [];
  rows.forEach((tr, idx) => {
    if(idx < 8){
      const cells = tr.querySelectorAll("td");
      tab3.push({
        stepName: cells[0].querySelector("input")?.value || `Step${idx+1}`,
        cycTime: parseFloat(cells[1].querySelector("input")?.value) || 0,
        msRate: parseFloat(cells[2].querySelector("input")?.value) || 0,
        lohnRate: parseFloat(cells[3].querySelector("input")?.value) || 0,
        ruestVal: parseFloat(cells[4].querySelector("input")?.value) || 0,
        tooling: parseFloat(cells[5].querySelector("input")?.value) || 0,
        fgkPct: parseFloat(cells[6].querySelector("input")?.value) || 0,
        co2Hour: parseFloat(cells[7].querySelector("input")?.value) || 0,
        kosten_100: parseFloat(cells[8].querySelector("span")?.innerText) || 0,
        co2_100: parseFloat(cells[9].querySelector("span")?.innerText) || 0
      });
    }
  });

  // Tab4 => Summen
  const tab4 = {
    matEinzel: parseFloat(document.getElementById("tdMatEinzel")?.innerText) || 0,
    matEinzel_co2: 1.0,  // Beispiel
    matAusschuss: 0.1,
    matAusschuss_co2: 0.1,
    matGemein: 0.1,
    matGemein_co2: 1.1,
    fremd: parseFloat(document.getElementById("tdFremd")?.innerText) || 0,
    summe_fert_cost: 1,
    summe_fert_co2: 1,
    fgk_cost: 1,
    fgk_co2: 1,
    tool_cost: 1,
    tool_co2: 1,
    fertAusschuss_cost: 1,
    fertAusschuss_co2: 1,
    herstell: parseFloat(document.getElementById("tdHerstell")?.innerText) || 0,
    herstell_co2: 1.0,
    sga: parseFloat(document.getElementById("tdSGA")?.innerText) || 0,
    sga_cost: 1.0,
    profit: parseFloat(document.getElementById("tdProfit")?.innerText) || 0,
    profit_cost: 1.0,
    total: parseFloat(document.getElementById("tdTotal")?.innerText) || 0,
    co2_100: 5.0
  };

  // 2) POST => /exports/baugruppe/excel_epic
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || "";
  const resp = await fetch("/exports/baugruppe/excel_epic", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrfToken
    },
    body: JSON.stringify({ tab1, tab2, tab3, tab4 })
  });

  if(!resp.ok){
    let errData = null;
    try { errData = await resp.json();} catch(e){}
    if(errData?.error) alert("Fehler: " + errData.error);
    else alert("Fehler: " + resp.status);
    return;
  }

  // 3) Download
  const blob = await resp.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "ParetoKalk_Gesamtuebersicht.xlsx";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}


function updateSliderLabel(rangeEl, labelId) {
  const labelEl = document.getElementById(labelId);
  if (!labelEl) return;
  labelEl.textContent = rangeEl.value;
}
/****************************************************************************
 * Chat-Funktionen für Maschinenstundensatz (machChat)
 ****************************************************************************/

/**
 * toggleMachChatWindow()
 *  - Öffnet/Schließt das Chat-Fenster (#machChatWindow)
 */
function toggleMachChatWindow() {
  const wnd = document.getElementById("machChatWindow");
  if (!wnd) return;
  if (wnd.style.display === "none" || !wnd.style.display) {
    wnd.style.display = "flex";
  } else {
    wnd.style.display = "none";
  }
}

/**
 * sendMachChat()
 *  - Liest #machChatInput
 *  - Schreibt "Du: ..." in #machChatBody
 *  - Ruft askCustomGPT(...) auf => "KI: ..." in #machChatBody
 *  - Error-Handling wie gehabt (Limit => Alert etc.)
 */
function sendMachChat() {
  const inputEl = document.getElementById("machChatInput");
  const chatBody = document.getElementById("machChatBody");
  if (!inputEl || !chatBody) return;

  const userText = inputEl.value.trim();
  if (!userText) return;

  // 1) User-Text anzeigen
  const userP = document.createElement("p");
  userP.innerHTML = `<strong>Du:</strong> ${userText}`;
  chatBody.appendChild(userP);
  chatBody.scrollTop = chatBody.scrollHeight;

  // 2) GPT anfragen
  askCustomGPT(userText)
    .then((reply) => {
      const aiP = document.createElement("p");
      aiP.innerHTML = `<strong>KI:</strong> ${reply}`;
      chatBody.appendChild(aiP);
      chatBody.scrollTop = chatBody.scrollHeight;
    })
    .catch((err) => {
      console.error("sendMachChat error:", err);
      const errP = document.createElement("p");
      errP.style.color = "red";
      errP.innerHTML = `Fehler: ${err.message}`;
      chatBody.appendChild(errP);

      if (err.message === "GPT usage limit exceeded") {
        alert("Dein GPT-Kontingent ist aufgebraucht. Bitte upgrade dein Abo!");
      }
      chatBody.scrollTop = chatBody.scrollHeight;
    });

  // Eingabefeld leeren
  inputEl.value = "";
}

/**
 * askMachPredefined(question)
 *  - Vordefinierte Frage: Chat-Fenster öffnen, Input setzen,
 *    und optional direkt abschicken (hier: manuell).
 */
function askMachPredefined(question) {
  toggleMachChatWindow(); // Chatfenster öffnen
  const inputEl = document.getElementById("machChatInput");
  if (inputEl) {
    inputEl.value = question;
  }
  // Optional: wenn du willst, dass es direkt gesendet wird:
  // sendMachChat();
}
function askPCBPredefined(question) {
  togglePcbChatWindow(); // Chatfenster öffnen
  const inputEl = document.getElementById("pcbChatInput");
  if (inputEl) {
    inputEl.value = question;
  }

  sendPcbChat();
}


function toggleSGChatWindow() {
  const wnd = document.getElementById("SGChatWindow");
  if (!wnd) return;
  if (wnd.style.display === "none" || !wnd.style.display) {
    wnd.style.display = "block";
  } else {
    wnd.style.display = "none";
  }
}

/**
 * sendPcbChat()
 *  - Liest den Wert aus #pcbChatInput,
 *  - postet "Du: ..." ins Chat-Fenster,
 *  - ruft askCustomGPT(...) auf => Antwort => "KI: ..." in Chat.
 *  - Falls GPT usage exceeded => alert(...), Fehlermeldung in Chat.
 */
function sendSGChat() {
  const inputEl = document.getElementById("SGChatInput");
  const chatBody = document.querySelector("#SGChatWindow .body");
  if (!inputEl || !chatBody) return;

  const userText = inputEl.value.trim();
  if (!userText) return;

  // 1) User-Text in den Chat schreiben
  const userP = document.createElement("p");
  userP.innerHTML = `<strong>Du:</strong> ${userText}`;
  chatBody.appendChild(userP);
  chatBody.scrollTop = chatBody.scrollHeight;

  // 2) GPT anfragen
  askCustomGPT(userText)
    .then((reply) => {
      const aiP = document.createElement("p");
      aiP.innerHTML = `<strong>KI:</strong> ${reply}`;
      chatBody.appendChild(aiP);
      chatBody.scrollTop = chatBody.scrollHeight;
    })
    .catch((err) => {
      console.error("sendSGChat error:", err);
      const errP = document.createElement("p");
      errP.style.color = "red";
      errP.innerHTML = `Fehler: ${err.message}`;
      chatBody.appendChild(errP);

      if (err.message === "GPT usage limit exceeded") {
        alert("Dein GPT-Kontingent ist aufgebraucht. Bitte upgrade dein Abo!");
      }
      chatBody.scrollTop = chatBody.scrollHeight;
    });

  // Eingabefeld leeren
  inputEl.value = "";
}
function askSGPredefined(question) {
  toggleSGChatWindow(); // Chatfenster öffnen
  const inputEl = document.getElementById("SGChatInput");
  if (inputEl) {
    inputEl.value = question;
  }

  sendSGChat();
}




function toggleFGChatWindow() {
  const wnd = document.getElementById("FGChatWindow");
  if (!wnd) return;
  if (wnd.style.display === "none" || !wnd.style.display) {
    wnd.style.display = "block";
  } else {
    wnd.style.display = "none";
  }
}

/**
 * sendPcbChat()
 *  - Liest den Wert aus #pcbChatInput,
 *  - postet "Du: ..." ins Chat-Fenster,
 *  - ruft askCustomGPT(...) auf => Antwort => "KI: ..." in Chat.
 *  - Falls GPT usage exceeded => alert(...), Fehlermeldung in Chat.
 */
function sendFGChat() {
  const inputEl = document.getElementById("FGChatInput");
  const chatBody = document.querySelector("#FGChatWindow .body");
  if (!inputEl || !chatBody) return;

  const userText = inputEl.value.trim();
  if (!userText) return;

  // 1) User-Text in den Chat schreiben
  const userP = document.createElement("p");
  userP.innerHTML = `<strong>Du:</strong> ${userText}`;
  chatBody.appendChild(userP);
  chatBody.scrollTop = chatBody.scrollHeight;

  // 2) GPT anfragen
  askCustomGPT(userText)
    .then((reply) => {
      const aiP = document.createElement("p");
      aiP.innerHTML = `<strong>KI:</strong> ${reply}`;
      chatBody.appendChild(aiP);
      chatBody.scrollTop = chatBody.scrollHeight;
    })
    .catch((err) => {
      console.error("sendFGChat error:", err);
      const errP = document.createElement("p");
      errP.style.color = "red";
      errP.innerHTML = `Fehler: ${err.message}`;
      chatBody.appendChild(errP);

      if (err.message === "GPT usage limit exceeded") {
        alert("Dein GPT-Kontingent ist aufgebraucht. Bitte upgrade dein Abo!");
      }
      chatBody.scrollTop = chatBody.scrollHeight;
    });

  // Eingabefeld leeren
  inputEl.value = "";
}
function askFGPredefined(question) {
  toggleFGChatWindow(); // Chatfenster öffnen
  const inputEl = document.getElementById("FGChatInput");
  if (inputEl) {
    inputEl.value = question;
  }

  sendFGChat();
}

 // ========== Hier ab: Chat-Logik für "mss" statt "pcb" ==========
  function toggleMssChatWindow() {
    const wnd = document.getElementById("mssChatWindow");
    if (!wnd) return;
    if (wnd.style.display === "none" || !wnd.style.display) {
      wnd.style.display = "block";
    } else {
      wnd.style.display = "none";
    }
  }

  /**
   * sendMssChat()
   *  - Liest den Wert aus #mssChatInput,
   *  - postet "Du: ..." ins Chat-Fenster,
   *  - ruft askCustomGPT(...) auf => Antwort => "KI: ..." in Chat.
   *  - Falls GPT usage exceeded => alert(...), Fehlermeldung in Chat.
   */
  function sendMssChat() {
    const inputEl = document.getElementById("mssChatInput");
    const chatBody = document.querySelector("#mssChatWindow .body");
    if (!inputEl || !chatBody) return;

    const userText = inputEl.value.trim();
    if (!userText) return;

    // 1) User-Text in den Chat schreiben
    const userP = document.createElement("p");
    userP.innerHTML = `<strong>Du:</strong> ${userText}`;
    chatBody.appendChild(userP);
    chatBody.scrollTop = chatBody.scrollHeight;

    // 2) GPT anfragen (Platzhalter-Implementierung)
    askCustomGPT(userText)
      .then((reply) => {
        const aiP = document.createElement("p");
        aiP.innerHTML = `<strong>KI:</strong> ${reply}`;
        chatBody.appendChild(aiP);
        chatBody.scrollTop = chatBody.scrollHeight;
      })
      .catch((err) => {
        console.error("sendMssChat error:", err);
        const errP = document.createElement("p");
        errP.style.color = "red";
        errP.innerHTML = `Fehler: ${err.message}`;
        chatBody.appendChild(errP);

        if (err.message === "GPT usage limit exceeded") {
          alert("Dein GPT-Kontingent ist aufgebraucht. Bitte upgrade dein Abo!");
        }
        chatBody.scrollTop = chatBody.scrollHeight;
      });

    // Eingabefeld leeren
    inputEl.value = "";
  }

  /**
   * askMssPredefined(question)
   *  - Öffnet das Chat-Fenster,
   *  - setzt die Eingabe auf "question",
   *  - ruft sendMssChat() auf.
   */
  function askMssPredefined(question) {
    toggleMssChatWindow(); // Chatfenster öffnen
    const inputEl = document.getElementById("mssChatInput");
    if (inputEl) {
      inputEl.value = question;
    }
    sendMssChat();
  }
