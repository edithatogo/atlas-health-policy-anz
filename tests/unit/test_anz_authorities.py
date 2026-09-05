"""Independent directory completeness, country boundaries and catalogue safety."""
from copy import deepcopy
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from australian_health_policy_atlas import authorities as a
from australian_health_policy_atlas.crawl import CrawlPolicy
from australian_health_policy_atlas.integrity import verify_seal
from australian_health_policy_atlas.operations import load_collection, main as operations_main
from australian_health_policy_atlas.distribution import build_zipapp
from australian_health_policy_atlas.nlp import analyse_with_spacy

ROOT = Path(__file__).resolve().parents[2]
SOURCES = ROOT / 'data/sources'


def test_independent_closed_directory_denominators():
    report = a.assert_directory_coverage(a.load_authorities(), a.load_contract())
    verify_seal(report)
    expected = {'au-national-boards':15, 'nz-hpca-authorities':18, 'au-external-accreditors':10,
        'au-accreditation-committees':6, 'au-specialist-colleges':16, 'nsw-professional-councils':15,
        'au-health-complaints':8, 'au-ahssqa-agencies':8, 'nz-designated-auditors':4}
    for row in report['groups']:
        if row['group_id'] in expected:
            assert row['registered'] == row['denominator'] == expected[row['group_id']]
            assert row['status'] == 'matched_directory_snapshot'
        else:
            assert row['status'] == 'open_scope' and row['denominator'] is None
        assert row['document_corpus_complete'] is False
    assert report['gate_b_passed'] is False and report['open_world_complete'] is False
    assert report['registered_bodies'] >= 212


def test_missing_and_substituted_members_cannot_hide_behind_counts():
    rows = a.load_authorities()
    next(row for row in rows if row['body_id']=='nz-dental-council')['body_id']='nz-invented-council'
    report = a.coverage_report(rows, a.load_contract())
    item = next(row for row in report['groups'] if row['group_id']=='nz-hpca-authorities')
    assert item['missing'] == ['nz-dental-council']
    assert item['unexpected'] == ['nz-invented-council']
    assert item['registered'] == item['denominator'] == 18
    with pytest.raises(ValueError, match='membership drift'):
        a.assert_directory_coverage(rows, a.load_contract())


@pytest.mark.parametrize('field,value',[
    ('body_id','../escape'),('body_id','UPPER'),('countries',[]),('countries',['AU','AU']),
    ('countries',['GB']),('countries',['NZ']),('jurisdiction','NZ'),('jurisdiction','unknown'),
    ('role','government-means-binding'),('url','http://example.org/'),('url','https://u:p@example.org/'),
    ('url','https://example.org/#fragment'),('url','https://example.org:4433/'),('url',None),
    ('url','no-host'),('groups',[]),('groups',['x','x']),('groups',['invalid group']),
    ('topics',['UPPER']),('topics',[]),
])
def test_invalid_body_fields(field,value):
    row = deepcopy(next(x for x in a.load_authorities() if x['body_id']=='au-medical-board'))
    row[field]=value
    with pytest.raises(ValueError):
        a.validate_authorities([row])


def test_empty_and_duplicate_bodies():
    with pytest.raises(ValueError): a.validate_authorities([])
    row=a.load_authorities()[0]
    with pytest.raises(ValueError): a.validate_authorities([row,row])


@pytest.mark.parametrize('mutation', ['schema-bool','universal-claim','duplicate-group','unknown-group','bad-universe','corpus-claim','empty-closed','duplicate-member','missing-date','bad-date','bad-url'])
def test_invalid_coverage_contract(mutation):
    c=deepcopy(a.load_contract()); rows=a.load_authorities()
    if mutation=='schema-bool': c['schema_version']=True
    elif mutation=='universal-claim': c['open_world_complete']=True
    elif mutation=='duplicate-group': c['groups'].append(c['groups'][0])
    elif mutation=='unknown-group': rows[0]['groups']=['undeclared']
    elif mutation=='bad-universe': c['groups'][0]['universe']='invented'
    elif mutation=='corpus-claim': c['groups'][0]['document_corpus_complete']=True
    elif mutation=='empty-closed': c['groups'][0]['required_members']=[]
    elif mutation=='duplicate-member': c['groups'][0]['required_members'] *= 2
    elif mutation=='missing-date': c['groups'][0]['observed_on']=None
    elif mutation=='bad-date': c['groups'][0]['observed_on']='not-a-date'
    elif mutation=='bad-url': c['groups'][0]['evidence_url']='http://example.org/'
    with pytest.raises(ValueError): a.coverage_report(rows,c)


