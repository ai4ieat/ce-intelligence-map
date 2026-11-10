"""Focused semantic regression tests for the contextual screening rules."""
import importlib.util,unittest
from pathlib import Path
p=Path(__file__).resolve().parents[1]/'scripts/build-data.py'
spec=importlib.util.spec_from_file_location('ce_rules',p);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
def tags(t):return {x['tag_id'] for x in module.screen(t)[0]}
class ContextTests(unittest.TestCase):
 def test_plastic_is_not_recycling(self):
  t=tags('ผลิตผลิตภัณฑ์พลาสติกและผลิตไฟฟ้าจากพลังงานแสงอาทิตย์เพื่อใช้ภายในโรงงาน')
  self.assertIn('M_PLASTIC',t);self.assertNotIn('A_RECYCLE',t);self.assertNotIn('A_ENERGY',t)
 def test_machine_for_recycling(self):
  self.assertNotIn('A_RECYCLE',tags('ผลิตและจำหน่ายเครื่องรีไซเคิลสารทำความเย็น'))
 def test_special_steel_not_scrap(self):
  self.assertNotIn('A_SORT',tags('การคัดแยก การเตรียมการขนส่ง เหล็กชนิดพิเศษ'))
 def test_glass_cup_is_not_glass_material(self):
  self.assertNotIn('M_GLASS',tags('ผลิตถ้วย แก้ว จากพลาสติก'))
 def test_polymer_is_not_substring_chemical(self):
  self.assertNotIn('M_CHEMICAL',tags('ผลิตเม็ดพลาสติกพอลิเอทิลีน'))
 def test_repair_material_and_energy_evidence(self):
  self.assertIn('A_REPAIR',tags('ซ่อมแซมเครื่องจักรและอุปกรณ์'))
  self.assertIn('A_ENERGY',tags('ผลิตไฟฟ้าจากขยะอุตสาหกรรม'))
  self.assertIn('A_SORT',tags('คัดแยกวัสดุที่ไม่ใช้แล้ว'))
 def test_general_power_is_not_recovery(self):
  self.assertNotIn('A_ENERGY',tags('ผลิตและจำหน่ายไฟฟ้าจากก๊าซธรรมชาติ'))
if __name__=='__main__':unittest.main()
