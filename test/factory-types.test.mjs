import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {prepare,initialState,filterFactories,factoryTypeCodes} from '../public/ce-model.js';
const read=n=>JSON.parse(fs.readFileSync(new URL('../public/data/'+n+'.json',import.meta.url),'utf8'));
const source=read('factory_type_flags');
const inputs=['registry','ce_tags','factory_ce_tags','ce_tag_assessments'].map(read);
const data=prepare(...inputs,source);
const ids=rows=>new Set(rows.map(f=>f.factory_id));

test('all flag values join by factory ID, including after source reorder',()=>{
 const reordered=prepare(...inputs,{...source,rows:[...source.rows].reverse()});
 for(const [id,...flags] of source.rows)factoryTypeCodes.forEach((c,i)=>assert.equal(reordered.factoryMap.get(id)['is_'+c],flags[i]));
 assert.deepEqual(factoryTypeCodes.map(c=>filterFactories(data,{...initialState(),factoryTypes:[c]}).length),[20,47,104]);
 assert.equal(source.rows.filter(r=>r.slice(1).every(v=>v===null)).length,2758);
});
test('multiple types form a union without duplicate factories; clearing restores all',()=>{
 for(let mask=1;mask<8;mask++){
  const selected=factoryTypeCodes.filter((_,i)=>mask&(1<<i));
  const expected=new Set(source.rows.filter(r=>selected.some(c=>r[source.columns.indexOf('is_'+c)]===true)).map(r=>r[0]));
  const actual=filterFactories(data,{...initialState(),factoryTypes:selected});
  assert.deepEqual(ids(actual),expected);
  assert.equal(actual.length,expected.size);
 }
 assert.equal(filterFactories(data,{...initialState(),factoryTypes:factoryTypeCodes}).length,130);
 assert.equal(filterFactories(data,initialState()).length,8604);
});
test('confirmed concatenated codes use Sheet flags',()=>{
 const expected={FAC_REG_AF450E24020D:[false,true,true],FAC_REG_4B9C0BE36E44:[false,false,true],FAC_REG_801FFDE7717E:[true,false,false],FAC_REG_A36C6E6756F8:[true,true,true]};
 for(const [id,flags] of Object.entries(expected))assert.deepEqual(factoryTypeCodes.map(c=>data.factoryMap.get(id)['is_'+c]),flags);
});
test('types intersect with area, tags, search, and no-tag filters',()=>{
 const base=filterFactories(data,{...initialState(),factoryTypes:['105','106']});
 const target=base.find(f=>f.province_id&&f.materials.length&&f.estate_id&&f.registration_number);
 assert.ok(target);
 const state={...initialState(),factoryTypes:['105','106'],province:target.province_id,estate:target.estate_id,materials:[target.materials[0]],search:target.registration_number};
 assert.deepEqual(ids(filterFactories(data,state)),ids(base.filter(f=>f.province_id===target.province_id&&f.estate_id===target.estate_id&&f.materials.includes(target.materials[0])&&f.searchText.includes(target.registration_number.toLowerCase()))));
 const noTags=filterFactories(data,{...initialState(),factoryTypes:['106'],untagged:true});
 assert.deepEqual(ids(noTags),ids(base.filter(f=>f.is_106===true&&!f.ce.length)));
 assert.equal(filterFactories(data,{...state,search:'unmatched factory xyz 000'}).length,0);
});
test('incomplete, duplicated, or string-valued flag data fails instead of silently misclassifying',()=>{
 assert.throws(()=>prepare(...inputs,{...source,rows:source.rows.slice(1)}),/Incomplete/);
 assert.throws(()=>prepare(...inputs,{...source,rows:[...source.rows,source.rows[0]]}),/Invalid/);
 const rows=source.rows.map(r=>[...r]);rows[0][1]='FALSE';
 assert.throws(()=>prepare(...inputs,{...source,rows}),/Invalid/);
});
