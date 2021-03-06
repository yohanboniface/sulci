#!/usr/bin/env python

import os
import unittest
import argparse

os.environ["SULCI_CONFIG_MODULE"] = "sulci.config.example"

from sulci.tests import textutils, sample, token, stemmedtext, semanticaltagger


if __name__ == "__main__":

    # Define arguments
    parser = argparse.ArgumentParser(description="Run sulci tests suite.")
    parser.add_argument(
        "tests",
        nargs="*",
        default=None,
        help="Tests (module, TestCase or TestCaseMethod) to run (use full path, eg. module.Class.test)."
    )
    parser.add_argument(
        "-v",
        "--verbosity",
        type=int,
        action="store",
        dest="verbosity",
        default=2,
        help="Verbosity of the runner."
    )
    args = parser.parse_args()

    if args.tests:
        # we have names
        suite = unittest.TestLoader().loadTestsFromNames(args.tests)
    else:
        # Run all the tests
        suites = []
        for mod in [textutils, sample, token, stemmedtext, semanticaltagger]:
            suite = unittest.TestLoader().loadTestsFromModule(mod)
            suites.append(suite)
        suite = unittest.TestSuite(suites)
    unittest.TextTestRunner(verbosity=args.verbosity).run(suite)
