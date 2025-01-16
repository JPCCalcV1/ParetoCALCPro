/********************************************************
 * feinguss_calculator.js – AJAX-Variante
 *
 * Übernimmt NICHT mehr die eigentliche Berechnung,
 * sondern holt sich das Ergebnis vom Backend.
 ********************************************************/

// Globale Chart-Objekte (damit wir sie zerstören können)
let feingussCostChartObj = null;
let feingussCo2ChartObj  = null;

function openFeingussModal() {
  // Schließt das ParamTools-Modal, falls offen
  const paramEl = document.getElementById("modalParamTools");
  if (paramEl) {
    const bsModal = bootstrap.Modal.getInstance(paramEl);
    bsModal?.hide();
  }
  // Öffne feingussModal
  const modalEl = document.getElementById("feingussModal");
  if (!modalEl) {
    console.error("feingussModal not found!");
    return;
  }
  const bsModal = new bootstrap.Modal(modalEl);
  bsModal.show();
}

/**
 * Sammelt die Eingaben aus dem Feinguss-Modal
 * und ruft das Backend /calc/param/feinguss auf.
 */
function calculateFeinguss() {
  // 1) Sammle Eingaben
  const matName   = document.getElementById("feingussMatSelect")?.value || "Stahl 1.4408";
  const landName  = document.getElementById("feingussCountrySelect")?.value || "DE";
  const shellName = document.getElementById("feingussShellSelect")?.value || "Medium";

  const gw_g      = parseFloat(document.getElementById("feingussPartWeight")?.value) || 50.0;
  const qty       = parseFloat(document.getElementById("feingussAnnualQty")?.value) || 10000;
  const ruest_min = parseFloat(document.getElementById("feingussRuestMin")?.value) || 90;
  const post_factor = parseFloat(document.getElementById("feingussPostproc")?.value) || 1.0;

  const payload = {
    matName,
    landName,
    shellName,
    gw_g,
    qty,
    ruest_min,
    post_factor
  };

  console.log("Feinguss => Sende Payload an Backend:", payload);

  // 2) AJAX-Call zum Backend
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || "";
  fetch("/calc/param/feinguss", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrfToken  // Falls du CSRF nutzt
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
      console.log("Feinguss-Ergebnis vom Backend:", data);
      if (data.error) {
        alert("Fehler: " + data.error);
        return;
      }
      if (!data.ok) {
        alert("Berechnung fehlgeschlagen oder unvollständig.");
        return;
      }
      // 3) Update UI
      updateFeingussUI(data);
    })
    .catch(err => {
      console.error("Feinguss AJAX Error:", err);
      alert("Feinguss-Request fehlgeschlagen: " + err);
    });
}

/**
 * Füllt #feingussResultText, #feingussCostChart, #feingussCo2Chart
 */
function updateFeingussUI(data) {
  // data enthält:
  // {
  //   "ok": true,
  //   "cost_per_part": 2.37,
  //   "co2_per_part": 1.09,
  //   "cost_material_total": ...,
  //   "cost_process": ...,
  //   "cost_ruest_each": ...,
  //   "cost_overhead": ...,
  //   "debug": {...}
  // }

  const textDiv = document.getElementById("feingussResultText");
  if (!textDiv) return;

  let html = `
    <p><b>Kosten/Teil:</b> ${data.cost_per_part?.toFixed(2) ?? "--"} €<br/>
    <b>CO₂/Teil:</b> ${data.co2_per_part?.toFixed(2) ?? "--"} kg</p>
    <p>
      Material: ${data.cost_material_total?.toFixed(2) ?? "--"} €<br/>
      Prozess: ${data.cost_process?.toFixed(2) ?? "--"} €<br/>
      Rüst/Teil: ${data.cost_ruest_each?.toFixed(2) ?? "--"} €<br/>
      Overhead: ${data.cost_overhead?.toFixed(2) ?? "--"} €<br/>
    </p>
    <p style="font-size:0.85rem; color:#666;">
      debug: ${JSON.stringify(data.debug)}
    </p>
  `;
  textDiv.innerHTML = html;

  // Pie 1 => cost
  const costCtx = document.getElementById("feingussCostChart");
  if (costCtx) {
    if (feingussCostChartObj) {
      feingussCostChartObj.destroy();
    }
    const cost_mat   = data.cost_material_total ?? 0;
    const cost_proc  = data.cost_process ?? 0;
    const cost_ruest = data.cost_ruest_each ?? 0;
    const cost_oh    = data.cost_overhead ?? 0;
    const totalCost  = data.cost_per_part ?? 0;
    const costData= {
      labels: ["Mat+Shell","Prozess","Rüst","Overhead"],
      datasets: [{
        data: [cost_mat, cost_proc, cost_ruest, cost_oh],
        backgroundColor: ["#FF6384","#36A2EB","#FFCE56","#8BC34A"]
      }]
    };
    feingussCostChartObj= new Chart(costCtx, {
      type: "pie",
      data: costData,
      options: {
        responsive:false,
        plugins: {
          title: {
            display: true,
            text: totalCost.toFixed(2) + " €/Teil"
          }
        }
      }
    });
  }

  // Pie 2 => CO2
  const co2Ctx = document.getElementById("feingussCo2Chart");
  if (co2Ctx) {
    if (feingussCo2ChartObj) {
      feingussCo2ChartObj.destroy();
    }
    const totalCo2 = data.co2_per_part ?? 0;
    // Einfacher Breakdown: 50/50
    // (Wenn du mehr Info vom Backend bräuchtest, kannst du es verfeinern.)
    let matCo2 = totalCo2*0.7;
    let procCo2= totalCo2 - matCo2;
    const co2Data= {
      labels:["Mat+Shell","Prozess"],
      datasets:[{
        data:[matCo2, procCo2],
        backgroundColor:["#9CCC65","#FF7043"]
      }]
    };
    feingussCo2ChartObj= new Chart(co2Ctx, {
      type:"pie",
      data:co2Data,
      options:{
        responsive:false,
        plugins:{
          title:{
            display:true,
            text: totalCo2.toFixed(2)+" kg CO₂/Teil"
          }
        }
      }
    });
  }
}

/**
 * Falls du "In Baugruppe übernehmen" Button nutzen willst
 */
function addFeingussToBaugruppe() {
  alert("Noch nicht implementiert. Hier könntest du 'data' von letzter Response speichern.");
}