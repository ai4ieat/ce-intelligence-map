"""Read-only registry import and conservative CE screening. No network or source writes.
Usage: python -X utf8 scripts/build-data.py --original <original.xlsx>
Source inputs: source/{factories,companies,addresses,estates,industry_groups}.json
Each is a Google Sheets bounded-range values array, header first.
"""
import json,re,hashlib,argparse,datetime
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[1]
DATE='2026-11-09'
VERSION='ce-context-rules-1.0'
def read(name):return json.loads((ROOT/name).read_text('utf8'))
def table(name):
 a=read('source/'+name+'.json');return [{k:(r[i] if i<len(r) else None) for i,k in enumerate(a[0])} for r in a[1:] if r and r[0]]
def save(name,value):
 p=ROOT/name;t=p.with_suffix('.next.json');t.write_text(json.dumps(value,ensure_ascii=False,separators=(',',':'),allow_nan=False),'utf8');t.replace(p)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
TAGS=[('M_PLASTIC','material','พลาสติก'),('M_METAL','material','โลหะ'),('M_PAPER','material','กระดาษและเยื่อกระดาษ'),('M_GLASS','material','แก้ว'),('M_RUBBER','material','ยาง'),('M_CHEMICAL','material','สารเคมี'),('M_BIOMASS','material','วัสดุอินทรีย์และชีวมวล'),('A_SORT','activity','การคัดแยกวัสดุ'),('A_RECYCLE','activity','การรีไซเคิลวัสดุ'),('A_REPAIR','activity','การซ่อมแซมและปรับสภาพ'),('A_REUSE','activity','การนำวัสดุกลับมาใช้ในการผลิต'),('A_RECOVER','activity','การกู้คืนสาร'),('A_ENERGY','activity','การกู้คืนพลังงาน')]
MATERIALS={
 'M_PLASTIC':r'พลาสติก|พอลิเมอร์|โพลิเมอร์|โพลีเอทิลีน|พอลิเอทิลีน|โพลีโพรพิลีน|พอลิโพรพิลีน|โพลีสไตรีน|โพลีคาร์บอเนต|polyethylene|polypropylene|polycarbonate|polyvinyl|plastic',
 'M_METAL':r'โลหะ|เหล็ก|อลูมิเนียม|อะลูมิเนียม|อลูมินัม|ทองแดง|ทองเหลือง|สแตนเลส|สเตนเลส|สังกะสี|ทังสเตน|steel|alumin(?:ium|um)|copper|brass|metal',
 'M_PAPER':r'กระดาษ|เยื่อกระดาษ|paper|pulp',
 'M_GLASS':r'กระจก|ใยแก้ว|ไฟเบอร์กลาส|(?:จาก|ด้วย|เนื้อ|ขวด|หลอม|เศษ|วัสดุ)แก้ว|แก้ว(?:แผ่น|บอโร)|fiberglass|\bglass\b',
 'M_RUBBER':r'ยางพารา|ยางสังเคราะห์|ยางธรรมชาติ|ยางรถ|ยางล้อ|น้ำยาง|ผลิตภัณฑ์ยาง|ชิ้นส่วนยาง|แผ่นยาง|ยางและ|ยางหรือ|ยางทุก|ขึ้นรูปยาง|แผ่นรองพื้นยาง|rubber|latex',
 'M_CHEMICAL':r'สารเคมี|เคมีภัณฑ์|ปิโตรเคมี|ตัวทำละลาย|กรดซัลฟิวริก|กรดกำมะถัน|โซดาไฟ|เมทานอล|เอทานอล|เอทธานอล|(?<!โพลี)(?<!พอลิ)(?<!พิลิ)เอทิลีน|(?<!โพลี)(?<!พอลิ)โพรพิลีน|เบนซีน|โทลูอีน|เรซิน|น้ำยาเคมี|chemical|solvent|benzene|toluene|methanol|\bethylene\b|\bpropylene\b|resin',
 'M_BIOMASS':r'ชีวมวล|ชานอ้อย|กากอ้อย|กากน้ำตาล|แกลบ|ขี้เลื่อย|เศษไม้|ไม้ยาง|ไม้แปรรูป|เยื่อไม้|แป้งมันสำปะหลัง|มันสำปะหลัง|น้ำมันปาล์ม|น้ำมันพืช|อาหารสัตว์|อาหารทะเล|เนื้อสัตว์|ผักและผลไม้|ปุ๋ยอินทรีย์|biomass|bagasse|wood pellet'
}
VERB=re.compile(r'ผลิต|ประกอบ|แปรรูป|ขึ้นรูป|ฉีด|เป่า|หลอม|รีด|ตัด|กลึง|เคลือบ|ชุบ|จำหน่าย|นำเข้า|นําเข้า|ส่งออก|ซื้อ|ขาย|เก็บ|บรรจุ|พิมพ์|รับจ้าง|คัดแยก|รีไซ|ซ่อม|ใช้|ทำ|ทํา|เกี่ยวกับ|manufactur|produc|recycl',re.I)
CE_SIGNAL=re.compile(r'รีไซ|recycl|คัดแยก|ซ่อม|ปรับสภาพ|กู้คืน|recovery|นำกลับ|นํากลับ|กลับมาใช้|ใช้แล้ว|ของเสีย|(?<!พิ)เศษ|ขยะ|เชื้อเพลิงทดแทน|RDF',re.I)
WASTE=r'(?:(?<!พิ)เศษ|ของเสีย|ขยะ|ใช้แล้ว|ไม่ใช้แล้ว|ที่ใช้แล้ว|เก่า|ทิ้ง|กากอุตสาหกรรม)'
def evidence(t,m):
 # Keep a verb-bearing context rather than the matched word alone. Exact source substring.
 a=max(0,m.start()-150);b=min(len(t),m.end()+160)
 return t[a:b]
