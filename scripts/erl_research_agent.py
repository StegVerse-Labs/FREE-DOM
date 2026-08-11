#!/usr/bin/env python3
"""ERL trajectory-scoped discovery for FREE-DOM.

Uses FREE-DOM's existing `data/sources/sources_whitelist.csv`; writes only to `research/`.
It never mutates `data/master`, `data/pending`, `data/unverified`, or native verification labels.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,pathlib,re,urllib.request
from datetime import datetime,timezone
from html.parser import HTMLParser
from urllib.parse import urljoin
UA='StegVerse-ERL-FREEDOM/1.0'
def now():return datetime.now(timezone.utc).isoformat()
def sid(*p):return hashlib.sha256('|'.join(map(str,p)).encode()).hexdigest()[:24]
def append(path,obj,dry):
    if dry:return
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('a',encoding='utf-8') as f:f.write(json.dumps(obj,sort_keys=True)+'\n')
def jsonl(path):return [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines() if x.strip()] if path.exists() else []
def load(path):return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
def sources(path):
    if not path.exists():return []
    with path.open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))
class Links(HTMLParser):
    def __init__(self):super().__init__();self.links=[];self.href=None;self.txt=[]
    def handle_starttag(self,tag,attrs):
        if tag=='a':self.href=dict(attrs).get('href');self.txt=[]
    def handle_data(self,d):
        if self.href is not None:self.txt.append(d)
    def handle_endtag(self,tag):
        if tag=='a' and self.href is not None:self.links.append((' '.join(self.txt).strip(),self.href));self.href=None;self.txt=[]
def active(base):
    out=jsonl(base/'research/acquisition_requests.jsonl');f=load(base/'research/frontier.json')
    for t in f.get('trajectories',[]):
        if t.get('state') in {'OPEN','ACTIVE'}:
            for q in t.get('acquisition_queries',[]):out.append({'request_id':'frontier-'+sid(t.get('trajectory_id'),q),'trajectory_ids':[t.get('trajectory_id')],'query':q,'state':'ACTIVE'})
    return [r for r in out if r.get('state','ACTIVE') in {'OPEN','ACTIVE','RETRY'}]
def main():
    p=argparse.ArgumentParser();p.add_argument('--base',default='.');p.add_argument('--dry-run',action='store_true');a=p.parse_args();b=pathlib.Path(a.base).resolve();R=active(b);S=sources(b/'data/sources/sources_whitelist.csv');count=0
    for req in R:
        terms=[x.lower() for x in re.findall(r'[A-Za-z0-9][A-Za-z0-9._-]{2,}',req.get('query',''))][:12]
        for src in S:
            u=(src.get('url') or '').strip()
            if not u:continue
            try:
                r=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':UA}),timeout=15);data=r.read(2_000_000);digest=hashlib.sha256(data).hexdigest();parser=Links();parser.feed(data.decode('utf-8',errors='ignore'));hits=[]
                for title,href in parser.links:
                    hay=(title+' '+href).lower()
                    if terms and not all(t in hay for t in terms):continue
                    hits.append((title,urljoin(u,href)))
                for title,link in hits[:10]:
                    append(b/'research/source_candidates.jsonl',{'candidate_id':'SRC-'+sid(req.get('request_id'),link),'repository':'StegVerse-Labs/FREE-DOM','trajectory_ids':req.get('trajectory_ids',[]),'acquisition_request_id':req.get('request_id'),'query':req.get('query',''),'source_url':link,'source_title':title,'retrieved_at':now(),'source_class':src.get('authority_class') or src.get('type') or 'unknown','verification_state':'unverified','evidence_role':'lead-only','native_records_mutated':False,'privacy_policy_preserved':True,'discovered_by':'scripts/erl_research_agent.py'},a.dry_run);count+=1
                append(b/'research/research_receipts.jsonl',{'receipt_id':'RSRCH-'+sid(req.get('request_id'),u,digest),'request_id':req.get('request_id'),'trajectory_ids':req.get('trajectory_ids',[]),'source_scanned':u,'retrieved_at':now(),'response_hash':digest,'hits':len(hits),'result':'NO_UPDATE' if not hits else 'CANDIDATES_EMITTED','native_records_mutated':False},a.dry_run)
            except Exception as e:append(b/'research/research_receipts.jsonl',{'receipt_id':'RSRCH-'+sid(req.get('request_id'),u,now()),'request_id':req.get('request_id'),'trajectory_ids':req.get('trajectory_ids',[]),'source_scanned':u,'retrieved_at':now(),'result':'FAILED','error':type(e).__name__,'native_records_mutated':False},a.dry_run)
    print(json.dumps({'requests':len(R),'sources':len(S),'candidates':count,'dry_run':a.dry_run,'native_records_mutated':False},sort_keys=True))
if __name__=='__main__':main()
