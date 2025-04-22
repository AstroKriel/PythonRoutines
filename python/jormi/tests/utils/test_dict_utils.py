## ###############################################################
## DEPENDENCIES
## ###############################################################
import unittest
from jormi.utils import dict_utils


## ###############################################################
## TESTS
## ###############################################################
class TestDictUtils(unittest.TestCase):

  def test_merge_dicts_basic(self):
    ## usual case 1: merging two dictionaries with a mix of nested and simple keys
    dict1 = {"a": 1, "b": {"c": 2}}
    dict2 = {"b": {"d": 3}, "e": 4, "d": {"f": 10}}
    dict_merged = dict_utils.merge_dicts(dict1, dict2)
    dict_expected = {"a": 1, "b": {"c": 2, "d": 3}, "e": 4, "d": {"f": 10}}
    self.assertEqual(dict_merged, dict_expected)
    self.assertEqual(dict1, {"a": 1, "b": {"c": 2}})
    self.assertEqual(dict2, {"b": {"d": 3}, "e": 4, "d": {"f": 10}})
    ## usual case 2: merging two dictionaries with lists in the same key
    dict_with_list = {"a": [1, 2], "b": 3}
    dict_to_merge = {"a": [3, 4], "c": 5}
    merged_lists = dict_utils.merge_dicts(dict_with_list, dict_to_merge)
    expected_lists = {"a": [1, 2, 3, 4], "b": 3, "c": 5}
    self.assertEqual(merged_lists, expected_lists)
    ## edge case 1: merging two empty dictionaries
    dict1_empty = {}
    dict2_empty = {}
    dict_merged = dict_utils.merge_dicts(dict1_empty, dict2_empty)
    self.assertEqual(dict_merged, {})
    ## edge case 2: merging a dictionary with values and an empty dictionary
    dict1_empty_value = {"a": 1}
    dict2_empty_value = {}
    dict_merged = dict_utils.merge_dicts(dict1_empty_value, dict2_empty_value)
    self.assertEqual(dict_merged, {"a": 1})
    ## edge case 3: merging an empty dictionary with a non-empty one
    dict_1 = {}
    dict_2 = {"a": 1, "b": 2}
    dict_merged = dict_utils.merge_dicts(dict_1, dict_2)
    dict_expected = {"a": 1, "b": 2}
    self.assertEqual(dict_merged, dict_expected)

  def test_merge_dicts_with_overwrite(self):
    ## typical case: merging two dictionaries with simple values types (integer and string)
    dict_1 = {"a": 1, "b": "hello"}
    dict_2 = {"a": {"c": 2}, "b": "world", "c": 3}
    dict_merged = dict_utils.merge_dicts(dict_1, dict_2)
    dict_expected = {"a": {"c": 2}, "b": "world", "c": 3}
    self.assertEqual(dict_merged, dict_expected)
    ## typical case: merging two dictionaries with simple values types (integer and string)
    dict_1 = {"a": 1, "b": "hello"}
    dict_2 = {"a": {"c": 2}, "b": "world", "c": 3}
    dict_merged = dict_utils.merge_dicts(dict_2, dict_1)
    dict_expected = {"a": 1, "b": "hello", "c": 3}
    self.assertEqual(dict_merged, dict_expected)

  def test_merge_dicts_no_side_effects(self):
    ## edge case: check that modifying the dict_merged dictionary does not affect the originals
    dict_1 = {"a": [1, 2]}
    dict_2 = {"a": [3, 4], "b": 5}
    dict_merged = dict_utils.merge_dicts(dict_1, dict_2)
    ## modify dict_merged dict and check originals are unchanged
    dict_merged["a"].append(10)
    self.assertEqual(dict_1, {"a": [1, 2]})
    self.assertEqual(dict_2, {"a": [3, 4], "b": 5})

  def test_merge_dicts_complex_structures(self):
    ## typical case: merging two complex dictionaries with mixed structures (lists, sets, and nested dictionaries)
    dict_1 = {
        "a": [1, 2],
        "b": {"x": 1},
        "c": {1, 2}
    }
    dict_2 = {
        "a": [3, 4],
        "b": {"y": 2},
        "c": {3, 4},
        "d": "new"
    }
    dict_merged = dict_utils.merge_dicts(dict_1, dict_2)
    dict_expected = {
        "a": [1, 2, 3, 4],
        "b": {"x": 1, "y": 2},
        "c": {1, 2, 3, 4},
        "d": "new"
    }
    self.assertEqual(dict_merged, dict_expected)

  def test_merge_dicts_key_conflict(self):
    ## edge case: merging a dictionary with a list with a value in the other dictionary that is not a list
    dict_1 = {"a": [1, 2]}
    dict_2 = {"a": 3}
    dict_merged = dict_utils.merge_dicts(dict_1, dict_2)
    dict_expected = {"a": 3}
    self.assertEqual(dict_merged, dict_expected)

  def test_merge_dicts_with_none_values(self):
    ## typical case: merging a dictionary with `None` values
    dict_1 = {"a": None, "b": 2}
    dict_2 = {"a": 1, "c": 3}
    dict_merged = dict_utils.merge_dicts(dict_1, dict_2)
    dict_expected = {"a": 1, "b": 2, "c": 3}
    self.assertEqual(dict_merged, dict_expected)

  def test_are_dicts_different(self):
    ## typical case 1: identical dictionaries
    dict1 = {"a": 1, "b": 2}
    dict2 = {"a": 1, "b": 2}
    self.assertFalse(dict_utils.are_dicts_different(dict1, dict2))
    ## typical case 2: different dictionaries
    dict3 = {"a": 1, "b": 3}
    dict4 = {"a": 1}
    self.assertTrue(dict_utils.are_dicts_different(dict1, dict3))
    self.assertTrue(dict_utils.are_dicts_different(dict1, dict4))
    ## edge case 1: comparing two empty dictionaries
    dict_empty1 = {}
    dict_empty2 = {}
    self.assertFalse(dict_utils.are_dicts_different(dict_empty1, dict_empty2))
    ## edge case 2: comparing an empty dictionary with a non-empty one
    dict_empty_non_empty = {}
    dict_non_empty = {"a": 1}
    self.assertTrue(dict_utils.are_dicts_different(dict_empty_non_empty, dict_non_empty))
    ## edge case 3: comparing dictionaries with lists in the same key
    dict_with_list1 = {"a": [1, 2], "b": 3}
    dict_with_list2 = {"a": [1, 2], "b": 4}
    self.assertTrue(dict_utils.are_dicts_different(dict_with_list1, dict_with_list2))
    ## edge case 4: comparing nested dictionaries
    dict_with_nested1 = {"a": 1, "b": {"c": 2}}
    dict_with_nested2 = {"a": 1, "b": {"c": 3}}
    self.assertTrue(dict_utils.are_dicts_different(dict_with_nested1, dict_with_nested2))
    ## edge case 5: comparing identical nested dictionaries
    dict_with_nested_same = {"a": 1, "b": {"c": 2}}
    self.assertFalse(dict_utils.are_dicts_different(dict_with_nested1, dict_with_nested_same))


## ###############################################################
## TEST ENTRY POINT
## ###############################################################
if __name__ == "__main__":
  unittest.main()


## END OF TEST