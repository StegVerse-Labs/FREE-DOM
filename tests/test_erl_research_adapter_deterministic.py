#!/usr/bin/env python3
from __future__ import annotations
import importlib.util,hashlib,json,pathlib,sys,tempfile
from unittest import mock
ROOT=pathlib.Path(__file__).resolve().parents[1]; ADAPTER=ROOT/'scripts'/'erl_research_agent.py'; REPOSITORY='StegVerse-Labs/FREE-DOM'
class FakeResponse:
    def __init__(self,body:bytes): self._body=body; self.headers={'Content-Type':'text/html'}
    def read(self,_limit=-1): return self._body
def load_adapter():
    spec=importlib.util.spec_from_file_location('erl_research_agent',ADAPTER); module=importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(module); return module
def read_jsonl(path): return [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines() if x.strip()]
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    adapter=load_adapter()
    with tempfile.TemporaryDirectory() as td:
        b=pathlib.Path(td); (b/'research').mkdir(parents=True); (b/'data/sources').mkdir(parents=True); (b/'data/master').mkdir(parents=True); (b/'data/unverified').mkdir(parents=True)
        sentinel_master=b/'data/master/sentinel.json'; sentinel_unverified=b/'data/unverified/sentinel.json'; sentinel_master.write_text('{"master":"unchanged"}'); sentinel_unverified.write_text('{"unverified":"unchanged"}')
        before_master=sha(sentinel_master); before_unverified=sha(sentinel_unverified)
        (b/'research/frontier.json').write_text(json.dumps({'trajectories':[{'trajectory_id':'T1','state':'ACTIVE','acquisition_queries':['alpha beta']},{'trajectory_id':'T2','state':'SATURATED','acquisition_queries':['alpha beta']}]}))
        for p in ['acquisition_requests.jsonl','source_candidates.jsonl','research_receipts.jsonl']:(b/'research'/p).write_text('')
        (b/'data/sources/sources_whitelist.csv').write_text('name,url,authority_class\npositive,https://fixture.local/positive,official\nnull,https://fixture.local/null,official\n')
        positive=b'<a href="/alpha-beta-support">alpha beta supporting record</a><a href="/alpha-beta-support">alpha beta supporting record</a><a href="/alpha-beta-contrary">alpha beta contrary record</a>'
        null=b'<a href="/unrelated">unrelated record</a>'
        def fake(request,timeout=15): return FakeResponse(null if getattr(request,'full_url',str(request)).endswith('/null') else positive)
        with mock.patch.object(adapter.urllib.request,'urlopen',side_effect=fake), mock.patch.object(sys,'argv',[str(ADAPTER),'--base',str(b)]): adapter.main()
        c=read_jsonl(b/'research/source_candidates.jsonl'); r=read_jsonl(b/'research/research_receipts.jsonl')
        assert len(c)==2 and len(r)==2; assert {x['source_title'] for x in c}=={'alpha beta supporting record','alpha beta contrary record'}
        assert all(x['repository']==REPOSITORY and x['native_records_mutated'] is False and x['evaluation_changed'] is False and x['privacy_policy_preserved'] is True for x in c)
        assert all(x['transport']['credential_authority']=='TV/TVC' and x['transport']['github_token_authority']=='NONE' and x['transport']['authority_effect']=='NONE' for x in c)
        assert any(x['result']=='NO_UPDATE' and x['hits']==0 for x in r); assert any(x['result']=='CANDIDATES_EMITTED' and x['hits']==2 for x in r)
        assert sha(sentinel_master)==before_master and sha(sentinel_unverified)==before_unverified, 'ERL sidecar must not mutate native FREE-DOM records'
        assert all(x.get('privacy_policy_preserved') is True for x in r)
        print(json.dumps({'status':'PASS','repository':REPOSITORY,'active_trajectory_requests':1,'saturated_trajectory_requests':0,'candidates':2,'receipts':2,'supporting_and_contrary_leads_preserved':True,'null_result_preserved':True,'duplicate_links_collapsed':True,'native_state_unchanged':True,'privacy_policy_preserved':True,'github_token_authority':'NONE','credential_authority':'TV/TVC','authority_effect':'NONE'},sort_keys=True))
    return 0
if __name__=='__main__': raise SystemExit(main())
