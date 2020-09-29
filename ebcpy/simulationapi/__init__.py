"""Module with the base class for all simulation APIs.
Different simulation modules like dymola_api or py_fmi
may inherit classes of this module."""

from abc import abstractmethod
from ebcpy.utils import visualizer


# Klasse vergleichbar mit Hannah's "BaseModel" Klasse
class SimulationAPI:
    """Base-class for simulation apis. Every simulation-api class
    must inherit from this class. It defines the structure of each class.

    :param str,os.path.normpath cd:
        Working directory path
    :param str model_name:
        Name of the model being simulated."""

    sim_setup = {}
    # Dynamic setup of simulation setup
    number_values = []

    def __init__(self, cd, model_name):
        self.cd = cd
        self.model_name = model_name
        # Setup the logger
        self.logger = visualizer.Logger(cd, "simulation_api")
        # Setup iteration counter
        self.count = 0

        # For extracting input-, output- & tuner-parameter
        self.model_inp = []         # input_sim_names
        self.model_out = []         # target_sim_names
        self.model_tuner_names = []
        self.model_tuner_initialvalues = []
        self.model_tuner_bounds = []

        # Current best tuner parameters of all recalibration steps (for penalty function)
        self.current_best_tuners = []

    @abstractmethod
    def set_cd(self, cd):
        """Base function for changing the current working directory."""
        raise NotImplementedError('{}.set_cd function is not '
                                  'defined'.format(self.__class__.__name__))

    def set_sim_setup(self, sim_setup):
        """
        Generic function for multiple entries in the simulation setup dictionary

        :param dict sim_setup:
            Dictionary object with the same keys as this class's sim_setup dictionary
        """
        _diff = set(sim_setup.keys()).difference(self.sim_setup.keys())
        if _diff:
            raise KeyError("The given sim_setup contains the following keys ({}) which are "
                           "not part of the dymola sim_setup.".format(" ,".join(list(_diff))))
        _number_values = ["startTime", "stopTime", "numberOfIntervals",
                          "outputInterval", "tolerance", "fixedstepsize"]
        for key, value in sim_setup.items():
            if key in self.number_values:
                _ref = (float, int)
            else:
                _ref = type(self.sim_setup[key])
            if isinstance(value, _ref):
                self.sim_setup[key] = value
            else:
                raise TypeError("{} is of type {} but should be"
                                " type {}".format(key, type(value).__name__, _ref))

    def set_initial_values(self, initial_values):
        """
        Overwrite inital values

        :param list initial_values:
            List containing initial values for the calibration
        """

        self.sim_setup["initialValues"] = list(initial_values)

    @abstractmethod
    def simulate(self, **kwargs):
        """Base function for simulating the simulation-model."""
        raise NotImplementedError('{}.simulate function is not '
                                  'defined'.format(self.__class__.__name__))

    @abstractmethod
    def do_step(self, **kwargs):
        """Base function for simulating one timestep."""
        raise NotImplementedError('{}.do_step function is not '
                                  'defined'.format(self.__class__.__name__))

    @abstractmethod
    def overwrite_model(self):
        """Base function for overwriting the model parameters."""
        raise NotImplementedError('{}.overwrite_model function is not '
                                  'defined'.format(self.__class__.__name__))

    @abstractmethod
    def close(self):
        """Base function for closing the simulation-program."""
        raise NotImplementedError('{}.close function is not '
                                  'defined'.format(self.__class__.__name__))