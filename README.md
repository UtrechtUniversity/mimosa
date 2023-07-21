# MIMOSA: Mathematical Integrated Model for Optimal and Stylised Assessment

MIMOSA is a recent simple IAM based on FAIR, with 26 regions covering the whole world. It is a relatively simple Cost-Benefit IAM but still covers the relevant technological and socio-economic dynamics. Temperature is a linear function of cumulative CO2 emissions. MIMOSA uses the DICE sea-level rise module. The mitigation costs, population, initial capital stock and baseline GDP and CO2 emissions are regional. The direct regional mitigation costs are calculated as area under the Marginal Abatement Cost (MAC) curve, and have been calibrated to the IPCC AR6 WGIII database.

### General

The model is written in the Python optimisation package [Pyomo](https://www.pyomo.org/). It is mainly an `AbstractModel`
(object containing all the variables, parameters and constraints, without the actual data values), which is then
transformed into a `ConcreteModel` by putting all the parameter values in it. This `ConcreteModel` is sent to the solver
([IPOPT](https://coin-or.github.io/Ipopt/), an open-source large-scale nonlinear optimisation suite).

### Structure

* [Abstract model](mimosa/model/abstract_model.py)
  * [Emission module](mimosa/model/components/emissions.py)
  * [Sea level rise module](mimosa/model/components/sealevelrise.py)
  * Damage and adaptation module
    * [COACCH](mimosa/model/components/damages/coacch.py)
    * Adaptation not yet implemented
  * [Abatement module](mimosa/model/components/abatement.py)
  * [Burden sharing module](mimosa/model/components/burdensharing.py)
  * Emission trading module
    * [Global cost pool](mimosa/model/components/emissiontrade/globalcostpool.py)
    * [No trade](mimosa/model/components/emissiontrade/notrade.py)
  * [Cobb-Douglas and economics module](mimosa/model/components/cobbdouglas.py)
  * Objective module
    * [Maximise utility](mimosa/model/components/objective/utility.py)
    * [Minimise global costs](mimosa/model/components/objective/globalcosts.py)
  * Welfare function module
    * [Global cost-minimising](mimosa/model/components/welfare/inequal_aversion_zero.py)
    * [Regional welfare loss-minimising](mimosa/model/components/welfare/inequal_aversion_elasmu.py)
* [Concrete model](mimosa/model/concrete_model/instantiate_params.py)
  * [Simulation mode](mimosa/model/concrete_model/simulation_mode/main.py) (when emission/temperature paths are imposed exogenously)

<br>
<br>

![](https://media.springernature.com/full/springer-static/image/art%3A10.1038%2Fs41467-021-22826-5/MediaObjects/41467_2021_22826_Fig1_HTML.png)
*Schematic overview of the MIMOSA model. From [[1]](#1).*
  
## Installing and running MIMOSA

MIMOSA can be installed using `pip`:
```bash
pip install mimosa
```

Since MIMOSA is an optimisation model, an optimisation engine needs to be specified. This can be installed locally (see [With IPOPT installed locally](#ipopt-local)), but an easier way is to use a free cloud-based optimisation service called NEOS.

<h4>Using the NEOS server</h4>
The MIMOSA runs can easily be sent to the NEOS server (https://neos-server.org) for remote optimisation. First, on their website, sign up for a free account. You can then run MIMOSA with NEOS enabled by providing it with the email address you used to sign up for NEOS:

```python
from mimosa import MIMOSA, load_params

params = load_params()

model1 = MIMOSA(params)
model1.solve(use_neos=True, neos_email="your.email@email.com")
model1.save("run1")
```

Depending on the MIMOSA parameters chosen and on how busy the NEOS server is, running the model might take a while (typically a couple of minutes).

<h4 id='ipopt-local'>With IPOPT installed locally</h4>

A faster way to run MIMOSA, and which doesn't require an internet connection, is to install the open-source optimisation engine IPOPT locally:
```
conda install -c conda-forge ipopt
```
However, this sometimes fails on Windows. To fix it, go to https://www.coin-or.org/download/binary/Ipopt/ and download the latest win64-version. Unzip the files. A subfolder `bin` should contain the file `ipopt.exe`. The next step is to add this folder to your PATH environment:
Windows > Edit the system environment variables > Environment variables... > Select "Path" and click Edit... > Click New and browse to the folder you just unzipped. Make sure to select the `bin` subfolder as this folder contains the file `ipopt.exe`.

Once IPOPT is installed, MIMOSA can be ran without NEOS:
```python
from mimosa import MIMOSA, load_params

params = load_params()

model1 = MIMOSA(params)
model1.solve()  # No NEOS required
model1.save("run1")
```

## How to cite
When using MIMOSA, please cite [[1]](#1) (global version) and [[2]](#2) (regional version).

## References
<a id="1">[1]</a> 
van der Wijst, KI., Hof, A.F. & van Vuuren, D.P. On the optimality of 2°C targets and a decomposition of uncertainty. *Nature Communications* **12**, 2575 (2021). https://doi.org/10.1038/s41467-021-22826-5

<a id="2">[2]</a> 
van der Wijst, KI., Bosello, F., Dasgupta, S. *et al*. New damage curves and multimodel analysis suggest lower optimal temperature. *Nature Climate Change* **13**, 434–441 (2023). https://doi.org/10.1038/s41558-023-01636-1