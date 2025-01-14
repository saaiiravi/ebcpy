[![pylint](https://ebc.pages.rwth-aachen.de/EBC_all/github_ci/ebcpy/master/pylint/pylint.svg )](https://ebc.pages.rwth-aachen.de/EBC_all/github_ci/ebcpy/master/pylint/pylint.html)
[![documentation](https://ebc.pages.rwth-aachen.de/EBC_all/github_ci/ebcpy/master/docs/doc.svg)](https://ebc.pages.rwth-aachen.de/EBC_all/github_ci/ebcpy/master/docs/index.html)
[![coverage](https://ebc.pages.rwth-aachen.de/EBC_all/github_ci/ebcpy/master/coverage/badge.svg)](https://ebc.pages.rwth-aachen.de/EBC_all/github_ci/ebcpy/master/coverage)
[![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)
[![build](https://ebc.pages.rwth-aachen.de/EBC_all/github_ci/ebcpy/master/build/build.svg)](https://ebc.pages.rwth-aachen.de/EBC_all/github_ci/ebcpy/master/build/build.svg)


# ebcpy

This **PY**thon package provides generic functions and classes commonly
used for the analysis and optimization of **e**nergy systems, **b**uildings and indoor **c**limate (**EBC**).

Key features are:

* `TimeSeriesData`
* `SimulationAPI`'s
* Optimization wrapper
* Pre-/Postprocessing
* Modelica utilities

# Installation

To install, simply run
```
pip install ebcpy
```

In order to use all optional dependencies (e.g. `pymoo` optimization), install via:

```
pip install ebcpy[full]
```

If you encounter an error with the installation of `scikit-learn`, first install `scikit-learn` separatly and then install `ebcpy`:

```
pip install scikit-learn
pip install ebcpy
```

If this still does not work, we refer to the troubleshooting section of `scikit-learn`: https://scikit-learn.org/stable/install.html#troubleshooting. Also check [issue 23](https://github.com/RWTH-EBC/ebcpy/issues/23) for updates.

In order to help development, install it as an egg:

```
git clone https://github.com/RWTH-EBC/ebcpy
pip install -e ebcpy
```

# How to get started?

We recommend running our jupyter-notebook to be guided through a **helpful tutorial**.  
For this, run the following code:
```
# If jupyter is not already installed:
pip install jupyter
# Go into your ebcpy-folder (cd \path_to_\ebcpy) or change the path to tutorial.ipynb and run:
jupyter notebook tutorial\tutorial.ipynb
```

Or, clone this repo and look at the examples\README.md file.
Here you will find several examples to execute.

# TimeSeriesData
Note that we use our own `TimeSeriesData` object which inherits from `pd.DataFrame`. The aim is to make tasks like loading different filetypes or applying multiple tags to one variable more convenient, while conserving the powerful tools of the DataFrame.
Just a quick intro here:

## Variables and tags
```
>>> from ebcpy.data_types import TimeSeriesData
>>> tsd = TimeSeriesData(r"path_to_a_supported_file")
>>> print(tsd)
Variables    T_heater              T_heater_1            
Tags             meas         sim        meas         sim
Time                                                     
0.0        313.165863  313.165863  293.173126  293.173126
1.0        312.090271  310.787750  293.233002  293.352448
2.0        312.090027  310.796753  293.385925  293.719055
3.0        312.109436  310.870331  293.589233  294.141754
```

As you can see, our first column level is always a variable, and the second one a tag.
This is especially handy when dealing with calibration or processing tasks, where you will have multiple
versions (tags) for one variable. The default tag is `raw` to indicate the unmodified data.
To access a variable, you have to call `.loc`. To access multiple variables that all hold one tag use `xs`:
```python
# All tags:
tsd.loc[:, "variable_name"]
# One specific tag:
tsd.loc[:, ("variable_name", "tag_name")]
# One tag, all variables:
tsd.xs("tag_name", axis=1, level=1)
```
## FloatIndex and DateTimeIndex
Measured data typically holds a datetime stamps (`DateTimeIndex`) while simulation result files hold absolute seconds (`FloatIndex`). 
You can easily convert back and forth using:
```python
# From Datetime to float
tsd.to_float_index()
# From float to datetime
tsd.to_datetime_index()
# To clean your data and create a common frequency:
tsd.clean_and_space_equally(desired_freq="1s")
```

# Documentation
Visit hour official [Documentation](https://ebc.pages.rwth-aachen.de/EBC_all/github_ci/ebcpy/master/docs/index.html).

# Problems?
Please [raise an issue here](https://github.com/RWTH-EBC/ebcpy/issues/new).
