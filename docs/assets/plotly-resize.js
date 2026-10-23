// Size newly visible plots before painting. Plots.resize waits 100 ms.
function resizeVisiblePlots(container) {
    if (!window.Plotly) return;
    container.querySelectorAll(".js-plotly-plot").forEach(plot => {
        if (plot._fullLayout && plot.clientWidth > 0 && plot.clientHeight > 0) {
            window.Plotly.relayout(plot, { autosize: true });
        }
    });
}

document.addEventListener("change", event => {
    if (event.target.matches('.tabbed-set > input[type="radio"]')) {
        resizeVisiblePlots(event.target.parentElement);
    }
});

// Details toggle events do not bubble, so listen during capture.
document.addEventListener("toggle", event => {
    if (event.target.matches("details") && event.target.open) {
        resizeVisiblePlots(event.target);
    }
}, true);
