// ==========================================
// FinSense Dashboard
// dashboard.js
// ==========================================

import {
    getDashboardSummary,
    getHighRisk,
    getAlerts
} from "./api.js";

import { renderTrendChart } from "./trendChart.js";

// ------------------------------------------
// DOM Elements
// ------------------------------------------

const greenCount = document.getElementById("greenCount");
const amberCount = document.getElementById("amberCount");
const orangeCount = document.getElementById("orangeCount");
const redCount = document.getElementById("redCount");

const alertCount = document.getElementById("alertCount");
const borrowerTable = document.getElementById("borrowerTable");

const searchBox = document.querySelector(".dash-search") || document.querySelector("input");

// Store fetched borrowers
let borrowers = [];

// ==========================================
// INITIALIZE DASHBOARD
// ==========================================

document.addEventListener("DOMContentLoaded", () => {

    loadDashboard();

});

// ==========================================
// MAIN LOADER
// ==========================================

async function loadDashboard() {

    try {

        await Promise.all([
            loadSummary(),
            loadBorrowers(),
            loadAlerts()
        ]);

    }

    catch (error) {

        console.error(error);

        alert("Unable to connect to FinSense API.");

    }

}

// ==========================================
// SUMMARY CARDS
// ==========================================

async function loadSummary() {

    const data = await getDashboardSummary();

    /*
        Expected API Response

        {
            green:3200,
            amber:950,
            orange:620,
            red:230,

            trend:[
                {month:"Jan",score:24},
                ...
            ]
        }

    */

    greenCount.textContent = data.green;
    amberCount.textContent = data.amber;
    orangeCount.textContent = data.orange;
    redCount.textContent = data.red;

    animateCounter(greenCount, data.green);
    animateCounter(amberCount, data.amber);
    animateCounter(orangeCount, data.orange);
    animateCounter(redCount, data.red);

    renderTrendChart(data.trend);

}

// ==========================================
// ALERTS
// ==========================================

async function loadAlerts() {

    const alerts = await getAlerts();

    alertCount.textContent = alerts.length;

}

// ==========================================
// HIGH RISK TABLE
// ==========================================

async function loadBorrowers() {

    borrowers = await getHighRisk();

    renderBorrowers(borrowers);

}

// ==========================================
// TABLE RENDER
// ==========================================

function renderBorrowers(data) {

    borrowerTable.innerHTML = "";

    data.forEach((loan) => {

        borrowerTable.innerHTML += `

        <tr class="transition" style="transition:background .2s" onmouseover="this.style.background='rgba(234,224,207,0.6)'" onmouseout="this.style.background=''">

            <td class="font-semibold">

                ${loan.borrower_name}

            </td>

            <td>

                ${loan.loan_type}

            </td>

            <td>

                ₹${Number(loan.outstanding_balance).toLocaleString()}

            </td>

            <td>

                ${loan.score.toFixed(1)}

            </td>

            <td>

                ${tierBadge(loan.tier)}

            </td>

            <td>

                <button
                    class="btn-dash btn-dash-primary"
                    onclick="openBorrower('${loan.loan_id}')">

                    View

                </button>

            </td>

        </tr>

        `;

    });

}

// ==========================================
// TIER BADGE
// ==========================================

function tierBadge(tier) {

    const t = tier.toLowerCase();

    return `
        <span class="badge ${t}">
            ${tier.toUpperCase()}
        </span>
    `;

}

// ==========================================
// SEARCH
// ==========================================

if (searchBox) {
searchBox.addEventListener("keyup", function () {

    const keyword = this.value.toLowerCase();

    const filtered = borrowers.filter((loan) => {

        return (

            loan.borrower_name
                .toLowerCase()
                .includes(keyword)

            ||

            loan.loan_type
                .toLowerCase()
                .includes(keyword)

        );

    });

    renderBorrowers(filtered);

});
}

// ==========================================
// COUNTER ANIMATION
// ==========================================

function animateCounter(element, target) {

    let current = 0;

    const increment = Math.ceil(target / 50);

    const timer = setInterval(() => {

        current += increment;

        if (current >= target) {

            current = target;

            clearInterval(timer);

        }

        element.textContent = current;

    }, 20);

}

// ==========================================
// NAVIGATION
// ==========================================

window.openBorrower = function (loanId) {

    window.location.href =
        `borrower.html?loan=${loanId}`;

};

// ==========================================
// AUTO REFRESH EVERY 30 SECONDS
// ==========================================

setInterval(() => {

    loadDashboard();

}, 30000);
