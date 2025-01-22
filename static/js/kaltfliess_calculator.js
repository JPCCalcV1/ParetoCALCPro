/*********************************************************
 * kaltfliess_calculator.js – AJAX-Version
 *
 * Sämtliche Rechenlogik liegt im Backend (calc_kaltfliess).
 * Dieses JS sammelt nur Eingaben, ruft den Endpoint,
 * und rendert das Ergebnis (Text + 2 Pie-Charts).
 *********************************************************/

let kaltfliessCostChartObj = null;
let kaltfliessCo2ChartObj  = null;

/**
 * Ruft den Backend-Endpoint /calc/param/kaltfliess auf
 * und füllt das Modal (#kaltfliessModal) mit den Ergebnissen.
 */
function calculateKaltfliess() {
  // 1) Eingabefelder aus dem Modal
  const matName  = document.getElementById("kaltfliessMatSelect")?.value || "C10 (Stahl)";
  const landName = document.getElementById("kaltfliessCountry")?.value || "DE";
  const gw_g     = parseFloat(document.getElementById("kaltfliessWeight")?.value) || 50.0;
  const los      = parseFloat(document.getElementById("kaltfliessLos")?.value) || 10000;

  const stufen   = parseInt(document.getElementById("kaltfliessStufen")?.value) || 3;
  const ruest_min= parseFloat(document.getElementById("kaltfliessRuestMin")?.value) || 60.0;
  const isKomplex= !!document.getElementById("kaltfliessKomplex")?.checked;
  const isAuto   = !!document.getElementById("kaltfliessAutoMach")?.checked;

  // manuelle Maschine => Index (0=200t,1=400t,2=600t)
  let machineIndex = 0;
  const comboEl = document.getElementById("kaltfliessMachineCombo");
  if (comboEl) {
    //  z.B. "200 t" => index=0
    //  "400 t" => index=1
    //  "600 t" => index=2
    machineIndex = comboEl.selectedIndex >= 0 ? comboEl.selectedIndex : 0;
  }

  // 2) JSON-Payload
  const payload = {
    matName,
    landName,
    gw_g,
    los,
    stufen,
    ruest_min,
    isKomplex,
    isAuto,
    machineIndex
  };

  console.log("Kaltfliess => Sende an /calc/param/kaltfliess:", payload);

  // 3) AJAX per Fetch
  fetch("/calc/param/kaltfliess", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
      // ggf. CSRF-Token:
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
        alert("Kaltfliess-Backend: Calculation failed or incomplete.");
        return;
      }
      // 4) Update UI
      updateKaltfliessUI(data);
    })
    .catch(err => {
      console.error("Kaltfliess AJAX Error:", err);
      alert("Kaltfliess-Request fehlgeschlagen: " + err);
    });
}

/**
 * updateKaltfliessUI(data):
 *  - data enthält Felder wie cost_sum, co2_sum etc.
 *  - Wir befüllen #kaltfliessResultText
 *  - Zeichnen 2 Pie-Charts
 */
function updateKaltfliessUI(data) {
  // data => {
  //   "ok": true,
  //   "pressforce_t": 12.3,
  //   "machine": {...},
  //   "cyc_s": 0.7,
  //   "parts_per_h": 5000.0,
  //   "cost_mat": 0.05,
  //   "cost_mach_each": 0.10,
  //   "cost_ruest_each": 0.02,
  //   "cost_sum": 0.17,
  //   "co2_mat": 0.03,
  //   "co2_mach": 0.01,
  //   "co2_sum": 0.04,
  //   "debug": {...}
  // }

  const textDiv = document.getElementById("kaltfliessResultText");
  if (!textDiv) return;

  let m = data.machine || {};
  let html = `
    <p><b>Pressforce (t):</b> ${data.pressforce_t?.toFixed(1) ?? "--"}</p>
    <p><b>Maschine:</b> ${m.tons ?? "--"} t,
       Rate=${m.rate_eur_h ?? "--"} €/h,
       Power=${m.power_kW ?? "--"} kW
    </p>
    <p><b>Cycle:</b> ${data.cyc_s?.toFixed(2) ?? "--"} s,
       => ~${data.parts_per_h?.toFixed(1) ?? "--"} Teile/h</p>
    <p>Kosten:
       <br/>Material: ${data.cost_mat?.toFixed(3)} €
       <br/>Maschine: ${data.cost_mach_each?.toFixed(3)} €
       <br/>Rüst: ${data.cost_ruest_each?.toFixed(3)} €
       <br/><b>Summe: ${data.cost_sum?.toFixed(3)} €/Teil</b>
    </p>
    <p>CO₂:
       <br/>Mat: ${data.co2_mat?.toFixed(3)} kg
       <br/>Mach: ${data.co2_mach?.toFixed(3)} kg
       <br/><b>Total: ${data.co2_sum?.toFixed(3)} kg/Teil</b>
    </p>

  `;
  textDiv.innerHTML = html;

  // Chart 1 => Kosten (Material, Maschine, Rüst)
  const costCtx = document.getElementById("kaltfliessCostChart");
  if (costCtx) {
    if (kaltfliessCostChartObj) {
      kaltfliessCostChartObj.destroy();
    }
    let cMat  = data.cost_mat ?? 0;
    let cMach = data.cost_mach_each ?? 0;
    let cRst  = data.cost_ruest_each ?? 0;
    let total = data.cost_sum ?? 0;

    const costData = {
      labels: ["Material","Maschine","Rüst"],
      datasets: [{
        data: [cMat, cMach, cRst],
        backgroundColor:["#FF6384","#36A2EB","#FFCE56"]
      }]
    };
    kaltfliessCostChartObj = new Chart(costCtx, {
      type:"pie",
      data: costData,
      options: {
        responsive:false,
        plugins: {
          title:{
            display:true,
            text:`${total.toFixed(2)} €/Teil`
          }
        }
      }
    });
  }

  // Chart 2 => CO2 (mat, mach)
  const co2Ctx = document.getElementById("kaltfliessCo2Chart");
  if (co2Ctx) {
    if (kaltfliessCo2ChartObj) {
      kaltfliessCo2ChartObj.destroy();
    }
    let co2Mat  = data.co2_mat ?? 0;
    let co2Mach = data.co2_mach ?? 0;
    let co2Tot  = data.co2_sum ?? 0;

    const co2Data = {
      labels: ["Material","Maschine"],
      datasets: [{
        data:[co2Mat, co2Mach],
        backgroundColor:["#9CCC65","#FF7043"]
      }]
    };
    kaltfliessCo2ChartObj = new Chart(co2Ctx, {
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

/**
 * Optional: Maschine-Checkbox-Listener (falls nötig)
 * => So wie in deinem alten Code "onKaltfliessAutoMachineToggle()"
 * => Hier aber ggf. nicht mehr zwingend nötig,
 *    da wir nur den isAuto-Wert abgreifen und
 *    combo per "disabled" toggeln.
 */