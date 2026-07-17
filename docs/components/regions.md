By default, MIMOSA uses the 26 IMAGE regions. More information about this regional definition is
available on the [IMAGE website](https://models.pbl.nl/image/Region_classification_map).

The model region definition is named by the [`regionstype`](../parameters.md#regionstype) setting,
while [`regions`](../parameters.md#regions) contains the region codes included in a run. The
configuration schema also recognises `SSP5` and `World` definitions. Using a different definition
requires matching time-dependent input data and, where necessary, a registered mapping for regional
parameters. See [Regional parameters](../extending/parameters.md#regional-params) for details.

The map and table below describe the default IMAGE26 regions. Hover over the map to see a region's
name:

``` plotly
{"file_path": "./assets/plots/image_regions.json"}
```


The full country to region mapping can be downloaded from:

[IMAGE26 country-to-region mapping :octicons-arrow-up-right-24:](https://raw.githubusercontent.com/UtrechtUniversity/mimosa/refs/heads/master/mimosa/inputdata/regions/ISO_IMAGE_regions_R5_regions.csv){.md-button}

The default IMAGE26 abbreviations correspond to the following regions:

{regions::definitions}
