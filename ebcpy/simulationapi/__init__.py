"""
Simulation APIs help you to perform automated
simulations for energy and building climate related models.
Parameters can easily be updated, and the initialization-process is
much more user-friendly than the provided APIs by Dymola or fmpy.
"""

import os
import itertools
import warnings
import numpy as np
from typing import Dict, Union, TypeVar, Any, List
from pydantic import BaseModel, Field, validator
from abc import abstractmethod
import multiprocessing as mp
from ebcpy.utils import setup_logger


class Variable(BaseModel):
    """
    Data-Class to store relevant information for a
    simulation variable (input, parameter, output or local/state).
    """
    value: Any = Field(
        description="Default variable value"
    )
    max: Union[float, int] = Field(
        default=np.inf,
        title='max',
        description='Maximal value (upper bound) of the variables value'
    )
    min: Union[float, int] = Field(
        default=-np.inf,
        title='min',
        description='Minimal value (lower bound) of the variables value'
    )


class SimulationSetup(BaseModel):
    start_time: float = Field(
        default=0,
        description="The start time of the simulation",
        title="start_time"
    )
    stop_time: float = Field(
        default=1,
        description="The stop / end time of the simulation",
        title="stop_time"
    )
    output_interval: float = Field(
        default=1,
        description="The step size of the simulation and "
                    "thus also output interval of results.",
        title="output_interval"
    )
    fixedstepsize: float = Field(
        title="fixedstepsize",
        default=0.0,
        description="Fixed step size for Euler"
    )
    solver: str = Field(
        title="solver",
        default="",  # Is added in the validator
        description="The solver to be used for numerical integration."
    )
    _default_solver: str = None
    _allowed_solvers: list = []

    @validator("solver", always=True, allow_reuse=True)
    def check_valid_solver(cls, solver):
        if not solver:
            return cls.__private_attributes__['_default_solver'].default
        allowed_solvers = cls.__private_attributes__['_allowed_solvers'].default
        if solver not in allowed_solvers:
            raise ValueError(f"Given solver '{solver}' is not supported! "
                             f"Supported are '{allowed_solvers}'")
        return solver

    class Config:
        extra = 'forbid'
        underscore_attrs_are_private = True


SimulationSetupClass = TypeVar("SimulationSetupClass", bound=SimulationSetup)


