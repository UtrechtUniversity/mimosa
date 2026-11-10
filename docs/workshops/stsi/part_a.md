---
variable_context: accreu_sectoral
---

For the first part of this assignment, you will do several MIMOSA runs to investigate the economic impacts of climate change, and how these are affected by different policy choices. You will also investigate the effect of different effort sharing approaches on the distribution of mitigation costs across regions. 

**What to hand in:** a short report with your answers to the questions on this page (marked with a :octicons-question-16: icon). You have to do exercise 1, and choose between exercise 2A and 2B. Exercise 2A focuses on adaptation and climate impacts, while exercise 2B focuses on equity and how to distribute mitigation effort.

## Exercise 1: cost-benefit analysis: optimal temperature and benefit-cost ratio

For this exercise, you will do two runs of MIMOSA: a no-policy run, and a cost-benefit analysis (CBA) run. The no-policy run will give a sense of the economic impacts of climate change if we don't do any policy, while the CBA run will allow you to find the optimal temperature target and get a sense of the residual damages and mitigation costs.

#### Step 1: Running MIMOSA

!!! tip "Task: Run MIMOSA"

    Create a new Python file, and using the code below, run both a no-policy run and a cost-benefit analysis (CBA) run.

    === "Run 1: No-policy run"

        This code will do a no-policy run. Since there is nothing to optimise, the code will do a *simulation*, and not an *optimisation* run.

        ```python
        --8<-- "docs/workshops/stsi/runs/run_nopolicy.py"
        ```

    === "Run 2: Cost-benefit run"

        Now that you have run a no-policy run, you can run MIMOSA in optimisation mode. This will allow you to find the cost-optimal temperature and benefit-cost ratio for the given parameters.

        ```python
        --8<-- "docs/workshops/stsi/runs/run_cba.py"
        ```

    !!! note

        Note that by default, MIMOSA runs until the year 2150. However, for the purpose of these exercises, we will only look at the results until 2100. The reason MIMOSA runs until 2150 is to avoid end-of-horizon effects in the optimisation.

#### Step 2: Analyse the results

