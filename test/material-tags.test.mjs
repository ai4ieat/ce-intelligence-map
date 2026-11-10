import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import crypto from 'node:crypto';
import {prepare, initialState, filterFactories} from '../public/ce-model.js';

const read=name=>JSON.parse(fs.readFileSync(new URL('../'+name,import.meta.url),'utf8'));
const registry=read('public/data/registry.json');
const links=read('public/data/factory_ce_tags.json');
const tags=read('public/data/ce_tags.json');
const data=prepare(registry,tags,links,read('public/data/ce_tag_assessments.json'));
const has=(id,tag)=>data.factoryMap.get(id).materials.includes(tag);

test('new material evidence stays tied to the reviewed activity text',()=>{
  const overrides=read('source/ce-overrides.json');
  for(const link of links.filter(l=>['M_EWASTE','M_SOLAR_PANEL','M_EV_BATTERY'].includes(l.tag_id))){
    const f=data.factoryMap.get(link.factory_id),review=overrides[f.factory_id];
    assert.equal(crypto.createHash('sha256').update(f.activity_text).digest('hex'),review.activity_text_sha256);
    assert.ok(f.activity_text.includes(link.evidence_text));
    assert.equal(link.review_status,'context_reviewed');
    assert.equal(link.claim_scope,'activity_text_only');
  }
});

test('e-waste excludes new-only electronics and used trays',()=>{
  assert.ok(has('FAC_REG_B5406B73A14D','M_EWASTE'));
  for(const id of ['FAC_REG_3410ED533E3B','FAC_REG_42D77CA104C1','FAC_REG_808E595BBC9A']) assert.ok(!has(id,'M_EWASTE'));
});

test('solar materials include products but exclude power-only and panel frames',()=>{
  assert.ok(has('FAC_REG_DE7C8DD56675','M_SOLAR_PANEL'));
  assert.ok(!data.factoryMap.get('FAC_REG_DE7C8DD56675').activities.includes('A_RECYCLE'));
  for(const id of ['FAC_REG_118EBBE24FD7','FAC_REG_EE42C2CD59B3']) assert.ok(!has(id,'M_SOLAR_PANEL'));
});

test('EV batteries require battery-specific vehicle evidence, including used hybrids',()=>{
  for(const id of ['FAC_REG_AEB3406B34C6','FAC_REG_13FFE0A5B6E6']) assert.ok(has(id,'M_EV_BATTERY'));
  for(const id of ['FAC_REG_27765EDEF56C','FAC_REG_480996DA5537','FAC_REG_800297E11813','FAC_REG_8A46EAEF6373','FAC_REG_76EA856497E6']) assert.ok(!has(id,'M_EV_BATTERY'));
});

test('material filters combine as OR and do not duplicate factories with multiple tags',()=>{
  const ids=['M_EWASTE','M_SOLAR_PANEL','M_EV_BATTERY'];
  const each=ids.map(id=>filterFactories(data,{...initialState(),materials:[id]}));
  assert.ok(each.every(rows=>rows.length>0));
  const combined=filterFactories(data,{...initialState(),materials:ids});
  assert.equal(combined.length,new Set(each.flat().map(f=>f.factory_id)).size);
  assert.ok(has('FAC_IEAT_20260923_R00212','M_EWASTE'));
  assert.ok(has('FAC_IEAT_20260923_R00212','M_SOLAR_PANEL'));
});
