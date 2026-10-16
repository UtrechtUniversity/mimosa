// Size newly visible plots before painting the tab. Plots.resize waits 100 ms.
document.addEventListener("change", event => {
    if (!event.target.matches('.tabbed-set > input[type="radio"]')) return;
    if (!window.Plotly) return;

    const tabs = event.target.parentElement;
    tabs.querySelectorAll(".js-plotly-plot").forEach(plot => {
        if (plot._fullLayout && plot.clientWidth > 0 && plot.clientHeight > 0) {
            window.Plotly.relayout(plot, { autosize: true });
        }
    });
});
