/*************************************************************
 * feinguss_calculator_v2.js – Reduzierte JS-Version für V2
 *
 * Alle wesentlichen Berechnungen liegen jetzt im Backend
 * (siehe routes_feinguss_v2.py). Dieses Skript sammelt nur
 * die Formulardaten aus dem Modal und ruft per AJAX die
 * Route /calc/param/feinguss auf. Das empfangene Ergebnis
 * (JSON) wird dann in die UI (Tabelle, Chart) geschrieben.
 *************************************************************/

"use strict";

// Globale Referenz auf das Chart-Objekt, damit wir es zerstören können, wenn nötig
let fgCostChartV2 = null;

/**
 * Öffnet das Feinguss-Modal.
 * (Falls du es woanders aufrufst, z.B. über openFeingussModal() etc.,
 *  kannst du diesen Code anpassen oder entfernen.)
 */
function openFeingussModal() {
  const paramEl = document.getElementById("modalParamTools");
  if (paramEl) {
    const bsModal = bootstrap.Modal.getInstance(paramEl);
    bsModal?.hide();
  }
  // Feinguss-Modal öffnen
  const modalEl = document.getElementById("feingussModal");
  if (!modalEl) {
    console.error("feingussModal nicht gefunden!");
    return;
  }
  const bsModal = new bootstrap.Modal(modalEl);
  bsModal.show();
}

/**
 * Sammelt die Eingaben aus dem Feinguss-Modal (V2),
 * macht einen POST-Request an /calc/param/feinguss
 * und schreibt das Ergebnis ins UI.
 */
function calculateFeinguss() {
  console.log("[Feinguss V2] Starte AJAX-Call zum Backend.");

  // 1) Eingaben sammeln
  const matKey    = document.getElementById("fgMatSelect")?.value         || "Stahl";
  const locKey    = document.getElementById("fgLocationSelect")?.value    || "DE";
  const weight    = parseFloat(document.getElementById("fgWeight")?.value) || 50.0;
  const scrapRate = parseFloat(document.getElementById("fgScrapRate")?.value) || 5.0;
  const qty       = parseFloat(document.getElementById("fgQuantity")?.value) || 1000.0;

  const compKey   = document.getElementById("fgComplexitySelect")?.value  || "Medium";
  const setupMin  = parseFloat(document.getElementById("fgSetupTimeMin")?.value)  || 60.0;
  const ohRate    = parseFloat(document.getElementById("fgOverheadRate")?.value)  || 15.0;
  const pfRate    = parseFloat(document.getElementById("fgProfitRate")?.value)    || 10.0;
  const toolCost  = parseFloat(document.getElementById("fgToolCost")?.value)      || 0.0;
  const postMin   = parseFloat(document.getElementById("fgPostProcMin")?.value)   || 0.5;

  // 2) Payload zusammenstellen
  const payload = {
    fgMatSelect:        matKey,
    fgLocationSelect:   locKey,
    fgWeight:           weight,
    fgScrapRate:        scrapRate,
    fgQuantity:         qty,

    fgComplexitySelect: compKey,
    fgSetupTimeMin:     setupMin,
    fgOverheadRate:     ohRate,
    fgProfitRate:       pfRate,
    fgToolCost:         toolCost,
    fgPostProcMin:      postMin
  };

  console.log("[Feinguss V2] Payload =>", payload);

  // 3) AJAX-Request (fetch) an den Backend-Endpunkt
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || "";
  fetch("/mycalc/feinguss", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrfToken
    },
    body: JSON.stringify(payload)
  })
    .then(response => {
      if (!response.ok) {
        throw new Error("HTTP " + response.status);
      }
      return response.json();
    })
    .then(data => {
      console.log("[Feinguss V2] Backend Response:", data);
      if (data.error) {
        alert("Fehler: " + data.error);
        return;
      }
      if (!data.ok) {
        alert("Feinguss-Berechnung unvollständig oder abgelehnt.");
        return;
      }
      // => UI-Update
      fillFeingussV2UI(data);
    })
    .catch(err => {
      console.error("[Feinguss V2] AJAX Error:", err);
      alert("Feinguss-Request fehlgeschlagen: " + err);
    });
}

/**
 * Schreibt das vom Backend gelieferte Ergebnis
 * in die Tabelle (#fgTableBody) und zeichnet das Pie-Chart (#fgCostChart).
 */
function fillFeingussV2UI(data) {
  // data={
  //   ok:true,
  //   costMatShell:3.25,
  //   costFertigung:2.10,
  //   overheadVal:0.83,
  //   profitVal:0.59,
  //   endPrice:6.77,
  //   msg:"Feinguss Parametric V2 erfolgreich"
  // }

  const tblBody = document.getElementById("fgTableBody");
  if (!tblBody) {
    console.warn("[Feinguss V2] fgTableBody not found!");
    return;
  }

  // Tabelle: 5 Zeilen
  //   1) Material + Shell
  //   2) Fertigung
  //   3) Overhead
  //   4) Gewinn
  //   5) Endpreis
  tblBody.innerHTML = "";
  const rows = [
    ["Material + Shell",    data.costMatShell?.toFixed(2) + " €"],
    ["Fertigung",           data.costFertigung?.toFixed(2) + " €"],
    ["Overhead",            data.overheadVal?.toFixed(2) + " €"],
    ["Gewinn",              data.profitVal?.toFixed(2) + " €"],
    ["Endpreis/Teil",       data.endPrice?.toFixed(2) + " €"]
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

  // Chart
  const costChartEl = document.getElementById("fgCostChart");
  if (!costChartEl) {
    console.warn("[Feinguss V2] fgCostChart not found!");
    return;
  }

  // Zerstöre altes Chart-Objekt, wenn vorhanden
  if (fgCostChartV2) {
    fgCostChartV2.destroy();
  }

  const dataVals = [
    data.costMatShell  ?? 0,
    data.costFertigung ?? 0,
    data.overheadVal   ?? 0,
    data.profitVal     ?? 0
  ];
  const dataLabels = ["Mat+Shell", "Fertigung", "Overhead", "Gewinn"];
  const endPriceVal = data.endPrice?.toFixed(2) ?? "--";

  fgCostChartV2 = new Chart(costChartEl, {
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
          text: `Kostenverteilung (Endpreis = ${endPriceVal} €)`
        }
      }
    }
  });
}

/**
 * initFeingussV2():
 *  - Optionale Init-Funktion, falls du beim Seitenladen
 *    bereits irgendwas definieren oder Events binden willst.
 */
function initFeingussV2() {
  // Beispiel: Button-Click an die Funktion binden:
  const calcBtn = document.getElementById("fgCalcBtn");
  if (calcBtn) {
    calcBtn.addEventListener("click", calculateFeingussParametric);
  }
  console.log("[Feinguss V2] initFeingussV2 aufgerufen.");
}
