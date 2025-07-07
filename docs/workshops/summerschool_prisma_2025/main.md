## Installing MIMOSA

Follow the instructions in the [installation guide](../../installation.md) to install MIMOSA.

??? info "Having trouble installing MIMOSA?"

    If you can't get MIMOSA to run, you can also use the following Google Colab notebook to run the exercises: [https://colab.research.google.com/drive/1Ra7RUdQ9F7zt46HmZtXNfl4iHRzjwt3b](https://colab.research.google.com/drive/1Ra7RUdQ9F7zt46HmZtXNfl4iHRzjwt3b)

## Exercise 1: cost-benefit analysis: optimal temperature and benefit-cost ratio

<span class="grey-bg" markdown>
**:material-clock-start: 11:30 - 12:30**
</span>

For this exercise, you will do two runs of MIMOSA: a no-policy baseline run, and a cost-benefit analysis (CBA) run. The no-policy baseline run will give a sense of the economic impacts of climate change if we don't do any policy, while the CBA run will allow you to find the optimal temperature target and get a sense of the residual damages and mitigation costs.

#### Step 1: Running MIMOSA

!!! tip "Task 1: Run MIMOSA"

    Create a new Python file, and using the code below, run both a no-policy baseline run and a cost-benefit analysis (CBA) run.

    === "Run 1: No-policy baseline run"

        This code will do a baseline run. Since there is nothing to optimise, the code will do a *simulation*, and not an *optimisation* run.

        ```python
        --8<-- "docs/workshops/summerschool_prisma_2025/run_baseline.py"
        ``` 

    === "Run 2: Cost-benefit run"

        Now that you have run a no-policy baseline run, you can run MIMOSA in optimisation mode. This will allow you to find the optimal temperature and benefit-cost ratio for the given parameters.

        ```python
        --8<-- "docs/workshops/summerschool_prisma_2025/run_cba.py"
        ```



#### Step 2: Analyse the results
The code will produce a CSV file with the results of the run. The file is saved in the `output` folder. You can either open the CSV file (e.g. `output/run_baseline_nopolicy.csv`) in Excel/Python, or you can use the MIMOSA Dashboard. Open the [MIMOSA Dashboard](https://dashboard-mimosa.onrender.com/) and drag and drop the CSV file into the dashboard. This will allow you to visualise the results of the simulation. You can also drag and drop multiple files to compare the results of different runs: try dropping both `run_baseline_nopolicy.csv` and `run_cba.csv` to compare the results of the no-policy baseline run and the CBA run.

In the dashboard, a lot of information is already shown in the various tabs. You can also go to the tab "All variables" to show any variable present in the output file.

!!! question "Question 1: global costs and benefits"

    Investigate the following policy-relevant questions:

    * What is the cost-optimal temperature target? And how high does temperature rise without any policy?
    * How big are the *global* economic damages in 2050 and 2100 in the baseline run, and in the CBA run? *Hint: look at the variable* `damage_relative_global`. And how big are the global avoided damages in the CBA run?
    * How big are the *global* mitigation costs in 2050 and 2100 in the CBA run? And how does this compare to the avoided damages? Calculate the benefit-cost ratio (BCR) for 2050 and 2100.



!!! question "Question 2: regional differences"

    Choose two regions: one from the Global North, one from the Global South (see the [regions documentation](../../components/regions.md) for the full list of regions).

    * For both regions, compare the damage costs, avoided damages, and mitigation costs in 2050 and 2100. What are the benefit-cost ratios for these two regions?

#### Step 3: Tweak parameters:

Rerun MIMOSA with different parameters. Have a look at the [parameter reference](../../parameters.md) to see which parameters you can change. Interesting parameters could be:

 * [`params["economics"]["PRTP"]`](../../parameters.md#economics.PRTP): The discount rate (pure rate of time preference). Choose values between 0.01 (low end) and 0.03 (high end). The default is 0.015 (corresponding to 1.5%/year).
 * [`params["economics"]["damages"]["quantile"]`](../../parameters.md#economics.damages.quantile): The quantile of the damages distribution. Choose values between 0.05 (low end) and 0.95 (high end). The default is 0.5 (corresponding to the median).
 * [`params["temperature"]["TCRE"]`](../../parameters.md#temperature.TCRE): The transient climate response to cumulative emissions. Choose values between 0.42 (low end) and 0.82 (high end). The default is 0.62&nbsp;&deg;C/TtCO<sub>2</sub> (corresponding to the median).


!!! question "Question 3: sensitivity analysis"

    * What is the new cost-optimal temperature target? What is the influence of the discount rate, the damage quantile, or the TCRE on the cost-optimal temperature target?
    * If you have time, how is the global or regional benefit-cost ratio affected?

## Exercise 2: effort sharing and equity

<span class="grey-bg" markdown>
**:material-clock-start: 13:30 - 14:30**
</span>

In the next exercise, you will run MIMOSA with different effort sharing approaches. Contrary to the previous exercise, you will not do a CBA run, but a fixed carbon budget. We will choose a carbon budget of 700 GtCO<sub>2</sub>, and run MIMOSA with different effort sharing approaches.

#### Step 1: Run MIMOSA

!!! tip "Task 2: Run MIMOSA with effort sharing approach"

    For this exercise, you will again do two runs: one with an effort-sharing regime of your choice, and one with the typical cost-minimising approach (default in most IAMs).

    === "Run 1: Effort sharing regime"

        First, choose which effort sharing regime you want to use. You can choose between:

        * [`"equal_mitigation_costs"`](../../parameters.md#effort sharing.regime)
        * [`"equal_total_costs"`](../../parameters.md#effort sharing.regime)
        * [`"per_cap_convergence"`](../../parameters.md#effort sharing.regime)
        * [`"ability_to_pay"`](../../parameters.md#effort sharing.regime)
        * [`"equal_cumulative_per_cap"`](../../parameters.md#effort sharing.regime)

        More information about these regimes can be found in [van den Berg et al. (2020)](https://doi.org/10.1007/s10584-019-02368-y) (specifically, [Table 1](https://link.springer.com/article/10.1007/s10584-019-02368-y/tables/1)).

        Then, run the following code where you change the variable `regime`. 

        ```python hl_lines="3 6"
        --8<-- "docs/workshops/summerschool_prisma_2025/run_effortsharing.py"
        ```

        1. Change this variable with the chosen option.
    
    === "Run 2: Cost-minimising regime"

        Next, run MIMOSA with the cost-minimising regime. There is no need for emission trading, so simply use the following code:

        ```python
        --8<-- "docs/workshops/summerschool_prisma_2025/run_noregime.py"
        ```

#### Step 2: Effect on equity

!!! question "Question 4: Regional mitigation costs and equity"

    * For the two chosen regions, compare the mitigation costs in 2050 and 2100. How do these costs compare to the global mitigation costs?
    * And how do they compare to the "CBA" run?


#### Step 3: Effect on sovereignty

!!! question "Question 5: Sovereignty and import/export of emission reductions"


    When emission trading is enabled, each region has to pay it's own domestic reductions, plus an import/export balance. This balance is positive if the region imports emission reductions (i.e. buys emission reductions from other regions), and negative if the region exports emission reductions (i.e. sells emission reductions to other regions).

    The sum of the variable `import_export_mitigation_cost_balance` is always zero. However, to get a sense of how large the financial flows each year are, you can sum all the positive values (or all the negative values) of this variable. Do this for 2050 and for 2100. How big are the financial flows? How does this compare to the global GDP in those years? 
