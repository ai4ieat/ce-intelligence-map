import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
const root=fileURLToPath(new URL('../',import.meta.url));
const read=n=>JSON.parse(fs.readFileSync(path.join(root,n),'utf8'));
const registry=read('public/data/registry.json'),tags=read('public/data/ce_tags.json'),links=read('public/data/factory_ce_tags.json'),assessments=read('public/data/ce_tag_assessments.json'),summary=read('public/data/ce-summary.json');
const fm=new Map(registry.factories.map(f=>[f.factory_id,f])),tm=new Map(tags.map(t=>[t.tag_id,t]));
assert.equal(fm.size,8604);assert.equal(assessments.length,8604);assert.equal(new Set(assessments.map(a=>a.factory_id)).size,8604);assert.equal(tm.size,13);
const seen=new Set();for(const l of links){assert.ok(fm.has(l.factory_id)&&tm.has(l.tag_id));assert.ok(fm.get(l.factory_id).activity_text.includes(l.evidence_text));assert.ok(l.evidence_text.length>5&&l.reason&&l.review_status&&l.assessed_on);assert.equal(l.source_row,fm.get(l.factory_id).source_row);const k=l.factory_id+'|'+l.tag_id;assert.ok(!seen.has(k));seen.add(k);}
for(const a of assessments){assert.ok(fm.has(a.factory_id));assert.equal(a.tag_count,links.filter(l=>l.factory_id===a.factory_id).length);}
assert.equal(summary.tagged_records,new Set(links.map(l=>l.factory_id)).size);assert.equal(summary.tagged_records+summary.untagged_records,8604);assert.equal(summary.needs_review_records,assessments.filter(a=>a.assessment_status==='needs_review').length);
for(const t of tags)assert.equal(summary.tag_counts[t.tag_id]||0,links.filter(l=>l.tag_id===t.tag_id).length);
const source=read('source/factories.json');assert.deepEqual(new Set(source.slice(1).map(r=>r[0])),new Set(fm.keys()));
const templateArg=process.argv.indexOf('--template-dir');
let templateFilesChecked=0;
if(templateArg!==-1){
 const template=process.argv[templateArg+1];assert.ok(template,'--template-dir requires a path');
 const hashes=read('source/template-hashes.json');
 for(const [name,hash] of Object.entries(hashes)){const file=path.join(template,name);assert.equal(crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex'),hash,'Template changed: '+name);templateFilesChecked++;}
}
for(const name of ['ce-app.js','ce-map.js','ce-model.js','index.html']){const text=fs.readFileSync(path.join(root,'public',name),'utf8');assert.ok(!/nong-prom|bio-model|research\.html|Worker|D1/.test(text),name);}
console.log(JSON.stringify({valid:true,records:fm.size,tags:tm.size,links:links.length,assessed:assessments.length,template_files_checked:templateFilesChecked}));
