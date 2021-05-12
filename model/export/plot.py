"""
Creates a big Plotly figure with each column a region, and these rows:
  Row 1: regional emissions (with baseline) and carbon price
  Row 2: Adapt/damage costs and adaptation levels
  Row 3: GDP (gross/net), consumption, capital stock and utility
  Row 4: Global emissions, temperature and sea level rise
"""

import os
from model.export.utils import Plot


def full_plot(m, filename, include_plotlyjs=True, custom_layout=None):

    if custom_layout is None:
        custom_layout = {}

    plot = Plot(m, horizontal_spacing=0.005, vertical_spacing=0.05)

    plot.add(m.baseline_emissions, row=1, is_fct=True, name="baseline_emissions")
    try:
        plot.add(m.baseline, row=1)
    except AttributeError:
        pass
    plot.add(m.regional_emissions, row=1)
    plot.add(m.carbonprice, row=1, secondary_y=True)
    try:
        plot.add(m.adapt_costs, row=2, stackgroup="costs")
        plot.add(m.resid_damages, row=2, stackgroup="costs")
        plot.add(m.gross_damages, row=2)
    except AttributeError:
        plot.add(m.damage_costs, row=2, stackgroup="costs")
    plot.add(m.rel_abatement_costs, row=2, stackgroup="costs")

    plot.add(m.capital_stock, row=3)
    plot.add(m.GDP_gross, row=3)
    plot.add(m.GDP_net, row=3)
    plot.add(m.consumption, row=3, visible="legendonly")
    plot.add(m.utility, row=3, secondary_y=True, visible="legendonly")
    plot.add(m.abatement_costs, row=3, visible="legendonly")
    plot.add(m.global_emissions, is_regional=False, row=4)
    plot.add(m.temperature, is_regional=False, row=4, secondary_y=True)
    plot.add(m.cumulative_emissions, is_regional=False, row=4, visible="legendonly")

    try:
        plot.add(
            m.global_rel_abatement_costs,
            is_regional=False,
            row=4,
            secondary_y=True,
            visible="legendonly",
        )
    except AttributeError:
        pass

    # Optional values

    try:
        plot.add(
            m.emission_relative_cumulative,
            is_regional=False,
            row=4,
            secondary_y=True,
            visible="legendonly",
        )
        plot.add(
            m.consumption_loss,
            is_regional=False,
            row=4,
            secondary_y=True,
            visible="legendonly",
        )
        plot.add(
            m.smoothed_factor,
            is_regional=False,
            row=4,
            secondary_y=True,
            visible="legendonly",
        )
        plot.add(
            m.netnegative_emissions, is_regional=False, row=4, visible="legendonly"
        )
        plot.add(m.overshoot, is_regional=False, row=4, visible="legendonly")
    except AttributeError:
        pass

    try:
        # RICE
        plot.add(m.adapt_level, row=2, secondary_y=True, visible="legendonly")
        plot.add(m.adapt_FAD, row=2, secondary_y=True, visible="legendonly")
        plot.add(m.adapt_SAD, row=2, secondary_y=True, visible="legendonly")
        plot.add(m.adapt_IAD, row=2, secondary_y=True, visible="legendonly")
        plot.add(m.SLR_damages, row=2, visible="legendonly")
        plot.add(
            m.total_SLR,
            is_regional=False,
            row=4,
            secondary_y=True,
            visible="legendonly",
        )
        plot.add(
            m.SLR, is_regional=False, row=4, secondary_y=True, visible="legendonly"
        )
        plot.add(
            m.CUMGSIC, is_regional=False, row=4, secondary_y=True, visible="legendonly"
        )
        plot.add(
            m.CUMGIS, is_regional=False, row=4, secondary_y=True, visible="legendonly"
        )
        plot.add(
            m.LBD_factor,
            is_regional=False,
            row=4,
            secondary_y=True,
            visible="legendonly",
        )
        plot.add(
            m.test, is_regional=False, row=4, secondary_y=True, visible="legendonly"
        )
    except AttributeError:
        pass

    try:
        # WITCH
        plot.add(m.adapt_costs_reactive, row=2, secondary_y=True, visible="legendonly")
        plot.add(m.adapt_costs_proactive, row=2, secondary_y=True, visible="legendonly")
        plot.add(m.adapt_costs_speccap, row=2, secondary_y=True, visible="legendonly")
        plot.add(m.adapt_Q_cap, row=2, secondary_y=True, visible="legendonly")
        plot.add(m.adapt_K_proactive, row=2, secondary_y=True, visible="legendonly")
    except AttributeError:
        pass

    plot.set_yaxes_titles(
        ["GtCO<sub>2</sub>/yr", "% GDP", "trillion US$2005/yr", "GtCO<sub>2</sub>/yr"]
    )
    plot.fig.update_yaxes(
        title="Carbon price", row=1, col=len(plot.regions), secondary_y=True
    )
    plot.fig.update_yaxes(
        title="Adaptation level", row=2, col=len(plot.regions), secondary_y=True
    )
    plot.fig.update_yaxes(rangemode="tozero", row=2)
    plot.set_layout()
    plot.fig.update_layout(custom_layout)

    outputdir = "output/plots"
    os.makedirs(outputdir + "/", exist_ok=True)
    outputfile = "{}/{}.html".format(outputdir, filename)
    print(f"Plot saved at {outputfile}")
    plot.fig.write_html(outputfile, include_plotlyjs=include_plotlyjs)