def screen(t):
 t=t or '';links=[];reasons=[]
 def add(tag,match,why):
  if tag not in {x['tag_id'] for x in links}:links.append(dict(tag_id=tag,evidence_text=evidence(t,match),reason=why,review_status='rule_supported',assessed_on=DATE,method=VERSION,claim_scope='activity_text_only'))
 for tag,pattern in MATERIALS.items():
  for m in re.finditer(pattern,t,re.I):
   context=evidence(t,m)
   if VERB.search(context) and not re.search(r'ไม่(?:รวม|ใช้|เกี่ยวข้องกับ)\s*'+re.escape(m.group()),t[max(0,m.start()-18):m.end()]):
    add(tag,m,'กิจการระบุวัสดุนี้ในบริบทการผลิต การค้า การจัดเก็บ หรือการให้บริการ ไม่ยืนยันว่าเป็นวัสดุรีไซเคิล');break
 # Activity patterns require a process and the handled object in the same local context.
 rules={
 'A_SORT':(r'คัดแยก[^.;\n]{0,100}'+WASTE, 'ระบุการคัดแยกวัสดุหรือวัสดุที่ใช้แล้วโดยตรง'),
 'A_RECYCLE':(r'(?:รีไซเคิล|รีไซเคิ้ล|recycl(?:e|ing|ed))|หลอม[^.;\n]{0,35}เศษ|เศษ[^.;\n]{0,45}(?:มาหลอม|เพื่อหลอม)|(?:วัสดุ|สิ่งของ)[^.;\n]{0,15}ไม่ใช้แล้ว[^.;\n]{0,80}(?:ผลิตเป็น|ผลิตวัตถุดิบ)|บด[^.;\n]{0,35}(?:พลาสติก|ยาง)[^.;\n]{0,20}(?:ใช้แล้ว|เก่า)', 'ระบุการรีไซเคิลหรือแปรวัสดุใช้แล้วเป็นวัสดุ/ผลิตภัณฑ์'),
 'A_REPAIR':(r'ซ่อม(?:แซม|บำรุง)?[^.;\n]{0,70}(?:เครื่อง|อุปกรณ์|รถ|เรือ|แม่พิมพ์|แผง|ชิ้นส่วน|ถัง|บรรจุภัณฑ์|สินค้า|กรง|มอเตอร์|วาล์ว|ปั๊ม)|(?:ประกอบ|ผลิต)[^.;\n]{0,12}ซ่อม[^.;\n]{0,50}|ปรับสภาพ[^.;\n]{0,50}(?:เครื่องจักร|อุปกรณ์|ถัง|ยางรถ|รถยนต์)', 'ระบุบริการซ่อมหรือปรับสภาพผลิตภัณฑ์/อุปกรณ์ ไม่ยืนยันรับงานภายนอกหรือรับของเสีย'),
 'A_REUSE':(r'(?:ใช้|นำ|นํา)[^.;\n]{0,45}(?:เศษ|ของเสีย|วัสดุที่ไม่ใช้แล้ว|พลาสติกรีไซเคิล|กระดาษใช้แล้ว)[^.;\n]{0,65}(?:เป็นวัตถุดิบ|ในการผลิต|มาผลิต|ผลิตเป็น)|(?:ผลิต|ขึ้นรูป)[^.;\n]{0,55}(?:จากเศษ|จากกระดาษใช้แล้ว|จากสายไฟที่ใช้แล้ว)|นำ[^.;\n]{0,40}กลับมาใช้[^.;\n]{0,25}(?:ผลิต|วัตถุดิบ)', 'ข้อความระบุการใช้วัสดุใช้แล้ว/เศษวัสดุเป็นวัตถุดิบในการผลิต'),
 'A_RECOVER':(r'(?:กู้คืน|นำกลับคืน|แยกคืน|recover)[^.;\n]{0,50}(?:สาร|ตัวทำละลาย|solvent|กรด|โลหะ)|(?:กลั่น|แปรรูป)[^.;\n]{0,35}(?:ตัวทำละลาย|solvent)[^.;\n]{0,35}(?:ใช้แล้ว|ของเสีย)|(?:ตัวทำละลาย|solvent)[^.;\n]{0,35}(?:ใช้แล้ว|ของเสีย)[^.;\n]{0,35}(?:กลั่น|นำกลับ|กลับมาใช้)', 'ระบุการกู้คืนสารหรือกลั่นตัวทำละลายที่ใช้แล้วโดยตรง'),
 'A_ENERGY':(r'(?:ผลิต|กู้คืน)[^.;\n]{0,25}(?:ไฟฟ้า|พลังงาน|ไอน้ำ|ความร้อน)[^.;\n]{0,50}(?:จากขยะ|จากของเสีย|จากก๊าซชีวภาพ|จากเศษไม้|จากกาก|จากแกลบ|จากชานอ้อย)|(?:ใช้|นำ|นํา)[^.;\n]{0,25}(?:ขยะ|ของเสีย|เศษไม้|กาก|แกลบ|ชานอ้อย)[^.;\n]{0,45}(?:เป็นเชื้อเพลิง|ผลิตไฟฟ้า|ผลิตไอน้ำ)|(?:ผลิต|แปรรูป)[^.;\n]{0,35}(?:เชื้อเพลิงขยะ|เชื้อเพลิงทดแทน|RDF)', 'ระบุพลังงานหรือเชื้อเพลิงจากของเสีย/วัสดุเหลือใช้ ไม่รวมไฟฟ้าทั่วไปและโซลาร์')
 }
 for tag,(pattern,why) in rules.items():
  for m in re.finditer(pattern,t,re.I):
   before=t[max(0,m.start()-55):m.start()]
   if tag=='A_RECYCLE' and re.search(r'(?:เครื่อง|เครื่องจักร|อุปกรณ์|เครื่องมือ)\s*$',before):
    reasons.append('ผลิต/ค้าเครื่องรีไซเคิล ไม่ยืนยันว่าดำเนินการรีไซเคิล');continue
   if re.search(r'(?:ไม่รวม|ยกเว้น|มิใช่|ไม่ทำ|ไม่รับ|สำหรับ|เพื่อใช้ในการ|เครื่องจักรที่ใช้ในกระบวนการ|อุปกรณ์สำหรับ)[^,.;\n]{0,25}$',before):
    reasons.append('พบคำกิจกรรมในบริบทข้อยกเว้น/อุปกรณ์ ต้องตรวจขอบเขต');continue
   if tag=='A_RECYCLE' and re.search(r'รีไซ|recycl',m.group(),re.I):
    local=t[max(0,m.start()-70):min(len(t),m.end()+90)]
    if not re.search(r'ผลิต|ดำเนิน|ประกอบกิจการ|รับจ้าง|แปรรูป|หลอม|บด|รีไซเคิลและ|รีไซเคิลวัสดุ|recycling',local,re.I):
     reasons.append('กล่าวถึงรีไซเคิลแต่ยังไม่ชัดว่าเป็นผู้ดำเนินการ');continue
    if re.search(r'(?:ซื้อ|จำหน่าย|นำเข้า|ส่งออก)[^.;]{0,30}(?:เม็ดพลาสติก|วัสดุ)[^.;]{0,10}รีไซ',local) and not re.search(r'ผลิต|แปรรูป|หลอม',local):
     reasons.append('เป็นการค้าวัสดุรีไซเคิล ไม่ยืนยันการรีไซเคิลเอง');continue
   add(tag,m,why);break
 if CE_SIGNAL.search(t) and not any(x['tag_id'].startswith('A_') for x in links):reasons.append('พบข้อความเกี่ยวกับเศษวัสดุ/ของเสีย/กระบวนการ แต่หลักฐานกิจกรรม CE ยังไม่พอ')
 # Even supported activity evidence needs an explicit contextual review for broad scope/negation.
 if any(x['tag_id'].startswith('A_') for x in links) and re.search(r'ยกเว้น|ไม่รวม|ไม่รับ|เฉพาะภายใน|เฉพาะของบริษัท',t):reasons.append('มีข้อจำกัดขอบเขตในกิจการ ให้ตรวจการตีความก่อนติดต่อใช้งาน')
 return links,sorted(set(reasons))
