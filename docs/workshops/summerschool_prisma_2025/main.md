## Installing MIMOSA

Follow the instructions in the [installation guide](../../installation.md) to install MIMOSA.

## Exercise 1: cost-benefit analysis: optimal temperature and benefit-cost ratio


#### Step 1: Do a no-policy baseline run
Run the following code to do a no-policy baseline run with MIMOSA. The code is already provided, so you can just run it. The code will run a baseline run. Since there is nothing to optimise, the code will do a *simulation*, and not an *optimisation* run.

```python
--8<-- "docs/workshops/summerschool_prisma_2025/run_baseline.py"
``` 

#### Step 2: Analyse the results
The code will produce a CSV file with the results of the run. The file is saved in the `output` folder. Open the file `output/run_baseline_nopolicy.csv` to see the
results of the simulation. The easiest way to visualise the results is to use the MIMOSA Dashboard. Open the [MIMOSA Dashboard](https://dashboard-mimosa.onrender.com/) and drag and drop the `output/run_baseline_nopolicy.csv` file into the dashboard. This will allow you to visualise the results of the simulation.

#### Step 3: Running MIMOSA in optimisation mode
Now that you have run a no-policy baseline run, you can run MIMOSA in optimisation mode. This will allow you to find the optimal temperature and benefit-cost ratio for the given parameters. The code is already provided, so you can just run it.

```python
--8<-- "docs/workshops/summerschool_prisma_2025/run_cba.py"
```

#### Step 4: Analyse the damages, mitigation costs, avoided damages and calculate the benefit-cost ratio

#### Step 5: Tweak parameters:

Have a look at the [parameter reference](../../parameters.md) to see which parameters you can change. Interesting parameters could be:

 * [`params["economics"]["PRTP"]`](../../parameters.md#economics.PRTP): The discount rate (pure rate of time preference). Choose values between 0.01 (low end) and 0.03 (high end). The default is 0.015 (corresponding to 1.5%/year).
 * [`params["economics"]["damages"]["quantile"]`](../../parameters.md#economics.damages.quantile): The quantile of the damages distribution. Choose values between 0.05 (low end) and 0.95 (high end). The default is 0.5 (corresponding to the median).
 * [`params["temperature"]["TCRE"]`](../../parameters.md#temperature.TCRE): The transient climate response to cumulative emissions. Choose values between 0.42 (low end) and 0.82 (high end). The default is 0.62&nbsp;&deg;C/TtCO<sub>2</sub> (corresponding to the median).


## Exercise 2: effort sharing and equity

In the next exercise, you will run MIMOSA with different effort sharing approaches. Contrary to the previous exercise, you will not do a CBA run, but a fixed carbon budget. We will choose a carbon budget of 700 GtCO<sub>2</sub>, and run MIMOSA with different effort sharing approaches.

#### Step 1: MIMOSA runs with various effort sharing approaches

First, choose which effort sharing regime you want to use. You can choose between:

* [`"equal_mitigation_costs"`](../../parameters.md#effort sharing.regime)
* [`"equal_total_costs"`](../../parameters.md#effort sharing.regime)
* [`"per_cap_convergence"`](../../parameters.md#effort sharing.regime)
* [`"ability_to_pay"`](../../parameters.md#effort sharing.regime)
* [`"equal_cumulative_per_cap"`](../../parameters.md#effort sharing.regime)

Then, run the following code where you change the variable `regime`. 

```python
--8<-- "docs/workshops/summerschool_prisma_2025/run_effortsharing.py"
```

1. Change this variable with the chosen option.

#### Step 2: Effect on equity

...

#### Step 3: Effect on sovereignty

When emission trading is enabled, each region has to pay it's own domestic reductions, plus an import/export balance. This balance is positive if the region imports emission reductions (i.e. buys emission reductions from other regions), and negative if the region exports emission reductions (i.e. sells emission reductions to other regions).

The sum of the variable `import_export_mitigation_cost_balance` is always zero. However, to get a sense of how large the financial flows each year are, you can sum all the positive values (or all the negative values) of this variable. Do this for 2050 and for 2100. How big are the financial flows? How does this compare to the global GDP in those years? 
