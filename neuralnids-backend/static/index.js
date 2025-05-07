import { invokeAlert, clearAlert } from "./notification.js";
import { TableRow } from "./TableRow.js";

let isDarkMode = false;
let chart;
let map;
let mapMarkers = [];
let alertActive = false;
const BASE_URL = "http://10.10.10.100:5000"; // Change this when you need to change all URLs

let previousMLTimestamps = new Set();  // Keep track of unique timestamps
let addressedAlerts = [];

async function fetchMLAlerts() {
    try {
        const res = await fetch(`${BASE_URL}/api/live-alerts`);
        const alerts = await res.json();

        const mlTable = document.getElementById("ml-alert-table");
        if (!mlTable) {
            console.warn("Could not find #ml-alert-table");
            return;
        }

        // Filter out previously seen alerts (by timestamp + confidence)
        const newAlerts = alerts.filter(entry => {
            const uniqueKey = `${entry.timestamp}_${entry.confidence}`;
            if (previousMLTimestamps.has(uniqueKey)) {
                return false;
            } else {
                previousMLTimestamps.add(uniqueKey);
                return true;
            }
        });

        // Only show last 10 alerts (clear and re-render)
        const last10 = Array.from(previousMLTimestamps).slice(-10).reverse();
        mlTable.innerHTML = "";

        if (last10.length === 0) {
            const row = document.createElement("tr");
            row.innerHTML = `<td colspan="3">No new ML alerts detected yet.</td>`;
            mlTable.appendChild(row);
            return;
        }

        last10.forEach(key => {
            const [timestamp, confidence] = key.split("_");
            const row = document.createElement("tr");
            const formattedTime = new Date(timestamp).toLocaleString(undefined, {
                year: "numeric", month: "2-digit", day: "2-digit",
                hour: "2-digit", minute: "2-digit", second: "2-digit",
                hour12: false
            });

            row.innerHTML = `
                <td>${formattedTime}</td>
                <td>ATTACK</td>
                <td>${parseFloat(confidence).toFixed(4)}</td>
            `;
            mlTable.appendChild(row);
        });

    } catch (err) {
        console.error("[x] Error fetching ML alerts:", err);
    }
}

function toggleDarkMode() {
    document.body.classList.toggle('dark-mode');
    isDarkMode = !isDarkMode;
    if (chart) {
        chart.options.plugins.title.color = isDarkMode ? '#fff' : '#000';
        chart.options.plugins.legend.labels.color = isDarkMode ? '#fff' : '#333';
        chart.update();
    }
}

// function formatTimestamp(ts) {
//     const d = new Date(ts);
//     const date = d.toLocaleDateString("en-US");
//     const time = d.toLocaleTimeString("en-US", { hour12: false });
//     return `${date} ${time}`;
// }

async function fetchDashboardData() {
    let critAlertDetected = false;
    const scrollY = window.scrollY;       // Save scroll position
    const alertRes = await fetch(`${BASE_URL}/api/alerts`);
    const alerts = await alertRes.json();

    const protocolCounts = {};
    let alertCount = 0, critical = 0, warning = 0;

    const table = document.getElementById("threat-table");
    table.innerHTML = "";

    const recentAlerts = alerts.slice(-8).reverse();

    recentAlerts.forEach(alert => {
        alertCount++;
        if (alert.severity <= 2) {
            critical++;
            alertActive = true;
            critAlertDetected = true;
        }
        else warning++;

        const proto = alert.protocol || 'Unknown';
        protocolCounts[proto] = (protocolCounts[proto] || 0) + 1;

        const conciseSig = alert.signature?.split("[")[0]?.trim() || "-";
        const row = document.createElement("tr");
        row.innerHTML = `<td>${formatTimestamp(alert.timestamp)}</td><td>${conciseSig}</td><td>${alert.severity}</td><td>1</td>`;
        table.appendChild(row);
    });

    if (critAlertDetected) {
        invokeAlert();
        sendEmailAlert();
    }

    document.getElementById("alert-count").innerText = alerts.length;
    document.getElementById("critical-count").innerText = critical;
    document.getElementById("warning-count").innerText = warning;

    if (chart) chart.destroy();
    const ctx = document.getElementById('protocol-chart').getContext('2d');
    chart = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: Object.keys(protocolCounts),
            datasets: [{
                data: Object.values(protocolCounts),
                backgroundColor: ['#e74c3c', '#3498db', '#2ecc71', '#9b59b6', '#f39c12']
            }]
        },
        options: {
            animation: false,
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: isDarkMode ? '#fff' : '#333'
                    }
                },
                title: {
                    display: true,
                    text: 'Traffic by Protocol',
                    color: isDarkMode ? '#fff' : '#000',
                    font: { size: 22 }
                }
            }
        }
    });
    critAlertDetected = false; // Reset after processing
    window.scrollTo({ top: scrollY });      // Restore scroll position
}

async function loadMap() {
    if (!map) {
        map = L.map('map').setView([20, 0], 2);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);
    }
    mapMarkers.forEach(marker => map.removeLayer(marker));
    mapMarkers = [];

    const geoRes = await fetch(`${BASE_URL}/api/locations`);
    const geoData = await geoRes.json();
    geoData.forEach(loc => {
        const marker = L.circle([loc.lat, loc.lng], { radius: 40000 })
            .addTo(map)
            .bindPopup(`${loc.ip} (${loc.count} hits)`);
        mapMarkers.push(marker);
    });
}

async function sendEmailAlert() {
    try {
        const response = await fetch(`${BASE_URL}/api/send-email`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ subject: "Alert", body: "An alert has been triggered." })
        })
    } catch (error) {
        console.error("Error sending email:", error);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    console.log("✅ DOM ready. Initializing dashboard...");



    const socket = io(BASE_URL);


    const table = document.getElementById("threat-table");

    socket.on('connect', () => {
        console.log("✅ Connected to WebSocket server.");
    });

    socket.on('alert_batch', (batch) => {
        let parsedBatch = JSON.parse(batch);
        if (Object.keys(parsedBatch).length > 0) {
            for (const key in parsedBatch) {
                let currentKey = key;
                console.log(parsedBatch[key].length);
                let newRow = new TableRow(key, parsedBatch[key]);

                let renderedRow = newRow.render();

                renderedRow.addEventListener("click", () => {
                    console.log("Clicked row:", newRow.signature);
                    if (newRow.expanded) {
                        table.deleteRow(renderedRow.rowIndex);
                        newRow.expanded = false;
                    } else {
                        let emptyRow = table.insertRow(renderedRow.rowIndex);
                        emptyRow.innerHTML = `<td colspan="4">${newRow.subTable.outerHTML}</td>`;
                        newRow.expanded = true;
                    }
                });
                table.appendChild(renderedRow);
            }
            console.log(batch);
        }
    })

    //fetchDashboardData();
    loadMap();
    fetchMLAlerts();

    //setInterval(fetchDashboardData, 5000);
    setInterval(loadMap, 5000);
    setInterval(fetchMLAlerts, 5000);

    setInterval(() => {
        if (alertActive) {
            alertActive = false;
            clearAlert();
        }
    }, 5000);
});