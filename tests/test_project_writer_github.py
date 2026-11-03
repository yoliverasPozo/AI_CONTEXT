"""Transport contract tests. No test calls GitHub or a real gh process."""
import copy
import unittest

from examples.project_sync.writer_github import Backend, validate_config, ADD_ONE
from examples.project_sync.writer import WriterError
from examples.project_sync.planner import PlanError


def config():
    return {"enabled":False, "project":{"id":"PROJECT","owner":"example","owner_type":"user","number":1},
            "target":{"id":"PR_NEW","repository":"example/widget","number":8,"head_sha":"a"*40},
            "limits":{"max_calls":30,"rate_floor":100,"max_pages":10,"page_size":20}}


def conn(nodes):
    return {"nodes":nodes,"totalCount":len(nodes),"pageInfo":{"hasNextPage":False,"endCursor":None}}


class Wire:
    def __init__(self):
        self.calls=[]
        self.item={"id":"OLD","isArchived":True,"content":{"__typename":"Issue","id":"I_OLD"},
                   "fieldValues":conn([{"__typename":"ProjectV2ItemFieldSingleSelectValue",
                                         "field":{"id":"F"},"optionId":"hold","name":"Hold"}])}
        self.project={"id":"PROJECT","number":1,"owner":{"__typename":"User","login":"example"},
                      "public":False,"closed":False,
                      "fields":conn([{"__typename":"ProjectV2SingleSelectField","id":"F","name":"Gate",
                                      "dataType":"SINGLE_SELECT","options":[{"id":"hold","name":"Hold","description":"","color":"RED"}]}])}
        self.target={"__typename":"PullRequest","id":"PR_NEW","number":8,"state":"OPEN",
                     "headRefOid":"a"*40,"repository":{"nameWithOwner":"example/widget"}}

    def __call__(self, document, variables):
        self.calls.append((document,variables))
        if document == ADD_ONE:
            return {"data":{"addProjectV2ItemById":{"item":{"id":"NEW"},"clientMutationId":variables["operation"]}}}
        project=copy.deepcopy(self.project)
        project["items"]=conn([copy.deepcopy(self.item)])
        return {"data":{"project":project,"target":copy.deepcopy(self.target),"viewer":{"login":"example"},
                        "rateLimit":{"remaining":4000,"cost":1}}}


