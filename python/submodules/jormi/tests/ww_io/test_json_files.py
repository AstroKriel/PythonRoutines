## ###############################################################
## DEPENDENCIES
## ###############################################################
import unittest
import os
import json
import numpy as np
from pathlib import Path
from jormi.ww_io import json_files
from jormi.utils import dict_utils


## ###############################################################
## FUNCTION WRAPPERS
## ###############################################################
def save_dict_to_json_file(*args, **kwargs):
  kwargs["verbose"] = False
  json_files.save_dict_to_json_file(*args, **kwargs)

def read_json_file_into_dict(*args, **kwargs):
  kwargs["verbose"] = False
  return json_files.read_json_file_into_dict(*args, **kwargs)


## ###############################################################
## TEST SUITE
## ###############################################################
class TestJsonUtils(unittest.TestCase):

  def setUp(self):
    self.test_file_path = Path("test_file.json")
    if self.test_file_path.exists():
      os.remove(self.test_file_path)

  def tearDown(self):
    if self.test_file_path.exists():
      os.remove(self.test_file_path)

  def test_create_new_json_file(self):
    data = {"a": 1, "b": [1, 2, 3]}
    save_dict_to_json_file(self.test_file_path, data)
    self.assertTrue(self.test_file_path.exists())
    result = read_json_file_into_dict(self.test_file_path)
    self.assertEqual(result, data)

  def test_add_dict_to_existing_json_file(self):
    data1 = {"a": 1}
    data2 = {"b": 2}
    expected = dict_utils.merge_dicts(data1, data2)
    save_dict_to_json_file(self.test_file_path, data1)
    save_dict_to_json_file(self.test_file_path, data2)
    result = read_json_file_into_dict(self.test_file_path)
    self.assertEqual(result, expected)

  def test_overwrite_json_file(self):
    data1 = {"a": 1}
    data2 = {"b": 2}
    save_dict_to_json_file(self.test_file_path, data1)
    json_files.save_dict_to_json_file(self.test_file_path, data2, overwrite=True, verbose=False)
    result = read_json_file_into_dict(self.test_file_path)
    self.assertEqual(result, data2)

  def test_read_nonexistent_json_file_raises(self):
    with self.assertRaises(FileNotFoundError):
      read_json_file_into_dict(file_path="nonexistent.json")

  def test_read_invalid_extension_raises(self):
    invalid_file = Path("invalid_file.txt")
    with self.assertRaises(ValueError):
      read_json_file_into_dict(file_path=invalid_file)

  def test_save_invalid_extension_raises(self):
    with self.assertRaises(ValueError):
      json_files._create_json_file_from_dict("invalid.txt", {"a": 1})

  def test_numpy_serialization(self):
    data = {
      "int"   : np.int32(42),
      "float" : np.float64(3.14),
      "bool"  : np.bool_(True),
      "array" : np.array([1, 2, 3])
    }
    save_dict_to_json_file(self.test_file_path, data)
    result = read_json_file_into_dict(self.test_file_path)
    expected = {
      "int": 42,
      "float": 3.14,
      "bool": True,
      "array": [1, 2, 3]
    }
    self.assertEqual(result, expected)

  def test_merge_with_nested_dicts(self):
    d1 = {"a": {"x": 1}, "b": 2}
    d2 = {"a": {"y": 3}, "c": 4}
    save_dict_to_json_file(self.test_file_path, d1)
    save_dict_to_json_file(self.test_file_path, d2)
    expected = dict_utils.merge_dicts(d1, d2)
    result = read_json_file_into_dict(self.test_file_path)
    self.assertEqual(result, expected)

  def test_scalar_overwritten_by_list(self):
    data1 = {"a": 1}
    data2 = {"a": [2, 3]}
    save_dict_to_json_file(self.test_file_path, data1)
    save_dict_to_json_file(self.test_file_path, data2)
    result = read_json_file_into_dict(self.test_file_path)
    self.assertEqual(result, {"a": [2, 3]})

  def test_list_overwritten_by_scalar(self):
    data1 = {"a": [1, 2]}
    data2 = {"a": 42}
    save_dict_to_json_file(self.test_file_path, data1)
    save_dict_to_json_file(self.test_file_path, data2)
    result = read_json_file_into_dict(self.test_file_path)
    self.assertEqual(result, {"a": 42})

  def test_nested_dict_overwritten_by_scalar(self):
    data1 = {"a": {"x": 1}}
    data2 = {"a": 100}
    save_dict_to_json_file(self.test_file_path, data1)
    save_dict_to_json_file(self.test_file_path, data2)
    result = read_json_file_into_dict(self.test_file_path)
    self.assertEqual(result, {"a": 100})

  def test_overwrite_with_none(self):
    data1 = {"key": "value"}
    data2 = {"key": None}
    save_dict_to_json_file(self.test_file_path, data1)
    save_dict_to_json_file(self.test_file_path, data2)
    result = read_json_file_into_dict(self.test_file_path)
    self.assertEqual(result, {"key": None})


## ###############################################################
## TEST ENTRY POINT
## ###############################################################
if __name__ == "__main__":
  unittest.main()


## END OF TEST