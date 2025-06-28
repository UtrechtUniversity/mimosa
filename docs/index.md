![](assets/logos/MIMOSA.svg){.off-glb}
# MIMOSA: Integrated Assessment Model for Cost-Benefit Analysis


[Documentation :octicons-arrow-right-24:](components/index.md){.md-button}
[Installation :octicons-arrow-right-24:](installation.md){.md-button}
[Running :octicons-arrow-right-24:](run.md){.md-button}
[Dashboard :octicons-arrow-up-right-24:](https://dashboard-mimosa.onrender.com/){.md-button}

MIMOSA is an Integrated Assessment Model (IAM) part of the [IMAGE family](https://www.pbl.nl/en/image/home), with 26 regions covering the whole world. It is a relatively simple Cost-Benefit IAM that still covers the relevant technological and socio-economic dynamics. The climate impacts are calculated using state-of-the-art COACCH damage functions, and the mitigation costs have been directly calibrated to the IPCC AR6 WGIII database.


MIMOSA is being developed at the [Copernicus Institute of Sustainable Development](https://www.uu.nl/en/research/copernicus-institute-of-sustainable-development) at Utrecht University, and is part of the [IMAGE modelling framework](https://www.pbl.nl/en/image/home).

[<img src="assets/logos/UU_logo_2021_EN_RGB.png#only-light" width="40%">](https://www.uu.nl/en/research/copernicus-institute-of-sustainable-development)
[<img src="assets/logos/UU_logo_2021_EN_RGB_diap.png#only-dark" width="40%">](https://www.uu.nl/en/research/copernicus-institute-of-sustainable-development)
[<img src="assets/logos/IMAGE.png#only-light" width="40%">](https://www.pbl.nl/en/image/home)
[<img src="assets/logos/IMAGE-for-dark-bg.png#only-dark" width="40%">](https://www.pbl.nl/en/image/home)


### General

The model is written in the Python optimisation package [Pyomo](https://www.pyomo.org/). It uses
[IPOPT](https://coin-or.github.io/Ipopt/) (an open-source large-scale nonlinear optimisation suite) to solve the model.


[![](assets/fig/mimosa_overview_dark.png#only-dark)
![](assets/fig/mimosa_overview.png#only-light)](components/index.md)
*Schematic overview of the MIMOSA model. Adapted from [[1]](#1).*


## How to cite
When using MIMOSA, please cite [[1]](#1) (global version) and [[2]](#2) (regional version).

## References
<a id="1">[1]</a> 
van der Wijst, KI., Hof, A.F. & van Vuuren, D.P. On the optimality of 2°C targets and a decomposition of uncertainty. *Nature Communications* **12**, 2575 (2021). <https://doi.org/10.1038/s41467-021-22826-5>

<a id="2">[2]</a> 
van der Wijst, KI., Bosello, F., Dasgupta, S. *et al*. New damage curves and multimodel analysis suggest lower optimal temperature. *Nature Climate Change* **13**, 434–441 (2023). <https://doi.org/10.1038/s41558-023-01636-1>

## What does MIMOSA stand for?

MIMOSA: Mathematical Integrated Model for Optimal and Stylised Assessment