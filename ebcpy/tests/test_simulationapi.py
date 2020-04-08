"""Test-module for all classes inside
ebcpy.simulationapi."""

import unittest
import os
import shutil
from ebcpy.simulationapi import dymola_api


class TestDymolaAPI(unittest.TestCase):
    """Test-Class for the DymolaAPI class."""

    def setUp(self):
        """Called before every test.
        Used to setup relevant paths and APIs etc."""
        framework_dir = os.path.dirname(os.path.dirname(__file__))
        self.example_dir = os.path.normpath(os.path.join(framework_dir, "examples", "data"))
        self.example_sim_dir = os.path.join(self.example_dir, "testzone")
        if not os.path.exists(self.example_sim_dir):
            os.mkdir(self.example_sim_dir)
        ebcpy_test_package_dir = os.path.normpath(os.path.join(framework_dir,
                                                               "examples",
                                                               "Modelica",
                                                               "AixCalTest",
                                                               "package.mo"))
        packages = [ebcpy_test_package_dir]
        model_name = "AixCalTest.TestModel"
        self.initial_names = ["C",
                              "heatConv_b",
                              "heatConv_a"]
        self.initial_values = [2000, 5, 5]

        self.dym_api = dymola_api.DymolaAPI(self.example_sim_dir,
                                            model_name,
                                            packages)

    @unittest.skip("Simulation does not work so far in ci.")
    def test_close(self):
        """Test close functionality of dymola api"""
        self.dym_api.close()
        self.assertIsNone(self.dym_api.dymola)

    @unittest.skip("Simulation does not work so far in ci.")
    def test_simulate(self):
        """Test simulate functionality of dymola api"""
        self.dym_api.set_sim_setup({"startTime": 0.0,
                                    "stopTime": 10.0})
        _filepath_dsres = self.dym_api.simulate()
        self.assertTrue(os.path.isfile(_filepath_dsres))

    @unittest.skip("Simulation does not work so far in ci.")
    def test_set_cd(self):
        """Test set_cd functionality of dymola api"""
        # Test the setting of the function
        self.dym_api.set_cd(self.example_dir)
        self.assertEqual(self.example_dir, self.dym_api.cd)

    @unittest.skip("Simulation does not work so far in ci.")
    def test_set_sim_setup(self):
        """Test set_sim_setup functionality of dymola api"""
        new_sim_setup = {'initialNames': self.initial_names,
                         'initialValues': self.initial_values}
        self.dym_api.set_sim_setup(new_sim_setup)
        self.assertEqual(self.dym_api.sim_setup['initialNames'],
                         new_sim_setup['initialNames'])
        self.assertEqual(self.dym_api.sim_setup['initialValues'],
                         new_sim_setup['initialValues'])
        with self.assertRaises(KeyError):
            self.dym_api.set_sim_setup({"NotAValidKey": None})
        with self.assertRaises(TypeError):
            self.dym_api.set_sim_setup({"stopTime": "not_a_float_or_int"})

    def tearDown(self):
        """Delete all files created while testing"""

        try:
            self.dym_api.close()
        except AttributeError:
            pass
        try:
            shutil.rmtree(self.example_sim_dir)
        except (FileNotFoundError, PermissionError):
            pass


if __name__ == "__main__":
    unittest.main()