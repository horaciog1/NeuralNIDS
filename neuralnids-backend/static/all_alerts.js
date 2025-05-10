const BASE_URL = "http://10.10.10.100:5000";

/**
 * Converts a given timestamp into a formatted string representation of date and time.
 *
 * @param {number|string|Date} ts - The timestamp to be formatted. It can be a number representing milliseconds since the Unix epoch,
 *                                   a date string, or a Date object.
 * @return {string} A formatted string containing the date and time in "MM/DD/YYYY HH:mm:ss" format.
 */
function formatTimestamp(ts) {
    const d = new Date(ts);
    const date = d.toLocaleDateString("en-US");
    const time = d.toLocaleTimeString("en-US", { hour12: false });
    return `${date} ${time}`;
}

/**
 * Fetches all alerts from the API, processes the data, and dynamically populates the "all-alerts-table" HTML table with the retrieved information.
 *
 * @return {Promise<void>} A promise that resolves once the data has been fetched, processed, and the table has been updated.
 */
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

/**
 * The `window.onload` event is triggered when the entire DOM, along with all dependent resources (such as stylesheets, images, and subframes), has fully loaded.
 * This property can be assigned a function to execute custom logic or initialization after the page load is complete.
 *
 * Assigning a function to `window.onload` will replace any previously assigned functions.
 * To allow multiple functions to run on load, consider using `addEventListener` with the `load` event.
 */
window.onload = () => {
    if (localStorage.getItem("dark-mode") === "enabled") {
        document.body.classList.add("dark-mode");
    }
};

/**
 * Toggles the dark mode for the application by adding or removing the 'dark-mode' class
 * on the document body. The state is persisted in the local storage to retain the user's choice.
 *
 * @return {void} Does not return a value.
 */
function toggleDarkMode() {
    const isDark = document.body.classList.toggle('dark-mode');
    localStorage.setItem("dark-mode", isDark ? "enabled" : "disabled");
}


loadAllAlerts();
