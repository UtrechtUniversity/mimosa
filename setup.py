from setuptools import setup

with open("README.md") as fh:
    description = fh.read()

setup(
    name="mimosa",
    version="0.1.0",
    author="Kaj-Ivar van der Wijst",
    author_email="k.i.vanderwijst@gmail.com",
    packages=["mimosa"],
    # url="http://pypi.python.org/pypi/PackageName/",
    license="LICENSE.txt",
    description="MIMOSA: Integrated Assessment Model for Cost-Benefit Analysis",
    long_description=description,
    install_requires=["numpy", "pandas", "pyomo", "pint", "pyyaml"],
    include_package_data=True,
)