class SimulationAPI:
    """Base-class for simulation apis. Every simulation-api class
    must inherit from this class. It defines the structure of each class.

    :param str,os.path.normpath cd:
        Working directory path
    :param str model_name:
        Name of the model being simulated.
    :keyword int n_cpu:
        Number of cores to be used by simulation.
        If None is given, single core will be used.
        Maximum number equals the cpu count of the device.
    """
    _sim_setup_class: SimulationSetupClass = SimulationSetup
    _items_to_drop = ['pool']

    def __init__(self, cd, model_name, **kwargs):
        self._sim_setup = self._sim_setup_class()
        self.cd = cd
        self.model_name = model_name
        # Setup the logger
        self.logger = setup_logger(cd=cd, name=self.__class__.__name__)
        self.logger.info(f'{"-" * 25}Initializing class {self.__class__.__name__}{"-" * 25}')
        self.inputs: Dict[str, Variable] = {}       # Inputs of model
        self.outputs: Dict[str, Variable] = {}      # Outputs of model
        self.parameters: Dict[str, Variable] = {}   # Parameter of model
        self.states: Dict[str, Variable] = {}       # States of model
        self.result_names = []
        # Check multiprocessing
        self.n_cpu = kwargs.get("n_cpu", 1)
        if self.n_cpu > mp.cpu_count():
            raise ValueError(f"Given n_cpu '{self.n_cpu}' is greater "
                             "than the available number of "
                             f"cpus on your machine '{mp.cpu_count()}'")
        if self.n_cpu > 1:
            self.pool = mp.Pool(processes=self.n_cpu)
            self.use_mp = True
        else:
            self.pool = None
            self.use_mp = False

    @abstractmethod
    def close(self):
        """Base function for closing the simulation-program."""
        raise NotImplementedError(f'{self.__class__.__name__}.close function is not defined')

    @abstractmethod
    def simulate(self,
                 parameters: dict = None,
                 return_option: str = "time_series",
                 **kwargs):
        """
        Base function for simulating the simulation-model.

        :param parameters Dict:
            Parameters to simulate.
            Names of parameters are key, values are value of the dict.
            Default is an empty dict.
        :param return_option str:
            How to handle the simulation results. Options are:
            - 'time_series': Returns a DataFrame with the results and does not store anything.
            Only variables specified in result_names will be returned.
            - 'last_point': Returns only the last point of the simulation.
            Relevant for integral metrics like energy consumption.
            Only variables specified in result_names will be returned.
            - 'savepath': Returns the savepath where the results are stored.
            Depending on the API, different kwargs may be used to specify file type etc.
        :keyword str,os.path.normpath savepath:
            If path is provided, the relevant simulation results will be saved
            in the given directory.
            Only relevant if return_option equals 'savepath' .
        :keyword str result_file_name:
            Name of the result file. Default is 'resultFile'.
            Only relevant if return_option equals 'savepath'.

        :return: str,os.path.normpath filepath:
            Only if return_option equals 'savepath'.
            Filepath of the result file.
        :return: dict:
            Only if return_option equals 'last_point'.
        :return: Union[List[pd.DataFrame],pd.DataFrame]:
            If parameters are scalar and squeeze=True,
            a DataFrame with the columns being equal to
            self.result_names.
            If multiple set's of initial values are given, one
            dataframe for each set is returned in a list
        """
        raise NotImplementedError(f'{self.__class__.__name__}.simulate function is not defined')

    @property
    def sim_setup(self) -> SimulationSetupClass:
        """Return current sim_setup"""
        return self._sim_setup

    @sim_setup.deleter
    def sim_setup(self):
        """In case user deletes the object, reset it to the default one."""
        self._sim_setup = self._sim_setup_class()

    def set_sim_setup(self, sim_setup):
        """
        Replaced in v0.1.7 by property function
        """
        new_setup = self._sim_setup.dict()
        new_setup.update(sim_setup)
        self._sim_setup = self._sim_setup_class(**new_setup)

    @property
    def model_name(self) -> str:
        """Name of the model being simulated"""
        return self._model_name

    @model_name.setter
    def model_name(self, model_name):
        """
        Set new model_name and trigger further functions
        to load parameters etc.
        """
        # Empty all variables again.
        self.outputs = {}
        self.parameters = {}
        self.states = {}
        self.inputs = {}
        self._model_name = model_name
        self._update_model()
        # Set all outputs to result_names:
        self.result_names = self.outputs.keys()

    @abstractmethod
    def _update_model(self):
        """
        Reimplement this to change variables etc.
        based on the new model.
        """
        raise NotImplementedError(f'{self.__class__.__name__}._update_model function is not defined')

    def set_cd(self, cd):
        """Base function for changing the current working directory."""
        self.cd = cd

    @property
    def cd(self) -> str:
        """Get the current working directory"""
        return self._cd

    @cd.setter
    def cd(self, cd: str):
        """Set the current working directory"""
        os.makedirs(cd, exist_ok=True)
        self._cd = cd

    @property
    def result_names(self) -> List[str]:
        """
        The variables names which to store in results.

        Returns:
            list: List of string where the string is the
            name of the variable to store in the result.
        """
        return self._result_names

    @result_names.setter
    def result_names(self, result_names):
        """
        Set the result names. If the name is not supported,
        an error is logged.
        """
        self.check_unsupported_variables(variables=result_names,
                                         type_of_var="variables")
        for res_name in result_names:
            if res_name not in self.variables:
                self.logger.error(
                    "Variable name '%s' not found in model. "
                    "Will most probably trigger an error when simulating.",
                    res_name
                )
        self._result_names = result_names

    @property
    def variables(self):
        """
        All variables of the simulation model
        """
        return itertools.chain(self.parameters.keys(),
                               self.outputs.keys(),
                               self.inputs.keys(),
                               self.states.keys())

    def check_unsupported_variables(self, variables: List[str], type_of_var: str):
        """Log warnings if variables are not supported."""
        if type_of_var == "parameters":
            ref = self.parameters.keys()
        elif type_of_var == "outputs":
            ref = self.outputs.keys()
        elif type_of_var == "inputs":
            ref = self.inputs.keys()
        elif type_of_var == "inputs":
            ref = self.states.keys()
        else:
            ref = self.variables

        diff = set(variables).difference(ref)
        if diff:
            self.logger.warning(
                "Variables '%s' not found in model '%s'. "
                "Will most probably trigger an error when simulating.",
                ', '.join(diff), self.model_name
            )
            return True
        return False

    def get_worker_idx(self):
        return mp.current_process()._identity[0]
