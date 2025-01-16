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
  let val = parseFloat(inputStr);
  if (isNaN(val)) {
    return fallbackVal;
  }
  return val;
}
// 1. Opening modals
function openParametrikModal() {
  const myModal = new bootstrap.Modal(document.getElementById('modalParametrik'));
  myModal.show();
}

function openTaktzeitModal() {
  const myModal = new bootstrap.Modal(document.getElementById('modalTaktzeit'));
  myModal.show();
}

// 2. AJAX to Parametrik
function calcParamFeinguss() {
  const csrftoken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
  fetch('/calc/param/feinguss', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrftoken
    },
    body: JSON.stringify({ someParam: 123 })
  })
  .then(res => res.json())
  .then(data => {
    document.getElementById('paramResult').innerText = data.result;
  });
}

function calcParamKaltflies() {
  // analog ...
}

function calcParamSchmieden() {
  // ...
}

function calcParamPcb() {
  // ...
}

// 3. Taktzeit
function calcTaktSpritzguss() {
  const csrftoken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
  fetch('/calc/takt/spritzguss', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrftoken
    },
    body: JSON.stringify({ paramA: 'example' })
  })
  .then(res => res.json())
  .then(data => {
    console.log("Spritzguss:", data.result);
    // evtl. ins Input-Feld zurückschreiben
    // document.getElementById('inputZykluszeit').value = data.result;
  });
}

// ... Druckguss, Zerspanung, Stanzen analog ...

// 4. Hauptberechnung
function triggerMainCalc() {
  const csrftoken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
  // Sammle Formdaten (z. B. stückzahl, gewinn, etc.)
  const stueck = document.getElementById('inputJahresStueck').value;
  const gewinn = document.getElementById('inputGewinn').value;

  fetch('/calc/compute', {
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
  .then(res => res.json())
  .then(data => {
    console.log("MainCalc result:", data);
    // Bsp: document.getElementById('spanTotalCosts').innerText = data.total_costs;
  });
}

// Deine calcAll() – umgebaut für Backend
function calcAll() {
  console.log("DEBUG: Sammle Eingaben für calcAll() ...");

  // Projekt
  const projectName = document.getElementById("txtProjectName").value || "";
  const partName    = document.getElementById("txtPartName").value    || "";

  // Beispiel: annualQty
  const annualQty = parseFloatAllowZero(
    document.getElementById("annualQty").value,
    1000
  );
  const lotSize   = parseFloatAllowZero(
    document.getElementById("lotSize").value,
    100
  );
  const scrapPct  = parseFloatAllowZero(
    document.getElementById("scrapPct").value,
    5
  );
  const sgaPct    = parseFloatAllowZero(
    document.getElementById("sgaPct").value,
    10
  );
  const profitPct = parseFloatAllowZero(
    document.getElementById("profitPct").value,
    5
  );
  const zielPrice = parseFloatAllowZero(
    document.getElementById("zielPrice").value,
    200
  );

  // Material
  const matName     = document.getElementById("matName").value || "";
  let   matPrice    = parseFloatAllowZero(
    document.getElementById("matPrice").value,
    2
  );
  let   matCo2      = parseFloatAllowZero(
    document.getElementById("matCo2").value,
    2
  );
  let   matGK       = parseFloatAllowZero(
    document.getElementById("matGK").value,
    5
  );
  let   matWeight   = parseFloatAllowZero(
    document.getElementById("matWeight").value,
    0.2
  );
  let   fremdVal    = parseFloatAllowZero(
    document.getElementById("fremdValue").value,
    0
  );

  // Fertigungstabelle => steps
  const fertRows = document.querySelectorAll("#fertTable tbody tr");
  let steps = [];
  fertRows.forEach((row) => {
    const cells = row.cells;
    let stepName = cells[0].querySelector("input").value || "";

    let cycTime  = parseFloatAllowZero(cells[1].querySelector("input").value, 0);
    let msRate   = parseFloatAllowZero(cells[2].querySelector("input").value, 0);
    let lohnRate = parseFloatAllowZero(cells[3].querySelector("input").value, 0);
    let ruestVal = parseFloatAllowZero(cells[4].querySelector("input").value, 0);
    let toolingVal = parseFloatAllowZero(cells[5].querySelector("input").value, 0);
    let fgkPct   = parseFloatAllowZero(cells[6].querySelector("input").value, 0);
    let co2Hour  = parseFloatAllowZero(cells[7].querySelector("input").value, 0);

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

  // Globale Faktoren anpassen
  matPrice = matPrice * material_factor;

  // labor/CO2-Faktor => MsRate & lohnRate, co2Hour
  steps = steps.map(st => ({
    ...st,
    msRate:   st.msRate   * labor_factor,
    lohnRate: st.lohnRate * labor_factor,
    co2Hour:  st.co2Hour  * co2_factor
  }));

  // final payload
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
      name: matName,
      price: matPrice,
      co2:   matCo2,
      gk:    matGK,
      weight: matWeight,
      fremdValue: fremdVal
    },
    steps
  };

  console.log("calcAll() => POST /calc/maincalc/compute, payload:", payload);

  const csrftoken = document
    .querySelector('meta[name="csrf-token"]')
    ?.getAttribute("content") || "";

  // 1) Sende die Daten an die neue Route
  fetch("/calc/maincalc/compute", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrftoken // Falls du globales CSRF nutzt
    },
    body: JSON.stringify(payload)
  })
    .then((res) => {
      console.log("HTTP-Status /calc/maincalc/compute:", res.status);
      if (!res.ok) {
        throw new Error("Server error: " + res.status);
      }
      return res.json();
    })
    .then((data) => {
      console.log("Response from /calc/maincalc/compute:", data);
      if (data.error) {
        alert("Fehler: " + data.error);
        return;
      }
      // 2) Fülle Felder / Charts etc.
      updateResultTable(data);
      updateCharts(data);

      // z. B. top area "Kosten/100" und "CO2/100"
      let cost_100 = data.totalAll100 ?? 0;
      let co2_100  = ((data.co2Mat100 ?? 0) + (data.co2Proc100 ?? 0));

      document.getElementById("txtCosts100").value  = cost_100.toFixed(2);
      document.getElementById("txtCo2Per100").value = co2_100.toFixed(2);
    })
    .catch((err) => {
      console.error("Fehler in calcAll():", err);
      alert("calcAll() error: " + err);
    });


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
}

