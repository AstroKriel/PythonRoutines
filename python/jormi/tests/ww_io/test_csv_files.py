## ###############################################################
## DEPENDENCIES
## ###############################################################
import unittest
import tempfile
import shutil
from pathlib import Path
from jormi.ww_io import csv_files


## ###############################################################
## FUNCTION WRAPPERS
## ###############################################################
def _save_dict_to_csv_file(*args, **kwargs):
  kwargs.setdefault("verbose", False)
  csv_files.save_dict_to_csv_file(*args, **kwargs)

def _read_csv_file_into_dict(*args, **kwargs):
  kwargs.setdefault("verbose", False)
  return csv_files.read_csv_file_into_dict(*args, **kwargs)


## ###############################################################
## TESTS
## ###############################################################
class TestCsvUtils(unittest.TestCase):

  def setUp(self):
    self.temp_dir = tempfile.mkdtemp()
    self.file_path = Path(self.temp_dir) / "test_data.csv"

  def tearDown(self):
    shutil.rmtree(self.temp_dir)

  def test_write_and_read_csv(self):
    ## typical case: write a new CSV and read it back
    data = {"x": [1.0, 2.0, 3.0], "y": [4.0, 5.0, 6.0]}
    _save_dict_to_csv_file(self.file_path, data)
    read_back = _read_csv_file_into_dict(self.file_path)
    self.assertEqual(read_back, data)

  def test_merge_column(self):
    ## typical case: add a compatible new column
    initial = {"x": [1.0, 2.0, 3.0]}
    added   = {"y": [4.0, 5.0, 6.0]}
    expected = {"x": [1.0, 2.0, 3.0], "y": [4.0, 5.0, 6.0]}
    _save_dict_to_csv_file(self.file_path, initial)
    _save_dict_to_csv_file(self.file_path, added)  # Merge mode
    result = _read_csv_file_into_dict(self.file_path)
    self.assertEqual(result, expected)

  def test_fail_on_mismatched_shared_column(self):
    ## edge case: attempt to merge conflicting values on shared key
    _save_dict_to_csv_file(self.file_path, {"x": [1.0, 2.0, 3.0]})
    with self.assertRaises(ValueError):
      _save_dict_to_csv_file(self.file_path, {"x": [9.0, 9.0, 9.0], "z": [7.0, 8.0, 9.0]})

  def test_fail_on_length_mismatch_new_column(self):
    ## edge case: new column length doesn't match existing data
    _save_dict_to_csv_file(self.file_path, {"x": [1.0, 2.0, 3.0]})
    with self.assertRaises(ValueError):
      _save_dict_to_csv_file(self.file_path, {"z": [9.0, 8.0]})

  def test_overwrite_existing_csv(self):
    ## overwrite flag: replace old file completely
    _save_dict_to_csv_file(self.file_path, {"x": [1.0, 2.0, 3.0]})
    _save_dict_to_csv_file(self.file_path, {"y": [4.0, 5.0, 6.0]}, overwrite=True)
    read_back = _read_csv_file_into_dict(self.file_path)
    self.assertEqual(read_back, {"y": [4.0, 5.0, 6.0]})

  def test_save_to_new_file(self):
    ## edge case: no file exists yet
    data = {"a": [10.0, 20.0, 30.0]}
    _save_dict_to_csv_file(self.file_path, data)
    self.assertTrue(self.file_path.exists())
    self.assertEqual(_read_csv_file_into_dict(self.file_path), data)


## ###############################################################
## TEST ENTRY POINT
## ###############################################################
if __name__ == "__main__":
  unittest.main()


## END OF TEST
