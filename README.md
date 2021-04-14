# MIMOSA: Mathematical Integrated Model for Optimal and Stylised Assessment

Also called KICE (**K**ICE **I**ntegrated model for **C**limate and **E**conomy).

### General

The model is written in the Python optimisation package [Pyomo](https://www.pyomo.org/). It is mainly an `AbstractModel`
(object containing all the variables, parameters and constraints, without the actual data values), which is then
transformed into a `ConcreteModel` by putting all the parameter values in it. This `ConcreteModel` is sent to the solver
([IPOPT](https://coin-or.github.io/Ipopt/), an open-source large-scale nonlinear optimisation suite).

### Structure

* [Abstract model](model/abstract_model.py)
  * [Emission module](model/components/emissions.py)
  * [Sea level rise module](model/components/sealevelrise.py)
  * Damage and adaptation module
    * [AD-RICE 2010](model/components/damages/AD_RICE2010.py)
    * [AD-RICE 2012](model/components/damages/AD_RICE2012.py)
    * [AD-WITCH](model/components/AD_WITCH.py) (not implemented yet)
    * [No damages](model/components/damages/nodamage.py)
  * [Abatement module](model/components/abatement.py)
  * [Cobb-Douglas and economics module](model/components/cobbdouglas.py)
  * Objective module
    * [Maximise utility](model/components/objective/utility.py)
    * [Minimise global costs](model/components/objective/globalcosts.py)
* [Concrete model](model/concrete_model/instantiate_params.py)
    
### Data

The parameter values are defined in the [`config.yaml`](inputdata/config.yaml) file in the `input` directory.
The baseline emissions, baseline GDP (for calculation of Total Factor Productivity) and population data is read in IIASA
database format. By default, the IMAGE data of [`inputdata/data/data_IMAGE_SSP.csv`](inputdata/data/data_IMAGE_SSP.csv) is used.
Damage and adaptation coefficients are read from [`inputdata/params/rice_damages_adapt.csv`](inputdata/params/rice_damages_adapt.csv).

The config parameter values and the input data are combined with the `AbstractModel` to create the `ConcreteModel` in
[`model/concrete_model/instantiate_params.py`](model/concrete_model/instantiate_params.py).

The main file of the model, where concrete model is created and the model is solved, is [`model/mimosa.py`](model/mimosa.py).

### Running the model

The simplest way to run the model is shown in [`run.py`](run.py). You can change parameter values by either editing the 
`config.yaml` file, or by updating the `params` variable (which is simply a Python dictionary containing the `config.yaml`
data).




### Legal notice
For use of the AD-RICE component, please contact the author Kelly de Bruin.
