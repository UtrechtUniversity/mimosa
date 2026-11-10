## Local installation

The preferred setup is to download and install MIMOSA on your local machine. To do this, download the following zip file with the MIMOSA code and extract it to a folder of your choice:

[Download MIMOSA](https://github.com/UtrechtUniversity/mimosa/archive/refs/heads/stsi.zip){.md-button}

Then, open an Anaconda Prompt (Windows) or terminal (Mac/Linux) and run the following commands:

Navigate to the folder where you extracted MIMOSA:

```bash
cd path/to/mimosa-stsi
```

Then activate the STSI conda environment:

```bash
conda activate STSI
```

Install MIMOSA in editable mode so you can make changes to the code and run them without reinstalling:

```bash
pip install -e .
```

Finally, install IPOPT, which is required to run the model:

```bash
conda install -c conda-forge ipopt
```

## Google Colab installation

If the above instructions don't work, you can run MIMOSA in Google Colab. This is a cloud-based Python environment that runs in your browser and does not require any installation. It is slower than running MIMOSA locally, requires a Google account, but it is easier to set up.

Save the following Google Colab notebook to your Google Drive and open it in Colab. It will install MIMOSA and its dependencies, and set up a working directory for the exercises.

[https://colab.research.google.com/drive/1DzkT0ECMVzHMK6B48whb_17PX7EbSsx-?usp=sharing](https://colab.research.google.com/drive/1DzkT0ECMVzHMK6B48whb_17PX7EbSsx-?usp=sharing)