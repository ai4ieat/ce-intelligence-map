# CE Intelligence Map

เว็บแผนที่สำหรับทีม Circular Economy สำรวจทะเบียนโรงงาน กนอ. 8,604 รายการ พร้อม Tag CE และข้อความหลักฐาน

เว็บสาธารณะ: https://ai4ieat.github.io/ce-intelligence-map/ — repository บน GitHub เป็น Public

## เปิดใช้งาน

ใช้ Node.js 22 ขึ้นไป ไม่ต้องติดตั้ง dependencies:

```sh
npm start
```

เปิด http://127.0.0.1:8020/ หากพอร์ตถูกใช้ เซิร์ฟเวอร์จะเลือกพอร์ตถัดไปและแสดง URL ตั้งตัวแปร `PORT` เพื่อระบุพอร์ตเองได้

## ความสามารถ

- ค้นชื่อบริษัท เลขทะเบียน นิคม และรายละเอียดกิจการ
- เลือกประเภทโรงงาน 101, 105, 106 พร้อมกันแบบ OR
- กรองวัสดุ กิจกรรม CE พื้นที่ และสถานะ Tag ร่วมกันแบบ AND
- แผงตัวกรองกระชับ เห็นสามกลุ่มหลักพร้อมกัน
- เปิดรายละเอียดโรงงาน ข้อความหลักฐาน และรายละเอียดนิคม
- ธีม Formal และธีม Forge โทนเขียวเข้ม–ทอง–แดงหม่น

จุดบนแผนที่เป็นนิคม/สำนักงาน/ท่าเรือ **ไม่ใช่ GPS โรงงาน** จำนวนเป็นรายการทะเบียนซึ่งอาจมีบริษัทซ้ำ

## ข้อมูล

ฐานทะเบียน ณ 23 กันยายน 2569 จาก [Google Sheets ต้นทาง](https://docs.google.com/spreadsheets/d/1yBnaU3q-zey4VP3XC3ni4P8JCSmTBhj_XiKZ2NG-oRI/edit) เว็บอ่าน JSON ในโปรเจกต์ ไม่ได้ซิงก์ Sheet อัตโนมัติ

- `public/data/registry.json`: ทะเบียนและข้อมูลอ้างอิง
- `public/data/ce_tags.json`, `factory_ce_tags.json`, `ce_tag_assessments.json`: วัสดุ 7 กลุ่มและกิจกรรม CE 6 กลุ่ม พร้อมหลักฐาน
- `public/data/factory_type_flags.json`: ค่าจาก `is_101`, `is_105`, `is_106` ของแท็บ `factories` ณ 10 พฤศจิกายน 2569 จับคู่ด้วย `factory_id`
- `source/`: ข้อมูลนำเข้า กฎแก้ไข และตารางจับคู่ชื่อนิคม

ประเภทโรงงานรวมผลยืนยันรหัสติดกันทั้ง 19 แถว: 101 = **20**, 105 = **47**, 106 = **104** รายการ เลือกทั้งสามเป็น **130** รายการโดยไม่ซ้ำ ID ช่องว่างเก็บเป็น `null` และไม่ผ่านตัวกรองประเภทที่เลือก

Tag บนเว็บเป็นชุดคัดกรอง 13 กลุ่มเดิม ไม่ใช่ชีต Activity Tags ชุด 36 กลุ่มที่สร้างแยกภายหลัง และไม่ใช่การรับรองความสามารถ ใบอนุญาต หรือการรับซื้อของเสีย

หากแก้ประเภทใน Sheet ให้ส่งออก A และ Q:S ในรอบเดียวกันแล้วแทนที่ไฟล์ประเภท โดยคงโครงสร้าง `columns`, `rows`, `source_url`, `sheet`, `retrieved_on` และค่า boolean/null จริง ตัวโหลดตรวจ ID ครบและไม่ซ้ำก่อนใช้งาน

## ตรวจสอบ

```sh
npm test
npm run validate
python -X utf8 test/tag-rules_test.py
```

การตรวจไฟล์เว็บและข้อมูลไม่ต้องมี Excel หรือต้นแบบเดิม หากต้องการตรวจว่าต้นแบบไม่เปลี่ยน ใช้ `node scripts/validate.mjs --template-dir /path/to/original-template`

การสร้างข้อมูลทะเบียนและ Tag ใหม่ต้องมี Excel ต้นฉบับและ Python package `openpyxl`:

```sh
python -X utf8 scripts/build-data.py --original /path/to/original.xlsx --assessed-on 2026-11-09 --retrieved-on 2026-11-09
```

คำสั่งนี้ไม่เขียนทับไฟล์ `factory_type_flags.json`

## โครงสร้าง

`public/` เป็นเว็บ static พร้อมเสิร์ฟ มี JavaScript, CSS, ฟอนต์ และข้อมูล ส่วนแผนที่พื้นหลังเรียกบริการภายนอกและต้องใช้อินเทอร์เน็ต GitHub Actions ตรวจข้อมูลและ tests ก่อนเผยแพร่เฉพาะ `public/` ไปยัง GitHub Pages ทุกครั้งที่ push สู่ `main` ตั้งค่า Repository → Settings → Pages → Source เป็น GitHub Actions

แหล่งที่มาและสิทธิ์ของ dependency อยู่ใน [ATTRIBUTION.md](ATTRIBUTION.md) และไฟล์ license ที่แนบ
