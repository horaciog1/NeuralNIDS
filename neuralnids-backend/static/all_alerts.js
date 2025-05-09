const BASE_URL = "http://10.10.10.100:5000";

function formatTimestamp(ts) {
    const d = new Date(ts);
    const date = d.toLocaleDateString("en-US");
    const time = d.toLocaleTimeString("en-US", { hour12: false });
    return `${date} ${time}`;
}

async function loadAllAlerts() {
    const res = await fetch(`${BASE_URL}/api/alerts`);
    const alerts = await res.json();
    const table = document.getElementById("all-alerts-table");

    alerts.reverse().forEach(alert => {
        const conciseSig = alert.signature?.split("[")[0]?.trim() || "-";
        const row = document.createElement("tr");
        row.innerHTML = `
            <td>${formatTimestamp(alert.timestamp)}</td>
            <td>${conciseSig}</td>
            <td>${alert.severity}</td>
            <td>1</td>
        `;
        table.appendChild(row);
    });
}

window.onload = () => {
    if (localStorage.getItem("dark-mode") === "enabled") {
        document.body.classList.add("dark-mode");
    }
};

function toggleDarkMode() {
    const isDark = document.body.classList.toggle('dark-mode');
    localStorage.setItem("dark-mode", isDark ? "enabled" : "disabled");
}


loadAllAlerts();
