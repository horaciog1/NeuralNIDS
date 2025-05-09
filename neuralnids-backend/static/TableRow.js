export class TableRow {
    constructor(signature, alerts) {
        this.signature = signature;
        this.alerts = alerts;
        this.subRows = [];
        this.expanded = false;
        this.subTable = document.createElement("table");
    }

    render(table) {
        const row = document.createElement("tr");
        row.innerHTML = `<td>${this.signature}</td><td>${this.alerts.length}</td>`;

        let header = this.subTable.insertRow();
        header.innerHTML = `<th>Timestamp</th><th>IP Address</th><th>Severity</th>`;


        this.alerts.forEach((alert) => {
            const subRow = document.createElement("tr");
            subRow.innerHTML = `<td>${formatTimestamp(alert["timestamp"])}</td><td>${alert["src_ip"]}</td><td>${alert["alert"]["severity"]}</td>`;
            this.subTable.appendChild(subRow);
        });

        row.addEventListener("click", () => {
            console.log("Clicked row:", this.signature);
            if (this.expanded) {
                table.deleteRow(row.rowIndex);
                this.expanded = false;
            } else {
                let emptyRow = table.insertRow(row.rowIndex);
                emptyRow.innerHTML = `<td colspan="4">${this.subTable.outerHTML}</td>`;
                this.expanded = true;
            }
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