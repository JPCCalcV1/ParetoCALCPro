/************************************************************
 * pcb_calculator.js – AJAX-Version
 *
 * Sämtliche Rechenlogik liegt im Backend (calc_pcb).
 * Dieses JS sammelt nur die Eingaben und aktualisiert die UI.
 ************************************************************/

// Globale Chart-Objekte, damit wir sie vor dem Neuzeichnen zerstören können
let pcbCostChartObj = null;
let pcbCo2ChartObj  = null;

/**
 * Sammelt die Eingaben aus dem PCB-Modal
 * und ruft /calc/param/pcb auf.
 */
function calculatePcb() {
  // 1) Eingaben
  const l_mm   = parseFloat(document.getElementById("pcbLen")?.value)   || 100.0;
  const b_mm   = parseFloat(document.getElementById("pcbWid")?.value)   || 80.0;
  const layer  = parseInt(document.getElementById("pcbLayer")?.value)   || 2;
  const qty    = parseInt(document.getElementById("pcbQty")?.value)     || 1000;
  const land   = document.getElementById("pcbLand")?.value             || "China";

  const thick  = parseFloat(document.getElementById("pcbThick")?.value) || 1.6;
  const cu_    = document.getElementById("pcbCu")?.value                || "35µm";
  const finish = document.getElementById("pcbFinish")?.value            || "HASL";
  const tooling= parseFloat(document.getElementById("pcbTooling")?.value) || 200.0;

  const do_assembly= !!document.getElementById("pcbAssemblyCheck")?.checked;
  const smd_count= parseInt(document.getElementById("pcbSmdCount")?.value) || 50;
  const tht_count= parseInt(document.getElementById("pcbThtCount")?.value) || 10;

  // 2) JSON-Payload
  const payload = {
    l_mm, b_mm,
    layer, qty,
    land, thick,
    cu: cu_,
    finish,
    tooling,
    do_assembly,
    smd_count,
    tht_count
  };

  console.log("PCB => Sende POST /calc/param/pcb:", payload);

  // 3) AJAX-Fetch
  fetch("/calc/param/pcb", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
      // Falls du global CSRF benutzt, brauchst du ggf.:
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
        alert("PCB-Backend: Calculation incomplete or missing fields.");
        return;
      }
      // 4) UI-Update
      updatePcbUI(data);
    })
    .catch(err => {
      console.error("PCB AJAX Error:", err);
      alert("PCB-Request fehlgeschlagen: " + err);
    });
}

/**
 * updatePcbUI(data):
 *  - data enthält Felder wie pcb_unit_cost, assembly_cost, total_unit_cost
 *  - raw_co2_board, assembly_co2, total_co2_board etc.
 */
function updatePcbUI(data) {
  // data => {
  //   "ok": true,
  //   "pcb_unit_cost": 1.23,
  //   "assembly_cost": 0.45,
  //   "total_unit_cost": 1.68,
  //   "raw_co2_board": 0.12,
  //   "assembly_co2": 0.03,
  //   "total_co2_board": 0.15,
  //   "debug": { ... }
  // }

  const textDiv = document.getElementById("pcbResultText");
  if (!textDiv) return;

  let html = `
    <p>Roh-PCB: ${data.pcb_unit_cost?.toFixed(2) ?? "--"} €/Stk<br/>
       Bestückung: ${data.assembly_cost?.toFixed(2) ?? "--"} €/Stk<br/>
       <b>Summe: ${data.total_unit_cost?.toFixed(2) ?? "--"} €/Stk</b>
    </p>
    <p>Roh-PCB-CO₂: ${data.raw_co2_board?.toFixed(3) ?? "--"} kg/Stk<br/>
       Bestückungs-CO₂: ${data.assembly_co2?.toFixed(3) ?? "--"} kg/Stk<br/>
       <b>Gesamt-CO₂: ${data.total_co2_board?.toFixed(3) ?? "--"} kg/Stk</b>
    </p>
    <p style="font-size:0.8rem; color:#666;">debug: ${JSON.stringify(data.debug)}</p>
  `;
  textDiv.innerHTML = html;

  // Cost Chart
  const costCtx = document.getElementById("pcbCostChart");
  if (costCtx) {
    if (pcbCostChartObj) {
      pcbCostChartObj.destroy();
    }
    const cPcb  = data.pcb_unit_cost ?? 0;
    const cAsm  = data.assembly_cost ?? 0;
    const cTot  = data.total_unit_cost ?? 0;

    const costData= {
      labels: ["Roh-PCB","Bestückung"],
      datasets:[{
        data: [cPcb, cAsm],
        backgroundColor:["#FF6384","#36A2EB"]
      }]
    };
    pcbCostChartObj= new Chart(costCtx, {
      type:"pie",
      data: costData,
      options:{
        responsive:false,
        plugins:{
          title:{
            display:true,
            text:`Summe= ${cTot.toFixed(2)} €`
          }
        }
      }
    });
  }

  // CO₂ Chart
  const co2Ctx = document.getElementById("pcbCo2Chart");
  if (co2Ctx) {
    if (pcbCo2ChartObj) {
      pcbCo2ChartObj.destroy();
    }
    const co2Pcb = data.raw_co2_board ?? 0;
    const co2Asm = data.assembly_co2 ?? 0;
    const co2Tot = data.total_co2_board ?? 0;

    const co2Data= {
      labels:["Roh-PCB","Bestück."],
      datasets:[{
        data:[co2Pcb, co2Asm],
        backgroundColor:["#9CCC65","#FF7043"]
      }]
    };
    pcbCo2ChartObj= new Chart(co2Ctx, {
      type:"pie",
      data: co2Data,
      options:{
        responsive:false,
        plugins:{
          title:{
            display:true,
            text:`CO₂= ${co2Tot.toFixed(3)} kg/Stk`
          }
        }
      }
    });
  }
}