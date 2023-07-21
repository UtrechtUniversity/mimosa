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
    
### Data

The parameter values are defined in the [`config.yaml`](mimosa/inputdata/config/config.yaml) file in the `input` directory, and for region- and component-specific parameters in:
* Initial capital factor: [`economics.csv`](mimosa/inputdata/params/economics.csv)
* MAC factors: [`mac.csv`](mimosa/inputdata/params/mac.csv)
* Regional damages and adaptation coefficients: [`COACCH.csv`](mimosa/inputdata/params/COACCH.csv)

The baseline emissions, baseline GDP (for calculation of Total Factor Productivity) and population data is read in IIASA
database format. By default, the IMAGE data of [`inputdata/data/data_IMAGE_SSP.csv`](mimosa/inputdata/data/data_IMAGE_SSP.csv) is used.

The config parameter values and the input data are combined with the `AbstractModel` to create the `ConcreteModel` in
[`model/concrete_model/instantiate_params.py`](mimosa/model/concrete_model/instantiate_params.py).

The main file of the model, where concrete model is created and the model is solved, is [`model/mimosa.py`](mimosa/model/mimosa.py).

### Running the model

The simplest way to run the model is shown in [`run.py`](run.py). You can change parameter values by either editing the 
`config.yaml` file, or by updating the `params` variable (which is simply a Python dictionary containing the `config.yaml`
data).

```python
from mimosa.model.mimosa import MIMOSA

from mimosa.model.common.config import parseconfig

params = parseconfig.load_params()
params["emissions"]["carbonbudget"] = False

model1 = MIMOSA(params)
model1.solve()
model1.save("run1")
```

#### With IPOPT installed locally

By default, this requires the optimisation package `ipopt` to be installed. The easiest way is to install it using
```
conda install -c conda-forge ipopt
```
However, this sometimes fails on Windows. To fix it, go to https://www.coin-or.org/download/binary/Ipopt/ and download the latest win64-version. Unzip the files. A subfolder `bin` should contain the file `ipopt.exe`. The next step is to add this folder to your PATH environment:
Windows > Edit the system environment variables > Environment variables... > Select "Path" and click Edit... > Click New and browse to the folder you just unzipped. Make sure to select the `bin` subfolder as this folder contains the file `ipopt.exe`.

#### Using the NEOS server
Even easier than installing IPOPT is by using the NEOS server: https://neos-server.org. The MIMOSA runs are then optimised on a remote server from the US optimisation community NEOS. On their website, sign up for a free account. You can then run MIMOSA with NEOS enabled by providing it with the email address you used to sign up for NEOS:
```python
from mimosa.model.mimosa import MIMOSA

from mimosa.model.common.config import parseconfig

params = parseconfig.load_params()
params["emissions"]["carbonbudget"] = False

model1 = MIMOSA(params)
model1.solve(use_neos=True, neos_email="your.email@email.com")
model1.save("run1")
```


