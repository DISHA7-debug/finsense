// =========================================
// FinSense Risk Gauge
// riskGauge.js
// =========================================

export function drawRiskGauge(score) {

    const gauge = document.getElementById("riskGauge");

    if (!gauge) return;

    gauge.innerHTML = "";

    //--------------------------------------------------
    // Configuration
    //--------------------------------------------------

    const size = 260;
    const stroke = 18;
    const radius = 95;
    const circumference = Math.PI * radius;

    //--------------------------------------------------
    // Tier
    //--------------------------------------------------

    let color = "#16a34a";
    let label = "Healthy";

    if (score > 75) {
        color = "#dc2626";
        label = "Pre-Default";
    }
    else if (score > 55) {
        color = "#ea580c";
        label = "High Risk";
    }
    else if (score > 30) {
        color = "#d97706";
        label = "Early Stress";
    }

    //--------------------------------------------------
    // HTML
    //--------------------------------------------------

    gauge.innerHTML = `

<div class="flex flex-col items-center">

<svg
width="${size}"
height="170"
viewBox="0 0 220 140">

<defs>

<linearGradient id="riskGradient">

<stop offset="0%" stop-color="${color}"/>

<stop offset="100%" stop-color="${color}"/>

</linearGradient>

<filter id="glow">

<feGaussianBlur stdDeviation="4" result="coloredBlur"/>

<feMerge>

<feMergeNode in="coloredBlur"/>

<feMergeNode in="SourceGraphic"/>

</feMerge>

</filter>

</defs>

<!-- Background -->

<path
d="M20 110 A90 90 0 0 1 200 110"
fill="none"
stroke="#e5e7eb"
stroke-width="${stroke}"
stroke-linecap="round"/>

<!-- Progress -->

<path
id="progressArc"
d="M20 110 A90 90 0 0 1 200 110"
fill="none"
stroke="url(#riskGradient)"
stroke-width="${stroke}"
stroke-linecap="round"
filter="url(#glow)"
stroke-dasharray="${circumference}"
stroke-dashoffset="${circumference}"/>

<!-- Needle -->

<line
id="needle"
x1="110"
y1="110"
x2="110"
y2="30"
stroke="${color}"
stroke-width="5"
stroke-linecap="round"/>

<circle
cx="110"
cy="110"
r="9"
fill="${color}"/>

</svg>

<div
id="riskValue"
class="text-5xl font-bold mt-2"
style="color:${color};">

0

</div>

<div
class="mt-3 px-6 py-2 rounded-full text-white font-semibold"
style="background:${color};">

${label}

</div>

</div>

`;

    //--------------------------------------------------
    // Animation
    //--------------------------------------------------

    const arc = document.getElementById("progressArc");
    const needle = document.getElementById("needle");
    const value = document.getElementById("riskValue");

    let current = 0;

    const animation = setInterval(() => {

        current++;

        if (current > score) {

            clearInterval(animation);

            return;

        }

        //-----------------------------------------
        // Arc
        //-----------------------------------------

        const progress = current / 100;

        arc.style.strokeDashoffset =
            circumference - progress * circumference;

        //-----------------------------------------
        // Needle Rotation
        //-----------------------------------------

        const angle = -90 + (180 * progress);

        needle.setAttribute(
            "transform",
            `rotate(${angle} 110 110)`
        );

        //-----------------------------------------
        // Counter
        //-----------------------------------------

        value.innerHTML = current;

    }, 15);

}