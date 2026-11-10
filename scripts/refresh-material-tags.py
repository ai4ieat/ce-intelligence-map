"""Apply reviewed material tags to the current registry without changing source data or other tags."""
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TAGS = [
    {'tag_id': 'M_EWASTE', 'tag_set': 'material', 'name': 'E-waste'},
    {'tag_id': 'M_SOLAR_PANEL', 'tag_set': 'material', 'name': 'Solar panel'},
    {'tag_id': 'M_EV_BATTERY', 'tag_set': 'material', 'name': 'EV battery'},
]
IDS = {t['tag_id'] for t in TAGS}
DATE = '2026-11-10'
METHOD = 'material-context-review-2026-11-10'

def read(name):
    return json.loads((ROOT / name).read_text(encoding='utf8'))

def write(name, value):
    target = ROOT / name
    pending = target.with_suffix('.next.json')
    pending.write_text(json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False), encoding='utf8')
    pending.replace(target)

def main():
    registry = read('public/data/registry.json')
    factories = {f['factory_id']: f for f in registry['factories']}
    overrides = read('source/ce-overrides.json')
    links = [t for t in read('public/data/factory_ce_tags.json') if t['tag_id'] not in IDS]
    reviewed = set()
    for fid, override in overrides.items():
        additions = [t for t in override.get('add', []) if t['tag_id'] in IDS]
        if not additions:
            continue
        f = factories[fid]
        text = f.get('activity_text') or ''
        assert f['source_row'] == override['source_row'], ('Changed source row', fid)
        assert hashlib.sha256(text.encode('utf8')).hexdigest() == override['activity_text_sha256'], ('Re-review changed activity_text', fid)
        for t in additions:
            assert t['evidence_text'] in text and len(t['evidence_text']) > 5, fid
            assert (fid, t['tag_id']) not in reviewed
            reviewed.add((fid, t['tag_id']))
            links.append(dict(t, factory_id=fid, source_row=f['source_row'], review_status='context_reviewed', assessed_on=DATE, method=METHOD, claim_scope='activity_text_only'))
    counts = Counter(t['factory_id'] for t in links)
    assessments = read('public/data/ce_tag_assessments.json')
    changed_ids = {fid for fid, _ in reviewed}
    for a in assessments:
        fid = a['factory_id']
        a['tag_count'] = counts[fid]
        if fid in changed_ids:
            a['assessed_on'] = DATE
            a['method'] = METHOD
            if a['assessment_status'] == 'insufficient_evidence':
                a.update(assessment_status='tagged', reason='พบหลักฐานวัสดุที่เกี่ยวข้องในข้อความกิจการ ไม่ได้ระบุว่าเป็น input หรือ output โดยเฉพาะ')
    tags = [t for t in read('public/data/ce_tags.json') if t['tag_id'] not in IDS]
    materials = [t for t in tags if t['tag_set'] == 'material']
    activities = [t for t in tags if t['tag_set'] == 'activity']
    summary = read('public/data/ce-summary.json')
    summary.update(tagged_records=sum(a['tag_count'] > 0 for a in assessments), untagged_records=sum(a['tag_count'] == 0 for a in assessments), insufficient_evidence_records=sum(a['assessment_status'] == 'insufficient_evidence' for a in assessments), tag_links=len(links), tag_counts=dict(Counter(t['tag_id'] for t in links)), material_reviewed_on=DATE)
    summary['tagged_needs_review_records'] = sum(a['tag_count'] > 0 and a['assessment_status'] == 'needs_review' for a in assessments)
    summary['untagged_needs_review_records'] = sum(a['tag_count'] == 0 and a['assessment_status'] == 'needs_review' for a in assessments)
    write('public/data/ce_tags.json', materials + TAGS + activities)
    write('public/data/factory_ce_tags.json', links)
    write('public/data/ce_tag_assessments.json', assessments)
    write('public/data/ce-summary.json', summary)
    print(json.dumps({'scanned_records': len(factories), 'material_tag_counts': {t['name']: summary['tag_counts'].get(t['tag_id'], 0) for t in TAGS}, 'tagged_records': summary['tagged_records']}, ensure_ascii=False))

if __name__ == '__main__':
    main()
