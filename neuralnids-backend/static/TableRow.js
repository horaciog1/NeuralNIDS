export class TableRow {
    constructor(signature, alerts) {
        this.signature = signature;
        this.alerts = alerts;
        this.subRows = [];
    }

    render() {
        const row = document.createElement("tr");
        row.innerHTML = `<td></td><td>${this.signature}</td><td></td><td>${this.alerts.length}</td>`;



        this.alerts.forEach((alert) => {
            const subRow = document.createElement("tr");
            subRow.innerHTML = `<td>${formatTimestamp(alert["timestamp"])}</td><td>${this.signature}</td><td>${alert["alert"]["severity"]}</td><td>1</td>`
            subRow.style.backgroundColor = "darkgray";
            this.subRows.push(subRow);
        });


        // this.data.forEach(cellData => {
        // const cell = document.createElement('td');
        // cell.textContent = cellData;
        // row.appendChild(cell);
        // });
        return row;
    }
}

function formatTimestamp(ts) {
    const d = new Date(ts);
    const date = d.toLocaleDateString("en-US");
    const time = d.toLocaleTimeString("en-US", { hour12: false });
    return `${date} ${time}`;
}