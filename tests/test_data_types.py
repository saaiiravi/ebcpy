"""Test-module for all classes inside
ebcpy.data_types."""

import os
import unittest
from pathlib import Path
import pandas as pd
from ebcpy import data_types


class TestDataTypes(unittest.TestCase):
    """Test-class for the data_types module of ebcpy."""

    def setUp(self):
        """Called before every test.
        Define example paths and parameters used in all test-functions.
        """
        self.framework_dir = Path(__file__).parents[1]
        self.example_dir = self.framework_dir.joinpath("ebcpy", "examples", "data")
        self.example_data_hdf_path = self.example_dir.joinpath("example_data.hdf")
        self.example_data_csv_path = self.example_dir.joinpath("example_data.CSV")
        self.example_data_mat_path = self.example_dir.joinpath("example_data.mat")

    def test_time_series_data(self):
        """Test the class TimeSeriesData"""
        # Test if wrong input leads to FileNotFoundError
        with self.assertRaises(FileNotFoundError):
            data_types.TimeSeriesData("Z:\\this_will_never_be_a_file_path.hdf")
        # Test if wrong file-ending leads to TypeError
        with self.assertRaises(TypeError):
            a_python_file = __file__
            data_types.TimeSeriesData(a_python_file)
        # If no key is provided, a KeyError has to be raised
        with self.assertRaises(KeyError):
            data_types.TimeSeriesData(self.example_data_hdf_path)
        with self.assertRaises(KeyError):
            data_types.TimeSeriesData(self.example_data_hdf_path,
                                      key="wrong_key")
        # Correctly load the .hdf:
        time_series_data = data_types.TimeSeriesData(self.example_data_hdf_path,
                                                     key="parameters")
        self.assertIsInstance(
            time_series_data,
            type(pd.DataFrame()))
        # Correctly load the .csv:
        time_series_data = data_types.TimeSeriesData(self.example_data_csv_path,
                                                     sep=",")
        self.assertIsInstance(
            time_series_data,
            type(pd.DataFrame()))
        # Correctly load the .mat:
        time_series_data = data_types.TimeSeriesData(self.example_data_mat_path)
        self.assertIsInstance(
            time_series_data,
            type(pd.DataFrame()))
        # Test load and set df functions:
        df = time_series_data
        self.assertIsInstance(
            df,
            type(pd.DataFrame()))
        # Test converters:
        tsd = data_types.TimeSeriesData(self.example_data_hdf_path,
                                        key="parameters")
        tsd.to_datetime_index()
        self.assertIsInstance(tsd.index, pd.DatetimeIndex)
        tsd.to_float_index()
        self.assertIsInstance(tsd.index, pd.Float64Index)
        tsd.to_datetime_index()
        self.assertIsInstance(tsd.index, pd.DatetimeIndex)
        tsd.clean_and_space_equally(desired_freq="1s")
        self.assertIsInstance(tsd.index, pd.DatetimeIndex)

    def test_time_series_tagging(self):
        """Test tagging functions"""
        with self.assertRaises(TypeError):
            data_types.TimeSeriesData(self.example_data_mat_path,
                                      default_tag=10)
        tsd1 = data_types.TimeSeriesData(self.example_data_mat_path,
                                         default_tag='other_default')
        with self.assertRaises(TypeError):
            tsd1.default_tag = 10
        self.assertEqual(tsd1.get_columns_by_tag('other_default').size,
                         tsd1.size)
        with self.assertRaises(KeyError):
            tsd1.get_columns_by_tag('this_is_never_a:tag')
        tsd2 = data_types.TimeSeriesData(self.example_data_mat_path,
                                         default_tag='new_data')
        tsd3 = pd.concat([tsd1, tsd2], axis=1)
        with self.assertRaises(KeyError):
            tsd3.default_tag = 'new_default_tag'
        self.assertEqual(tsd3.size,
                         tsd1.size + tsd2.size)
        self.assertEqual(tsd3.get_columns_by_tag('new_data').size,
                         tsd2.size)

    def test_time_series_utils(self):
        """Test the utils for time series"""
        tsd = data_types.TimeSeriesData(self.example_data_mat_path)
        self.assertEqual(len(tsd.get_variable_names()), tsd.shape[1])
        self.assertIsNotNone(tsd.get_tags())
        self.assertLessEqual(len(tsd.get_variable_names()), tsd.shape[1])

    def test_get_keys_of_hdf_file(self):
        """Test the function get_keys_of_hdf_file.
        Check the keys of the file with e.g. the SDFEditor and
        use those keys as a reference list.
        """
        # pylint: disable=import-outside-toplevel
        # pylint: disable=unused-import
        try:
            import h5py
        except ImportError:
            self.skipTest("Test only makes sense if h5py is installed")
        reference_list = ['parameters', 'trajectories']
        return_val = data_types.get_keys_of_hdf_file(self.example_data_hdf_path)
        self.assertListEqual(return_val, reference_list)


if __name__ == "__main__":
    unittest.main()
