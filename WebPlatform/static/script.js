const btnHeadful = document.getElementById("btn-headful");
const btnHeadless = document.getElementById("btn-headless");
const statusMsg = document.getElementById("status-msg");
const progressBar = document.getElementById("progress-bar");
const progressFill = document.getElementById("progress-fill");
const botName = document.getElementById('bot-select').value;

async function executeBot(mode) {
    btnHeadful.disabled = true;
    btnHeadless.disabled = true;
    statusMsg.textContent = "Starting...";

    if (mode === "Headless") {
        progressBar.classList.remove("hidden");
        progressFill.style.width = "0%";
    }

    try {
        const response = await fetch("/api/run", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ bot_name: botName, mode: mode }),
        });

        const result = await response.json();
        if (!response.ok) throw new Error(result.message || "Error");
        
        const interval = setInterval(async () => {
            try {
                const progRes = await fetch("/api/progress");
                const data = await progRes.json();
                
                if (mode === "Headless") {
                    progressFill.style.width = data.value + "%";
                    progressFill.textContent = data.value + "%";
                } else {
                    statusMsg.textContent = `Running... (${data.value}%)`;
                }
                
                if (data.status === "done") {
                    clearInterval(interval);
                    statusMsg.textContent = "Run completed! Refreshing page...";
                    setTimeout(() => { window.location.reload(); }, 1000);
                }
            } catch (e) {
                clearInterval(interval);
            }
        }, 1000);

    } catch (error) {
        statusMsg.textContent = "Error: " + error.message;
        btnHeadful.disabled = false;
        btnHeadless.disabled = false;
        progressBar.classList.add("hidden");
    }
}

btnHeadful.addEventListener("click", () => executeBot("Headful"));
btnHeadless.addEventListener("click", () => executeBot("Headless"));