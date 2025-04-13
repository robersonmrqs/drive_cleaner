function checkProgress() {
    fetch("/progress")
        .then(response => response.json())
        .then(data => {
            const percent = data.percent;
            const current = data.current;
            const total = data.total;

            document.getElementById("progress-bar").style.width = percent + "%";
            document.getElementById("progress-text").innerText = `${current} / ${total} arquivos (${percent}%)`;

            if (percent < 100) {
                setTimeout(checkProgress, 1000);
            }
        });
}

document.addEventListener("DOMContentLoaded", () => {
    if (document.getElementById("progress-bar")) {
        checkProgress();
    }
});