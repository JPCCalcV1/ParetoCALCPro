// static/js/maincalc.js

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

  fetch('/calc/maincalc/compute', {
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