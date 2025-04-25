## ###############################################################
## DEPENDENCIES
## ###############################################################
import unittest
import os
from pathlib import Path
from jormi.ww_io import csv_files


## ###############################################################
## FUNCTION WRAPPERS
## ###############################################################
def save_dict_to_csv_file_wrapper(*args, **kwargs):
  kwargs["verbose"] = False
  csv_files.save_dict_to_csv_file(*args, **kwargs)

def read_csv_file_into_dict_wrapper(*args, **kwargs):
  kwargs["verbose"] = False
  return csv_files.read_csv_file_into_dict(*args, **kwargs)


## ###############################################################
## TEST SUITE
## ###############################################################
class TestCsvUtils(unittest.TestCase):

  def setUp(self):
    self.test_file_path = Path("test_file.csv")
    if self.test_file_path.exists():
      os.remove(self.test_file_path)

  def tearDown(self):
    if self.test_file_path.exists():
      os.remove(self.test_file_path)

  def test_save_dict_to_csv_file(self):
    data = {"a": [1, 2, 3], "b": [0.1, 0.2, 0.3]}
    save_dict_to_csv_file_wrapper(self.test_file_path, data)
    self.assertTrue(self.test_file_path.exists())
    result = read_csv_file_into_dict_wrapper(self.test_file_path)
    self.assertEqual(result, data)

  def test_save_dict_to_csv_file_append(self):
    data_1 = {"a": [1, 2], "b": [0.1, 0.2]}
    data_2 = {"a": [3, 4], "b": [0.3, 0.4]}
    save_dict_to_csv_file_wrapper(self.test_file_path, data_1)
    save_dict_to_csv_file_wrapper(self.test_file_path, data_2, overwrite=False)
    expected = {"a": [1, 2, 3, 4], "b": [0.1, 0.2, 0.3, 0.4]}
    result = read_csv_file_into_dict_wrapper(self.test_file_path)
    self.assertEqual(result, expected)

  def test_save_dict_to_csv_file_overwrite(self):
    data_1 = {"a": [1, 2], "b": [0.1, 0.2]}
    data_2 = {"a": [3, 4], "b": [0.3, 0.4]}
    save_dict_to_csv_file_wrapper(self.test_file_path, data_1)
    save_dict_to_csv_file_wrapper(self.test_file_path, data_2, overwrite=True)
    result = read_csv_file_into_dict_wrapper(self.test_file_path)
    self.assertEqual(result, data_2)

  def test_save_dict_to_csv_file_extend(self):
    data_1 = {"a": [1, 2], "b": [0.1, 0.2]}
    data_2 = {"a": [3, 4], "b": [0.3, 0.4], "c": [10, 20, 30, 40]}
    save_dict_to_csv_file_wrapper(self.test_file_path, data_1)
    save_dict_to_csv_file_wrapper(self.test_file_path, data_2)
    result = read_csv_file_into_dict_wrapper(self.test_file_path)
    expected = {"a": [1, 2, 3, 4], "b": [0.1, 0.2, 0.3, 0.4], "c": [10, 20, 30, 40]}
    self.assertEqual(result, expected)

  def test_new_file_with_unequal_column_lengths_should_fail(self):
    data = {"a": [1, 2], "b": [0.1]}
    with self.assertRaises(ValueError):
      save_dict_to_csv_file_wrapper(self.test_file_path, data)

  def test_extend_with_short_new_column_should_fail(self):
    data_1 = {"a": [1, 2], "b": [0.1, 0.2]}
    save_dict_to_csv_file_wrapper(self.test_file_path, data_1)
    data_2 = {"a": [3, 4], "b": [0.3, 0.4], "c": [100.0]}
    with self.assertRaises(ValueError):
      save_dict_to_csv_file_wrapper(self.test_file_path, data_2)

  def test_extend_with_inconsistent_existing_lengths_should_fail(self):
    data_1 = {"a": [1, 2], "b": [0.1, 0.2]}
    save_dict_to_csv_file_wrapper(self.test_file_path, data_1)
    data_2 = {"a": [3, 4], "b": [0.3]}
    with self.assertRaises(ValueError):
      save_dict_to_csv_file_wrapper(self.test_file_path, data_2)

  def test_extend_with_new_column_correct_length_should_pass(self):
    data_1 = {"x": [1, 2]}
    save_dict_to_csv_file_wrapper(self.test_file_path, data_1)
    data_2 = {"x": [3, 4]}
    save_dict_to_csv_file_wrapper(self.test_file_path, data_2)
    data_3 = {"y": [10, 20, 30, 40]}
    save_dict_to_csv_file_wrapper(self.test_file_path, data_3)
    result = read_csv_file_into_dict_wrapper(self.test_file_path)
    expected = {"x": [1, 2, 3, 4], "y": [10, 20, 30, 40]}
    self.assertEqual(result, expected)

  def test_overwrite_with_unequal_lengths_should_fail(self):
    data_1 = {"a": [1, 2], "b": [0.1, 0.2]}
    data_2 = {"a": [3], "b": [0.3, 0.4]}
    save_dict_to_csv_file_wrapper(self.test_file_path, data_1)
    with self.assertRaises(ValueError):
      save_dict_to_csv_file_wrapper(self.test_file_path, data_2, overwrite=True)

  def test_save_empty_dict_should_fail(self):
    data = {}
    with self.assertRaises(ValueError):
      save_dict_to_csv_file_wrapper(self.test_file_path, data)

  def test_dict_with_non_list_values_should_fail(self):
    data = {"a": 123, "b": "hello"}
    with self.assertRaises(TypeError):
      save_dict_to_csv_file_wrapper(self.test_file_path, data)

  def test_non_string_keys_should_fail(self):
    data = {1: [1, 2], 2: [3, 4]}
    with self.assertRaises(TypeError):
      save_dict_to_csv_file_wrapper(self.test_file_path, data)

  def test_read_nonexistent_file_should_fail(self):
    with self.assertRaises(FileNotFoundError):
      read_csv_file_into_dict_wrapper(Path("nonexistent.csv"))



## ###############################################################
## TEST ENTRY POINT
## ###############################################################
if __name__ == "__main__":
  unittest.main()


## END OF TEST