def test_expanded_collection_preserves_frozen_au_v1():
    au=load_collection('au-v1'); nz=load_collection('nz-v1'); full=load_collection('anz-v1')
    assert len(au)==28
    assert not {'NZ','ANZ'} & {p.jurisdiction for p in au}
    assert {p.jurisdiction for p in nz} <= {'NZ','ANZ'}
    assert {p.source_id for p in au} <= {p.source_id for p in full}
    assert len(full) <=256 and len(full)==len({p.source_id for p in full})
    assert any(p.source_id=='authority-nz-healthnz' for p in nz)
    assert len(load_collection('authorities-v1')) + len(au) ==len(full)
    with pytest.raises(ValueError): load_collection('unknown')
    with pytest.raises(ValueError): a.acquisition_sources('au-v1')


def test_shared_portal_deduplicates_capture_not_bodies():
    sources=a.acquisition_sources()
    councils=[s for s in sources if s['url']=='https://www.hpca.nsw.gov.au/councils']
    assert len(councils)==1 and len(councils[0]['body_ids'])==15
    assert councils[0]['bindingness']=='not_inferred'
    assert all(s['capture_status']=='configured_unqualified' for s in sources)
    assert a.load_contract()['federation']['preservation']=='edithatogo/archive-govt-nz'


def test_graph_does_not_forge_legal_edges():
    g=a.authority_graph()
    assert len([n for n in g.nodes.values() if n.kind=='authority'])==212
    assert {e.relation for e in g.edges} == {'REGISTERED_ROLE','SELECTED_FOR_COMPARISON','HAS_REGISTERED_SOURCE'}
    assert 'authority:nz-medsafe' in g.nodes and 'authority:nz-pharmac' in g.nodes
    assert g.nodes['authority:nz-pharmac'].properties['role']=='funding_authority'
    assert g.nodes['authority:nz-medsafe'].properties['role']=='sector_regulator'


def test_new_country_values_but_no_legacy_dhb_jurisdictions():
    for j in ['NZ','ANZ']:
        CrawlPolicy('test',j,'https://example.org/',('example.org',),'2026-09-05').validate()
    with pytest.raises(ValueError):
        CrawlPolicy('test','Auckland-DHB','https://example.org/',('example.org',),'2026-09-05').validate()


def test_nz_nlp_exact_offsets_and_no_fake_independence():
    text='In New Zealand, Ngā Paerewa and Te Tiriti o Waitangi matter.'
    result=analyse_with_spacy(text)
    assert result.available
    assert not result.independent_method
    assert {'New Zealand','Ngā Paerewa','Te Tiriti o Waitangi'} <= {s.text for s in result.spans}
    assert all(text[s.start_char:s.end_char]==s.text for s in result.spans)


def test_cli_and_portable_data(tmp_path,capsys):
    assert a.main([])==0
    assert json.loads(capsys.readouterr().out)['registered_bodies']==212
    assert a.main(['--sources','nz-v1'])==0
    assert json.loads(capsys.readouterr().out)
    assert a.main(['--graph'])==0
    assert json.loads(capsys.readouterr().out)['kind']=='authority-catalogue-projection'
    assert operations_main(['--collection','nz-v1','--matrix'])==0
    assert 'authority-nz-medsafe' in json.loads(capsys.readouterr().out)['source_id']
    app=tmp_path/'atlas.pyz'; build_zipapp(ROOT,app)
    result=subprocess.run([sys.executable,'-c',"import sys;sys.path.insert(0,sys.argv[1]);from australian_health_policy_atlas.authorities import load_authorities,load_contract,assert_directory_coverage;assert_directory_coverage(load_authorities(),load_contract());print(len(load_authorities()))",str(app)],cwd=tmp_path,text=True,capture_output=True,check=True)
    assert result.stdout.strip()=='212'


def test_bad_csv_and_symlink(tmp_path):
    p=tmp_path/'authorities-anz-v1.csv'
    p.write_text('wrong,columns\n')
    with pytest.raises(ValueError):a.load_authorities(tmp_path)
    p.write_text(','.join(a.FIELDS)+'\n'+','.join(['x']*7)+'\n')
    with pytest.raises(ValueError):a.load_authorities(tmp_path)
    p.unlink(); p.symlink_to(SOURCES/'authorities-anz-v1.csv')
    with pytest.raises(ValueError): a.load_authorities(tmp_path)
    with pytest.raises(ValueError): a.source_bytes('../escape',tmp_path)
