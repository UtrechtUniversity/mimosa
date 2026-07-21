# Getting started

To change MIMOSA itself or contribute to its documentation, first fork or clone
the repository and open a terminal in its root directory (the directory
containing `pyproject.toml`). We recommend using a separate conda environment:

```bash
conda create --name mimosa-dev python=3.11
conda activate mimosa-dev
```

Install MIMOSA in editable mode, together with the packages needed for testing
and building the documentation:

```bash
python -m pip install --editable ".[test,docs]"
```

Editable installation means that changes to the source code are used directly;
you do not need to reinstall MIMOSA after every change. If you only need one set
of extra packages, use `.[test]` or `.[docs]` instead.

## Running the tests

The following command runs the tests that do not require IPOPT:

```bash
python -m pytest tests -m "not ipopt"
```

After [installing IPOPT](../installation.md#installing-the-optimisation-engine-ipopt),
run the full test suite with:

```bash
python -m pytest tests
```

## Working on the documentation

To preview the documentation while editing it, run:

```bash
python -m mkdocs serve
```

MkDocs prints the local address where the preview is available and updates it
when a documentation file changes. Before submitting documentation changes,
also run the same strict build used by the documentation check in GitHub:

```bash
python -m mkdocs build --strict
```

Run these commands from the repository root so that MkDocs can find its
configuration, hooks and source files.


[Next: How MIMOSA is structured :octicons-arrow-right-24:](index.md){.md-button}
