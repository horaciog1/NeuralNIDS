export class TableRow {
    constructor(signature, alerts) {
        this.signature = signature;
        this.alerts = alerts;
    }

    render() {
        const row = document.createElement("tr");
        row.innerHTML = `<td></td><td>${this.signature}</td><td></td><td>${this.alerts.length}</td>`;

        // this.data.forEach(cellData => {
        // const cell = document.createElement('td');
        // cell.textContent = cellData;
        // row.appendChild(cell);
        // });
        return row;
    }
}