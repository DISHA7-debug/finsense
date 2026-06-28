// =========================================
// FinSense Borrower Detail Controller
// borrower.js
// =========================================

import {
    getLoanDetail,
    getLoanRisk,
    rescoreLoan
} from "./api.js";

import { drawRiskGauge } from "./riskGauge.js";
import { renderShapBars } from "./shapBar.js";
import { renderTrendChart } from "./trendChart.js";
import { initializeAgent } from "./agent.js";

initializeAgent(loanId);

// -------------------------------------
// Get Loan ID from URL
// borrower.html?loan=101
// -------------------------------------

const params = new URLSearchParams(window.location.search);
const loanId = params.get("loan");

// -------------------------------------
// Buttons
// -------------------------------------

const rescoreBtn = document.getElementById("rescoreBtn");
const chatBtn = document.getElementById("chatBtn");

// -------------------------------------
// Load Everything
// -------------------------------------

document.addEventListener("DOMContentLoaded", () => {

    if (!loanId) {

        alert("Loan ID missing.");

        window.location.href = "dashboard.html";

        return;

    }

    loadBorrower();

});

// =====================================
// Main Loader
// =====================================

async function loadBorrower() {

    try {

        //------------------------------------------------
        // Load Detail + Risk simultaneously
        //------------------------------------------------

        const [detail, risk] = await Promise.all([

            getLoanDetail(loanId),

            getLoanRisk(loanId)

        ]);

        populateBorrower(detail);

        drawRiskGauge(risk.score);

        renderShapBars(risk.shap_factors);

        renderTrendChart(risk.history);

    }

    catch (err) {

        console.error(err);

        alert("Unable to load borrower.");

    }

}

// =====================================
// Populate Borrower Information
// =====================================

function populateBorrower(data) {

    document.getElementById("borrowerName").textContent =
        data.borrower_name;

    document.getElementById("loanType").textContent =
        data.loan_type;

    document.getElementById("loanId").textContent =
        data.loan_id;

    document.getElementById("balance").textContent =
        "₹" + Number(data.outstanding_balance).toLocaleString();

    document.getElementById("emi").textContent =
        "₹" + Number(data.emi).toLocaleString();

    document.getElementById("interest").textContent =
        data.interest_rate + "%";

    document.getElementById("tenure").textContent =
        data.remaining_tenure + " Months";

    //---------------------------------------

    document.getElementById("income").textContent =
        "₹" + Number(data.monthly_income).toLocaleString();

    document.getElementById("employment").textContent =
        data.employment;

    document.getElementById("city").textContent =
        data.city;

    document.getElementById("credit").textContent =
        data.credit_score;

    document.getElementById("updated").textContent =
        new Date(data.updated_at).toLocaleDateString();

}

// =====================================
// Manual Re-Score
// =====================================

rescoreBtn.addEventListener("click", async () => {

    try {

        rescoreBtn.disabled = true;

        rescoreBtn.innerHTML = `
        <i class="ri-loader-4-line animate-spin"></i>
        Re-Scoring...
        `;

        await rescoreLoan(loanId);

        await loadBorrower();

        rescoreBtn.innerHTML = `
        <i class="ri-check-line"></i>
        Updated
        `;

        setTimeout(() => {

            rescoreBtn.innerHTML = `
            <i class="ri-refresh-line"></i>
            Re-Score
            `;

            rescoreBtn.disabled = false;

        }, 1500);

    }

    catch (err) {

        console.error(err);

        alert("Unable to re-score borrower.");

        rescoreBtn.disabled = false;

        rescoreBtn.innerHTML = `
        <i class="ri-refresh-line"></i>
        Re-Score
        `;

    }

});

// =====================================
// AI Agent
// =====================================

chatBtn.addEventListener("click", () => {

    window.location.href =
        `agent.html?loan=${loanId}`;

});

// =====================================
// Auto Refresh Every 30 Seconds
// =====================================

setInterval(() => {

    loadBorrower();

}, 30000);