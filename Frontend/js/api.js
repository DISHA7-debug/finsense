// ============================================
// FinSense API Client
// js/api.js
// ============================================

const API_BASE = "http://localhost:8000/api";

/*------------------------------------------
Dashboard
------------------------------------------*/

export async function getDashboardSummary() {
    const response = await fetch(`${API_BASE}/dashboard/summary`);

    if (!response.ok)
        throw new Error("Failed to fetch dashboard summary");

    return await response.json();
}

export async function getHighRisk(tiers = "orange,red", limit = 20) {

    const response = await fetch(
        `${API_BASE}/dashboard/high-risk?tier=${tiers}&limit=${limit}`
    );

    if (!response.ok)
        throw new Error("Failed to fetch high risk borrowers");

    return await response.json();
}

/*------------------------------------------
Risk
------------------------------------------*/

export async function getLoanRisk(loanId) {

    const response = await fetch(
        `${API_BASE}/risk/${loanId}`
    );

    if (!response.ok)
        throw new Error("Unable to fetch risk score");

    return await response.json();
}

export async function rescoreLoan(loanId) {

    const response = await fetch(
        `${API_BASE}/risk/${loanId}/score`,
        {
            method: "POST"
        }
    );

    if (!response.ok)
        throw new Error("Unable to rescore borrower");

    return await response.json();
}

/*------------------------------------------
Loan Details
------------------------------------------*/

export async function getLoanDetail(loanId) {

    const response = await fetch(
        `${API_BASE}/loans/${loanId}`
    );

    if (!response.ok)
        throw new Error("Unable to fetch loan details");

    return await response.json();
}

/*------------------------------------------
Alerts
------------------------------------------*/

export async function getAlerts() {

    const response = await fetch(
        `${API_BASE}/dashboard/alerts`
    );

    if (!response.ok)
        throw new Error("Unable to fetch alerts");

    return await response.json();
}

export async function markAlertRead(alertId) {

    const response = await fetch(
        `${API_BASE}/dashboard/alerts/${alertId}/read`,
        {
            method: "PATCH"
        }
    );

    if (!response.ok)
        throw new Error("Unable to mark alert");

    return await response.json();
}

/*------------------------------------------
AI Agent
------------------------------------------*/

export async function startAgentConversation(
    loanId,
    channel = "in_app"
) {

    const response = await fetch(
        `${API_BASE}/agent/${loanId}/start`,
        {
            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                channel
            })
        }
    );

    if (!response.ok)
        throw new Error("Unable to start conversation");

    return await response.json();
}

export async function sendAgentMessage(
    loanId,
    conversationId,
    message
) {

    const response = await fetch(
        `${API_BASE}/agent/${loanId}/message`,
        {
            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                conversation_id: conversationId,
                message: message
            })
        }
    );

    if (!response.ok)
        throw new Error("Unable to send message");

    return await response.json();
}