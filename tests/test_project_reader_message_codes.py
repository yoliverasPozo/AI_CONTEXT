import copy
import unittest

from examples.project_sync.writer_diagnostics import error_code
from examples.project_sync.writer_github import Backend, value, validate_config
from tests.test_project_writer_github import Wire, config


class ReaderMessageTests(unittest.TestCase):
    def test_pr_lens_identity_and_unavailable_findings(self):
        for mode,want in (("missing","project_or_pr_unavailable"),("viewer","unexpected_identity")):
            wire=Wire()
            def transport(document,variables):
                result=wire(document,variables)
                if mode=="missing":result["data"]["project"]=None
                else:result["data"]["viewer"]["login"]="other"
                return result
            backend=Backend(config(),transport=transport)
            with self.assertRaises(Exception):backend.read()
            self.assertEqual(backend.read_evidence["failure_code"],want)

    def test_pr_lens_relation_failures_are_specific(self):
        cases=[("User",{"users":{"nodes":[{}],"totalCount":1,"pageInfo":{"hasNextPage":False}}},"unreadable_field_relation"),
               ("Repository",{"repository":{"id":"R","nameWithOwner":"invalid"}},"unreadable_field_relation"),
               ("Milestone",{"milestone":{"id":"M","title":"x","state":"INVALID","dueOn":None}},"unreadable_field_relation"),
               ("User",{},"field_collection_incomplete"),
               ("User",{"users":{"nodes":[{"id":"U"},{"id":"U"}],"totalCount":2,"pageInfo":{"hasNextPage":False}}},"duplicate_field_relation")]
        for kind,payload,want in cases:
            with self.subTest(kind=kind,payload=payload):
                with self.assertRaises(Exception) as caught:value(dict(payload,__typename="ProjectV2ItemField"+kind+"Value",field={"id":"F"}))
                self.assertEqual(error_code(caught.exception),want)

    def test_value_and_field_identity_shape_failures_have_codes(self):
        for node,want in ((None,"unreadable_field_value"),({"__typename":"ProjectV2ItemFieldTextValue","text":"x","field":None},"field_identity_unavailable")):
            with self.assertRaises(Exception) as caught:value(node)
            self.assertEqual(error_code(caught.exception),want)

    def test_config_and_add_gates_are_classified_without_contact(self):
        with self.assertRaises(Exception) as caught:validate_config(dict(config(),enabled="yes"))
        self.assertEqual(error_code(caught.exception),"invalid_configuration")
        backend=Backend(config(),transport=lambda *a:self.fail("must not call transport"))
        with self.assertRaises(Exception) as caught:backend.add("PROJECT","PR_NEW","op")
        self.assertEqual(error_code(caught.exception),"mutation_not_armed")
