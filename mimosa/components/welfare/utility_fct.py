"""
Common utility function
"""

from mimosa.common import soft_min


def calc_utility(consumption, population, elasmu):
    """
    The utility function is a concave function of per-capita consumption, given by:

    $$ \\text{utility}(C, L) = \\left( \\left(\\frac{C}{L}\\right)^{1 - \\text{elasmu}} - 1 \\right) \\cdot \\frac{1}{1 - \\text{elasmu}}$$

    where $C$ is the consumption and $L$ the population of a region. $\\text{elasmu}$ is the elasticity of marginal utility. A value of $\\text{elasmu}$ close to 1 approaches a logarithmic utility function:
    ``` plotly
    {"file_path": "./assets/plots/utility_fct.json"}
    ```

    """

    # Note that the `soft_min` function is used to avoid division by zero
    return (soft_min(consumption / population) ** (1 - elasmu) - 1) / (1 - elasmu)
