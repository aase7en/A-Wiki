# /A-Med-Order — ใบสั่งซื้อยา end-to-end

Maps to: `skills/awiki/a-med-order/SKILL.md`

## When to use
- รายการยาหมด / ต้องสั่งยา
- รับลิสต์ยาหมดที่พิมพ์มั่ว (ไทยปนอังกฤษ / คาราโอเกะ / สะกดผิด / หน่วยเพี้ยน) → normalize + verify → ออก Excel

Auto-picks on: `รายการยาหมด`, `รายการสั่งยา`, `สั่งยา`, `ใบสั่งยา`, `ยาหมด`, ลิสต์ชื่อยาหลายบรรทัด

## Flow
1. รับลิสต์ยา → normalize + verify ชื่อยาจากสต๊อกจริงและเว็บ
2. ตรวจคำผิด → ชื่อการค้า + ตัวยา + ความแรง + ขนาดบรรจุ
3. ไฟล์ Excel / Google Sheet ตาม template (12 หมวด, ช่องกรอกจำนวน, ทุน/หน่วย)
4. ผู้ใช้กรอกจำนวน → สรุปเป็นข้อความ copy วาง LINE ครั้งเดียวจบ

เต็ม ๆ: `skills/awiki/a-med-order/SKILL.md` · ตาราง routing: `wiki/A-ROUTER.md`
