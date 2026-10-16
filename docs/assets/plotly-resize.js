// Plots created in hidden tabs need to measure their width once visible.
document.addEventListener("change", event => {
    if (!event.target.matches('.tabbed-set > input[type="radio"]')) return;

    const tabs = event.target.parentElement;
    requestAnimationFrame(() => {
        if (!window.Plotly) return;
        tabs.querySelectorAll(".js-plotly-plot").forEach(plot => {
            if (plot._fullLayout && plot.clientWidth > 0 && plot.clientHeight > 0) {
                window.Plotly.Plots.resize(plot);
            }
        });
    });
});
