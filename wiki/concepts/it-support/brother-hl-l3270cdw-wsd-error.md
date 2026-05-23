---
type: concept
category: it-support
tags: [printer, brother, windows, wsd-port, troubleshooting]
created: 2026-05-01
updated: 2026-05-01
---

# Brother HL-L3270CDW — ปริ้นไม่ได้ Error (WSD Port เสีย)

**อุปกรณ์**: Brother HL-L3270CDW  
**การเชื่อมต่อ**: WiFi Direct (Brother Direct)  
**ระบบปฏิบัติการ**: Windows 11  

---

## อาการ

- กดปริ้นแล้ว print job ค้างสถานะ **Error / Printing** ทันที
- ปริ้นไม่ออก แม้ว่าก่อนหน้านี้ใช้งานได้ปกติ
- เมื่อเช็คผ่าน PowerShell พบ `PrinterStatus: Error` และ `JobCount: 1`
- ลบ job แล้ว job ใหม่ก็ Error อีกทันทีที่ส่งงาน

---

## สาเหตุ

**WSD Port เสีย (Stale WSD Port)**

เมื่อติดตั้ง printer ครั้งแรก Windows จะค้นหา printer ผ่าน WSD (Web Services for Devices) และบันทึก endpoint ไว้ใน port เช่น `WSD-ff5d12bd-5535-4ae8-8a58-13a6b88a0984`

WSD record นั้นหมดอายุหรือชี้ไปที่ endpoint ผิด แต่ Windows ยังพยายามส่งงานไปยัง endpoint เดิม → job Error ทุกครั้งที่ส่ง

**ทำไมถึงเกิดกับ WiFi Direct**  
Brother HL-L3270CDW ใช้ WiFi Direct ซึ่ง printer สร้าง WiFi เอง IP ของ printer อาจเปลี่ยนเมื่อ:
- Printer ถูกรีสตาร์ท
- มีการ reset network settings บน printer
- Windows Update เปลี่ยนวิธี WSD discovery

---

## วิธีแก้ไข (ทำได้เร็ว ~3 นาที)

### ขั้นตอน

1. **เปิด Settings** → Bluetooth & devices → Printers & scanners
2. คลิก **Brother HL-L3270CDW** → กด **Remove**
3. กลับหน้า Printers & scanners → กด **Add device**
4. รอ Windows ค้นหา → ถ้าหาไม่เจออัตโนมัติ คลิก **"The printer that I want isn't listed"**
5. เลือก **"Add a printer using a TCP/IP address or hostname"**
6. ใส่ IP: **`192.168.118.1`** (IP ของ printer บน WiFi Direct subnet)
7. กด Next → Windows ดึง driver อัตโนมัติ → Finish

### ตรวจสอบหลังแก้

```powershell
Get-Printer -Name "Brother HL-L3270CDW*" | Select Name, PrinterStatus, PortName
```

ผลที่ถูกต้อง: `PrinterStatus: Normal`

---

## วินิจฉัยเบื้องต้น (ก่อนแก้)

```powershell
# เช็คสถานะและ job ค้าง
Get-Printer | Where-Object {$_.Name -like "*Brother*"} | Select Name, PrinterStatus, PortName, JobCount
Get-PrintJob -PrinterName "Brother HL-L3270CDW" | Select Id, JobStatus, DocumentName

# ลบ job ค้างชั่วคราว (แก้ได้แค่ session นั้น ถ้า port เสียจริงจะ error อีก)
Remove-PrintJob -PrinterName "Brother HL-L3270CDW" -ID <ID>

# ทดสอบว่า printer ตอบสนองได้ไหม
Test-Connection -ComputerName 192.168.118.1 -Count 2
Test-NetConnection -ComputerName 192.168.118.1 -Port 9100
```

---

## หมายเหตุเพิ่มเติม

- **IP WiFi Direct ของ printer**: `192.168.118.1` (gateway ของ subnet 192.168.118.x)
- **Driver ที่ Windows ติดตั้งอัตโนมัติ**: Microsoft IPP Class Driver — ใช้ได้ปกติแม้ไม่ใช่ Brother driver จริงๆ
- **Port ที่ printer ตอบ**: 80 (HTTP), 443 (HTTPS), 631 (IPP), 9100 (RAW printing)
- การสร้าง TCP/IP port ด้วย PowerShell (`Add-PrinterPort`) และ `prnport.vbs` **ไม่สำเร็จ** บนระบบนี้ — ให้ใช้ Add Printer Wizard แทนเสมอ

---

## ความสัมพันธ์

- IT troubleshooting ในที่ทำงาน — ดู index รวม `index-it.md`
