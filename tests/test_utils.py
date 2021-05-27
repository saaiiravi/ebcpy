"""Test-module for all classes inside
ebcpy.utils."""

import unittest
import os
from pathlib import Path
import numpy as np
import scipy.io as spio
from ebcpy.utils import setup_logger
from ebcpy.utils import conversion
from ebcpy.utils import statistics_analyzer


class TestConversion(unittest.TestCase):
    """Test-class for preprocessing."""

    def setUp(self):
        """Called before every test.
        Used to setup relevant paths and APIs etc."""
        self.framework_dir = Path(__file__).parents[1]
        self.example_dir = self.framework_dir.joinpath("ebcpy", "examples", "data")
        self.example_data_hdf_path = self.example_dir.joinpath("example_data.hdf")

    def test_conversion_hdf_to_mat(self):
        """Test function conversion.convert_hdf_to_modelica_mat().
        For an example, see the doctest in the function."""
        # First convert the file
        save_path = self.example_dir.joinpath("example_data_converted.mat")
        columns = ["sine.y / "]
        # Test both conversion with specification of columns and without passing the names.
        for col in [columns, None]:
            res, filepath_mat = conversion.convert_hdf_to_modelica_mat(self.example_data_hdf_path,
                                                                       save_path,
                                                                       columns=col,
                                                                       key="trajectories")
            # Check if successfully converted
            self.assertTrue(res)
            # Check if converted file exists
            self.assertTrue(os.path.isfile(filepath_mat))
            # Check if converted filepath is provided filepath
            self.assertEqual(filepath_mat, str(save_path))
            # Now check if the created mat-file can be used.
            self.assertIsInstance(spio.loadmat(save_path), dict)
            # Remove converted file again
            os.remove(save_path)

    def test_conversion_hdf_to_modelica_txt(self):
        """Test function conversion.convert_hdf_to_modelica_txt().
        For an example, see the doctest in the function."""
        columns = ["sine.y / "]
        for col in [columns, None]:
            res, filepath_txt = conversion.convert_hdf_to_modelica_txt(self.example_data_hdf_path,
                                                                       table_name="dummy",
                                                                       columns=col,
                                                                       key="trajectories",)
            # Check if successfully converted
            self.assertTrue(res)
            # Check if converted file exists
            self.assertTrue(os.path.isfile(filepath_txt))
            # Check if converted filepath is provided filepath
            self.assertTrue(filepath_txt.endswith(".txt"))
            # Remove converted file again
            os.remove(filepath_txt)

    def test_conversion_hdf_to_clustering_txt(self):
        """Test function conversion.convert_hdf_to_clustering_txt().
        For an example, see the doctest in the function."""
        # First convert the file
        save_path = os.path.normpath(os.path.join(self.example_dir, "example_data_converted.txt"))
        columns = ["sine.y / "]
        # Test both conversion with specification of columns and without passing the names.
        for col in [columns, None]:
            res, filepath_txt = conversion.convert_hdf_to_clustering_txt(self.example_data_hdf_path,
                                                                         save_path,
                                                                         columns=col,
                                                                         key="trajectories")
            # Check if successfully converted
            self.assertTrue(res)
            # Check if converted file exists
            self.assertTrue(os.path.isfile(filepath_txt))
            # Check if converted filepath is provided filepath
            self.assertEqual(filepath_txt, save_path)
            # Remove converted file again
            os.remove(save_path)


class TestStatisticsAnalyzer(unittest.TestCase):
    """Test-class for the StatisticsAnalyzer-Class"""

    def setUp(self):
        """Called before every test.
        Used to setup relevant paths and APIs etc."""
        self.framework_dir = os.path.dirname(os.path.dirname(__file__))
        self.example_dir = os.path.normpath(os.path.join(self.framework_dir, "examples", "data"))
        self.meas_ex = np.random.rand(1000)
        self.sim_ex = np.random.rand(1000)*10

    def test_calc(self):
        """Test class StatisticsAnalyzer"""
        sup_methods = ["mae", "r2", "mse", "rmse", "cvrmse", "nrmse"]
        for method in sup_methods:
            stat_analyzer = statistics_analyzer.StatisticsAnalyzer(method)
            self.assertIsInstance(stat_analyzer.calc(self.meas_ex, self.sim_ex),
                                  float)
        with self.assertRaises(ValueError):
            stat_analyzer = statistics_analyzer.StatisticsAnalyzer("not_supported_method")
        # Test factor:
        stat_analyzer_min = statistics_analyzer.StatisticsAnalyzer("R2")
        stat_analyzer_max = statistics_analyzer.StatisticsAnalyzer("R2", for_minimization=False)
        self.assertEqual(-1 * stat_analyzer_min.calc(self.meas_ex, self.sim_ex),
                         stat_analyzer_max.calc(self.meas_ex, self.sim_ex))

    def test_calc_rmse(self):
        """Test static function calc_rmse"""
        stat_analyzer = statistics_analyzer.StatisticsAnalyzer
        self.assertIsInstance(stat_analyzer.calc_rmse(self.meas_ex, self.sim_ex),
                              float)

    def test_calc_mse(self):
        """Test static function calc_mse"""
        stat_analyzer = statistics_analyzer.StatisticsAnalyzer
        self.assertIsInstance(stat_analyzer.calc_mse(self.meas_ex, self.sim_ex),
                              float)

    def test_calc_mae(self):
        """Test static function calc_mae"""
        stat_analyzer = statistics_analyzer.StatisticsAnalyzer
        self.assertIsInstance(stat_analyzer.calc_mae(self.meas_ex, self.sim_ex),
                              float)

    def test_calc_nrmse(self):
        """Test static function calc_nrmse"""
        stat_analyzer = statistics_analyzer.StatisticsAnalyzer
        self.assertIsInstance(stat_analyzer.calc_nrmse(self.meas_ex, self.sim_ex),
                              float)
        with self.assertRaises(ValueError):
            custom_meas = self.meas_ex/self.meas_ex
            stat_analyzer.calc_nrmse(custom_meas, self.sim_ex)

    def test_calc_cvrmse(self):
        """Test static function calc_cvrmse"""
        stat_analyzer = statistics_analyzer.StatisticsAnalyzer
        self.assertIsInstance(stat_analyzer.calc_cvrmse(self.meas_ex, self.sim_ex),
                              float)
        with self.assertRaises(ValueError):
            custom_meas = self.meas_ex - self.meas_ex
            stat_analyzer.calc_cvrmse(custom_meas, self.sim_ex)

    def test_calc_r2(self):
        """Test static function calc_r2"""
        stat_analyzer = statistics_analyzer.StatisticsAnalyzer
        self.assertIsInstance(stat_analyzer.calc_r2(self.meas_ex, self.sim_ex),
                              float)


class TestLogger(unittest.TestCase):
    """Test-class for the logger function."""

    def setUp(self):
        """Called before every test.
        Used to setup relevant paths and APIs etc."""
        self.example_dir = os.path.normpath(
            os.path.join(os.path.dirname(os.path.dirname(__file__)),
                         "examples", "data"))
        self.logger = setup_logger(cd=self.example_dir,
                                   name="test_logger")

    def test_logging(self):
        """Test if logging works."""
        example_str = "This is a test"
        self.logger.info(example_str)
        with open(self.logger.handlers[1].baseFilename, "r") as logfile:
            logfile.seek(0)
            self.assertTrue(example_str in logfile.read())

    def tearDown(self):
        """Remove created files."""
        self.logger.handlers[0].close()
        try:
            os.remove(self.logger.handlers[1].baseFilename)
        except PermissionError:
            pass


if __name__ == "__main__":
    unittest.main()
