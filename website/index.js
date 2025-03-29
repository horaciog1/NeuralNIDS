let isDarkMode = false;
let chart;
let map;
let mapMarkers = [];

function toggleDarkMode() {
    document.body.classList.toggle('dark-mode');
    isDarkMode = !isDarkMode;
    if (chart) {
        chart.options.plugins.title.color = isDarkMode ? '#fff' : '#000';
        chart.options.plugins.legend.labels.color = isDarkMode ? '#fff' : '#333';
        chart.update();
    }
}

function formatTimestamp(ts) {
    const d = new Date(ts);
    const date = d.toLocaleDateString("en-US");
    const time = d.toLocaleTimeString("en-US", { hour12: false });
    return `${date} ${time}`;
}

async function fetchDashboardData() {
    const scrollY = window.scrollY;       // Save scroll position
    const alertRes = await fetch('http://192.168.1.214:5000/api/alerts');
    const alerts = await alertRes.json();

    const protocolCounts = {};
    let alertCount = 0, critical = 0, warning = 0;

    const table = document.getElementById("threat-table");
    table.innerHTML = "";

    const recentAlerts = alerts.slice(-8).reverse();

    recentAlerts.forEach(alert => {
        alertCount++;
        if (alert.severity <= 2) critical++;
        else warning++;

        const proto = alert.protocol || 'Unknown';
        protocolCounts[proto] = (protocolCounts[proto] || 0) + 1;

        const conciseSig = alert.signature?.split("[")[0]?.trim() || "-";
        const row = document.createElement("tr");
        row.innerHTML = `<td>${formatTimestamp(alert.timestamp)}</td><td>${conciseSig}</td><td>${alert.severity}</td><td>1</td>`;
        table.appendChild(row);
    });

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
    window.scrollTo({ top: scrollY });      // Restore scroll position
}

async function loadMap() {
    if (!map) {
        map = L.map('map').setView([20, 0], 2);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);
    }
    mapMarkers.forEach(marker => map.removeLayer(marker));
    mapMarkers = [];

    const geoRes = await fetch('http://192.168.1.221:5000/api/locations');
    const geoData = await geoRes.json();
    geoData.forEach(loc => {
        const marker = L.circle([loc.lat, loc.lng], { radius: 40000 })
            .addTo(map)
            .bindPopup(`${loc.ip} (${loc.count} hits)`);
        mapMarkers.push(marker);
    });
}

fetchDashboardData();
loadMap();
setInterval(() => {
    fetchDashboardData();
    loadMap();
}, 5000);