"""Test-module for all classes inside
ebcpy.preprocessing."""
import unittest
import os
import random
from datetime import datetime
import scipy.io as spio
import numpy as np
import pandas as pd
from ebcpy.preprocessing import conversion
from ebcpy.preprocessing import preprocessing


class TestConversion(unittest.TestCase):
    """Test-class for preprocessing."""

    def setUp(self):
        """Called before every test.
        Used to setup relevant paths and APIs etc."""
        self.framework_dir = os.path.dirname(os.path.dirname(__file__))
        self.example_dir = os.path.normpath(self.framework_dir + "//examples//data")
        self.example_data_hdf_path = os.path.normpath(self.example_dir +
                                                      "//example_data.hdf")

    def test_conversion_hdf_to_mat(self):
        """Test function conversion.convert_hdf_to_mat().
        For an example, see the doctest in the function."""
        # First convert the file
        save_path = os.path.normpath(self.example_dir + "//example_data_converted.mat")
        columns = ["sine.y / "]
        # Test both conversion with specification of columns and without passing the names.
        for col in [columns, None]:
            res, filepath_mat = conversion.convert_hdf_to_mat(self.example_data_hdf_path,
                                                              save_path,
                                                              columns=col,
                                                              key="trajectories")
            # Check if successfully converted
            self.assertTrue(res)
            # Check if converted file exists
            self.assertTrue(os.path.isfile(filepath_mat))
            # Check if converted filepath is provided filepath
            self.assertEqual(filepath_mat, save_path)
            # Now check if the created mat-file can be used.
            self.assertIsInstance(spio.loadmat(save_path), dict)
            # Remove converted file again
            os.remove(save_path)


