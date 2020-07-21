
from model.export.utils import Plot


def full_plot(m, filename):

    plot = Plot(m, horizontal_spacing=0.02, vertical_spacing=0.05)
    
    plot.add(m.baseline_emissions, row=1, is_fct=True, name='baseline_emissions')
    try:
        plot.add(m.baseline, row=1)
    except:
        pass
    plot.add(m.regional_emissions, row=1)
    plot.add(m.carbonprice, row=1, secondary_y=True)
    plot.add(m.adapt_costs, row=2, stackgroup='costs')
    plot.add(m.resid_damages, row=2, stackgroup='costs')
    plot.add(m.rel_abatement_costs, row=2, stackgroup='costs')
    plot.add(m.gross_damages, row=2)

    plot.add(m.capital_stock, row=3)
    plot.add(m.GDP_gross, row=3)
    plot.add(m.GDP_net, row=3)
    plot.add(m.global_emissions, is_regional=False, row=4)
    plot.add(m.temperature, is_regional=False, row=4, secondary_y=True)
    plot.add(m.cumulative_emissions, is_regional=False, row=4, visible='legendonly')

    

    # Optional values

    try:
        plot.add(m.emission_relative_cumulative, is_regional=False, row=4, secondary_y=True, visible='legendonly')
        plot.add(m.consumption_loss, is_regional=False, row=4, secondary_y=True, visible='legendonly')
        plot.add(m.smoothed_factor, is_regional=False, row=4, secondary_y=True, visible='legendonly')
    except:
        pass

    try:
        # RICE
        plot.add(m.adapt_level, row=2, secondary_y=True, visible='legendonly')
        plot.add(m.adapt_IAD, row=2, secondary_y=True, visible='legendonly')
        plot.add(m.adapt_FAD, row=2, secondary_y=True, visible='legendonly')
        plot.add(m.adapt_SAD, row=2, secondary_y=True, visible='legendonly')
    except:
        pass

    try:
        # WITCH
        plot.add(m.adapt_costs_reactive, row=2, secondary_y=True, visible='legendonly')
        plot.add(m.adapt_costs_proactive, row=2, secondary_y=True, visible='legendonly')
        plot.add(m.adapt_costs_speccap, row=2, secondary_y=True, visible='legendonly')
        plot.add(m.adapt_Q_cap, row=2, secondary_y=True, visible='legendonly')
        plot.add(m.adapt_K_proactive, row=2, secondary_y=True, visible='legendonly')
    except:
        pass

    plot.set_yaxes_titles(['GtCO<sub>2</sub>/yr','% GDP', 'trillion US$2005/yr', 'GtCO<sub>2</sub>/yr'])
    plot.fig.update_yaxes(title='Carbon price', row=1, col=len(plot.regions), secondary_y=True)
    plot.fig.update_yaxes(title='Adaptation level', row=2, col=len(plot.regions), secondary_y=True)
    plot.set_layout()

    plot.fig.write_html('output/plots/{}.html'.format(filename))