class BackendTests(unittest.TestCase):
    def test_reads_archived_items_all_fields_and_exact_target(self):
        wire=Wire(); backend=Backend(config(),transport=wire)
        result=backend.read()
        self.assertTrue(result["complete"])
        self.assertTrue(result["items"][0]["archived"])
        self.assertEqual(result["items"][0]["values"][0]["value"]["optionId"],"hold")
        self.assertEqual(result["project"]["fields"][0]["options"][0]["color"],"RED")
        self.assertTrue(all(doc.startswith("query ") for doc,_ in wire.calls))
        self.assertIn("archivedStates:[ARCHIVED, NOT_ARCHIVED]",wire.calls[0][0])
        self.assertEqual(backend.metrics["read_calls"],1)

    def test_wrong_identity_unknown_field_or_truncated_values_fail_closed(self):
        for mode in ("owner","head","unknown","truncated","redacted","field"):
            wire=Wire()
            if mode=="owner": wire.project["owner"]["login"]="other"
            if mode=="head": wire.target["headRefOid"]="b"*40
            if mode=="unknown": wire.item["fieldValues"]["nodes"][0]["__typename"]="FutureValue"
            if mode=="truncated": wire.item["fieldValues"]["totalCount"]=2
            if mode=="redacted": wire.item["content"]=None
            if mode=="field": wire.project["fields"]["nodes"][0]["__typename"]="FutureField"
            with self.subTest(mode=mode), self.assertRaises((WriterError,PlanError)):
                Backend(config(),transport=wire).read()

    def test_disabled_or_wrong_scope_cannot_invoke_fixed_mutation(self):
        wire=Wire(); backend=Backend(config(),transport=wire)
        with self.assertRaises(WriterError): backend.add("PROJECT","PR_NEW","op")
        enabled=config();enabled["enabled"]=True
        backend=Backend(enabled,transport=wire,armed=True)
        with self.assertRaises(WriterError): backend.add("OTHER","PR_NEW","op")
        self.assertEqual(wire.calls,[])

    def test_fixed_add_is_one_attempt_and_response_must_echo_operation(self):
        wire=Wire(); cfg=config();cfg["enabled"]=True
        backend=Backend(cfg,transport=wire,armed=True)
        backend.read()
        self.assertEqual(backend.add("PROJECT","PR_NEW","op"),"NEW")
        with self.assertRaises(WriterError): backend.add("PROJECT","PR_NEW","op")
        self.assertEqual(sum(d==ADD_ONE for d,_ in wire.calls),1)

    def test_rate_floor_and_api_errors_never_produce_partial_snapshot(self):
        for response in ({"errors":[{"message":"private secret"}]},
                         {"data":{"rateLimit":{"remaining":1,"cost":1}}}):
            with self.assertRaises(PlanError): Backend(config(),transport=lambda *a:response).read()

    def test_configuration_is_narrow_and_disabled_example_is_valid(self):
        self.assertFalse(validate_config(config())["enabled"])
        for change in ({"enabled":"false"},{"extra":True},{"limits":{"max_calls":100000}}):
            with self.assertRaises(WriterError): validate_config(dict(config(),**change))

    def test_organization_scope_is_explicitly_unsupported(self):
        cfg=config();cfg["project"]["owner_type"]="organization"
        with self.assertRaises(WriterError): validate_config(cfg)

    def test_actual_pagination_and_duplicate_ids_are_checked(self):
        wire=Wire()
        def transport(document,variables):
            response=wire(document,variables)
            items=response["data"]["project"]["items"]
            items["totalCount"]=2
            if variables["cursor"] is None:
                items["pageInfo"]={"hasNextPage":True,"endCursor":"next"}
            else:
                items["nodes"][0]["id"]="SECOND"
                items["nodes"][0]["content"]["id"]="I_SECOND"
            return response
        self.assertEqual(len(Backend(config(),transport=transport).read()["items"]),2)
        wire=Wire()
        def repeated(document,variables):
            response=wire(document,variables)
            items=response["data"]["project"]["items"];items["totalCount"]=2
            items["pageInfo"]={"hasNextPage":variables["cursor"] is None,"endCursor":"next"}
            return response
        with self.assertRaises(WriterError): Backend(config(),transport=repeated).read()

    def test_unknown_outcome_spends_transport_and_sanitizes_error(self):
        wire=Wire(); cfg=config();cfg["enabled"]=True
        def transport(document,variables):
            if document==ADD_ONE: raise TimeoutError("credential-like private text")
            return wire(document,variables)
        backend=Backend(cfg,transport=transport,armed=True);backend.read()
        with self.assertRaisesRegex(WriterError,"outcome uncertain") as caught: backend.add("PROJECT","PR_NEW","one")
        self.assertNotIn("private text",str(caught.exception))
        with self.assertRaises(WriterError): backend.add("PROJECT","PR_NEW","one")
        self.assertEqual(backend.metrics["mutation_attempts"],1)

    def test_redacted_or_malformed_populated_relations_fail_closed(self):
        for kind,key in (("Repository","repository"),("Milestone","milestone")):
            for relation in (None,{}, {"id":"RELATION"}):
                wire=Wire()
                wire.item["fieldValues"]["nodes"]=[{"__typename":"ProjectV2ItemField"+kind+"Value","field":{"id":"F"},key:relation}]
                with self.subTest(kind=kind,relation=relation),self.assertRaises(WriterError):
                    Backend(config(),transport=wire).read()

    def test_paging_definition_or_head_drift_repeated_cursor_and_duplicate_content_refuse(self):
        for mode in ("definition","head","cursor","content"):
            wire=Wire()
            def transport(document,variables):
                response=wire(document,variables);p=response["data"]["project"]
                p["items"]["totalCount"]=3 if mode=="cursor" else 2
                p["items"]["pageInfo"]={"hasNextPage":variables["cursor"] is None or mode=="cursor","endCursor":"next"}
                if variables["cursor"] is not None:
                    p["items"]["nodes"][0]["id"]="SECOND"
                    if mode!="content": p["items"]["nodes"][0]["content"]["id"]="I_SECOND"
                    if mode=="definition": p["fields"]["nodes"][0]["name"]="Human changed definition"
                    if mode=="head": response["data"]["target"]["headRefOid"]="b"*40
                return response
            with self.subTest(mode=mode),self.assertRaises(WriterError): Backend(config(),transport=transport).read()

    def test_missing_or_mismatched_mutation_ack_is_uncertain_and_never_retried(self):
        for response in ({"data":{"addProjectV2ItemById":{"clientMutationId":"other","item":{"id":"NEW"}}}},
                         {"data":{"addProjectV2ItemById":{"clientMutationId":"one","item":None}}},
                         {"errors":[{"message":"sensitive server error"}]}):
            wire=Wire();cfg=config();cfg["enabled"]=True
            def transport(document,variables): return response if document==ADD_ONE else wire(document,variables)
            backend=Backend(cfg,transport=transport,armed=True);backend.read()
            with self.subTest(response=response),self.assertRaises(WriterError): backend.add("PROJECT","PR_NEW","one")
            with self.assertRaises(WriterError): backend.add("PROJECT","PR_NEW","one")
            self.assertEqual(backend.metrics["mutation_attempts"],1)
