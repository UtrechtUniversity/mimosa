"""
Plot functions. Not necessary if dashboard is used.
"""

import pandas as pd

try:
    import plotly.express as px
except ModuleNotFoundError:
    pass


def visualise_ipopt_output(output_file):
    with open(output_file, "r") as file:
        in_iterations = False

        iterations = []

        for line in file:
            if line.startswith("iter "):
                in_iterations = True
            if line.strip() == "":
                in_iterations = False

            if in_iterations and line.startswith(" "):
                split = line.strip().split(" ")[:4]

                # Check if it was a recovered iteration
                if "r" in split[0]:
                    recovered = True
                    split = split[0].split("r") + split[1:-1]
                else:
                    recovered = False
                iterations.append(split + [recovered])

        iterations_df = pd.DataFrame(
            iterations, columns=["iter", "objective", "inf_pr", "inf_du", "recovered"]
        )
        iterations_df = iterations_df.astype(
            {"iter": int, "objective": float, "inf_pr": float, "inf_du": float}
        )

    fig = (
        px.scatter(
            iterations_df,
            x="iter",
            y=["objective", "inf_pr", "inf_du"],
            facet_row="variable",
            color="recovered",
        )
        .update_yaxes(matches=None, type="log")
        .update_yaxes(row=3, type="linear")
    )

    fig.write_html(output_file.split(".")[0] + ".html", include_plotlyjs="cdn")
