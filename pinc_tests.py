#!/usr/bin/env python3

import unittest
from pinc import version_compare
from pinc import PkgVer

same_versions = [
    ("1.2.12.102", "1.2.12.102"),
    ("monkey", "monkey"),
    ("g-2.e", "g-2.e"),
    ("1-1", "1-1"),
]

outdated_versions = [
    ("1-1", "2-1"),
    ("1-1", "1-2"),
    ("1.2.3-1", "1.2.4-1"),
    ("1.8rc1+6+g0f377f94-1", "1.8rc2+1+g7e949283-1"),
    ("1.8rc2", "1.9rc1"),
    ("2.99.917+812+g75795523-1", "2.99.917+823+gd9bf46e4-1"),
    ("1.2.9-1", "1.2.10-1"),
    ("1.2-1", "1.2.1-1"),
    ("1.0.2_r0-1", "1.0.2_r0-2"),
    ("1.0.2_r0-1", "1.0.2_r1-1"),
    ("1.0.2_r0-1", "1.0.3_r0-1"),
]

deLorean_versions = [
    ("2-1", "1-1"),
    ("1-2", "1-1"),
    ("1.2.10-1", "1.2.9-1"),
    ("3.1-14", "2.1-9"),
    ("1.8rc1+6+g0f377f94-1", "1.8rc1+1+g7e949283-1"),
    ("1.2.1-1", "1.2-1"),
    ("0.7-4", "0.7+4+gd8d8c67-1"),  # Moved from outdated
]


class TestVersionComparing(unittest.TestCase):
    def test_up_to_date(self):
        for test_case in same_versions:
            self.assertEqual(version_compare(test_case[0], test_case[1]), PkgVer.uptodate)

    def test_out_of_date(self):
        for test_case in outdated_versions:
            self.assertEqual(version_compare(test_case[0], test_case[1]), PkgVer.outofdate)

    def test_deLorean(self):
        for test_case in deLorean_versions:
            self.assertEqual(version_compare(test_case[0], test_case[1]), PkgVer.newer)


if __name__ == '__main__':
    unittest.main()