The code will produce a CSV file with the results of the run. The file is saved in the `output` folder. You can either open the CSV file (e.g. `output/run_nopolicy.csv`) in Excel/Python, or you can use the MIMOSA Dashboard. Open the [MIMOSA Dashboard](https://dashboard-mimosa.onrender.com/) and drag and drop the CSV file into the dashboard. This will allow you to visualise the results of the simulation. You can also drag and drop multiple files to compare the results of different runs: try dropping both `run_nopolicy.csv` and `run_cba.csv` to compare the results of the no-policy run and the CBA run.

In the dashboard, a lot of information is already shown in the various tabs. You can also go to the tab "All variables" to show any variable present in the output file.

!!! question "Question 1: global costs and benefits"

    Investigate the following policy-relevant questions:

    * **Q1a:** What is the cost-optimal temperature in 2100? And how high does temperature rise in 2100 without any policy?
    * **Q1b:** How big are the *global* economic damages in 2050 and 2100 in the baseline run, and in the CBA run? *Hint: look at varref::accreu_sectoral::global_damage_costs and varref::accreu_sectoral::global_avoided_damage_costs.*
    * **Q1c:** How big are the *global* mitigation costs (varref::accreu_sectoral::global_mitigation_costs) in 2050 and 2100 in the CBA run? And how does this compare to the avoided damages? Calculate the benefit-cost ratio (BCR) for 2050 and 2100. What does this say about the distribution of costs and benefits over time?
    * **Q1d:** How does the global mortality in 2050 and 2100 change in the two runs? And how does the global BCR change if you include the monetised value of mortality in the damages? *Hint: find the variable that combines the (avoided) economic damages and the monetised value of mortality.*

!!! question "Question 2: regional differences"

    Choose two regions: one from the Global North, one from the Global South (see the [regions documentation](../../components/regions.md) for the full list of regions).

    * **Q2a:** For both regions, compare the damage costs, avoided damages, and mitigation costs in 2050 and 2100. What are the benefit-cost ratios for these two regions?

#### Step 3: Tweak parameters:

Rerun MIMOSA with different parameters. Have a look at the [parameter reference](../../parameters.md) to see which parameters you can change. Interesting parameters could be:

- [`params["economics"]["PRTP"]`](#param__economics.PRTP): The discount rate (pure rate of time preference). Choose values between 0.00 (low end) and 0.03 (high end). The default is 0.015 (corresponding to 1.5%/year).
- [`params["economics"]["damages"]["scale factor"]`](#param__economics.damages.scale%20factor): Scale the damages up or down to see the effect of higher or lower damages. This multiplies all market damages (riverine flooding, labour productivity, sea-level rise). The default is 1.0. Example sensitivity values could be 0.5 (half the damages) or 2.0 (double the damages).
- [`params["temperature"]["TCRE"]`](#param__temperature.TCRE): The transient climate response to cumulative emissions. Choose values between 0.42&nbsp;&deg;C/TtCO<sub>2</sub> (low end) and 0.82&nbsp;&deg;C/TtCO<sub>2</sub> (high end). The default is 0.62&nbsp;&deg;C/TtCO<sub>2</sub> (corresponding to the median).

!!! question "Question 3: sensitivity analysis"

    * **Q3a:** Choose one of the parameters above, or another parameter of your choice, and rerun MIMOSA with two values of that parameter, different than the default. Briefly explain what this parameter means and why you choose this parameter. What normative judgement does this parameter reflect?
    * **Q3b:** What is the new cost-optimal temperature target? 
    * **Q3c:** Make a small causal loop diagram to explain why the change in parameter leads to a different optimal temperature target. *Hint: what does your parameter affect, and how does that affect the optimal temperature target?* If you choose the TCRE as parameter, also include the cumulative emissions until 2100 in your reflection.


## Exercise 2A: impact sectors and adaptation

In the first exercise, you analysed the interplay between climate impacts and mitigation. In this exercise, you will further decompose the sources of climate impacts, and analyse the effect of adaptation.

#### Step 1: Decomposition of climate impacts

!!! question "Question 4: decomposition of climate impacts"

    For this question, use the no-policy run you did in the first exercise.

    * **Q4a:** For the two regions you chose in the previous exercise, compare the damage costs in 2050 and 2100 for the three impact sectors (riverine flooding, labour productivity, and sea-level rise). Which sector is most important for each region? How does this compare to the global picture?

#### Step 2: Including adaptation

!!! tip "Task: Run MIMOSA with adaptation"

    Now that you have analysed the decomposition of climate impacts without adaptation and mitigation, you can analyse the effect of adaptation. Run the following two scenarios:

    === "Run 3: Adaptation-only run"

        In the adaptation only scenario, the only policy response to climate change is through adaptation. The model optimises the regional adaptation costs for each sector, and uses these to reduce the damages in each sector according to the adaptation level. No mitigation is undertaken.

        ```python
        --8<-- "docs/workshops/stsi/runs/run_accreu_ada.py"
        ```

    === "Run 4: Mitigation and adaptation run"

        Here, a cost-benefit analysis is carried out in which adaptation and mitigation policies are implemented simultaneously. As such, the model weighs expenditures on adaptation and mitigation against one another. 

        ```python
        --8<-- "docs/workshops/stsi/runs/run_accreu_mit_ada_joint.py"
        ```

        !!! warning 

            This scenario can take longer to run, because the optimisation is more complex. Instead of just optimising the mitigation level for each region and time, it also needs to optimise the adaptation costs for each region, sector, and time simultaneously.

!!! question "Question 5: effect of adaptation"

    * **Q5a:** In the adaptation-only scenario, how much lower are the *global* damage costs in 2100 compared to the no-policy run? How much are the *global* adaptation costs? What is the benefit-cost ratio for adaptation?
    * **Q5b:** Is the effect of adaptation similar across the three impact sectors (riverine flooding, labour productivity, and sea-level rise)? Which sector benefits most from adaptation? Do you think this is realistic? Why or why not?
    * **Q5c:** In the "mitigation and adaptation" scenario, how much lower are the *global* damage costs in 2100 compared to the no-policy run. How do the adaptation costs compare to the mitigation costs? 
    * **Q5d:** The mitigation and adaptation are optimised simultaneously in that scenario. How does the optimal end-of-century temperature compare to the mitigation-only scenario from exercise 1? Why is it the same/different?

## Exercise 2B: effort sharing and equity

In the next exercise, you will run MIMOSA with different effort sharing approaches. Contrary to the previous exercise, you will not do a CBA run, but a fixed carbon budget. We will choose a carbon budget of 700 GtCO<sub>2</sub>, and run MIMOSA with different effort sharing approaches.

#### Step 1: Run MIMOSA

!!! tip "Task: Run MIMOSA with effort sharing approach"

    For this exercise, you will again do two runs: one with an effort-sharing regime of your choice, and one with the typical cost-minimising approach (default in most IAMs).

    === "Run 1: Effort sharing regime"

        First, choose which effort sharing regime you want to use. You can choose between:

        * [`"equal_mitigation_costs"`](../../components/effortsharing.md#equal-mitigation-costs)
        * [`"equal_total_costs"`](../../components/effortsharing.md#equal-total-costs)
        * [`"per_cap_convergence"`](../../components/effortsharing.md#per-capita-convergence)
        * [`"ability_to_pay"`](../../components/effortsharing.md#ability-to-pay)
        * [`"equal_cumulative_per_cap"`](../../components/effortsharing.md#equal-cumulative-per-capita-emissions)

        More information about these regimes can be found at the [Effort sharing](../../components/effortsharing.md) page in the documentation, or in [van den Berg et al. (2020)](https://doi.org/10.1007/s10584-019-02368-y) (specifically, [Table 1](https://link.springer.com/article/10.1007/s10584-019-02368-y/tables/1)).

        Then, run the following code where you change the variable `regime`.

        ```python hl_lines="3 6"
        --8<-- "docs/workshops/stsi/runs/run_effortsharing.py"
        ```

        1. Change this variable with the chosen option.

    === "Run 2: Cost-minimising regime"

        Next, run MIMOSA with the cost-minimising regime. There is no need for emission trading, so simply use the following code:

        ```python
        --8<-- "docs/workshops/stsi/runs/run_noregime.py"
        ```

#### Step 2: Effect on equity

!!! question "Question 4: Attributed mitigation costs and equity"

    * **Q4a:** Briefly describe the chosen effort sharing regime in your own words, and describe which equity aspects it takes into account, and which ones not.
    * **Q4b:** For the two chosen regions in exercise 1, compare the [mitigation costs](#var__mitigation_costs) in 2050 and 2100. How do these costs compare to the global mitigation costs?
    * **Q4c:** And how do they compare to the cost-benefit run from exercise 1?

#### Step 3: Effect on sovereignty

!!! question "Question 5: Sovereignty and trading of emission reductions"

    When emission trading is enabled, each region's attributed [`mitigation_costs_abs`](#var__emissiontrade::mitigation_costs_abs) consist of its [`domestic_mitigation_costs_abs`](#var__emissiontrade::domestic_mitigation_costs_abs) plus its [`mitigation_cost_trading_balance`](#var__emissiontrade::mitigation_cost_trading_balance). A positive balance means that attributed costs and emission reductions exceed those occurring physically within the region: they need to pay for reductions in other regions; a negative balance means that they are lower: they receive money from other regions to finance their own mitigation effort.

    The sum of [`mitigation_cost_trading_balance`](#var__emissiontrade::mitigation_cost_trading_balance) across regions is always zero. However, to get a sense of how large the financial flows are each year, you can sum all positive values (or all negative values) of this variable.
    
    **Q5a:** How large are the global financial flows in 2050 and in 2100? How do they compare to global GDP in those years? Put this in the context of the 100 billion dollar pledge in the Paris Agreement. How realistic do you think your chosen effort sharing regime is?
