import { invokeAlert, clearAlert } from "./notification.js";
import { TableRow } from "./TableRow.js";

let isDarkMode = false;
let chart;
let map;
let mapMarkers = [];
let alertActive = false;

const BASE_URL = "http://10.10.10.100:5000"; // Change this when you need to change all URLs
const socket = io(BASE_URL);
let alertCount = 0, critical = 0, warning = 0;
let protocolCounts = {};

let previousMLTimestamps = new Set();  // Keep track of unique timestamps

/**
 * Fetches machine learning alerts from a remote API, processes the data to filter out previously seen alerts,
 * and updates the corresponding table in the DOM with the latest alerts.
 * The table is cleared and updated to display only the 10 most recent alerts.
 * If no new alerts are found, a message is displayed in the table.
 *
 * @return {Promise<void>} A promise that resolves when the alerts have been fetched, processed, and rendered in the DOM.
 * The function logs errors to the console if the fetch operation fails or if issues occur during processing.
 */
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

/**
 * Toggles the dark mode by adding or removing the 'dark-mode' class from the document body.
 * Persists the user's choice in local storage and updates the chart to match the current mode.
 *
 * @return {void} Does not return a value.
 */
function toggleDarkMode() {
    // Toggle the class and persist the choice
    const isDark = document.body.classList.toggle('dark-mode');
    localStorage.setItem('dark-mode', isDark ? 'enabled' : 'disabled');

    // Keep chart in sync
    isDarkMode = isDark;
    if (chart) {
        chart.options.plugins.title.color = isDark ? '#fff' : '#000';
        chart.options.plugins.legend.labels.color = isDark ? '#fff' : '#333';
        chart.update();
    }
}

// Expose globally
window.toggleDarkMode = toggleDarkMode;

/**
 * Fetches and processes data required to populate the dashboard, including threat alerts
 * and protocol distribution. Updates the UI elements accordingly such as tables and charts.
 * Handles critical alerts by invoking necessary notifications and resets state post-processing.
 *
 * @return {Promise<void>} A promise that resolves when the dashboard data is successfully fetched
 * and UI updates are completed.
 */
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

    if (critAlertDetected) {
        invokeAlert();
        sendEmailAlert();
    }

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

/**
 * Loads and initializes the map view with markers based on location data retrieved from an API.
 * If the map has not been initialized, it creates the map, sets its view, and applies a tile layer.
 * It then clears existing markers, fetches location data, and adds new markers to the map.
 *
 * @return {Promise<void>} A promise that resolves when the map and markers have been loaded completely.
 */
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

/**
 * Sends an email alert containing a list of alert details.
 *
 * @param {Array<Object>} alerts - An array of alert objects containing details such as timestamp, source IP, signature, and severity of each alert.
 * @return {Promise<void>} A promise that resolves when the email alert is successfully sent or logs an error if the process fails.
 */
async function sendEmailAlert(alerts) {
    let alertString = "";
    alerts.forEach(alert => {
        alertString += `\n${alert.timestamp} - ${alert["src_ip"]} - ${alert.signature} - ${alert.severity}`;
    });
    try {
        const response = await fetch(`${BASE_URL}/api/send-email`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ subject: "Alert", body: alertString })
        })
    } catch (error) {
        console.error("Error sending email:", error);
    }
}

/**
 * Initializes the dashboard once the DOM has fully loaded.
 * This function:
 * - Loads and applies the user's dark mode preference from local storage.
 * - Logs a confirmation message to the console when the DOM is ready.
 * - Establishes a WebSocket connection and logs its status.
 * - Initializes data structures for protocol counting.
 * - Loads the initial map view and machine learning alerts.
 * - Sets recurring intervals to refresh the map and ML alerts every 5 seconds.
 * - Sets a recurring interval to automatically clear active alerts every 5 seconds if applicable.
 *
 * @return {void} This function runs automatically after the DOM is ready and performs initialization side effects.
 */
document.addEventListener("DOMContentLoaded", () => {
    // load dark-mode preference
    if (localStorage.getItem("dark-mode") === "enabled") {
        document.body.classList.add("dark-mode");
        isDarkMode = true;
    }

    console.log("✅ DOM ready. Initializing dashboard...");

    socket.on('connect', () => {
        console.log("✅ Connected to WebSocket server.");
    });

    protocolCounts = {};

    loadMap();
    fetchMLAlerts();

    setInterval(loadMap, 5000);
    setInterval(fetchMLAlerts, 5000);

    setInterval(() => {
        if (alertActive) {
            alertActive = false;
            clearAlert();
        }
    }, 5000);
});

/**
 * Handles incoming alert batches received via a WebSocket event ('alert_batch').
 * This function:
 * - Parses the incoming JSON batch of alerts.
 * - Invokes a UI alert notification to inform the user of new threats.
 * - Iterates over each alert key and its associated alerts:
 *    - Creates and appends a new table row for the alerts.
 *    - Updates global counters for total alerts, critical alerts, and warnings.
 *    - Updates the protocol count histogram.
 * - Updates the dashboard's alert counters displayed in the UI.
 * - Regenerates the protocol pie chart to reflect updated protocol counts.
 * - Logs the parsed alert batch and individual alerts to the console for debugging.
 *
 * @param {string} batch - A JSON string representing a batch of alerts grouped by a key (e.g., timestamp or source IP).
 * @return {void} This function updates the DOM and internal state in response to receiving new alerts.
 */
socket.on('alert_batch', (batch) => {
    const table = document.getElementById("threat-table");
    let parsedBatch = JSON.parse(batch);
    if (Object.keys(parsedBatch).length > 0) {
        invokeAlert();
        alertActive = true;
        for (const key in parsedBatch) {
            let individualAlerts = parsedBatch[key];
            //sendEmailAlert(individualAlerts);

            let newRow = new TableRow(key, individualAlerts);
            let renderedRow = newRow.render(table);
            table.appendChild(renderedRow);

            individualAlerts.forEach(alert => {
                console.log(alert);
                alertCount++;
                if (alert["alert"]["severity"] <= 2) {
                    critical++;
                } else {
                    warning++;
                }
                const proto = alert["app_proto"] || 'Unknown';
                protocolCounts[proto] = (protocolCounts[proto] || 0) + 1;
            });
        }

        document.getElementById("alert-count").innerText = alertCount;
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
        console.log(batch);
    }
});