def main():
 global DATE
 ap=argparse.ArgumentParser();ap.add_argument('--original',required=True);ap.add_argument('--assessed-on',default=DATE);ap.add_argument('--retrieved-on',default='2026-11-09');args=ap.parse_args();DATE=datetime.date.fromisoformat(args.assessed_on).isoformat();retrieved_on=datetime.date.fromisoformat(args.retrieved_on).isoformat()
 from openpyxl import load_workbook
 src=Path(args.original);w=load_workbook(src,read_only=True,data_only=True);original=list(w.worksheets[0].values);w.close()
 counts=Counter(str(r[49] or 'ไม่ระบุ') for r in original[1:]);assert len(original)-1==11136 and counts['ปกติ']==8604
 tables={n:table(n) for n in ['factories','companies','addresses','estates','industry_groups']}
 f=tables['factories'];assert len(f)==8604 and len({x['factory_id'] for x in f})==8604
 companies={x['company_id']:x for x in tables['companies']};addresses={x['address_id']:x for x in tables['addresses']};industries={x['industry_group_id']:x for x in tables['industry_groups']}
 cross={x['estate_id']:x for x in read('source/estate-crosswalk.json')};estates=[]
 for e in tables['estates']:
  prev=cross.get(e['estate_id'],{});assert not prev or prev['estate_name']==e['estate_name']
  estates.append({**e,'map_id':e.get('existing_map_estate_id') or prev.get('map_id'),'match_basis':'sheet_verified' if e.get('existing_map_estate_id') else prev.get('match_basis','unmatched')})
 polys=read('public/data/provinces.geojson')['features'];provinces=[dict(id='PROV_'+x['properties']['code'],name=x['properties']['name'],region=x['properties']['region_id']) for x in polys];pids={x['id'] for x in provinces}
 factories=[];links=[];assessments=[];mismatches=[]
 overrides=read('source/ce-overrides.json') if (ROOT/'source/ce-overrides.json').exists() else {}
 for x in f:
  fid=x['factory_id'];r=original[int(x['source_row'])-1];assert r[49]=='ปกติ' and x['operating_status']=='ปกติ'
  if (x.get('activity_text') or '')!=(r[10] or ''):mismatches.append(fid)
  c=companies[x['company_id']];a=addresses.get(x['address_id'],{});assert not x['industry_group_id'] or x['industry_group_id'] in industries
  facts=dict(x,name=c.get('name_th') or c.get('name_en'),name_en=c.get('name_en'),province_id=a.get('province_id') if a.get('province_id') in pids else None,district_id=a.get('district_id'),district=a.get('district_name'),address=a.get('address_clean'),address_review_status=a.get('review_status'))
  factories.append(facts)
  ts,rs=screen(x.get('activity_text'))
  override=overrides.get(fid,{})
  if override:assert override['source_row']==x['source_row'],('Override source row changed',fid)
  ts=[t for t in ts if t['tag_id'] not in override.get('remove',[])]
  for t in override.get('add',[]):
   assert t['evidence_text'] in (x.get('activity_text') or '')
   ts=[q for q in ts if q['tag_id']!=t['tag_id']]
   ts.append(dict(t,review_status='context_reviewed',assessed_on=DATE,method='context-review-v1',claim_scope='activity_text_only'))
  if override.get('review_reason'):rs.append(override['review_reason'])
  if fid in mismatches:rs.append('ข้อความกิจการในชีตแตกต่างจาก Excel ต้นฉบับบางอักขระ ต้องตรวจเทียบต้นทาง')
  for t in ts:links.append(dict(factory_id=fid,source_row=x['source_row'],**t))
  assessments.append(dict(factory_id=fid,source_row=x['source_row'],assessed_on=DATE,method=VERSION,assessment_status='needs_review' if rs else 'tagged' if ts else 'insufficient_evidence',review_status='needs_review' if rs else 'screened_not_human_verified',tag_count=len(ts),review_reasons=rs,reason='; '.join(rs) if rs else ('พบหลักฐานรองรับ Tag ในข้อความกิจการ' if ts else 'ไม่พบหลักฐานที่ชัดเจนเพียงพอตามขอบเขตคำและกฎรอบนี้ ไม่ได้ยืนยันว่าไม่เกี่ยวข้อง')))
 # Preserve the authoritative live Sheet text; report every source discrepancy for review.
 assert {int(x['source_row']) for x in f}=={i for i,r in enumerate(original,1) if i>1 and r[49]=='ปกติ'}
 summary=dict(total_records=len(f),assessed_records=len(assessments),tagged_records=sum(x['tag_count']>0 for x in assessments),untagged_records=sum(x['tag_count']==0 for x in assessments),insufficient_evidence_records=sum(x['assessment_status']=='insufficient_evidence' for x in assessments),needs_review_records=sum(x['assessment_status']=='needs_review' for x in assessments),activity_tagged_records=len({x['factory_id'] for x in links if x['tag_id'].startswith('A_')}),tag_links=len(links),tag_counts=dict(Counter(x['tag_id'] for x in links)),missing_province=sum(not x['province_id'] for x in factories),estate_matches=sum(bool(x['map_id']) for x in estates),estate_total=len(estates),source_activity_exact_matches=len(f)-len(mismatches),original_status_counts=dict(counts),original_rows=len(original)-1,source_date='2026-09-23',assessed_on=DATE,method=VERSION,human_verified_all=False)
 summary['tagged_needs_review_records']=sum(x['tag_count']>0 and x['assessment_status']=='needs_review' for x in assessments)
 summary['untagged_needs_review_records']=sum(x['tag_count']==0 and x['assessment_status']=='needs_review' for x in assessments)
 provenance=dict(source_url='https://docs.google.com/spreadsheets/d/1yBnaU3q-zey4VP3XC3ni4P8JCSmTBhj_XiKZ2NG-oRI/edit',retrieved_on=retrieved_on,original_sha256=sha(src),original_filename=src.name,table_sha256={n:sha(ROOT/'source'/(n+'.json')) for n in tables},source_rows_trace='factory_id + source_row mapped to original XLSX row; K equality checked for all 8604: 8602 exact, 2 control-character encoding differences')
 save('public/data/registry.json',dict(schema_version=1,provenance=provenance,factories=factories,estates=estates,provinces=provinces,industry_groups=tables['industry_groups']))
 save('public/data/ce_tags.json',[dict(tag_id=i,tag_set=s,name=n) for i,s,n in TAGS]);save('public/data/factory_ce_tags.json',links);save('public/data/ce_tag_assessments.json',assessments);save('public/data/ce-summary.json',summary)
 save('data-import-report.json',dict(summary=summary,provenance=provenance,activity_mismatch_factory_ids=mismatches));print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
