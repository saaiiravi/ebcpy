"""Module for classes using a fmu to
simulate models."""

import os
import fmpy
import shutil
import pandas as pd
import numpy as np
from ebcpy import simulationapi


class FMU_API(simulationapi.SimulationAPI):
    """
    Class for simulation using the fmpy library and
    a functional mockup interface as a model input.
    """

    sim_setup = {'startTime': 0.0,
                 'stopTime': 1.0,
                 'numberOfIntervals': 0,
                 'outputInterval': 1,
                 'solver': 'CVode',
                 'initialNames': [],
                 'initialValues': [],
                 'resultNames': [],
                 'timeout': np.inf}

    # Dynamic setup of simulation setup
    number_values = [key for key, value in sim_setup.items() if
                     (isinstance(value, (int, float)) and not isinstance(value, bool))]

    def __init__(self, cd, model_name):
        """Instantiate class parameters"""
        super().__init__(cd, model_name)
        if not model_name.lower().endswith(".fmu"):
            raise ValueError("{} is not a valid fmu file!".format(model_name))

        # Setup the fmu instance
        self.setup_fmu_instance()

    def close(self):
        """
        Closes the fmu.
        :return:
            True on success
        """
        # Remove the extracted files
        shutil.rmtree(self.unzipdir, ignore_errors=True)

    def set_cd(self, cd):
        """
        Set current working directory for storing files etc.
        :param str,os.path.normpath cd:
            New working directory
        :return:
        """
        os.makedirs(cd, exist_ok=True)
        self.cd = cd

    def simulate(self, **kwargs):
        """
        Simulate current simulation-setup.

        :param str,os.path.normpath savepath_files:
            Savepath were to store result files of the simulation.
        :keyword Boolean fail_on_error:
            If True, an error in fmpy will trigger an error in this script.
            Default is false
        :return:
            Filepath of the mat-file.
        """
        start_values = {self.sim_setup["initialNames"][i]: value
                        for i, value in enumerate(self.sim_setup["initialValues"])}
        try:
            res = fmpy.simulate_fmu(
                     self.unzipdir,
                     start_time=self.sim_setup["startTime"],
                     stop_time=self.sim_setup["stopTime"],
                     solver=self.sim_setup["solver"],
                     step_size=self.sim_setup["numberOfIntervals"],
                     relative_tolerance=None,
                     output_interval=self.sim_setup["outputInterval"],
                     record_events=False,
                     start_values=start_values,
                     apply_default_start_values=False,
                     input=None,
                     output=self.sim_setup["resultNames"],
                     timeout=self.sim_setup["timeout"],
                     step_finished=None,
                     model_description=None,
                     fmu_instance=None)
        except Exception as error:
            print(f"[SIMULATION ERROR] Error occured while running FMU: \n {error}")
            if kwargs.get("fail_on_error", False):
                raise error
            return None

        # Reshape result:
        df = pd.DataFrame(res).set_index("time")
        df.index = df.index.astype("float64")

        # Options if dll error occurs:
        #self.fmu_instance.fmi2FreeInstance(fmu.component)
        #fmpy.freeLibrary(self.fmu_instance.dll._handle)

        return df

    def setup_fmu_instance(self):
        """
        Manually set up and extract the data to
        avoid this step in the simulate function
        :return:
        """
        self.unzipdir = fmpy.extract(self.model_name,
                                     unzipdir=os.path.join(self.cd,
                                                           os.path.basename(self.model_name)[:-4] + "_extracted")
                                     )


    def set_initial_values(self, initial_values):
        """
        Overwrite inital values

        :param list initial_values:
            List containing initial values for the dymola interface
        """
        self.sim_setup["initialValues"] = list(initial_values)


if __name__=="__main__":
    import numpy as np
    path = r"D:\pme-fwu\00_testzone\00_dymola\StandardFlowsheet_Propane.fmu"
    p = FMU_API(cd=os.path.dirname(path), model_name=path)
    for q_hp in np.linspace(10000, 20000, 1000):
        print(f"Simulation {q_hp}")
        p.set_sim_setup({"stopTime": 86400,
                         "resultNames": ["W_el", "Demand.thermalZoneOneElement.volAir.T"],
                         "initialNames": ["optimizationVariables.Q_HP_Nom"],
                         "initialValues": [q_hp],
                         "outputInterval": 500})
        res = p.simulate()
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(nrows=2, ncols=1)
    ax[0].plot(res["Demand.thermalZoneOneElement.volAir.T"])
    ax[1].plot(res["W_el"])
    plt.show()
