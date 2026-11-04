"""Real reader/policy/journal with synthetic post-add pages; no GitHub calls."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from examples.project_sync.writer import prepare, apply
from examples.project_sync.writer_github import Backend, ADD_ONE, validate_config
from examples.project_sync.writer_journal import Journal
from tests.test_project_writer import NOW
from tests.test_project_writer_github import Wire, config, conn


class Clock:
    def __init__(self):self.value=0.0
    def __call__(self):return self.value


class Pages:
    def __init__(self,modes,clock):
        self.wire=Wire();self.clock=clock;self.modes=modes;self.adds=0;self.attempt=0;self.cursors=[];self.step=0.1
        self.old=[]
        for index in range(3):
            item=copy.deepcopy(self.wire.item);item['id']=f'OLD_{index}';item['content']['id']=f'I_{index}';self.old.append(item)

    def __call__(self,document,variables):
        if document==ADD_ONE:
            self.adds+=1
            return {'data':{'addProjectV2ItemById':{'item':{'id':'NEW'},'clientMutationId':variables['operation']}}}
        response=self.wire(document,variables);self.clock.value+=self.step
        rows=copy.deepcopy(self.old);mode='before'
        if self.adds:
            if variables['cursor'] is None:self.attempt+=1
            self.cursors.append((self.attempt,variables['cursor']))
            mode=self.modes[min(self.attempt-1,len(self.modes)-1)]
            if mode=='unknown':raise RuntimeError('private-error-token')
            if mode=='unknown_as_count':raise RuntimeError('membership count changed during pagination')
            rows.append({'id':'NEW','isArchived':False,'content':{'__typename':'PullRequest','id':'PR_NEW'},
                         'fieldValues':conn([{'__typename':'ProjectV2ItemFieldSingleSelectValue','field':{'id':'F'},'optionId':'todo','name':'Todo'}])})
            if mode=='unrelated':
                rows.append(dict(copy.deepcopy(self.old[0]),id='OTHER',content={'__typename':'Issue','id':'I_OTHER'}))
            if mode=='changing_original':rows[0]['fieldValues']['nodes'][0]['name']='Human decision'
            if mode=='field_drift':response['data']['project']['fields']['nodes'][0]['name']='Human field change'
            if mode=='changing_bad_archive':rows[-1]['isArchived']=None
            if mode=='changing_bad_fields':
                rows[-1]['fieldValues']['nodes']*=2;rows[-1]['fieldValues']['totalCount']=2
            if mode=='changing_unknown_field':rows[-1]['fieldValues']['nodes'][0]['field']['id']='UNSEEN'
            if mode=='changing_archived':rows[-1]['isArchived']=True
            if mode=='missing_original':rows.pop(0)
        start=int(variables['cursor'] or 0);end=min(start+2,len(rows))
        count=len(rows)
        if mode in ('changing','changing_original','changing_bad_archive','changing_bad_fields','changing_unknown_field','changing_archived','changing_cursor') and start==0:count=3
        response['data']['project']['items']={'nodes':rows[start:end],'totalCount':count,
            'pageInfo':{'hasNextPage':end<len(rows) or (mode=='changing_cursor' and start>0),'endCursor':str(start) if mode=='changing_cursor' and start>0 else str(end)}}
        response['data']['rateLimit']={'cost':1,'remaining':199 if mode=='rate' else 4000}
        return response


class StabilizationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.case=0

    def run_case(self,modes,policy=None,step=0.1,default=False,lifetime=30,receipt_step=0,validation_step=0,record_failure=False):
        clock=Clock();wire=Pages(modes,clock);wire.step=step
        cfg=config();cfg['enabled']=True;cfg['limits'].update(page_size=2,rate_floor=200,max_calls=lifetime)
        if not default:cfg['verification']=policy or {'max_attempts':3,'max_seconds':30,'max_calls':8}
        before=Backend(cfg,transport=wire).read()
        proposal=prepare(before,'synthetic',NOW,NOW+900)
        approval={'action':'add_one','operation_id':'synthetic','proposal_sha256':proposal['sha256'],
                  'project_id':'PROJECT','content_id':'PR_NEW','expires_at':NOW+900}
        self.case+=1
        journal=Journal.create(Path(self.temp.name)/f'operation-{self.case}',proposal)
        original_append=journal.append
        def append(kind,data):
            if kind=='verification_read' and record_failure:raise OSError('private receipt path')
            original_append(kind,data)
            if kind=='verification_read':clock.value+=receipt_step
        journal.append=append
        backend=Backend(cfg,transport=wire,armed=True,monotonic=clock)
        from examples.project_sync import writer
        normalizer=writer.normalize
        def normalize(source):
            snapshot=normalizer(source)
            if any(i['id']=='NEW' for i in snapshot['items']):clock.value+=validation_step
            return snapshot
        with patch('examples.project_sync.writer.normalize',normalize):
            result=apply(proposal,backend,journal,enabled=True,execute=True,approval=approval,now=NOW+1,clock=lambda:NOW+1)
        return result,wire,journal,backend,proposal,approval

    def test_transient_count_restarts_from_first_page_and_preserves_failed_evidence(self):
        result,wire,journal,*_=self.run_case(['changing','stable'])
        self.assertEqual(result['status'],'verified_present')
        self.assertEqual(wire.adds,1)
        self.assertEqual(wire.cursors,[(1,None),(1,'2'),(2,None),(2,'2')])
        records=[e['data'] for e in journal.events() if e['kind']=='verification_read']
        self.assertEqual(records[0]['diagnostic']['code'],'pagination_count_changed')
        self.assertEqual([p['total_count'] for p in records[0]['diagnostic']['read_evidence']['pages']],[3,4])
        after=journal.events()[-1]['data']['after']
        self.assertEqual(len(after['items']),4)
        self.assertEqual(after['items'][0]['id'],'NEW')

    def test_eventual_stable_third_attempt_keeps_both_failed_attempts(self):
        result,wire,journal,*_=self.run_case(['changing','changing','stable'])
        self.assertEqual(result['status'],'verified_present');self.assertEqual(wire.attempt,3);self.assertEqual(wire.adds,1)
        failed=[e for e in journal.events() if e['kind']=='verification_read' and e['data']['outcome']=='failed']
        self.assertEqual(len(failed),2)

    def test_persistent_count_change_stops_at_attempt_bound(self):
        result,wire,journal,*_=self.run_case(['changing'])
        self.assertEqual(result['status'],'needs_review');self.assertEqual(wire.attempt,3)
        self.assertEqual(result['diagnostic']['code'],'pagination_count_changed');self.assertEqual(wire.adds,1)
        self.assertFalse(any(e['kind']=='complete' for e in journal.events()))

    def test_default_is_one_read_attempt(self):
        result,wire,*_=self.run_case(['changing','stable'],default=True)
        self.assertEqual(result['status'],'needs_review');self.assertEqual(wire.attempt,1);self.assertEqual(wire.adds,1)

    def test_genuine_drift_and_unknown_errors_are_not_retried(self):
        for mode,want in (('changing_original','original_item_changed'),('field_drift','project_or_target_changed'),
                          ('unrelated','unexpected_membership'),('unknown','unexpected_error'),
                          ('unknown_as_count','unexpected_error'),('rate','rate_floor_reached'),
                          ('changing_bad_archive','invalid_item'),('changing_bad_fields','invalid_item_fields'),
                          ('changing_unknown_field','invalid_item_fields'),('changing_archived','target_archived'),
                          ('changing_cursor','pagination_cursor_repeated'),('missing_original','original_item_changed')):
            with self.subTest(mode=mode):
                result,wire,journal,*_=self.run_case([mode,'stable'])
                self.assertEqual(result['status'],'needs_review');self.assertEqual(result['diagnostic']['code'],want)
                self.assertEqual(wire.attempt,1);self.assertEqual(wire.adds,1)
                self.assertNotIn('private-error-token',json.dumps(journal.events()))

    def test_call_budget_shared_across_restarts(self):
        result,wire,_,backend,*_=self.run_case(['changing','stable'],policy={'max_attempts':3,'max_seconds':30,'max_calls':3})
        self.assertEqual(result['status'],'needs_review');self.assertEqual(result['diagnostic']['code'],'verification_call_budget_exhausted')
        self.assertEqual(backend.metrics['read_calls'],5);self.assertEqual(wire.adds,1)

    def test_call_budget_exhausted_exactly_at_restart_is_reported_as_budget(self):
        result,wire,_,backend,*_=self.run_case(['changing','stable'],policy={'max_attempts':3,'max_seconds':30,'max_calls':2})
        self.assertEqual(result['diagnostic']['code'],'verification_call_budget_exhausted')
        self.assertEqual(backend.metrics['read_calls'],4);self.assertEqual(wire.adds,1)

    def test_lifetime_call_budget_not_reset_between_attempts(self):
        result,wire,_,backend,*_=self.run_case(['changing','stable'],lifetime=4)
        self.assertEqual(result['diagnostic']['code'],'call_budget_exhausted')
        self.assertEqual(backend.metrics['read_calls'],4);self.assertEqual(wire.adds,1)

    def test_monotonic_deadline_stops_without_a_second_attempt(self):
        result,wire,*_=self.run_case(['changing','stable'],policy={'max_attempts':3,'max_seconds':1,'max_calls':8},step=2)
        self.assertEqual(result['status'],'needs_review');self.assertEqual(result['diagnostic']['code'],'verification_time_exhausted')
        self.assertEqual(wire.attempt,1);self.assertEqual(wire.adds,1)

    def test_receipt_fsync_time_is_part_of_total_elapsed_bound(self):
        result,wire,*_=self.run_case(['stable'],policy={'max_attempts':3,'max_seconds':1,'max_calls':8},receipt_step=2)
        self.assertEqual(result['status'],'needs_review');self.assertEqual(result['diagnostic']['code'],'verification_time_exhausted')
        self.assertEqual(wire.attempt,1);self.assertEqual(wire.adds,1)

    def test_final_state_validation_is_inside_verification_deadline(self):
        result,wire,*_=self.run_case(['stable'],policy={'max_attempts':3,'max_seconds':1,'max_calls':8},validation_step=2)
        self.assertEqual(result['status'],'needs_review');self.assertEqual(result['diagnostic']['code'],'verification_time_exhausted')
        self.assertGreaterEqual(result['verification']['elapsed_milliseconds'],2000)
        self.assertEqual(wire.adds,1)

    def test_failed_attempt_must_be_durable_before_restart(self):
        result,wire,journal,*_=self.run_case(['changing','stable'],record_failure=True)
        self.assertEqual(result['status'],'needs_review');self.assertEqual(result['diagnostic']['code'],'verification_receipt_failed')
        self.assertEqual(wire.attempt,1);self.assertEqual(wire.adds,1)
        self.assertNotIn('private receipt path',json.dumps(journal.events()))

    def test_default_gh_transport_timeout_is_bounded_by_remaining_deadline(self):
        cfg=config();cfg['verification']={'max_attempts':1,'max_seconds':2,'max_calls':2}
        cfg['limits']['rate_floor']=200
        wire=Wire();timeouts=[]
        def gh(document,variables,*,timeout=45):
            timeouts.append(timeout);return wire(document,variables)
        with patch('examples.project_sync.writer_github.gh_transport',gh):
            backend=Backend(cfg);before=backend.read()
            backend.read_for_verification(before,'NEW',lambda record:None)
        self.assertEqual(timeouts[0],45)
        self.assertGreater(timeouts[-1],0);self.assertLessEqual(timeouts[-1],2)

    def test_spent_needs_review_cannot_be_promoted_by_apply(self):
        result,wire,journal,backend,proposal,approval=self.run_case(['changing','stable'],default=True)
        self.assertEqual(result['status'],'needs_review')
        backend.config['verification']={'max_attempts':3,'max_seconds':30,'max_calls':8}
        repeated=apply(proposal,backend,journal,enabled=True,execute=True,approval=approval,now=NOW+1,clock=lambda:NOW+1)
        self.assertEqual(repeated['status'],'recovery_required');self.assertEqual(wire.attempt,1);self.assertEqual(wire.adds,1)

    def test_retry_policy_validation_rejects_unsafe_limits(self):
        for policy in ({'max_attempts':6,'max_seconds':30,'max_calls':8},{'max_attempts':2,'max_seconds':0,'max_calls':8},
                       {'max_attempts':True,'max_seconds':30,'max_calls':8},{'max_attempts':2,'max_seconds':30,'max_calls':31}):
            cfg=config();cfg['verification']=policy
            with self.assertRaises(Exception):validate_config(cfg)
