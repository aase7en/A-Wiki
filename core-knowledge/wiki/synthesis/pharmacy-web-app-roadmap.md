---
type: synthesis
tags: [pharmacy, web-app, roadmap, development]
sources: [pharmacy-context, pharmacy-ui-instructions]
created: 2026-04-30
updated: 2026-04-30
---

# Pharmacy Web App Roadmap

## คำถามที่ตอบ

**วิธีพัฒนา web app สำหรับร้านยา ให้ลูกค้าสั่งยาผ่าน LINE/form ได้ง่ายขึ้น?**

## สรุป

สร้าง **FastAPI + React web app** บน **Raspberry Pi 5** พร้อมการใช้ **Claude API** สำหรับ:
- OCR ของรูปภาพยา (ลูกค้าส่งรูป)
- Drug name validation + fuzzy matching
- Interactive order form

## Phase 1: Prototype (2-4 สัปดาห์)

### 1.1 Backend (FastAPI)
```python
# Endpoints
GET /api/drugs/search?q=amox
POST /api/drugs/validate
POST /api/orders/create
GET /api/orders/export?format=csv|json
```

**Dependencies**:
- fastapi, uvicorn
- json file loader (sp_drugs_full_3760.json)
- fuzzywuzzy สำหรับ fuzzy match
- pydantic สำหรับ validation

### 1.2 Frontend (React)
- Input field ตรวจสอบชื่อยา (live search)
- Interactive form เลือก quantity
- Export buttons (CSV, Copy LINE, JSON)
- Badge indicators (✅ ⚠️ ❌)

### 1.3 Drug Aliases Database
- Load `drug-aliases.md` เป็น JSON
- Mapping: alias → standard name
- Example:
  ```json
  {
    "อมอก": "Amoxicillin",
    "amox": "Amoxicillin",
    "การา": "Paracetamol",
    ...
  }
  ```

### 1.4 Data Source
- Load `sp_drugs_full_3760.json`
- Parse structure: code, category, name, strength, unit, supplier

---

## Phase 2: Claude API Integration (2-3 สัปดาห์)

### 2.1 Image OCR
```python
# client.py with vision capability
image_path = "drug_list.jpg"
response = claude.messages.create(
    model="claude-opus-4-7",
    max_tokens=1024,
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": base64_image,
                    },
                },
                {
                    "type": "text",
                    "text": "Extract drug names from this image. Return JSON array."
                }
            ],
        }
    ],
)
```

### 2.2 Drug Name Validation
- ส่งชื่อยา (หรือ OCR output) ไปยัง Claude
- Claude ทำ fuzzy match + alias lookup
- Return: { matched_name, category, confidence }

### 2.3 Endpoint
```python
POST /api/ocr
{
  "image_base64": "..."
}
→ response:
{
  "drugs": [
    {"name": "OMEPRAZOLE GPO 20mg", "confidence": 0.95},
    ...
  ]
}
```

---

## Phase 3: Database & Inventory (3-4 สัปดาห์)

### 3.1 SQL Database (SQLite → MySQL)
```sql
CREATE TABLE drugs (
  id INT PRIMARY KEY,
  code VARCHAR(100) UNIQUE,
  category_code VARCHAR(10),
  category_name VARCHAR(100),
  name VARCHAR(200),
  strength VARCHAR(50),
  unit VARCHAR(20),
  supplier VARCHAR(100),
  stock INT DEFAULT 0,
  created_at TIMESTAMP
);

CREATE TABLE orders (
  id INT PRIMARY KEY AUTO_INCREMENT,
  created_at TIMESTAMP,
  customer_name VARCHAR(100),
  items JSON,
  exported_at TIMESTAMP,
  status ENUM('draft', 'exported', 'completed')
);
```

### 3.2 Integration with S.P. Drugstore API (ถ้ามี)
- Sync stock updates
- Real-time availability check
- Price updates

---

## Phase 4: Telegram/Line Bot (2-3 สัปดาห์)

### 4.1 Line Bot
```python
# Handle incoming messages
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text
    # Search drugs
    results = db.search(text)
    # Return interactive message with buttons
```

### 4.2 Interactive Buttons
- ให้ลูกค้าเลือกจากผลลัพธ์ search
- Quantity input
- Confirm order

---

## Phase 5: Production Deployment

### 5.1 Hardware
- **Host**: Raspberry Pi 5 (4GB+)
- **Storage**: 32GB+ microSD
- **Network**: Wi-Fi 6 or Ethernet
- **Power**: 5V/3A USB-C

### 5.2 Docker Setup
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 5.3 Reverse Proxy (nginx)
```nginx
server {
    listen 80;
    location / {
        proxy_pass http://localhost:8000;
    }
}
```

### 5.4 Monitoring
- Logs to file
- Alerts for errors
- Uptime monitoring

---

## Constraints & Considerations

| ประเด็น | ข้อแนะนำ |
|--------|---------|
| **Data Privacy** | Don't log sensitive customer data |
| **API Rate Limit** | Claude API $5/1M input tokens |
| **Offline Mode** | Support local fuzzy match without Claude |
| **Performance** | Cache drug list in memory |
| **Updates** | Auto-sync drug DB monthly from S.P. |

---

## Timeline Estimate

| Phase | Duration | Effort |
|-------|----------|--------|
| Phase 1 (Prototype) | 2-4 weeks | 40 hours |
| Phase 2 (Claude API) | 2-3 weeks | 30 hours |
| Phase 3 (Database) | 3-4 weeks | 50 hours |
| Phase 4 (Bot) | 2-3 weeks | 25 hours |
| Phase 5 (Deploy) | 1-2 weeks | 20 hours |
| **Total** | **3-4 months** | **165 hours** |

---

## Success Metrics

- ✅ Drug matching accuracy > 95%
- ✅ Order processing time < 2 min
- ✅ API uptime > 99%
- ✅ OCR accuracy > 90% for clear images
- ✅ User satisfaction (NPS > 7)

---

## ความเกี่ยวข้อง

- [[wiki/entities/pharmacy/pharmacy-business]] — ร้านยา
- [[concepts/pharmacy/ordering-workflow]] — ขั้นตอนสั่งซื้อ
- [[wiki/concepts/pharmacy/ui-design-pharmacy]] — ออกแบบ UI
- [[wiki/entities/pharmacy/drug-matching-system]] — ระบบจับคู่

## แหล่งข้อมูล

- [[wiki/sources/pharmacy-context]]
- [[wiki/sources/pharmacy-ui-instructions]]
