// =========================================
// FinSense Trend Chart
// trendChart.js
// =========================================

let chart = null;

export function renderTrendChart(history) {

    const canvas = document.getElementById("trendChart");

    if (!canvas) return;

    const ctx = canvas.getContext("2d");

    // Destroy previous chart before creating a new one
    if (chart) {
        chart.destroy();
    }

    chart = new Chart(ctx, {

        type: "line",

        data: {

            labels: history.map(item => item.month),

            datasets: [

                {
                    label: "Portfolio Risk",
                    data: history.map(item => item.score),
                    borderColor: "#4B5694",
                    backgroundColor: "rgba(75, 86, 148, 0.2)",
                    borderWidth: 3,
                    pointRadius: 5,
                    pointHoverRadius: 8,
                    pointBackgroundColor: "#7288AE",
                    pointBorderColor: "#111844",
                    pointBorderWidth: 2,
                    fill: true,
                    tension: 0.45
                },

                {
                    label: "High Risk Count",
                    data: history.map(item => item.high_risk ?? item.score * 0.6),
                    borderColor: "#111844",
                    backgroundColor: "rgba(17, 24, 68, 0.08)",
                    borderWidth: 3,
                    pointRadius: 0,
                    pointHoverRadius: 6,
                    fill: true,
                    tension: 0.45
                }

            ]

        },

        options: {

            responsive: true,

            maintainAspectRatio: false,

            animation: {

                duration: 1500,

                easing: "easeOutQuart"

            },

            interaction: {

                mode: "index",

                intersect: false

            },

            plugins: {

                legend: {

                    display: false

                },

                tooltip: {

                    backgroundColor: "#111844",

                    titleColor: "#ffffff",

                    bodyColor: "#ffffff",

                    padding: 14,

                    displayColors: false,

                    callbacks: {

                        label: function(context){

                            return `Risk Score : ${context.raw}`;

                        }

                    }

                }

            },

            scales: {

                x: {

                    grid: {

                        display: false

                    },

                    ticks: {

                        color: "#4B5694",

                        font: {

                            size: 13,

                            weight: "600"

                        }

                    }

                },

                y: {

                    min: 0,

                    max: 100,

                    ticks: {

                        stepSize: 10,

                        color: "#7288AE"

                    },

                    grid: {

                        color: "rgba(114, 136, 174, 0.25)"

                    }

                }

            }

        },

        plugins: [

            riskZonesPlugin

        ]

    });

}

// =========================================
// Draw Colored Risk Zones
// =========================================

const riskZonesPlugin = {

    id: "riskZones",

    beforeDraw(chart) {

        const {

            ctx,

            chartArea,

            scales

        } = chart;

        const y = scales.y;

        if (!chartArea) return;

        ctx.save();

        drawZone(0,30,"rgba(22,163,74,0.08)");
        drawZone(30,55,"rgba(245,158,11,0.08)");
        drawZone(55,75,"rgba(249,115,22,0.08)");
        drawZone(75,100,"rgba(220,38,38,0.08)");

        function drawZone(start,end,color){

            const top = y.getPixelForValue(end);

            const bottom = y.getPixelForValue(start);

            ctx.fillStyle = color;

            ctx.fillRect(

                chartArea.left,

                top,

                chartArea.right-chartArea.left,

                bottom-top

            );

        }

        ctx.restore();

    }

};