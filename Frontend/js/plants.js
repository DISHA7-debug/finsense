/**
 * FinSense — Plant glow on click (no idle animation)
 */

document.addEventListener("DOMContentLoaded", () => {
    const scene = document.getElementById("plantScene");
    const plant = document.getElementById("moneyPlant");
    if (!scene || !plant) return;

    scene.addEventListener("click", () => {
        scene.classList.add("glowing");
        plant.classList.add("glowing");
        clearTimeout(scene._glowTimer);
        scene._glowTimer = setTimeout(() => {
            scene.classList.remove("glowing");
            plant.classList.remove("glowing");
        }, 1400);
    });
});
