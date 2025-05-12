from setuptools import setup

with open("README.md") as fh:
    description = fh.read()

with open("LICENSE") as fh:
    license_txt = fh.read()

setup(
    name="mimosa",
    version="0.1.8",
    author="Kaj-Ivar van der Wijst",
    author_email="k.vanderwijst@uu.nl",
    packages=["mimosa"],
    url="https://utrechtuniversity.github.io/mimosa/",
    license=license_txt,
    description="MIMOSA: Integrated Assessment Model for Cost-Benefit Analysis",
    long_description=description,
    long_description_content_type="text/markdown",
    install_requires=["numpy<2.0", "pandas", "pyomo<=6.7.1", "pint", "pyyaml", "scipy"],
    include_package_data=True,
)
