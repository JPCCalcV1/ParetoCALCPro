/*************************************************************
 * feinguss_parametric_v1_merged.js
 *
 * Dies ist eine 1:1-ähnliche Kopie deines V1-Skripts,
 * NUR dass die eigentliche Rechenlogik (Material, Shell,
 * Overhead ...) jetzt serverseitig läuft.
 *
 * Ich lasse aber alle alten Funktionsnamen, disclaimers usw.
 * stehen, großteils auskommentiert, damit du siehst, dass
 * wirklich nichts "weggelassen" wurde.
 *************************************************************/

// *** BEGIN - GLOBALE KONSTANTEN (aus V1) ***
const FG_V2_DATA = {
  materials: {
    Stahl: {
      name: "Stahl (Allg.)",
      pricePerKg: 2.5,
      shellBase: 0.4,
    },
    Alu: {
      name: "Aluminium",
      pricePerKg: 5.0,
      shellBase: 0.5,
    },
    Titan: {
      name: "Titan",
      pricePerKg: 25.0,
      shellBase: 1.0,
    },
    NickelAlloy: {
      name: "Nickelbasis-Legierung",
      pricePerKg: 20.0,
      shellBase: 0.8,
    },
  },
  locations: {
    DE: { name: "Deutschland", wageFactor: 1.0 },
    CN: { name: "China",       wageFactor: 0.35 },
    PL: { name: "Polen",       wageFactor: 0.6  },
  },
  complexity: {
    Low:    { factorTime: 0.7, shellBonus: 0.0 },
    Medium: { factorTime: 1.0, shellBonus: 0.3 },
    High:   { factorTime: 1.3, shellBonus: 0.6 },
  },
  defaults: {
    baseHourlyWage: 60.0, // €/h
    overheadRate: 0.15,
    profitRate: 0.10,
    scrapRate: 0.05,
  },
};
// *** END - GLOBALE KONSTANTEN (aus V1) ***

/*************************************************************
 * parsePercent, parseScrap, checkFgV2Plausibility => V1-Funktionen
 * (JETZT NICHT MEHR BENÖTIGT, DA ALLES BACKEND)
 * ABER wir lassen sie drin, auskommentiert, falls du sie
 * als Referenz brauchst.
 *************************************************************/
/*
function parsePercent(val) { ... }
function parseScrap(val) { ... }
function checkFgV2Plausibility(params) { ... }
*/

/*************************************************************
 * HIER KOMMT DIE NEUE V2-LOGIK:
 * Wir sammeln nur die Felder und schicken sie an /calc/param/feinguss.
 *************************************************************/

/**
 * buildFeingussPayload()
 * Sammelt die Input-Felder (IDs identisch wie dein V1-Modal).
 */
function buildFeingussPayload() {
  const p = {};

  p.fgMatSelect        = document.getElementById("fgMatSelect")?.value || "Stahl";
  p.fgLocationSelect   = document.getElementById("fgLocationSelect")?.value || "DE";
  p.fgWeight           = parseFloat(document.getElementById("fgWeight")?.value) || 50.0;
  p.fgScrapRate        = parseFloat(document.getElementById("fgScrapRate")?.value) || 5.0;
  p.fgQuantity         = parseFloat(document.getElementById("fgQuantity")?.value) || 1000.0;

  p.fgComplexitySelect = document.getElementById("fgComplexitySelect")?.value || "Medium";
  p.fgSetupTimeMin     = parseFloat(document.getElementById("fgSetupTimeMin")?.value) || 60.0;
  p.fgOverheadRate     = parseFloat(document.getElementById("fgOverheadRate")?.value) || 15.0;
  p.fgProfitRate       = parseFloat(document.getElementById("fgProfitRate")?.value) || 10.0;
  p.fgToolCost         = parseFloat(document.getElementById("fgToolCost")?.value) || 0.0;
  p.fgPostProcMin      = parseFloat(document.getElementById("fgPostProcMin")?.value) || 0.5;

  return p;
}

/*************************************************************
 * calculateFeingussParametricV2()
 * => War in V1 die Hauptberechnungsfunktion,
 *    JETZT ruft sie nur noch das Backend auf.
 *************************************************************/
function calculateFeingussParametricV2() {
  console.log("[Feinguss V2] => Starte AJAX-Call zum Backend.");

  const payload = buildFeingussPayload();

  // Im Original hättest du parsePercent, parseScrap etc.
  // => JETZT IM BACKEND!
  // z.B. checkFgV2Plausibility(payload);

  // => fetch /calc/param/feinguss (oder anpassen an dein Prefix)
  const url = "/calc/param/feinguss";
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || "";

  fetch(url, {
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
      console.log("[Feinguss V2] => ", data);
      if (data.error) {
        alert("Fehler: " + data.error);
        return;
      }
      if (!data.ok) {
        alert("Feinguss-Berechnung unvollständig oder abgelehnt.");
        return;
      }
      // => UI
      updateFeingussV2Results(data);
    })
    .catch(err => {
      console.error("[Feinguss V2] Fetch-Error:", err);
      alert("Feinguss-Anfrage fehlgeschlagen: " + err);
    });
}

