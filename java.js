```javascript
const API_URL = "http://127.0.0.1:8000";

const altitude = document.querySelector("#altitude");
const inclination = document.querySelector("#inclination");
const duration = document.querySelector("#duration");

const altitudeValue =
    document.querySelector("#altitudeValue");

const inclinationValue =
    document.querySelector("#inclinationValue");

const simulateBtn =
    document.querySelector("#simulateBtn");

const simulationStatus =
    document.querySelector("#simulationStatus");

const objectsAnalyzed =
    document.querySelector("#objectsAnalyzed");

const riskResult =
    document.querySelector("#riskResult");

const simulationMessage =
    document.querySelector("#simulationMessage");

const eventLog =
    document.querySelector("#eventLog");


function updateControls() {
    altitudeValue.textContent = `${altitude.value} km`;
    inclinationValue.textContent = `${inclination.value}°`;
}


function addLog(message) {
    const item = document.createElement("li");

    item.textContent =
        `${new Date().toLocaleTimeString()} — ${message}`;

    eventLog.prepend(item);
}


altitude.addEventListener("input", updateControls);

inclination.addEventListener("input", updateControls);


simulateBtn.addEventListener("click", async () => {

    simulateBtn.disabled = true;

    simulationStatus.textContent = "Connecting...";
    riskResult.textContent = "Not calculated";

    simulationMessage.textContent =
        "Sending mission settings to the backend...";

    addLog("Demo simulation requested.");

    try {

        const response = await fetch(
            `${API_URL}/simulate`,
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    altitude_km: Number(altitude.value),
                    inclination_deg: Number(inclination.value),
                    duration_hours: Number(duration.value)
                })
            }
        );

        const result = await response.json();

        if (!response.ok) {
            throw new Error(
                JSON.stringify(result.detail || response.status)
            );
        }

        simulationStatus.textContent = "Completed (Demo)";

        objectsAnalyzed.textContent =
            result.objects_analyzed;

        riskResult.textContent =
            result.risk_level;

        simulationMessage.textContent =
            result.message;

        addLog("Backend returned a demo response.");

    } catch (error) {

        simulationStatus.textContent = "API unavailable";

        objectsAnalyzed.textContent = "—";

        riskResult.textContent = "Not calculated";

        simulationMessage.textContent =
            "Backend connect nahi hua. Python server start karein.";

        addLog(`Request failed: ${error.message}`);

        console.error(error);

    } finally {

        simulateBtn.disabled = false;

    }
});


updateControls();
```
