import unittest

import test_forms
import test_models
import test_templatetags
import test_views

def suite():
    suite1 = unittest.TestLoader().loadTestsFromModule(test_templatetags)
    suite2 = unittest.TestLoader().loadTestsFromModule(test_views)
    suite3 = unittest.TestLoader().loadTestsFromModule(test_models)
    suite4 = unittest.TestLoader().loadTestsFromModule(test_forms)
    
    alltests = unittest.TestSuite([suite1, suite2, suite3, suite4])
    
    return alltests

def load_tests(loader, tests, pattern):
    return suite()