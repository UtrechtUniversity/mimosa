from setuptools import setup

with open("README.md") as fh:
    description = fh.read()

with open("LICENSE") as fh:
    license_txt = fh.read()

setup(
    name="mimosa",
    version="0.2.5",
    author="Kaj-Ivar van der Wijst",
    author_email="k.vanderwijst@uu.nl",
    packages=["mimosa"],
    url="https://utrechtuniversity.github.io/mimosa/",
    license=license_txt,
    description="MIMOSA: Integrated Assessment Model for Cost-Benefit Analysis",
    long_description=description,
    long_description_content_type="text/markdown",
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.22",
        "pandas",
        "pyomo",
        "pint",
        "pyyaml",
        "scipy",
        "networkx",
    ],
    include_package_data=True,
)
