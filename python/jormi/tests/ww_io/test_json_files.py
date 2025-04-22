## ###############################################################
## DEPENDENCIES
## ###############################################################
import unittest
import tempfile
import shutil
import numpy as np
from pathlib import Path
from jormi.ww_io import json_files


## ###############################################################
## FUNCTION WRAPPERS
## ###############################################################
def _save_dict_to_json_file(*args, **kwargs):
  kwargs.setdefault("verbose", False)
  json_files.save_dict_to_json_file(*args, **kwargs)

def _read_json_file_into_dict(*args, **kwargs):
  kwargs.setdefault("verbose", False)
  return json_files.read_json_file_into_dict(*args, **kwargs)


## ###############################################################
## TESTS
## ###############################################################
class TestJsonUtils(unittest.TestCase):

  def setUp(self):
    self.temp_dir = tempfile.mkdtemp()
    self.file_path = Path(self.temp_dir) / "data.json"

  def tearDown(self):
    shutil.rmtree(self.temp_dir)

  def test_create_and_read_json_file(self):
    ## typical case: save a dict and read it back
    data = {"x": [1, 2, 3], "y": [4.0, 5.0, 6.0]}
    _save_dict_to_json_file(self.file_path, data)
    read_data = _read_json_file_into_dict(file_path=self.file_path)
    self.assertEqual(read_data, data)

  def test_merge_data_into_existing_file(self):
    ## typical case: merge new data into existing file
    data1 = {"a": 1, "b": [1, 2]}
    data2 = {"c": 3}
    expected = {"a": 1, "b": [1, 2], "c": 3}
    _save_dict_to_json_file(self.file_path, data1)
    _save_dict_to_json_file(self.file_path, data2)
    result = _read_json_file_into_dict(file_path=self.file_path)
    self.assertEqual(result, expected)

  def test_overwrite_data_in_existing_file(self):
    ## typical case: file exists and data is overwritten.
    data1 = {"a": 1, "b": [2]}
    data2 = {"b": 3}
    expected = {"a": 1, "b": 3}
    _save_dict_to_json_file(self.file_path, data1)
    _save_dict_to_json_file(self.file_path, data2)
    result = _read_json_file_into_dict(file_path=self.file_path)
    self.assertEqual(result, expected)

  def test_extend_data_in_existing_file(self):
    ## typical case: file exists and data is overwritten.
    data1 = {"a": 1, "b": [2, 3]}
    data2 = {"b": [4]}
    expected = {"a": 1, "b": [2,3,4]}
    _save_dict_to_json_file(self.file_path, data1)
    _save_dict_to_json_file(self.file_path, data2)
    result = _read_json_file_into_dict(file_path=self.file_path)
    self.assertEqual(result, expected)

  def test_numpy_serialization(self):
    ## edge case: ensure numpy types are serialized correctly
    np_data = {
      "int": np.int32(42),
      "float": np.float64(3.14),
      "bool": np.bool_(True),
      "array": np.array([1, 2, 3])
    }
    expected = {
      "int": 42,
      "float": 3.14,
      "bool": True,
      "array": [1, 2, 3]
    }
    _save_dict_to_json_file(self.file_path, np_data)
    read_back = _read_json_file_into_dict(file_path=self.file_path)
    self.assertEqual(read_back, expected)

  def test_file_not_found(self):
    ## edge case: read from missing file
    with self.assertRaises(FileNotFoundError):
      _read_json_file_into_dict(file_path=self.file_path)

  def test_invalid_extension(self):
    ## edge case: file doesn't end in .json
    bad_path = Path(self.temp_dir) / "wrong.txt"
    with self.assertRaises(ValueError):
      _save_dict_to_json_file(bad_path, {"a": 1})
    with self.assertRaises(ValueError):
      _read_json_file_into_dict(file_path=bad_path)


## ###############################################################
## TEST ENTRY POINT
## ###############################################################
if __name__ == "__main__":
  unittest.main()


## END OF TEST