class TestPreProcessing(unittest.TestCase):
    """Test-class for preprocessing."""

    def setUp(self):
        """Called before every test.
        Used to setup relevant paths and APIs etc."""
        self.framework_dir = os.path.dirname(os.path.dirname(__file__))
        self.example_dir = os.path.normpath(self.framework_dir + "//examples//data")
        self.example_data_hdf_path = os.path.normpath(self.example_dir +
                                                      "//example_data.hdf")

    def test_build_average_on_duplicate_rows(self):
        """Test function of preprocessing.build_average_on_duplicate_rows().
        For an example, see the doctest in the function."""
        # Choose random number to check if function works in every dimension
        dim = np.random.randint(1, 1000)
        vals = np.random.rand(dim)
        # instantiate df with index all 1
        df = pd.DataFrame({"idx": np.ones(dim), "val": vals}).set_index("idx")
        df = preprocessing.build_average_on_duplicate_rows(df)
        # Check if the length has been reduced to 1
        self.assertEqual(len(df), 1)
        # Check if the average is computed correctly
        self.assertEqual(df.iloc[0].val, np.average(vals))

    def test_convert_index_to_datetime_index(self):
        """Test function of preprocessing.convert_index_to_datetime_index().
        For an example, see the doctest in the function."""

        dim = np.random.randint(1, 10000)
        df = pd.DataFrame(np.random.rand(dim, 4), columns=list('ABCD'))
        df_temp = preprocessing.convert_index_to_datetime_index(df)
        # Check if index is correctly created
        self.assertIsInstance(df_temp.index, pd.DatetimeIndex)
        # Check different unit-formats:
        for unit in ["ms", "s", "h", "d", "min"]:
            df_temp = preprocessing.convert_index_to_datetime_index(df,
                                                                    unit_of_index=unit)
        # Test different datetime:
        df_temp = preprocessing.convert_index_to_datetime_index(df, origin=datetime(2007, 1, 1))
        # Test wrong unit-input:
        with self.assertRaises(ValueError):
            df_temp = preprocessing.convert_index_to_datetime_index(df,
                                                                    unit_of_index="not_a_unit")

    def test_clean_and_space_equally_time_series(self):
        """Test function of preprocessing.clean_and_space_equally_time_series().
        For an example, see the doctest in the function."""
        # Generate a random frequency
        supported_frequencys = ["s", "min", "h", "ms"]
        freq = "{}{}".format(np.random.randint(1, 60), random.choice(supported_frequencys))
        dim = np.random.randint(1, 10000)
        df = pd.DataFrame(np.random.randint(0, 100, size=(dim, 4)),
                          columns=list('ABCD')).set_index("A").sort_index()
        # Check if wrong index input raises error:
        with self.assertRaises(TypeError):
            preprocessing.clean_and_space_equally_time_series(df, freq)
        df = preprocessing.convert_index_to_datetime_index(df)
        df_temp = preprocessing.clean_and_space_equally_time_series(df, freq)
        self.assertIsInstance(df_temp, pd.DataFrame)
        # Test non-numeric input
        df.iloc[0, 0] = "not_a_number"
        with self.assertRaises(ValueError):
            df_temp = preprocessing.clean_and_space_equally_time_series(df, freq)
        # Trigger NaN-input print statement
        df.iloc[0, 0] = np.NaN
        df_temp = preprocessing.clean_and_space_equally_time_series(df, freq)

    def test_low_pass_filter(self):
        """Test function of preprocessing.low_pass_filter().
        For an example, see the doctest in the function."""
        # Randomly generate all inputs to assure that different
        # inputs will always work.
        dim = np.random.randint(1, 10000)
        vals = np.random.rand(dim)
        freq = np.random.randint(1, 100)/100
        order = np.random.randint(1, 5)
        output = preprocessing.low_pass_filter(vals, freq, order)
        self.assertIsInstance(output, np.ndarray)

    def test_moving_average(self):
        """Test function of preprocessing.moving_average().
        For an example, see the doctest in the function."""
        series = np.sin(np.linspace(-30, 30, 1000))
        window = np.random.randint(1, len(series))
        output = preprocessing.moving_average(series, window)
        self.assertIsInstance(output, np.ndarray)

    def test_create_on_off_signal(self):
        """Test function of preprocessing.create_on_off_signal().
        For an example, see the doctest in the function."""
        df = pd.DataFrame()
        with self.assertRaises(IndexError):
            # Give too many new names
            preprocessing.create_on_off_signal(df, col_names=["Dummy"], threshold=None,
                                               col_names_new=["One", "too much"])
        with self.assertRaises(IndexError):
            # Too many thresholds given
            preprocessing.create_on_off_signal(df, col_names=["Dummy"],
                                               threshold=[1, 2, 3, 4],
                                               col_names_new=["Dummy_signal"])
        time_df = pd.DataFrame({"dummy_P_el": np.sin(np.linspace(-20, 20, 100))*100})
        df = preprocessing.create_on_off_signal(time_df,
                                                col_names=["dummy_P_el"],
                                                threshold=25,
                                                col_names_new=["dummy_signal"])
        self.assertIsInstance(df["dummy_signal"], pd.Series)
        self.assertIsInstance(df, pd.DataFrame)

    def test_number_lines_totally_na(self):
        """Test function of preprocessing.number_lines_totally_na().
        For an example, see the doctest in the function."""
        dim = np.random.randint(100)
        nan_col = [np.NaN for i in range(dim)]
        col = [i for i in range(dim)]
        df_nan = pd.DataFrame({"col_1": nan_col, "col_2": nan_col})
        df_normal = pd.DataFrame({"col_1": nan_col, "col_2": col})
        self.assertEqual(preprocessing.number_lines_totally_na(df_nan), dim)
        self.assertEqual(preprocessing.number_lines_totally_na(df_normal), 0)
        # Test wrong input
        with self.assertRaises(TypeError):
            preprocessing.number_lines_totally_na("not_a_df")

    def test_z_score(self):
        """Test function of preprocessing.z_score().
        For an example, see the doctest in the function."""
        normal_dis = np.random.normal(0, 1, 1000)
        res = preprocessing.z_score(normal_dis, limit=2)
        self.assertIsInstance(res, np.ndarray)

    def test_modified_z_score(self):
        """Test function of preprocessing.modified_z_score().
        For an example, see the doctest in the function."""
        normal_dis = np.random.normal(0, 1, 1000)
        res = preprocessing.modified_z_score(normal_dis, limit=2)
        self.assertIsInstance(res, np.ndarray)

    def test_interquartile_range(self):
        """Test function of preprocessing.interquartile_range().
        For an example, see the doctest in the function."""
        normal_dis = np.random.normal(0, 1, 1000)
        res = preprocessing.interquartile_range(normal_dis)
        self.assertIsInstance(res, np.ndarray)

    def test_cross_validation(self):
        """Test function of preprocessing.cross_validation().
        For an example, see the doctest in the function.
        """
        dim = np.random.randint(1, 1000)
        test_size = np.random.rand(1)[0]
        x = np.random.rand(dim)
        y = np.random.rand(dim)
        ret = preprocessing.cross_validation(x, y, test_size=test_size)
        self.assertEqual(len(ret), 4)
        # Compare sizes of test and train-sets
        self.assertEqual(len(ret[0]), len(ret[2]))
        self.assertEqual(len(ret[1]), len(ret[3]))


if __name__ == "__main__":
    unittest.main()
