/***********************************************************
 * schmieden_calculator.js – AJAX-Version
 *
 * Hier liegt KEINE echte Rechenlogik mehr;
 * stattdessen ruft calculateSchmieden() das Backend an.
 ***********************************************************/

// Globale Variablen für Charts (damit wir sie zerstören können)
let schmiedenCostChartObj = null;
let schmiedenCo2ChartObj  = null;

/**
 * Zeigt das Schmieden-Modal (wenn das Tools-Modal offen ist, schließe es).
 */
function openSchmiedenModal() {
  // Optional: Param-Tools-Modal schließen
  const paramEl = document.getElementById("modalParamTools");
  if (paramEl) {
    const bsModal = bootstrap.Modal.getInstance(paramEl);
    bsModal?.hide();
  }
  // Schmieden-Modal öffnen
  const modalEl = document.getElementById("schmiedenModal");
  if (!modalEl) return;
  let bsModal= new bootstrap.Modal(modalEl);
  bsModal.show();
}

/**
 * Sammelt die Eingaben aus dem Schmieden-Modal
 * und ruft POST /calc/param/schmieden auf.
 */
function calculateSchmieden() {
  // 1) Eingaben
  const mat_str   = document.getElementById("schmiedenMaterial")?.value || "C45 (Stahl)";
  const land_str  = document.getElementById("schmiedenCountry")?.value || "DE";
  const part_w    = parseFloat(document.getElementById("schmiedenPartWeight")?.value) || 0.50;
  const losg      = parseFloat(document.getElementById("schmiedenLos")?.value) || 10000;
  const scrapPct  = parseFloat(document.getElementById("schmiedenScrapPct")?.value) || 15.0;
  const area_cm2  = parseFloat(document.getElementById("schmiedenArea")?.value) || 10.0;
  const ruest_min = parseFloat(document.getElementById("schmiedenRuestMin")?.value) || 60.0;

  // 2) JSON-Payload
  const payload = {
    mat_str,
    land_str,
    part_w,
    losg,
    scrapPct,
    area_cm2,
    ruest_min
  };

  console.log("Schmieden => Sende an /calc/param/schmieden:", payload);

  // 3) AJAX-Fetch
  fetch("/mycalc/schmieden", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
      // Falls du global CSRF nutzt:
      // "X-CSRFToken": document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || ""
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
        alert("Schmieden-Backend: Calculation incomplete.");
        return;
      }
      // 4) UI-Update
      updateSchmiedenUI(data);
    })
    .catch(err => {
      console.error("Schmieden AJAX Error:", err);
      alert("Schmieden-Request fehlgeschlagen: " + err);
    });
}

/**
 * Schreibt die Backend-Ergebnisse in #schmiedenResultText,
 * zeichnet 2 Pie-Charts (schmiedenCostChart, schmiedenCo2Chart).
 */
function updateSchmiedenUI(data) {
  // data => {
  //   "ok": true,
  //   "pressforce_t": 200,
  //   "chosen_mach": {"tons":1000, "rate":80.0, "shots_h":1200},
  //   "cyc_s": 3.0,
  //   "cost_mat": 0.12,
  //   "cost_ofen": 0.05,
  //   "cost_machine_each": 0.02,
  //   "cost_ruest_each": 0.01,
  //   "cost_sum": 0.20,
  //   "mat_co2": 0.03,
  //   "ofen_co2": 0.02,
  //   "mach_co2": 0.01,
  //   "co2_sum": 0.06,
  //   "debug": { ... }
  // }

  const textDiv= document.getElementById("schmiedenResultText");
  if (!textDiv) return;

  const mach= data.chosen_mach || {};
  let html= `
    <p><b>Presskraft:</b> ${data.pressforce_t?.toFixed(2) ?? "--"} t<br/>
       Maschine: ${mach.tons ?? "--"} t, Rate=${mach.rate ?? "--"} €/h, 
       Shots/h=${mach.shots_h ?? "--"} (Zyklus~${data.cyc_s?.toFixed(2) ?? "--"} s)
    </p>
    <p>Kosten pro Teil:
       <br/>Mat= ${data.cost_mat?.toFixed(2)} €
       <br/>Ofen= ${data.cost_ofen?.toFixed(2)} €
       <br/>Maschine= ${data.cost_machine_each?.toFixed(3)} €
       <br/>Rüst= ${data.cost_ruest_each?.toFixed(3)} €
       <br/><b>Summe= ${data.cost_sum?.toFixed(2)} €/Teil</b>
    </p>
    <p>CO₂:
       <br/>Mat= ${data.mat_co2?.toFixed(2)} kg
       <br/>Ofen= ${data.ofen_co2?.toFixed(2)} kg
       <br/>Maschine= ${data.mach_co2?.toFixed(2)} kg
       <br/><b>Total= ${data.co2_sum?.toFixed(2)} kg/Teil</b>
    </p>
    <p style="font-size:0.8rem;color:#666;">
      debug: ${JSON.stringify(data.debug)}
    </p>
  `;
  textDiv.innerHTML= html;

  // Cost Chart => schmiedenCostChart
  const costCtx= document.getElementById("schmiedenCostChart");
  if (costCtx) {
    if (schmiedenCostChartObj) {
      schmiedenCostChartObj.destroy();
    }
    let cMat = data.cost_mat ?? 0;
    let cOfn = data.cost_ofen ?? 0;
    let cMach= data.cost_machine_each ?? 0;
    let cRst = data.cost_ruest_each ?? 0;
    let cSum = data.cost_sum ?? 0;

    const costData= {
      labels: ["Material","Ofen","Maschine","Rüst"],
      datasets: [{
        data: [cMat, cOfn, cMach, cRst],
        backgroundColor:["#FF6384","#36A2EB","#FFCE56","#8BC34A"]
      }]
    };
    schmiedenCostChartObj= new Chart(costCtx, {
      type:"pie",
      data: costData,
      options:{
        responsive:false,
        plugins:{
          title:{
            display:true,
            text:`${cSum.toFixed(2)} €/Teil`
          }
        }
      }
    });
  }

  // CO2 Chart => schmiedenCo2Chart
  const co2Ctx= document.getElementById("schmiedenCo2Chart");
  if (co2Ctx) {
    if (schmiedenCo2ChartObj) {
      schmiedenCo2ChartObj.destroy();
    }
    let co2Mat  = data.mat_co2 ?? 0;
    let co2Ofn  = data.ofen_co2 ?? 0;
    let co2Mach = data.mach_co2 ?? 0;
    let co2Tot  = data.co2_sum ?? 0;

    const co2Data= {
      labels:["Material","Ofen","Maschine"],
      datasets:[{
        data:[co2Mat, co2Ofn, co2Mach],
        backgroundColor:["#9CCC65","#FF7043","#42A5F5"]
      }]
    };
    schmiedenCo2ChartObj= new Chart(co2Ctx, {
      type:"pie",
      data: co2Data,
      options:{
        responsive:false,
        plugins:{
          title:{
            display:true,
            text:`${co2Tot.toFixed(2)} kg CO₂/Teil`
          }
        }
      }
    });
  }
}