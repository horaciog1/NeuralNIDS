export class TableRow {
    constructor(signature, alerts) {
        this.signature = signature;
        this.alerts = alerts;
        this.subRows = [];
        this.expanded = false;
        this.subTable = document.createElement("table");
    }

    render() {
        const row = document.createElement("tr");
        row.innerHTML = `<td>${this.signature}</td><td>${this.alerts.length}</td>`;

        let header = this.subTable.insertRow();
        header.innerHTML = `<th>Timestamp</th><th>IP Address</th><th>Severity</th>`;


        this.alerts.forEach((alert) => {
            const subRow = document.createElement("tr");
            subRow.innerHTML = `<td>${formatTimestamp(alert["timestamp"])}</td><td>${alert["src_ip"]}</td><td>${alert["alert"]["severity"]}</td>`;
            this.subTable.appendChild(subRow);
        });
        return row;
    }
}

function formatTimestamp(ts) {
    const d = new Date(ts);
    const date = d.toLocaleDateString("en-US");
    const time = d.toLocaleTimeString("en-US", { hour12: false });
    return `${date} ${time}`;
}