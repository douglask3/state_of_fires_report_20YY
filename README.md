# Bayesian-based fire models

## Table of Contents
- [Introduction](#introduction)
- [Features](#features)
- [Installation](#installation)
- [Obtaining Driving Data](#obtaining-driving-data)
- [Configuration Settings](#configuration-settings)
- [Running the Models](#running-the-models)
- [Results](#results)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)
- [State of Wildfires report](#State-of-Wildfires-report)



## Introduction
This repository contains a series of Bayesian-based fire models. These models follow a common inference and sampling workflow to predict fire behaviour based on various driving data. . At the moment, we have two models that target burned area:
*	ConFire, has been tested and is working as expected.
*	FLAME, is also operational but is located in a separate repository. It needs to undergo testing in our current environment. You can find it at https://github.com/malu-barbosa/FLAME.
  
Additionally, we are in the process of working on INFERNO, which is derived from JULES-ES-INFERNO ([Mangeon et al. 2016]( https://gmd.copernicus.org/articles/9/2685/2016/)) and working on a  fireMIP ensemble optimisation scheme. We are also extending these two models to cover other aspects of fire regimes beyond burned area.

## Features
- Bayesian inference for fire modelling
- Flexible configuration settings
- Different fire models for relating drivers to burnt area
- Scalable to different data sets and scenarios
- Detailed logging and result output

## Installation
Follow these steps to install the necessary software and dependencies:

1. Clone the repository:
    ```bash
    git clone [https://github.com/yourusername/your-repo.git](https://github.com/douglask3/Bayesian_fire_models.git)
    ```
2. Navigate into the project directory:
    ```bash
    cd Bayesian_fire_models
    ```
3. Install the required packages:
    
    ```bash
    conda env create -f environment.yml
    conda activate bayesian-fire-models
    ```

## Obtaining Driving Data
The driving data required for the models are listed [here](https://github.com/douglask3/Bayesian_fire_models/blob/main/README/Datasets). Once you have downloaded the dataset you want, save it to the `data/data/driving_data/` directory within the project folder or update the path in the corresponding configuration file (see below) to its location.

## Configuration Settings
Configuration settings can be found in the text files in `namelists\` dir. [namelists/nrt-evaluation.txt](https://github.com/douglask3/Bayesian_fire_models/blob/main/namelists/nrt-evaluation.txt) is quite a good simple example that works for [ConFire](https://github.com/douglask3/Bayesian_fire_models/blob/main/README/ConFire.md). There are some model speific parameters, so you'll have to check specific under [Model Setup](#model-setup). But this is common to all models.

Each parameter is set using `parameter_name:: parameter_value'. "parameter_name" is a parameter or setting used by the framework. "parameter_value" covers most common Python objects (ints, floats, string, lists, common function or class objects) and some extra objects from sync or this repo. Some fields allow wildcard entries that are set as a list within another parameter and looped over, thereby saving lines in the configuration file. These are indicated in the example, but wildcards are never compulsory. 



| Parameter               | Description                                                   | Compulsory | Example                                                                                      |
|-------------------------|---------------------------------------------------------------|------------|-----------------------------------------------------------------------------------------|
| `regions`               | List of regions to model - useful if running the exact same run over multiple  driving datasets  | No - but required if using `<<region>>` wildcards.  | `['Greece', 'Canada', 'NW_Amazon']`            |
| `model_title`           | Title of the model. Can use `regions` to set up a new run for each region | Yes        | `'ConFire_<<region>>-nrt-evaluation1'`                                  |
| `dir_training`          | Directory containing driving/target data for training         | Yes        | `"data/data/driving_data/<<region>>/nrt/period_2013_2023/"`                                  |
| `y_filen`               | Netcdf filename for target variable, either within  `dir_training` or relative for pull path is starting with '.' or '~'  | Yes        | `"burnt_area.nc"`           |
| `CA_filen` | Netcdf filename for area weights for model training - i.e. if you want to weigh some grid cells more than others.                     | No         | `None`                      |
| `x_filen_list`          | List of filenames for predictor variables                     | Yes        | `["VOD-12monthMax.nc", "VOD-12Annual.nc", "Fuel-Moisture-Live.nc", ...]`                     |
| `model_class`           | The name of the fire model we are going to use. Coded up in `fire_model/'.     | Yes        | `ConFire`                                                              |
| `link_func_class`       | The name of the link function/assumed error distribution. Coded up in `link_distribution/`         | Yes        | `zero_inflated_logit`                              |
| `priors`                | Priors for Bayesian inference. These use their own funky definition rather than a standard Python object, but are defined using a dict, with the following fields that need filling out, depending on prior type: | At least one. This is model and link function specific. These are parameters used in either the model or link function | Some examples below: |
|     |  `pname` is the parameter name used by the model. See the specific model for details. if `npame` starts with the string `link-`, then it is a parameter used in the link function. Again, see the specific link function for info. |   | `{'pname': "link-sigma", 'np': 1, 'dist': 'HalfNormal', 'sigma': 0.5}`  |
|     |  `dist`. The prior can be based on a pymc prior distribution. If it is, you can use any in the pymc library: [https://www.pymc.io/projects/docs/en/stable/api/distributions.html](https://www.pymc.io/projects/docs/en/stable/api/distributions.html). To use one of these, enter a pymc distribution name in the entry `dist`. You then enter each input used by that distribution as a new dict item (e.g. `upper` and `lower` in the example). `np` is normally an optional field (though some models or link functions may require it) that says how many times you need this distribution. See model or link function for specifcs | | `{'pname': "Fmax", 'np': 1, 'dist': 'Uniform', 'lower': 0.00001, 'upper': 0.9999}`  |
|                         |                                                         |            | `{'pname': "x0", 'np': 6, 'dist': 'Normal', 'mu': 0.0, 'sigma': 10.0}`                       |
|                         |  Sometime you want more certain priors (i.e, these are fixed and do not change  during optimization). For this, the only addition dict field you need is `value` and the value matches the python object required by that parameter in the model you are using    |            | `{'pname': "driver_Direction", 'value': [[1, 1], [1, 1], [1, 1, -1], [1, 1, 1], [1, 1, 1, 1], [1]]}`          |
 `niterations`           | This is the number of iterations or sample the model with use when traning the data. When sampling the optimised distribution, you wont be able to sample more than niterations x cores, so make sure there two parameters are se high enough                                          | Yes        | `1000`                                                                                         |
| `cores`                 | This is the number of chains (optimisation attempts) AND the number of computer cores on platforms where multicore-ing in a thing   | Yes        | `100`                                                                   |
| `fraction_data_for_sample` | The fraction of the target data used for optimization | Yes        | `0.5`                                                                                        |
| `subset_function`       | Function to subset the data                                   | No, and you can have multiple too        | `sub_year_months`                                                                            |
|                         |                                                               |            | `sub_year_range`                                                                             |
| `subset_function_args`  | Arguments for subset function. As a sict with inputs for the subset function. One line for each function above in order.   | If  any of the the subset functions requires them        | `{'months_of_year': [4, 5, 6, 7, 8]}`                                                        |
|                         |                                                               |            | `{'year_range': [2013, 2017]}`                                                               |
| `subset_function_args_eval` | This can replace the subset function aregument when you are sampling the posterior. Useful for out-of-sample experiments.  | No        | `{'months_of_year': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]}`                                 |
|                         |                                                               |            | `{'year_range': [2018, 2023]}`                                                               |
| `grab_old_trace`        | Whether to use old traces and sample from previous optimisation attempts. If `True`, then it will attempt to find old files that have a similar look to this configiration file. But its not fullproof so if in doubt, set to `False`                   | No         | `True`                                                                                       |
| `dir_outputs`           | Directory for outputs                                         | Yes        | `'outputs/'`                                                                                 |
| `sample_for_plot`       | Number of samples from the optimised trace for evaluation and plotting                                | Yes        | `100`                                                                                        |
| `levels`                | colourmap levels for burnt area maps                                      | Yes        | `[0, 0.01, 0.03, 0.1, 0.3, 0.5, 1.0]`                                                        |
| `dlevels`               | colourmap levels for difference in burnt area maps                                 | Yes        | `[-20, -10, -5, -2, -1, -0.1, 0.1, 1, 2, 5, 10, 20]`                                        |
| `cmap`                  | Colormap for plots                                            | Yes        | `'OrRd'`                                                                                     |
| `dcmap`                 | Differential colormap for plots                               | Yes        | `'RdBu_r'`                                                                                   |




## Running the Models
Over the next few months, we will generalise the model's running so it works the same way for any more setups, and you define the name list at runtime. For now, though, we have basic model execution files for ConFire: one for near real-time studies (`run_ConFire-NRT.py`) and one for ISI-MIP-driven runs for attribution and future projections (`run_ConFire.py`). For each, open the file, under `__main__`, make sure the variable is set to you namelist, and the run:

* for isimip
```bash
python run_ConFire.py
```

* for nrt
```bash
python run_ConFire-NRT.py
```

## Results
The results will be saved in the `outputs/` directory, though this can be updated in the namelists. There are some model specific files that will get produced, but common across all models are:

## Contributing
Contributions are welcome! Please read the [CONTRIBUTING.md](README/CONTRIBUTING.md) file for guidelines on how to contribute.

## License
This project is licensed under the  GNU GENERAL PUBLIC LICENSE version 3 License. See the [LICENSE](LICENSE) file for details.

## Contact
Please contact [Dougas Kelley] at [doukel@ceh.ac.uk] for any questions or issues.

## State of Wildfires report
The State of Wildfires report has been a major driver of this development. Here's some info for anyone whose found their way here and wants to perform those runs again

### 2023/24

To reproduce results in the State of Wildfire's report, make sure you have the version at tag SoW23_sub (or download the Zenodo archived code that can be found with the paper: https://doi.org/10.5194/essd-2024-218, along with dataset information). The results from this paper were obtained using the [Running the Models](#running-the-models) commands above. The namelists are already set within these files, but you may need to update paths in the following in the `namelists` directory:
* `isimip.txt` - used for attribution and future projections
* `isimip-evaluation.txt` used to evalute the configuration for attribution and future projections
* `nrt.txt` used for 2023 fire season driver analysis
* `nrt-evalution.txt` - used to evaluate the driver analysis configuation




### Notes on constraining area


#### *Political areas*
When opening data, setting ''Country'' or ''Continent'' will constrain the extent to that country or continent, and mask areas outside of it. Uses Natural Earth. If you define a country, it one look at the continent. Use None is you don't want any. Continent options are:
* 'South America'
* 'Oceania'
* 'Europe'
* 'Afria'
* 'North America'
* 'Asia'

#### *Ecoregions*
''ecoregions'' is a numeric list (i.e [3, 7, 8]) where numbers pick Olson bomes and mask out everywhere else. If you  pick more than one, it returns a map of all of them.
* **None** Return all areas.
* **1** Tropical and subtropical moist broadleaf forests
* **2** Tropical and subtropical dry broadleaf forests
* **3** Tropical and suptropical coniferous forests
* **4** Temperate broadleaf and mixed forests
* **5** Temperate Coniferous Forest
* **6** Boreal forests / Taiga
* **7** Tropical and subtropical grasslands, savannas and shrublands
* **8** Temperate grasslands, savannas and shrublands
* **9** Flooded grasslands and savannas
* **10** Montane grasslands and shrublands
* **11** Tundra
* **12** Mediterranean Forests, woodlands and scrubs
* **13** Deserts and xeric shrublands
* **14** Mangroves

#### *Brazillian legal Biomes*

''Biomes'' is a numeric list where numbers pick Brazilian biomes and mask out everywhere else. If you pick more than one, it returns a map of all of them.

* **1** Amazonia
* **2** Caatinga
* **3** Cerrado
* **4** Atlantic Forest
* **5** Pampa
* **6** Pantanal

#### *GFED Regions*

#### *AR6 regions*

#### *To year range*

#### *To months of year*

