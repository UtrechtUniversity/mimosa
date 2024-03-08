from setuptools import setup

with open("README.md") as fh:
    description = fh.read()

with open("LICENSE") as fh:
    license_txt = fh.read()

setup(
    name="mimosa",
    version="0.1.5",
    author="Kaj-Ivar van der Wijst",
    author_email="k.i.vanderwijst@gmail.com",
    packages=["mimosa"],
    url="https://kvanderwijst.github.io/MIMOSA/",
    license=license_txt,
    description="MIMOSA: Integrated Assessment Model for Cost-Benefit Analysis",
    long_description=description,
    long_description_content_type="text/markdown",
    install_requires=["numpy", "pandas", "pyomo", "pint", "pyyaml", "scipy"],
    include_package_data=True,
)
