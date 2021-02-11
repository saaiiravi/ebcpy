"""Module containing the DymolaAPI used for simulation
of Modelica-Models."""

import sys
import os
import warnings
import atexit
import pandas as pd
from ebcpy import simulationapi
from ebcpy import data_types
from ebcpy.modelica import manipulate_ds
DymolaInterface = None  # Create dummy to later be used for global-import
DymolaConnectionException = None  # Create dummy to later be used for global-import


class DymolaAPI(simulationapi.SimulationAPI):
    """
    Dymola interface class

    :param str,os.path.normpath cd:
        Dirpath for the current working directory of dymola
    :param str model_name:
        Name of the model to be simulated
    :param list packages:
        List with path's to the packages needed to simulate the model
    :keyword Boolean show_window:
        True to show the Dymola window. Default is False
    :keyword Boolean get_structural_parameters:
        True to automatically read the structural parameters of the
        simulation model and set them via Modelica modifiers. Default 
        is True
    :keyword Boolean equidistant_output:
        If True (Default), Dymola stores variables in an 
        equisdistant output and does not store variables at events.
    :keyword str dymola_path:
         Path to the dymola installation on the device. Necessary 
         e.g. on linux, if we can't find the path automatically.
    :keyword str dymola_interface_path:
        Same as for dymola_path. If we can't find the dymola installation,
        you can pass the path to your dymola.egg via this parameter.
    :keyword int n_restart:
        Number of iterations after which Dymola should restart.
        This is done to free memory. Default value -1. For values
        below 1 Dymola does not restart.
    """

    show_window = False
    get_structural_parameters = True
    # Alter the output-format so all simulations will result in the same array-length
    equidistant_output = True
    _supported_kwargs = ["show_window",
                         "get_structural_parameters",
                         "dymola_path",
                         "dymola_interface_path",
                         "equidistant_output",
                         "n_restart"]
    dymola_path = ""
    _bit_64 = True  # Whether to use 32 bit or not.

    dymola = None
    # Default simulation setup
    sim_setup = {'startTime': 0.0,
                 'stopTime': 1.0,
                 'numberOfIntervals': 0,
                 'outputInterval': 1,
                 'method': 'Dassl',
                 'tolerance': 0.0001,
                 'fixedstepsize': 0.0,
                 'resultFile': 'resultFile',
                 'autoLoad': False,
                 'initialNames': [],
                 'initialValues': [],
                 'resultNames': []}

    def __init__(self, cd, model_name, packages, **kwargs):
        """Instantiate class objects."""
        super().__init__(cd, model_name)

        # First import the dymola-interface
        if "dymola_interface_path" in kwargs:
            if not kwargs["dymola_interface_path"].endswith(".egg"):
                raise TypeError("Please provide an .egg-file for the dymola-interface.")
            dymola_interface_path = kwargs["dymola_interface_path"]
            if not (os.path.isfile(dymola_interface_path) and
                    os.path.exists(dymola_interface_path)):
                raise FileNotFoundError(f"Given path {dymola_interface_path} can not be found on "
                                        "your machine.")
        else:
            dymola_interface_path = None

        if "dymola_path" in kwargs:
            dymola_path = kwargs["dymola_path"]
            if not (os.path.isfile(dymola_path) and os.path.exists(dymola_path)):
                raise FileNotFoundError(f"Given path {dymola_path} can not be found on "
                                        "your machine.")
        else:
            dymola_path = None

        if (not dymola_path) or (not dymola_interface_path):
            # First get the dymola-install-path:
            _dym_install = self.get_dymola_install_path()
            if _dym_install:
                if not dymola_path:
                    dymola_path = self.get_dymola_path(_dym_install)
                if not dymola_interface_path:
                    dymola_interface_path = self.get_dymola_interface_path(_dym_install)
            else:
                raise FileNotFoundError("Could not find a dymola-interface on your machine.")

        # Set the path variables:
        self.dymola_interface_path = dymola_interface_path
        self.dymola_path = dymola_path
        if "bin64" not in self.dymola_path:
            self._bit_64 = False

        self._global_import_dymola()
        self.packages = packages

        # Update kwargs with regard to what kwargs are supported.
        _not_supported = set(kwargs.keys()).difference(self._supported_kwargs)
        if _not_supported:
            raise KeyError("The following keyword-arguments are not "
                           f"supported: \n{', '.join(list(_not_supported))}")

        # By know only supported kwargs are in the dictionary.
        self.__dict__.update(kwargs)

        # Import n_restart
        self.sim_counter = 0
        self.n_restart = kwargs.get("n_restart", -1)
        if not isinstance(self.n_restart, int):
            raise TypeError(f"n_restart has to be type int but "
                            f"is of type {type(kwargs['n_restart'])}")

        self._dummy_dymola_instance = None  # Ensure self._close_dummy gets the attribute.
        if self.n_restart > 0:
            self.logger.info("Open blank placeholder Dymola instance to ensure"
                             " a licence during Dymola restarts")
            self._dummy_dymola_instance = self._open_dymola_interface()
            atexit.register(self._close_dummy)

        # List storing structural parameters for later modifying the simulation-name.
        self._structural_params = []
        # Parameter for raising a warning if to many dymola-instances are running
        self._critical_number_instances = 10
        self._setup_dymola_interface()
        # Register this class to the atexit module to always close dymola-instances

    def simulate(self, savepath_files="", show_eventlog = False, squeeze=True):
        """
        Simulate the current setup.
        If simulation terminates without an error, you can either
         - save the files in a given savepath (savepath_files) or
         - get the trajectories specified by `resultNames` returned.

         Some Notes on using `resultNames`:
        - You can't use `outputInterval`. Instead you have to use `numberOfIntervals`.
          An attempt is made to convert it internally. For this to work,
          `outputInterval` has to be an even divisor of the interval given
          by`stopTime-startTime`. In the case of `startTime=0, stopTime=100`,
          `outputInterval` should be  `1, 2, 4, 5, 10, ...`. `80` would not work.
          :raises ValueError if `outputInterval` is wrong
        - You have to pass an `initialName` and `initialValue`.
          Else the result is always empty
        - If `initialValues` is a 1D list (e.g. `[1, 2]`), an error get's thrown.
          It has to be 2D list (e.g. [[1, 2]]). As we normally use only
          one parameter at a time, we automatically convert any 1D list
          to a 2D list. Passing a 2D list to the `sim_setup` also works.
        - The resulting dataframe has size `numberOfIntervals + 1` this is
          due to the structure in Modelica.

        :param str,os.path.normpath savepath_files:
            If path is provided, the relevant simulation results will be saved
            in the given directory.
            If not, the simulation setting `resultNames` is used to store the
            trajectories of the simulation and return them (See also: returns)
        :param Boolean show_eventlog:
            Default False. True to show evenlog of simulation (advanced)
        :param Boolean squeeze:
            Default True. If only one set of initialValues is provided,
            a DataFrame is returned directly instead of a list.

        Returns:
        if savepath_files:
            :return str,os.path.normpath filepath:
                Filepath of the result file.
        else
            :return pd.DataFrame,list dfs:
                If len(sim_setup['initialValues']) is one and squeeze=True,
                a DataFrame with the columns being equal to
                sim_setup['resultNames'] and an index of length
                sim_setup['numberOfIntervals'] + 1
                If multiple set's of initial values are given, one
                dataframe for each set is returned in a list
        """
        if show_eventlog:
            self.dymola.experimentSetupOutput(events=True)
            self.dymola.ExecuteCommand("Advanced.Debug.LogEvents = true")
            self.dymola.ExecuteCommand("Advanced.Debug.LogEventsInitialization = true")

        if self._structural_params:
            warnings.warn(f"Warning: Currently, the model is re-translating for each simulation.\n"
                          f"You should add to your Modelica tuner parameters \"annotation(Evaluate=false)\".\n"
                          f"Check for these parameters: {', '.join(self._structural_params)}")
            # Alter the model_name for the next simulation
            self.model_name = self._alter_model_name(self.sim_setup,
                                                     self.model_name, self._structural_params)

        # Restart Dymola after n_restart iterations
        self._check_restart()

        if savepath_files:
            res = self.dymola.simulateExtendedModel(
                self.model_name,
                startTime=self.sim_setup['startTime'],
                stopTime=self.sim_setup['stopTime'],
                numberOfIntervals=self.sim_setup['numberOfIntervals'],
                outputInterval=self.sim_setup['outputInterval'],
                method=self.sim_setup['method'],
                tolerance=self.sim_setup['tolerance'],
                fixedstepsize=self.sim_setup['fixedstepsize'],
                resultFile=self.sim_setup['resultFile'],
                initialNames=self.sim_setup['initialNames'],
                initialValues=self.sim_setup['initialValues'])
        else:
            # Internally convert output Interval to number of intervals
            # (Required by function simulateMultiResultsModel

            num_ints = self.sim_setup['numberOfIntervals']
            if num_ints == 0:
                generated_num_ints = (self.sim_setup['stopTime'] - self.sim_setup['startTime']) / \
                                     self.sim_setup['outputInterval']
                if int(generated_num_ints) != generated_num_ints:
                    raise ValueError(
                        "Given outputInterval and time interval did not yield an integer numberOfIntervals."
                        "To use this functions without savepaths, you have to provide either a numberOfIntervals"
                        "or a value for outputInterval which can be converted to numberOfIntervals.")
                else:
                    num_ints = generated_num_ints
            # Handle 1 and 2 D initial names
            initial_values = self.sim_setup.get('initialValues', [])
            # Convert a 1D list to 2D list
            if isinstance(initial_values[0], (float, int)):
                initial_values = [initial_values]

            # Handle the time of the simulation:
            res_names = self.sim_setup['resultNames']
            if "Time" not in res_names:
                res_names.append("Time")
            res = self.dymola.simulateMultiResultsModel(
                self.model_name,
                startTime=self.sim_setup['startTime'],
                stopTime=self.sim_setup['stopTime'],
                numberOfIntervals=int(num_ints),
                method=self.sim_setup['method'],
                tolerance=self.sim_setup['tolerance'],
                fixedstepsize=self.sim_setup['fixedstepsize'],
                resultFile=None,
                initialNames=self.sim_setup['initialNames'],
                initialValues=initial_values,
                resultNames=res_names)

        if not res[0]:
            self.logger.error("Simulation failed!")
            self.logger.error("The last error log from Dymola:")
            self.logger.error(self.dymola.getLastErrorLog())
            raise Exception(f"Simulation failed: Look into dslog.txt "
                            f"at {os.path.join(self.cd, 'dslog.txt')} of the simulation.")

        if self.get_structural_parameters:
            # Get the structural parameters based on the error log
            self._structural_params = self._filter_error_log(self.dymola.getLastErrorLog())

        if savepath_files:
            _save_name_dsres = f"{self.sim_setup['resultFile']}.mat"
            if not os.path.isdir(savepath_files):
                os.mkdir(savepath_files)
            for filepath in [_save_name_dsres, "dslog.txt", "dsfinal.txt"]:
                # Delete existing files
                if os.path.isfile(os.path.join(savepath_files, filepath)):
                    os.remove(os.path.join(savepath_files, filepath))
                # Move files
                os.rename(os.path.join(self.cd, filepath),
                          os.path.join(savepath_files, filepath))
            return os.path.join(savepath_files, _save_name_dsres)
        else:
            data = res[1]
            dfs = []
            for ini_val_set in data:
                df = pd.DataFrame({result_name: ini_val_set[idx] for idx, result_name
                                   in enumerate(res_names)})
                # Set time index
                df = df.set_index("Time")
                # Convert it to float
                df.index = df.index.astype("float64")
                dfs.append(df)
            # Most of the cases, only one set is provided. In that case, avoid
            if len(dfs) == 1 and squeeze:
                dfs = dfs[0]
            return dfs

    def set_initial_values(self, initial_values):
        """
        Overwrite inital values

        :param list initial_values:
            List containing initial values for the dymola interface
        """
        self.sim_setup["initialValues"] = list(initial_values)

    def set_sim_setup(self, sim_setup):
        """
        Overwrites multiple entries in the simulation setup dictionary

        :param dict sim_setup:
            Dictionary object with the same keys as this class's sim_setup dictionary
        """
        _diff = set(sim_setup.keys()).difference(self.sim_setup.keys())
        if _diff:
            raise KeyError(f"The given sim_setup contains the following keys "
                           f"({' ,'.join(list(_diff))} which are not part of "
                           f"the dymola sim_setup.")
        _number_values = ["startTime", "stopTime", "numberOfIntervals",
                          "outputInterval", "tolerance", "fixedstepsize"]
        for key, value in sim_setup.items():
            if key in _number_values:
                _ref = (float, int)
            else:
                _ref = type(self.sim_setup[key])
            if isinstance(value, _ref):
                self.sim_setup[key] = value
            else:
                raise TypeError(f"{key} is of type {type(value).__name__} but "
                                f"should be type {_ref}")


    def set_compiler(self, name, path, dll=False, dde=False, opc=False):
        """
        Set up the compiler and compiler options on Windows.
        Optional: Specify if you want to enable dll, dde or opc.

        :param str name:
            Name of the compiler, avaiable options:
            - 'vs': Visual Studio
            - 'gcc': GCC
        :param str,os.path.normpath path:
            Path to the compiler files.
            Example for name='vs': path='C:/Program Files (x86)/Microsoft Visual Studio 10.0/Vc'
            Example for name='gcc': path='C:/MinGW/bin/gcc'
        :param Boolean dll:
            Set option for dll support. Check Dymolas Manual on what this exactly does.
        :param Boolean dde:
            Set option for dde support. Check Dymolas Manual on what this exactly does.
        :param Boolean opc:
            Set option for opc support. Check Dymolas Manual on what this exactly does.
        :return: True, on success.
        """
        # Lookup dict for internal name of CCompiler-Variable
        _name_int = {"vs": "MSVC",
                     "gcc": "GCC"}

        if "win" not in sys.platform:
            raise OSError(f"set_compiler function only implemented "
                          f"for windows systems, you are using {sys.platform}")
        # Manually check correct input as Dymola's error are not a help
        name = name.lower()
        if name not in ["vs", "gcc"]:
            raise ValueError(f"Given compiler name {name} not supported.")
        if not os.path.exists(path):
            raise FileNotFoundError(f"Given compiler path {path} does not exist on your machine.")
        # Convert path for correct input
        path = self._make_modelica_normpath(path)

        res = self.dymola.SetDymolaCompiler(name.lower(),
                                            [f"CCompiler={_name_int[name]}",
                                             f"{_name_int[name]}DIR={path}",
                                             f"DLL={int(dll)}",
                                             f"DDE={int(dde)}",
                                             f"OPC={int(opc)}"])

        return res

    def import_initial(self, filepath):
        """
        Load given dsfinal.txt into dymola

        :param str,os.path.normpath filepath:
            Path to the dsfinal.txt to be loaded
        """
        if not os.path.isfile(filepath):
            raise FileNotFoundError(f"Given filepath {filepath} does not exist")
        if not os.path.splitext(filepath)[1] == ".txt":
            raise TypeError('File is not of type .txt')
        res = self.dymola.importInitial(dsName=filepath)
        if res:
            self.logger.info("Successfully loaded dsfinal.txt")
        else:
            raise Exception("Could not load dsfinal into Dymola.")

    def set_cd(self, cd):
        """Set the working directory to the given path"""
        super().set_cd(cd)
        # Also set the cd in the dymola api
        modelica_normpath = self._make_modelica_normpath(cd)
        res = self.dymola.cd(modelica_normpath)
        if not res:
            raise OSError(f"Could not change working directory to {cd}")

    def close(self):
        """Closes dymola."""
        self.logger.info('Closing Dymola')
        # Change so the atexit function works without an error.
        if self.dymola is not None:
            self.dymola.close()
        # Set dymola object to None to avoid further access to it.
        self.dymola = None
        self.logger.info('Successfully closed Dymola')

    def _close_dummy(self):
        """
        Closes dummy instance at the end of the execution
        """
        if self._dummy_dymola_instance is not None:
            self.logger.info('Closing dummy Dymola instance')
            self._dummy_dymola_instance.close()
            self.logger.info('Successfully closed dummy Dymola instance')

    def get_all_parameters(self):
        """Get all parameters of the model by
        translating it and then processing the dsin
        using modelicares.
        Returns a dict with keys the following keys and values:
            names: List of names
            initial_values: List of initial values
        """
        # Translate model
        res = self.dymola.translateModel(self.model_name)
        if not res:
            self.logger.error("Translation failed!")
            self.logger.error("The last error log from Dymola:")
            self.logger.error(self.dymola.getLastErrorLog())
            raise Exception("Translation failed!")
        # Get path to dsin:
        dsin_path = os.path.join(self.cd, "dsin.txt")
        df = manipulate_ds.convert_ds_file_to_dataframe(dsin_path)
        # Convert and return all parameters of dsin to initial values and names
        df = df[df["5"] == "1"]
        names = df.index
        initial_values = pd.to_numeric(df["2"].values)
        return {'names': names, 'initial_values': initial_value}

    def _setup_dymola_interface(self):
        """Load all packages and change the current working directory"""
        self.dymola = self._open_dymola_interface()
        # Register the function now in case of an error.
        atexit.register(self.close)
        self._check_dymola_instances()
        self.set_cd(self.cd)
        for package in self.packages:
            self.logger.info("Loading Model %s" % os.path.dirname(package).split("\\")[-1])
            res = self.dymola.openModel(package, changeDirectory=False)
            if not res:
                raise ImportError(self.dymola.getLastErrorLog())
        self.logger.info("Loaded modules")
        if self.equidistant_output:
            # Change the Simulation Output, to ensure all
            # simulation results have the same array shape.
            # Events can also cause errors in the shape.
            self.dymola.experimentSetupOutput(equidistant=True,
                                              events=False)
        if not self.dymola.RequestOption("Standard"):
            warnings.warn("You have no licence to use Dymola. "
                          "Hence you can only simulate models with 8 or less equations.")

    def _open_dymola_interface(self):
        """Open an instance of dymola and return the API-Object"""
        try:
            return DymolaInterface(showwindow=self.show_window,
                                   dymolapath=self.dymola_path)
        except DymolaConnectionException as error:
            raise ConnectionError(error)

    def to_dict(self):
        """
        Store the most relevant information of this class
        into a dictionary. This may be used for future configuration.

        :return: dict config:
            Dictionary with keys to re-init this class.
        """
        config = {"cd": self.cd,
                  "packages": self.packages,
                  "model_name": self.model_name,
                  "type": "DymolaAPI",
                  }
        # Update kwargs
        config.update({kwarg: self.__dict__.get(kwarg, None)
                       for kwarg in self._supported_kwargs})

        return config

    @staticmethod
    def _make_modelica_normpath(path):
        """
        Convert given path to a path readable in dymola.
        If the base path does not exist, create it.

        :param str,os.path.normpath path:
            Either a file or a folder path. The base to this
            path is created in non existent.
        :return: str
            Path readable in dymola
        """
        # Create base directory:
        _basedir = os.path.dirname(path)
        if not os.path.isdir(_basedir):
            os.makedirs(_basedir)

        path = path.replace("\\", "/")
        # Search for e.g. "D:testzone" and replace it with D:/testzone
        loc = path.find(":")
        if path[loc + 1] != "/" and loc != -1:
            path = path.replace(":", ":/")
        return path

    @staticmethod
    def get_dymola_interface_path(dymola_install_dir):
        """
        Function to get the path of the newest dymola interface
        installment on the used machine

        :param str dymola_install_dir:
            The dymola installation folder. Example:
            "C://Program Files//Dymola 2020"
        :return: str
            Path to the dymola.egg-file
        """
        path_to_egg_file = os.path.normpath("Modelica/Library/python_interface/dymola.egg")
        egg_file = os.path.join(dymola_install_dir, path_to_egg_file)
        if not os.path.isfile(egg_file):
            raise FileNotFoundError(f"The given dymola installation directory {dymola_install_dir}"
                                    " has no dymola-interface egg-file.")
        return egg_file

    @staticmethod
    def get_dymola_path(dymola_install_dir, dymola_name=None):
        """
        Function to get the path of the dymola exe-file
        on the current used machine.

        :param str dymola_install_dir:
            The dymola installation folder. Example:
            "C://Program Files//Dymola 2020"
        :param str dymola_name:
            Name of the executable. On Windows it is always Dymola.exe, on
            linux just dymola.
        :return: str
            Path to the dymola-exe-file.
        """
        if dymola_name is None:
            if "linux" in sys.platform:
                dymola_name = "dymola"
            elif "win" in sys.platform:
                dymola_name = "Dymola.exe"
            else:
                raise OSError(f"Your operating system {sys.platform} has no default dymola-name."
                              f"Please provide one.")

        bin_64 = os.path.join(dymola_install_dir, "bin64", dymola_name)
        bin_32 = os.path.join(dymola_install_dir, "bin", dymola_name)
        if os.path.isfile(bin_64): # First check for 64bit installation
            dym_file = bin_64
        elif os.path.isfile(bin_32): # Else use the 32bit version
            dym_file = bin_32
        else:
            raise FileNotFoundError(f"The given dymola file{bin_32} is not found. Either the "
                                    f"dymola_install_dir, or the dymola_name have false values.")

        return dym_file

    @staticmethod
    def get_dymola_install_path(basedir=None):
        """
        Function to get the path of the newest dymola installment
        on the used machine. Supported platforms are:
        * Windows
        * Linux
        * Mac OS X
        If multiple installation of Dymola are found, the newest version will be returned.
        This assumes the names are sortable, e.g. Dymola 2020, Dymola 2019 etc.

        :param str basedir:
            The base-directory to search for the dymola-installation.
            The default value depends on the platform one is using.
            On Windows it is "C://Program Files" or "C://Program Files (x86)" (for 64 bit)
            On Linux it is "/opt" (based on our ci-Docker configuration
            On Mac OS X "/Application" (based on the default)
        :return: str
            Path to the dymola-installation
        """

        if basedir is None:
            if "linux" in sys.platform:
                basedir = os.path.normpath("/opt")
            elif "win" in sys.platform:
                basedir = os.path.normpath("C:/Program Files")
            elif "darwin" in sys.platform:
                basedir = os.path.normpath("/Applications")
            else:
                raise OSError(f"Your operating system ({sys.platform})does not support "
                              f"a default basedir. Please provide one.")

        syspaths = [basedir]
        # Check if 64bit is installed (Windows only)
        systempath_64 = os.path.normpath("C://Program Files (x86)")
        if os.path.exists(systempath_64):
            syspaths.append(systempath_64)
        # Get all folders in both path's
        temp_list = []
        for systempath in syspaths:
            temp_list += os.listdir(systempath)
        # Filter programs that are not Dymola
        dym_versions = []
        for folder_name in temp_list:
            # Catch both Dymola and dymola folder-names
            if "dymola" in folder_name.lower():
                dym_versions.append(folder_name)
        del temp_list
        # Find the newest version and return the egg-file
        # This sorting only works with a good Folder structure, eg. Dymola 2020, Dymola 2019 etc.
        dym_versions.sort()
        for dym_version in reversed(dym_versions):
            for system_path in syspaths:
                full_path = os.path.join(system_path, dym_version)
                if os.path.isdir(full_path):
                    return full_path
        # If still inside the function, no interface was found
        return None

    def _check_dymola_instances(self):
        """
        Check how many dymola instances are running on the machine.
        Raise a warning if the number exceeds a certain amount.
        """
        # The option may be useful. However the explicit requirement leads to
        # Problems on linux, therefore the feature is not worth the trouble.
        try:
            import psutil
        except ImportError:
            return
        counter = 0
        for proc in psutil.process_iter():
            try:
                if "Dymola" in proc.name():
                    counter += 1
            except psutil.AccessDenied:
                continue
        if counter >= self._critical_number_instances:
            warnings.warn("There are currently %s Dymola-Instances "
                          "running on your machine!" % counter)

    @staticmethod
    def _alter_model_name(sim_setup, model_name, structural_params):
        """
        Creates a modifier for all structural parameters,
        based on the modelname and the initalNames and values.

        :param dict sim_setup:
            Simulation setup dictionary
        :param str model_name:
            Name of the model to be modified
        :param list structural_params:
            List of strings with structural parameters
        :return: str altered_modelName:
            modified model name
        """
        initial_values = sim_setup["initialValues"]
        initial_names = sim_setup["initialNames"]
        model_name = model_name.split("(")[0] # Trim old modifier
        if structural_params == [] or initial_names == []:
            return model_name
        all_modifiers = []
        for structural_para in structural_params:
            # Checks if the structural parameter is inside the initialNames to be altered
            if structural_para in initial_names:
                # Get the location of the parameter for
                # extraction of the corresponding initial value
                k = initial_names.index(structural_para)
                all_modifiers.append("%s = %s" % (structural_para, initial_values[k]))
        altered_model_name = "%s(%s)" % (model_name, ",".join(all_modifiers))
        return altered_model_name

    @staticmethod
    def _filter_error_log(error_log):
        """
        Filters the error log to detect recurring errors or structural parameters.
        Each structural parameter will raise this warning:
        'Warning: Setting n has no effect in model.\n
        After translation you can only set literal start-values\n
        and non-evaluated parameters.'
        Filtering of this string will extract 'n' in the given case.

        :param str error_log:
            Error log from the dymola_interface.getLastErrorLog() function
        :return: str filtered_log:
        """
        _trigger_string = "After translation you can only set " \
                          "literal start-values and non-evaluated parameters"
        structural_params = []
        split_error = error_log.split("\n")
        for i in range(1, len(split_error)):  # First line will never match the string
            if _trigger_string in split_error[i]:
                prev_line = split_error[i - 1]
                prev_line = prev_line.replace("Warning: Setting ", "")
                param = prev_line.replace(" has no effect in model.", "")
                structural_params.append(param)
        return structural_params

    def _global_import_dymola(self):
        sys.path.insert(0, self.dymola_interface_path)
        global DymolaInterface
        global DymolaConnectionException
        try:
            from dymola.dymola_interface import DymolaInterface
            from dymola.dymola_exception import DymolaConnectionException
        except ImportError:
            raise ImportError("Given dymola-interface could "
                              "not be loaded:\n %s" % self.dymola_interface_path)

    def _check_restart(self):
        """Restart Dymola every n_restart iterations in order to free memory"""

        if self.sim_counter == self.n_restart:
            self.logger.info("Closing and restarting Dymola to free memory")
            self.close()
            self._setup_dymola_interface()
            self.sim_counter = 1
        else:
            self.sim_counter += 1



