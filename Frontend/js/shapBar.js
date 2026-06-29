// =========================================
// FinSense SHAP Explainability Panel
// shapBar.js
// =========================================

export function renderShapBars(factors) {

    const container = document.getElementById("shapBars");

    if (!container) return;

    container.innerHTML = "";

    if (!factors || factors.length === 0) {

        container.innerHTML = `
            <div class="text-center text-gray-500 py-10">
                No SHAP explanation available.
            </div>
        `;

        return;
    }

    // ---------------------------------------
    // Maximum impact
    // ---------------------------------------

    const maxImpact = Math.max(
        ...factors.map(f => Math.abs(f.impact))
    );

    // ---------------------------------------
    // Sort largest contributors first
    // ---------------------------------------

    factors.sort((a, b) =>
        Math.abs(b.impact) - Math.abs(a.impact)
    );

    // ---------------------------------------
    // Render Bars
    // ---------------------------------------

    factors.forEach((factor, index) => {

        const percentage =
            (Math.abs(factor.impact) / maxImpact) * 100;

        const isRisk =
            factor.direction === "increasing_risk";

        const color = isRisk
            ? "#dc2626"
            : "#16a34a";

        const sign = isRisk ? "+" : "-";

        const row = document.createElement("div");

        row.className =
            "mb-5 opacity-0 translate-y-4 transition-all duration-500";

        row.innerHTML = `

<div class="flex justify-between items-center mb-2">

    <div>

        <h4 class="font-semibold text-gray-700">

            ${factor.human_label}

        </h4>

    </div>

    <div
        class="font-bold"
        style="color:${color}">

        ${sign}${Math.round(Math.abs(factor.impact) * 100)}

    </div>

</div>

<div
class="w-full bg-gray-200 rounded-full overflow-hidden h-4">

    <div

        class="rounded-full h-4"

        style="
            width:0%;
            background:${color};
            transition:width 1s ease;
        "

    ></div>

</div>

`;

        container.appendChild(row);

        //--------------------------------------
        // Animate
        //--------------------------------------

        setTimeout(() => {

            row.classList.remove("opacity-0");
            row.classList.remove("translate-y-4");

            row.querySelector("div div").style.width =
                percentage + "%";

        }, index * 150);

    });

}