/**
 * initCharts() – erstellt costChart + co2Chart,
 * falls noch nicht vorhanden.
 */
/**
 * initCharts() – erstellt costChart + co2Chart,
 * falls noch nicht vorhanden.
 */
function initCharts() {
  if (chartInitialized && costChart) {
    costChart.destroy();
  }
  if (chartInitialized && co2Chart) {
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
}


/************************************************************
 * "Dritter Teil": Fertigungs-Tabelle-Funktionen + Material-
 * und Maschinen-/Lohn-Funktionen (CSRF-ready).
 ************************************************************/

/** Globale Variable zum Speichern der Daten */


/** ============ TABS (Prev/Next) ============ */
function goPrevTab() {
  const allBtns = document.querySelectorAll("#calcTab button");
  const idx = Array.from(allBtns).findIndex((btn) => btn.classList.contains("active"));
  if (idx > 0) allBtns[idx - 1].click();
}
function goNextTab() {
  const allBtns = document.querySelectorAll("#calcTab button");
  const idx = Array.from(allBtns).findIndex((btn) => btn.classList.contains("active"));
  if (idx < allBtns.length - 1) allBtns[idx + 1].click();
}

/** ============ Fertigungs-Tabelle: init, addRow, attachRowEvents ============ */
function initFertRows(rowCount) {
  const tbody = document.querySelector("#fertTable tbody");
  if (!tbody) return;

  tbody.innerHTML = "";
  for (let i = 0; i < rowCount; i++) {
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
  attachRowEvents();
}

/** Neue Zeile in FertTable hinzufügen */
function addFertRow() {
  const tbody = document.querySelector("#fertTable tbody");
  if (!tbody) return;

  const rowIdx = tbody.rows.length;
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
}

/** attachRowEvents(): z. B. wenn Input-Felder sich ändern => updateRowCalc */
function attachRowEvents() {
  const rows = document.querySelectorAll("#fertTable tbody tr");
  rows.forEach((row, rowIdx) => {
    row.querySelectorAll("input").forEach((inp) => {
      inp.addEventListener("change", () => {
        const lotVal = parseFloat(document.getElementById("lotSize")?.value) || 100;
        updateRowCalc(rowIdx, lotVal);
      });
    });
  });
}

/** updateRowCalc(rowIdx, lotSize): rechnet die Zeile neu (dummy) */
function updateRowCalc(rowIdx, lotSize) {
  console.log("updateRowCalc => row:", rowIdx, " lotSize:", lotSize);
  // Hier könntest du die Eingaben lesen,
  // (Zyklus * msRate / lotSize => etc.)
  // Dann in die <span> Felder (cost/100, co2/100) reinschreiben
  const rows = document.querySelectorAll("#fertTable tbody tr");
  if (rowIdx< 0 || rowIdx>= rows.length) return;
  const row= rows[rowIdx];

  // Bsp:
  const cycTime = parseFloat(row.cells[1].querySelector("input").value) || 0;
  const msRate  = parseFloat(row.cells[2].querySelector("input").value) || 0;

  let cost100 = 0;
  if (lotSize>0) cost100= (cycTime* msRate)/ (3600.0)* 100;
  row.cells[8].querySelector("span").textContent= cost100.toFixed(2);

  const co2Val = parseFloat(row.cells[7].querySelector("input").value) || 0;
  // Bsp: co2 pro stück * 100
  row.cells[9].querySelector("span").textContent= (co2Val*100).toFixed(2);
}

/** ============== Material-Funktionen ============== */

/**
 * openMaterialModal() – ruft /auth/whoami => check license => /mycalc/material_list
 * => Füllt Tabelle => Öffnet Modal
 */
function openMaterialModal() {
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || "";

  // Lizenzstatus abfragen
  fetch("/auth/whoami", {
    headers:{ "X-CSRFToken": csrfToken }
  })
    .then(res => res.json())
    .then(data => {
      if (data.license === "extended") {
        // Materialliste laden
        return fetch("/mycalc/material_list", {
          method: "GET",
          headers:{ "X-CSRFToken": csrfToken }
        });
      } else {
        throw new Error("Lizenz nicht ausreichend.");
      }
    })
    .then(res => {
      if (res.ok) {
        return res.json();
      } else {
        throw new Error("HTTP Error " + res.status);
      }
    })
    .then(data => {
      // fülle Tabelle
      fillMaterialTable(data);

      // Modal anzeigen
      let modalEl = document.getElementById("modalMaterial");
      let bsModal = new bootstrap.Modal(modalEl);
      bsModal.show();
    })
    .catch(err => {
      console.error("openMaterialModal error:", err);
      alert(
        err.message === "Lizenz nicht ausreichend."
          ? "Ihre Lizenz reicht nicht aus, um die Materialliste zu öffnen."
          : "Fehler beim Laden der Materialliste."
      );
    });
}

/** fillMaterialTable(matArray) – füllt #tblMaterialList */
function fillMaterialTable(matArray) {
  const tbody = document.querySelector("#tblMaterialList tbody");
  if (!tbody) return;

  // Tabelle leeren
  tbody.innerHTML = "";
  window.materialData = matArray; // optional

  matArray.forEach((m, idx) => {
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
}

/** selectMaterial(idx): schreibt in #matName, #matPrice, #matCo2 */
function selectMaterial(idx) {
  const row = document.querySelector(`#tblMaterialList tbody tr[data-index="${idx}"]`);
  if (!row) return;

  document.getElementById("matName").value  = row.dataset.matName || "";
  document.getElementById("matPrice").value = row.dataset.matPrice||"0.00";
  document.getElementById("matCo2").value   = row.dataset.matCo2  ||"0.00";

  // Modal schließen
  const modalEl = document.getElementById("modalMaterial");
  const bsModal = bootstrap.Modal.getInstance(modalEl);
  bsModal.hide();
}

/** filterMaterialList(): optionaler Filter auf window.materialData */
function filterMaterialList() {
  const filterVal = document.getElementById("matFilterInput")?.value.toLowerCase() || "";
  if (!window.materialData) return;

  const filtered = window.materialData.filter(m => {
    const matN = (m.material || "").toLowerCase();
    const verF= (m.verfahrensTyp||"").toLowerCase();
    return matN.includes(filterVal) || verF.includes(filterVal);
  });
  fillMaterialTable(filtered);
}

/** openZyklusModalWithTakt(rowIndex) => #modalZyklusBild öffnen */
function openZyklusModalWithTakt(rowIndex) {
  currentTaktRow = rowIndex;
  const modalEl = document.getElementById("modalZyklusBild");
  if (!modalEl) return;
  const bsModal= new bootstrap.Modal(modalEl);
  bsModal.show();
}

/** =========== Maschinen-Funktionen =========== */

function openMachineModal(rowIdx) {
  currentMachineRow = rowIdx;
  const modalEl= document.getElementById("modalMachine");
  if (!modalEl) return;
  new bootstrap.Modal(modalEl).show();
}

/** openMachineListModal() => holt /mycalc/machine_list */
function openMachineListModal() {
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || "";

  fetch("/mycalc/machine_list", {
    method: "GET",
    headers:{ "X-CSRFToken": csrfToken }
  })
    .then((res) => {
      if (!res.ok) {
        if (res.status===403) throw new Error("Lizenz nicht ausreichend. Bitte upgraden!");
        throw new Error("Fehler beim Laden der Maschinenliste: "+ res.status);
      }
      return res.json();
    })
    .then((data) => {
      fillMachineTable(data);

      const modalEl= document.getElementById("modalMachineList");
      new bootstrap.Modal(modalEl).show();
    })
    .catch((err) => {
      console.error("Maschinenliste Fehler:", err);
      alert(err.message || "Maschinenliste nicht verfügbar.");
    });
}

/** fillMachineTable(machArr) => #tblMachineList */
function fillMachineTable(machArr) {
  const tbody = document.querySelector("#tblMachineList tbody");
  if (!tbody) return;

  tbody.innerHTML= "";
  machArr.forEach((m, idx) => {
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
}

/** selectMachine(idx): schreibt in #machKaufpreis, #machKW */
function selectMachine(idx) {
  const row = document.querySelector(`#tblMachineList tbody tr[data-index="${idx}"]`);
  if (!row) return;

  const kaufVal  = parseFloat(row.dataset.kauf)  || 0;
  const powerVal = parseFloat(row.dataset.power) || 0;

  document.getElementById("machKaufpreis").value= kaufVal.toFixed(0);
  document.getElementById("machKW").value       = powerVal.toFixed(1);

  // Modal schließen
  const modalEl= document.getElementById("modalMachineList");
  const bsModal= bootstrap.Modal.getInstance(modalEl);
  bsModal.hide();
}

/** =========== Lohn-Funktionen =========== */
function openLohnModal(rowIndex) {
  currentLohnRow= rowIndex;
  const csrfToken= document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || "";

  fetch("/mycalc/lohn_list", {
    method: "GET",
    headers:{ "X-CSRFToken": csrfToken }
  })
    .then((res) => {
      if (!res.ok) {
        if (res.status===403) throw new Error("Lizenz nicht ausreichend. Bitte upgraden!");
        throw new Error("Fehler beim Laden der Lohnliste: "+ res.status);
      }
      return res.json();
    })
    .then((lohnData) => {
      fillLohnTable(lohnData);

      const modalEl= document.getElementById("modalLohn");
      new bootstrap.Modal(modalEl).show();
    })
    .catch((err) => {
      console.error("Lohnliste Fehler:", err);
      alert(err.message || "Lohnliste nicht verfügbar.");
    });
}

/** fillLohnTable(lohnArr) => #tblLohnList */
function fillLohnTable(lohnArr) {
  const tbody = document.querySelector("#tblLohnList tbody");
  if (!tbody) return;

  tbody.innerHTML= "";
  lohnArr.forEach((item, idx) => {
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
    tr.dataset.index   = idx;
    tr.dataset.allIneurh= allIn;
    tbody.appendChild(tr);
  });
}

/** selectLohn(idx): schreibt den Lohn in FertTable row => col Lohn */
function selectLohn(idx) {
  const row = document.querySelector(`#tblLohnList tbody tr[data-index="${idx}"]`);
  if (!row) return;

  const rate     = parseFloat(row.dataset.allIneurh) || 0;
  const ops      = parseFloat(document.getElementById("operatorsPerMachine")?.value) || 0.5;
  const lohnGesc = rate * ops; // Gesamtlohn

  const fertRows = document.querySelectorAll("#fertTable tbody tr");
  if (currentLohnRow >= 0 && currentLohnRow< fertRows.length) {
    fertRows[currentLohnRow].cells[3].querySelector("input").value = lohnGesc.toFixed(2);
  }

  // Modal schließen
  const modalEl= document.getElementById("modalLohn");
  const bsModal= bootstrap.Modal.getInstance(modalEl);
  bsModal.hide();
}

/** =========== ExtendedMachineRate + acceptMachine => (aus 2. Code)
 *   Falls du hier hast => Im dritter Teil integrieren?
 *   ...
**/

// End of "dritter Teil"
/**
 * updateCharts(resultData) – aktualisiert costChart & co2Chart
 * basierend auf den Werten im resultData.
 */
function updateCharts(resultData) {
  if (!chartInitialized) {
    initCharts(); // Falls noch nicht initiiert
  }

  // Beispiel:
  //   - Material = matEinzel100 + matGemein100
  //   - Fertigung = mach100 + lohn100 + fgk100
  //   - Rest = sga100 + profit100 + fremd100
  const matVal = (resultData.matEinzel100 ?? 0) + (resultData.matGemein100 ?? 0);
  const fertVal= (resultData.mach100 ?? 0) + (resultData.lohn100 ?? 0) + (resultData.fgk100 ?? 0);
  const restVal= (resultData.sga100  ?? 0) + (resultData.profit100 ?? 0) + (resultData.fremd100 ?? 0);

  costChart.data.datasets[0].data = [matVal, fertVal, restVal];
  costChart.update();

  // CO2:
  const co2Mat = resultData.co2Mat100  ?? 0;
  const co2Proc= resultData.co2Proc100 ?? 0;

  co2Chart.data.datasets[0].data = [co2Mat, co2Proc];
  co2Chart.update();
}

/**
 * onSliderMaterialChange(e) – ändert material_factor
 * und ruft calcAll().
 */
function onSliderMaterialChange(e) {
  // e = int % (z.B. -30..+30)
  material_factor = 1 + e / 100;
  calcAll(); // Deine lokale Rechenfunktion
}

/**
 * onSliderLaborChange(e)
 */
function onSliderLaborChange(e) {
  labor_factor = 1 + e / 100;
  calcAll();
}

/**
 * onSliderCO2Change(e)
 */
function onSliderCO2Change(e) {
  co2_factor = 1 + e / 100;
  calcAll();
}

/**
 * Beispiel-Funktion (optional) –
 * CSRF-sicheres AJAX an /calc/chartsData
 * Falls du später Charts-Updates aus dem Backend holen willst.
 */
function exampleFetchChartsData() {
  const csrftoken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || "";
  fetch("/calc/chartsData", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrftoken
    },
    body: JSON.stringify({ someParam: 123 })
  })
    .then(res => res.json())
    .then(data => {
      // data enthält z. B. { matVal, fertVal, restVal, co2Mat, co2Proc }
      costChart.data.datasets[0].data = [data.matVal, data.fertVal, data.restVal];
      costChart.update();

      co2Chart.data.datasets[0].data = [data.co2Mat, data.co2Proc];
      co2Chart.update();
    })
    .catch(err => {
      console.error("chartsData fetch error:", err);
    });
}


  /*********************************************************
 * Baugruppen-Funktionen (renderBaugruppeItems,
 * calcBaugruppeSum, addResultToBaugruppeFromTab4,
 * resetBaugruppenListe, addManualBaugruppe,
 * exportBaugruppenAsCSV)
 *
 * V2-kompatibel, CSRF-konform.
 *********************************************************/





window.baugruppenItems = window.baugruppenItems || [];

/**
 * Zeichnet die Tabelle in Tab 5 (baugruppeTable)
 * anhand von window.baugruppenItems
 */
function renderBaugruppeItems() {
  const tb = document.querySelector("#baugruppeTable tbody");
  if (!tb) return;
  tb.innerHTML = ""; // Tabelle leeren

  for (let i = 0; i < baugruppenItems.length; i++) {
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

/**
 * Zykluszeit-Modal (4 Verfahren)
 */
function openZyklusModalwithtakt() {
  const zyklusModalEl = document.getElementById("modalZyklusBild");
  if (!zyklusModalEl) {
    console.error("modalZyklusBild not found!");
    return;
  }
  const bsModal = new bootstrap.Modal(zyklusModalEl);
  bsModal.show();
}

/**
 * Schließt Zyklus-Modal (falls offen).
 */
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

/**
 * Druckguss – Platzhalter
 */

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

/**
 * Zerspanung – Platzhalter
 */
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

/**
 * Stanzen – Platzhalter
 */
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

/**
 * Feinguss
 */
function openFeingussModal() {
  closeParamToolsModal();
  const modalEl = document.getElementById("feingussModal");
  if (!modalEl) return;
  const bsModal = new bootstrap.Modal(modalEl);
  bsModal.show();
}

/**
 * Schmieden – Placeholder
 */
function openSchmiedenModal() {
  closeParamToolsModal();
  alert("Schmieden-Modal not implemented.");
}

/**
/**
 * Kaltfließpressen: öffnet das Kaltfliess-Modal
 */
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

/**
 * PCB – Placeholder
 */
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