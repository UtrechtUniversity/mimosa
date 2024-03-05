![image](assets/logo.svg)
# MIMOSA: Mathematical Integrated Model for Optimal and Stylised Assessment
???+ warning
    This documentation is still under construction and will be updated regularly.

MIMOSA is a recent simple IAM based on FAIR, with 26 regions covering the whole world. It is a relatively simple Cost-Benefit IAM but still covers the relevant technological and socio-economic dynamics. Temperature is a linear function of cumulative CO2 emissions. MIMOSA uses the DICE sea-level rise module. The mitigation costs, population, initial capital stock and baseline GDP and CO2 emissions are regional. The direct regional mitigation costs are calculated as area under the Marginal Abatement Cost (MAC) curve, and have been calibrated to the IPCC AR6 WGIII database.


[Documentation :octicons-arrow-right-24:](components/general.md){.md-button}
[Installation :octicons-arrow-right-24:](installation.md){.md-button}
[Running :octicons-arrow-right-24:](run.md){.md-button}

### General

The model is written in the Python optimisation package [Pyomo](https://www.pyomo.org/). It is mainly an `AbstractModel`
(object containing all the variables, parameters and constraints, without the actual data values), which is then
transformed into a `ConcreteModel` by putting all the parameter values in it. This `ConcreteModel` is sent to the solver
([IPOPT](https://coin-or.github.io/Ipopt/), an open-source large-scale nonlinear optimisation suite).


![](https://media.springernature.com/full/springer-static/image/art%3A10.1038%2Fs41467-021-22826-5/MediaObjects/41467_2021_22826_Fig1_HTML.png)
*Schematic overview of the MIMOSA model. From [[1]](#1).*


## How to cite
When using MIMOSA, please cite [[1]](#1) (global version) and [[2]](#2) (regional version).

## References
<a id="1">[1]</a> 
van der Wijst, KI., Hof, A.F. & van Vuuren, D.P. On the optimality of 2°C targets and a decomposition of uncertainty. *Nature Communications* **12**, 2575 (2021). <https://doi.org/10.1038/s41467-021-22826-5>

<a id="2">[2]</a> 
van der Wijst, KI., Bosello, F., Dasgupta, S. *et al*. New damage curves and multimodel analysis suggest lower optimal temperature. *Nature Climate Change* **13**, 434–441 (2023). <https://doi.org/10.1038/s41558-023-01636-1>