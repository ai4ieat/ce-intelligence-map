export const number=(x,d=0)=>new Intl.NumberFormat('th-TH',{maximumFractionDigits:d}).format(x);
export const escapeHTML=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export const factoryTypeCodes=['101','105','106'];
export function initialState(){return {province:'all',region:'all',district:'all',estate:'all',search:'',factoryTypes:[],materials:[],activities:[],untagged:false,review:false};}
export function prepare(registry,tags,links,assessments,typeFlags){
 const by=new Map(registry.factories.map(f=>[f.factory_id,{...f,ce:[],materials:[],activities:[]}]));
 if(typeFlags){
  const fields=['factory_id',...factoryTypeCodes.map(c=>'is_'+c)];
  if(JSON.stringify(typeFlags.columns)!==JSON.stringify(fields))throw Error('Invalid factory type columns');
  const seen=new Set();
  for(const [id,...flags] of typeFlags.rows){
   if(!by.has(id)||seen.has(id)||flags.length!==3||flags.some(v=>v!==null&&typeof v!=='boolean'))throw Error('Invalid factory type record: '+id);
   seen.add(id);factoryTypeCodes.forEach((c,i)=>{by.get(id)['is_'+c]=flags[i];});
  }
  if(seen.size!==by.size)throw Error('Incomplete factory type data');
 }
 const tm=new Map(tags.map(t=>[t.tag_id,t]));
 const em=new Map(registry.estates.map(e=>[e.estate_id,e]));
 const pm=new Map(registry.provinces.map(p=>[p.id,p]));
 const im=new Map(registry.industry_groups.map(i=>[i.industry_group_id,i.industry_group_name]));
 for(const l of links){const f=by.get(l.factory_id),t=tm.get(l.tag_id);if(!f||!t)throw Error('Invalid CE reference');f.ce.push(l);f[t.tag_set==='material'?'materials':'activities'].push(t.tag_id);}
 for(const a of assessments){if(!by.has(a.factory_id))throw Error('Invalid assessment');by.get(a.factory_id).assessment=a;}
 for(const f of by.values()){f.estate=em.get(f.estate_id);f.province=pm.get(f.province_id);f.industry=im.get(f.industry_group_id)||'ไม่ระบุ';f.searchText=[f.name,f.name_en,f.registration_number,f.activity_text,f.estate?.estate_name,f.factory_id].join(' ').toLocaleLowerCase();}
 return {...registry,tags,tagMap:tm,factories:[...by.values()],factoryMap:by};
}
export function filterFactories(data,s){return data.factories.filter(f=>{
 if(s.factoryTypes?.length&&!s.factoryTypes.some(c=>factoryTypeCodes.includes(c)&&f['is_'+c]===true))return false;
 if(s.province==='unknown'?f.province_id:s.province!=='all'&&f.province_id!==s.province)return false;
 if(s.region!=='all'&&f.province?.region!==s.region)return false;
 if(s.district!=='all'&&(f.district_id||f.district||'unknown')!==s.district)return false;
 if(s.estate!=='all'&&(s.estate.startsWith('map:')?f.estate?.map_id!==s.estate.slice(4):f.estate_id!==s.estate))return false;
 if(s.search&&!s.search.trim().toLocaleLowerCase().split(/\s+/).every(q=>f.searchText.includes(q)))return false;
 if(s.untagged&&f.ce.length)return false;
 if(s.review&&f.assessment?.assessment_status!=='needs_review')return false;
 if(s.materials.length&&!s.materials.some(t=>f.materials.includes(t)))return false;
 if(s.activities.length&&!s.activities.some(t=>f.activities.includes(t)))return false;
 return true;
});}