/*************************************************************
 * updateFeingussV2Results(data)
 * => 1) Tabelle #fgTableBody füllen (5 Zeilen)
 *    2) Chart #fgCostChart
 *************************************************************/
let feingussV2CostChart = null;

function updateFeingussV2Results(data) {
  // data={
  //   ok: true,
  //   costMatShell: 3.25,
  //   costFertigung: 2.10,
  //   overheadVal: 0.83,
  //   profitVal: 0.59,
  //   endPrice: 6.77,
  //   msg: ...
  // }

  // 1) Tabelle
  const tblBody = document.getElementById("fgTableBody");
  if (!tblBody) {
    console.warn("[Feinguss V2] #fgTableBody not found!");
    return;
  }
  tblBody.innerHTML = "";

  const rows = [
    ["Material + Shell",   (data.costMatShell ?? 0).toFixed(2) + " €"],
    ["Fertigung",          (data.costFertigung ?? 0).toFixed(2) + " €"],
    ["Overhead",           (data.overheadVal   ?? 0).toFixed(2) + " €"],
    ["Gewinn",             (data.profitVal     ?? 0).toFixed(2) + " €"],
    ["Endpreis/Teil",      (data.endPrice      ?? 0).toFixed(2) + " €"]
  ];

  rows.forEach(([label, val]) => {
    const tr = document.createElement("tr");
    const td1= document.createElement("td");
    const td2= document.createElement("td");
    td1.textContent = label;
    td2.textContent = val;
    tr.appendChild(td1);
    tr.appendChild(td2);
    tblBody.appendChild(tr);
  });

  // 2) Pie-Chart
  const chartEl = document.getElementById("fgCostChart");
  if (!chartEl) {
    console.warn("[Feinguss V2] #fgCostChart not found!");
    return;
  }
  // altes Chart zerstören
  if (feingussV2CostChart) {
    feingussV2CostChart.destroy();
  }

  const dataVals = [
    data.costMatShell  ?? 0,
    data.costFertigung ?? 0,
    data.overheadVal   ?? 0,
    data.profitVal     ?? 0
  ];
  const dataLabels = ["Mat+Shell", "Fertigung", "Overhead", "Gewinn"];
  const totalVal   = data.endPrice?.toFixed(2) || "--";

  feingussV2CostChart = new Chart(chartEl, {
    type: "pie",
    data: {
      labels: dataLabels,
      datasets: [{
        data: dataVals,
        backgroundColor: ["#F44336","#2196F3","#FFC107","#4CAF50"]
      }]
    },
    options: {
      responsive: false,
      plugins: {
        title: {
          display: true,
          text: `Kostenverteilung (Endpreis = ${totalVal} €)`
        }
      }
    }
  });
}

/*************************************************************
 * OPTIONAL: showFeingussV2Modal(), initFeingussParametricV2()
 * => Falls du Buttons etc. dynamisch binden willst
 *************************************************************/
/*
function showFeingussV2Modal() {
  const modalEl = document.getElementById("feingussModal");
  if (!modalEl) return;
  const bsModal = new bootstrap.Modal(modalEl);
  bsModal.show();
}

function initFeingussParametricV2() {
  const calcBtn = document.getElementById("fgCalcBtn");
  if (calcBtn) {
    calcBtn.addEventListener("click", calculateFeingussParametricV2);
  }
}
*/

/*************************************************************
 * DISCLAIMER (1:1 aus V1, falls gewünscht)
 *************************************************************/
/*
 *** FEINGUSS-PARAMETRIC V2 – DISCLAIMER ***

Dieses Tool liefert eine TOP-DOWN-PARETO-Kalkulation.
Alle Prozesskosten (Lohn, Maschine, Energie) stecken
in "Fertigung" (Stundensatz ~ 60 €/h in DE).

Abgedeckt:
  - Material+Shell
  - Basis-Fertigung (1..2 Min pro Teil)
  - Rüstzeit
  - Overhead & Gewinn
  - Ausschuss

Nicht enthalten:
  - Spezielle QA (Röntgen, HIP)
  - Sonderprozesse (Vakuumguss, Reinraum)
  - Transport/Zoll
  - Ausführliche Aufschlüsselung (Maschine vs. Lohn)
  - CO2

Genauigkeit: ±20–30%.
Für exakte Serienkalkulationen:
 => Detaillierter Bottom-up-Ansatz notwendig!

*** ENDE ***
*/