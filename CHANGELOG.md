- v0.1.0:
   - Implemented necessary features to run together with AixCaliBuHa and EnSTATS
- v0.1.1:
   - Fixed bugs necessary to work with AixCaliBuHa and EnSTATS and refactor functions based on feedback
- v0.1.2:
   - Move CalibrationClass to AixCaliBuHa
   - Add scipy.optimize.differential_evolution as an optimizer
- v0.1.3:
   - Move conversion.py to utils and make preprocessing a direct module
   - Introduce current_best_iterate as a parameter for optimization to ensure that the best solution to a problem is still saved even if an iteration step causes an error
   - Make interrupt of optimization through Keyboard-Interrupt possible
   - Adjust Goals functions to make slicing of multiple time-intervals possible.
- v0.1.4:
   - Create a tutorial with juypter-notebook
   - Introduce MultiIndex (from pandas) and make TimeSeriesData extend of the standard DataFrame
   - Adjust all classes, most notably Goals. This class will go into AixCaliBuHa, as it is only relevant for Calibrations.
- v0.1.5:
   - Remove dlib and PyQt5 from setup.py and delete TunerParas.show()
   - Refactor Optimizer so the framework parameter is only necessary to call optimize()
- v0.1.6:
   - Issue23: Change conversion functions to correctly handle multiheaders
   - Issue24: Add converters and correctly inherit from pd.DataFame in TimeSeriesData
   - Add functions for configuration using yaml
   - Add regex functions for extraction of modelica variables
   - Add option to directly return results as a dataframe using simulateMultiResultsModel.
- v0.1.7:
   - Issue13: Add an FMU API as simulation api
   - Issue36: Use Python Logging as default logger in all modules
   - Issue38: Fix future warning in pandas loffset
   - Issue39: Add simres from modelicares to avoid version errors with matplotlib.
   - Issue41: Fix inheritance of `pd.DataFrame` in `TimeSeriesData`.
              This also enables converting any single-index df to the required multi-index format (See #37).
   - Issue42: Move `TunerParas` to `AixCaliBuHA`
   - Add unit-tests for the dymola-api.
   - Use f-strings only
   - Update setup.py and requirements
   - Use `TimeSeriesData` in classes as output in the simulation api
- v0.1.8:
   - Drop support for Python 3.6 (See #44)
      - Breaking changes in pandas forces us to increase the version required
      - Pandas dropped the support for Python 3.6
- v0.2.0:
   - Prepare JOSS publication. Fixed #48
   - Prepare workshop using new examples. Fixes #49
   - Add multiprocessing to Simulation APIs. Fixed #5
   - Genereal restructuring of examples, tutorials and tests
   - Several new functions for easier access / utility
   - Add inputs option for `DymolaAPI`