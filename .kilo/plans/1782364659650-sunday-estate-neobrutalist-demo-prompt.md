# AI Demo Generation Prompt: Sunday Estate Webapp + Neo-Brutalist Theme

## Context
Create a full React demo application that replicates the Sunday Estate webapp structure and adds a Neo-Brutalist theme as the 4th selectable theme option.

---

## Phase 1: Setup & Project Structure

### 1.1 Initialize Project
```
Create: npx create-react-app sunday-estate-demo --template typescript
Or use: Vite + React (faster dev server)
```

### 1.2 Project Structure
```
sunday-estate-demo/
├── src/
│   ├── components/
│   │   ├── ui/
│   │   │   ├── Icon.tsx
│   │   │   ├── Tag.tsx
│   │   │   ├── Sparkline.tsx
│   │   │   └── Card.tsx
│   │   ├── shell/
│   │   │   ├── Sidebar.tsx
│   │   │   ├── Topbar.tsx
│   │   │   └── AppShell.tsx
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Loans.tsx
│   │   │   ├── Lands.tsx
│   │   │   └── AI.tsx
│   │   ├── dashboard/
│   │   │   ├── CashFlowWidget.tsx
│   │   │   ├── PortfolioWidget.tsx
│   │   │   ├── DueWidget.tsx
│   │   │   ├── AlertsWidget.tsx
│   │   │   └── MapWidget.tsx
│   │   └── data/
│   │       └── mockData.ts
│   ├── styles/
│   │   ├── base.css
│   │   ├── themes.css
│   │   └── components.css
│   ├── App.tsx
│   └── index.css
├── public/
│   └── assets/
└── package.json
```

---

## Phase 2: Design Tokens & CSS Architecture

### 2.1 Base Theme Variables (Sunday Estate Brand)
```css
/* Sunday Estate — Design Tokens & base styles */
:root {
  /* Light theme (default) — Sunday Estate brand: navy + gold on cream */
  --bg: #f8f9fa;
  --surface: #ffffff;
  --surface-2: #f1f4f9;
  --elev: #ffffff;
  --border: rgba(0, 44, 95, 0.14);
  --border-strong: rgba(0, 44, 95, 0.22);
  --text: #002c5f;
  --text-2: #0a3d7d;
  --muted: rgba(8, 24, 50, 0.68);
  --accent: #f6a800;
  --accent-soft: rgba(246, 168, 0, 0.14);
  --accent-text: #a96800;
  --brand-glow: rgba(246, 168, 0, 0.45);
  --success: #4ade80;
  --success-soft: rgba(74, 222, 128, 0.14);
  --warn: #fb923c;
  --warn-soft: rgba(251, 146, 60, 0.14);
  --danger: #f87171;
  --danger-soft: rgba(248, 113, 113, 0.14);
  --info: #60a5fa;
  --info-soft: rgba(96, 165, 250, 0.14);

  --shadow-sm: 0 1px 2px rgba(20, 18, 14, 0.04);
  --shadow-md: 0 4px 12px rgba(20, 18, 14, 0.06), 0 1px 2px rgba(20, 18, 14, 0.04);
  --shadow-lg: 0 12px 32px rgba(20, 18, 14, 0.08), 0 2px 6px rgba(20, 18, 14, 0.04);

  --d-radius: 10px;
  --d-radius-sm: 6px;
  --d-pad: 20px;
  --d-card-pad: 24px;

  --font-sans: "IBM Plex Sans Thai", "IBM Plex Sans", system-ui, sans-serif;
  --font-mono: "IBM Plex Mono", ui-monospace, monospace;
  --font-display: "IBM Plex Sans", "IBM Plex Sans Thai", system-ui, sans-serif;
}
```

### 2.2 Dark Theme
```css
[data-theme="dark"] {
  --bg: #0a0f1c;
  --surface: #131b2e;
  --surface-2: #1a253d;
  --elev: #1a253d;
  --border: rgba(255, 255, 255, 0.08);
  --border-strong: rgba(255, 255, 255, 0.14);
  --text: #e2e8f0;
  --text-2: #cbd5e1;
  --muted: rgba(226, 232, 240, 0.68);
  --accent: #f6a800;
  --accent-soft: rgba(246, 168, 0, 0.18);
  --accent-text: #fbbf24;
  --brand-glow: rgba(246, 168, 0, 0.35);
  --success: #4ade80;
  --success-soft: rgba(74, 222, 128, 0.18);
  --warn: #fb923c;
  --warn-soft: rgba(251, 146, 60, 0.18);
  --danger: #f87171;
  --danger-soft: rgba(248, 113, 113, 0.18);
  --info: #60a5fa;
  --info-soft: rgba(96, 165, 250, 0.18);

  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.4), 0 1px 2px rgba(0, 0, 0, 0.3);
  --shadow-lg: 0 12px 32px rgba(0, 0, 0, 0.5), 0 2px 6px rgba(0, 0, 0, 0.3);
}
```

### 2.3 Modern Theme
```css
[data-theme="modern"] {
  --bg: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  --surface: rgba(255, 255, 255, 0.92);
  --surface-2: rgba(255, 255, 255, 0.72);
  --elev: rgba(255, 255, 255, 0.95);
  --border: rgba(0, 44, 95, 0.08);
  --border-strong: rgba(0, 44, 95, 0.12);
  --text: #002c5f;
  --text-2: #0a3d7d;
  --muted: rgba(8, 24, 50, 0.64);
  --accent: #f6a800;
  --accent-soft: rgba(246, 168, 0, 0.12);
  --accent-text: #a96800;
  --brand-glow: rgba(246, 168, 0, 0.5);

  --d-radius: 16px;
  --d-radius-sm: 10px;

  --shadow-sm: 0 2px 4px rgba(0, 0, 0, 0.02);
  --shadow-md: 0 8px 16px rgba(0, 0, 0, 0.04), 0 2px 4px rgba(0, 0, 0, 0.02);
  --shadow-lg: 0 20px 40px rgba(0, 0, 0, 0.06), 0 4px 8px rgba(0, 0, 0, 0.03);
}
```

### 2.4 Neo-Brutalist Theme (NEW - Main Feature)
```css
[data-theme="neobrutalist"] {
  /* Off-white background */
  --bg: #F9F9F9;
  --surface: #FFFFFF;
  --surface-2: #F3F4F6;
  --elev: #FFFFFF;

  /* 1px solid black borders */
  --border: #000000;
  --border-strong: #000000;
  --border-thin: #000000;
  --border-dashed: #000000;

  /* High-contrast text */
  --text: #1F2937;
  --text-2: #374151;
  --muted: #6B7280;

  /* Sunday Estate accent color (gold) for key actions only */
  --accent: #F6A800;
  --accent-soft: rgba(246, 168, 0, 0.1);
  --accent-text: #A96800;

  /* Status colors (bright, no soft variants) */
  --success: #4ADE80;
  --success-soft: rgba(74, 222, 128, 0.08);
  --warn: #F97316;
  --warn-soft: rgba(249, 115, 22, 0.08);
  --danger: #EF4444;
  --danger-soft: rgba(239, 68, 68, 0.08);
  --info: #8B5CF6;
  --info-soft: rgba(139, 92, 246, 0.08);

  /* Minimal shadows or no shadows */
  --shadow-sm: none;
  --shadow-md: 0 1px 0 #000000;
  --shadow-lg: 0 2px 0 #000000;

  /* Sharp borders, minimal radius */
  --d-radius: 0px;
  --d-radius-sm: 0px;
  --d-radius-lg: 4px; /* For buttons only */

  /* Standard padding */
  --d-pad: 16px;
  --d-card-pad: 20px;

  /* Font stack: Inter (sans) + JetBrains Mono (mono, sparingly) */
  --font-sans: "Inter", system-ui, -apple-system, sans-serif;
  --font-mono: "JetBrains Mono", ui-monospace, "SF Mono", monospace;
  --font-display: "Inter", system-ui, sans-serif;

  /* Neo-Brutalist specific variables */
  --bracket-color: #000000;
  --tech-badge-bg: #F3F4F6;
  --tech-badge-border: #000000;
  --blink-status-on: #4ADE80;
  --blink-status-off: #9CA3AF;
}

/* Neo-Brutalist specific component overrides */
[data-theme="neobrutalist"] .card {
  border: 2px solid var(--border) !important;
  box-shadow: var(--shadow-md) !important;
}

[data-theme="neobrutalist"] .btn {
  border: 1px solid #000000;
  border-radius: 4px;
  box-shadow: 0 2px 0 #000000;
  font-weight: 600;
}

[data-theme="neobrutalist"] .btn:active {
  transform: translateY(2px);
  box-shadow: none;
}

[data-theme="neobrutalist"] .tag {
  border: 1px solid var(--border) !important;
  background: var(--tech-badge-bg) !important;
  font-family: var(--font-mono);
  font-size: 11px;
  padding: 4px 8px;
}

[data-theme="neobrutalist"] .kpi-value {
  font-family: var(--font-mono);
  letter-spacing: -0.02em;
}

[data-theme="neobrutalist"] .ai-message {
  border-left: 3px solid var(--border);
  background: var(--surface-2);
  padding: 16px;
  margin: 8px 0;
}

[data-theme="neobrutalist"] .status-blink {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--blink-status-off);
  animation: blink 2s infinite;
}

[data-theme="neobrutalist"] .status-blink.active {
  background: var(--blink-status-on);
}

@keyframes blink {
  0%, 49% { opacity: 1; }
  50%, 100% { opacity: 0.3; }
}

[data-theme="neobrutalist"] .tech-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-family: var(--font-mono);
  font-size: 11px;
  padding: 2px 6px;
  border: 1px solid var(--tech-badge-border);
  background: var(--tech-badge-bg);
  border-radius: 2px;
}

[data-theme="neobrutalist"] .bracket {
  font-family: var(--font-mono);
  color: var(--bracket-color);
  font-size: 14px;
}

[data-theme="neobrutalist"] .mono-data {
  font-family: var(--font-mono);
  letter-spacing: -0.02em;
  font-weight: 500;
}
```

---

## Phase 3: Font Integration

### 3.1 Add Google Fonts to index.html
```html
<!-- Add to public/index.html in <head> -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Thai:wght@300;400;500;600;700&family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
```

---

## Phase 4: Core Components

### 4.1 Icon Component
```typescript
// src/components/ui/Icon.tsx
export const Icon = ({ name, size = 16 }: { name: string; size?: number }) => {
  const paths: Record<string, JSX.Element> = {
    dashboard: <><rect x="2" y="2" width="5.5" height="6.5" rx="1.2"/><rect x="8.5" y="2" width="5.5" height="3.5" rx="1.2"/><rect x="8.5" y="6.5" width="5.5" height="7.5" rx="1.2"/><rect x="2" y="9.5" width="5.5" height="4.5" rx="1.2"/></>,
    loan: <><path d="M3 6h10v8H3z"/><path d="M5 6V4h6v2"/><circle cx="8" cy="10" r="1.6"/></>,
    land: <><path d="M2 12l4-6 3 4 5-7"/><path d="M2 14h12"/></>,
    calendar: <><rect x="2" y="3" width="12" height="11" rx="1.5"/><path d="M2 6h12"/><path d="M5 2v3M11 2v3"/></>,
    ai: <><path d="M2 12l4-6 3 4 5-7"/><path d="M2 14h12"/></>,
    sparkle: <><path d="M8 2v3M8 11v3M2 8h3M11 8h3M3.5 3.5l2 2M10.5 10.5l2 2M3.5 12.5l2-2M10.5 5.5l2-2"/></>,
    neobrutalist: <><rect x="2" y="2" width="12" height="12" stroke-width="2"/><path d="M4 6h8M4 8h8M4 10h4"/></>, // New icon for Neo-Brutalist theme
    // ... add more icons as needed
  };

  return (
    <svg width={size} height={size} viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth={1.4} strokeLinecap="round" strokeLinejoin="round">
      {paths[name] || paths.sparkle}
    </svg>
  );
};
```

### 4.2 Theme Switcher Component
```typescript
// src/components/shell/Topbar.tsx
import { Icon } from '../ui/Icon';

const THEMES = ['light', 'dark', 'modern', 'neobrutalist'] as const;
type Theme = typeof THEMES[number];

export const ThemeSwitcher = ({ currentTheme, onThemeChange }: { currentTheme: Theme; onThemeChange: (theme: Theme) => void }) => {
  const themeIcons: Record<Theme, string> = {
    light: 'sun',
    dark: 'moon',
    modern: 'sparkle',
    neobrutalist: 'neobrutalist',
  };

  const cycleTheme = () => {
    const currentIndex = THEMES.indexOf(currentTheme);
    const nextIndex = (currentIndex + 1) % THEMES.length;
    onThemeChange(THEMES[nextIndex]);
  };

  return (
    <button
      className="iconbtn"
      onClick={cycleTheme}
      title={`Theme: ${currentTheme}`}
      style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '8px 12px' }}
    >
      <Icon name={themeIcons[currentTheme]} size={18} />
      <span style={{ fontSize: '12px', fontWeight: 500 }}>{currentTheme}</span>
    </button>
  );
};
```

### 4.3 AppShell Component with Theme Management
```typescript
// src/components/shell/AppShell.tsx
import { useState, useEffect } from 'react';
import { ThemeSwitcher } from './Topbar';

export const AppShell = ({ children }: { children: React.ReactNode }) => {
  const [theme, setTheme] = useState<'light' | 'dark' | 'modern' | 'neobrutalist'>('light');

  useEffect(() => {
    document.body.setAttribute('data-theme', theme);
  }, [theme]);

  return (
    <div className="app-shell">
      <header style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '16px 24px',
        borderBottom: '1px solid var(--border)',
        background: 'var(--surface)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontWeight: 600, fontSize: '18px' }}>Sunday Estate</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <ThemeSwitcher currentTheme={theme} onThemeChange={setTheme} />
        </div>
      </header>
      <main style={{ minHeight: 'calc(100vh - 73px)', padding: '24px' }}>
        {children}
      </main>
    </div>
  );
};
```

---

## Phase 5: Page Components

### 5.1 Dashboard Page
```typescript
// src/components/pages/Dashboard.tsx
export const Dashboard = () => {
  return (
    <div className="dashboard">
      <h1 style={{ marginBottom: '24px' }}>Dashboard</h1>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '20px', marginBottom: '24px' }}>
        <KpiCard title="Cash Flow" value="฿2.4M" trend="+12%" />
        <KpiCard title="Portfolio" value="฿15.8M" trend="+8%" />
        <KpiCard title="Due Today" value="3" trend="-1" />
        <KpiCard title="Active Loans" value="12" trend="+2" />
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '20px' }}>
        <WidgetCard title="Cash Flow Chart" />
        <WidgetCard title="Recent Alerts" />
      </div>
    </div>
  );
};

const KpiCard = ({ title, value, trend }: { title: string; value: string; trend: string }) => (
  <div className="card" style={{ padding: '20px' }}>
    <div style={{ fontSize: '12px', color: 'var(--muted)', marginBottom: '8px', textTransform: 'uppercase' }}>{title}</div>
    <div style={{ fontSize: '28px', fontWeight: 600, marginBottom: '8px', fontFamily: 'var(--font-mono)' }}>{value}</div>
    <div style={{ fontSize: '14px', color: trend.startsWith('+') ? 'var(--success)' : 'var(--danger)' }}>{trend}</div>
  </div>
);

const WidgetCard = ({ title }: { title: string }) => (
  <div className="card" style={{ padding: '20px', minHeight: '300px' }}>
    <h3 style={{ fontSize: '14px', fontWeight: 600, marginBottom: '16px' }}>{title}</h3>
    <div style={{ color: 'var(--muted)', fontSize: '14px' }}>Widget content placeholder</div>
  </div>
);
```

### 5.2 Loans Page
```typescript
// src/components/pages/Loans.tsx
const mockLoans = [
  { id: 'L001', borrower: 'สมชาย ใจดี', type: 'Bridging', principal: 500000, balance: 420000, rate: 1.5, due: '2024-01-15', status: 'active' },
  { id: 'L002', borrower: 'วิภาวี มั่งมี', type: 'Construction', principal: 2000000, balance: 1800000, rate: 1.8, due: '2024-02-01', status: 'due-soon' },
  { id: 'L003', borrower: 'นราธิป ศรีสุข', type: 'Bridging', principal: 350000, balance: 350000, rate: 1.5, due: '2024-01-20', status: 'overdue' },
];

export const Loans = () => {
  return (
    <div className="loans">
      <h1 style={{ marginBottom: '24px' }}>Loans Management</h1>
      <div className="card" style={{ padding: '20px' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '2px solid var(--border)', textAlign: 'left' }}>
              <th style={{ padding: '12px', fontSize: '12px', textTransform: 'uppercase' }}>ID</th>
              <th style={{ padding: '12px', fontSize: '12px', textTransform: 'uppercase' }}>Borrower</th>
              <th style={{ padding: '12px', fontSize: '12px', textTransform: 'uppercase' }}>Type</th>
              <th style={{ padding: '12px', fontSize: '12px', textTransform: 'uppercase' }}>Principal</th>
              <th style={{ padding: '12px', fontSize: '12px', textTransform: 'uppercase' }}>Balance</th>
              <th style={{ padding: '12px', fontSize: '12px', textTransform: 'uppercase' }}>Rate</th>
              <th style={{ padding: '12px', fontSize: '12px', textTransform: 'uppercase' }}>Due</th>
              <th style={{ padding: '12px', fontSize: '12px', textTransform: 'uppercase' }}>Status</th>
            </tr>
          </thead>
          <tbody>
            {mockLoans.map((loan) => (
              <tr key={loan.id} style={{ borderBottom: '1px solid var(--border)' }}>
                <td style={{ padding: '12px', fontFamily: 'var(--font-mono)' }}>{loan.id}</td>
                <td style={{ padding: '12px' }}>{loan.borrower}</td>
                <td style={{ padding: '12px' }}>{loan.type}</td>
                <td style={{ padding: '12px', fontFamily: 'var(--font-mono)' }}>฿{loan.principal.toLocaleString()}</td>
                <td style={{ padding: '12px', fontFamily: 'var(--font-mono)' }}>฿{loan.balance.toLocaleString()}</td>
                <td style={{ padding: '12px', fontFamily: 'var(--font-mono)' }}>{loan.rate}%</td>
                <td style={{ padding: '12px', fontFamily: 'var(--font-mono)' }}>{loan.due}</td>
                <td style={{ padding: '12px' }}><StatusTag status={loan.status} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

const StatusTag = ({ status }: { status: string }) => {
  const colors: Record<string, { bg: string; text: string; border: string }> = {
    active: { bg: 'var(--success-soft)', text: 'var(--success)', border: 'var(--success)' },
    'due-soon': { bg: 'var(--warn-soft)', text: 'var(--warn)', border: 'var(--warn)' },
    overdue: { bg: 'var(--danger-soft)', text: 'var(--danger)', border: 'var(--danger)' },
  };

  const style = colors[status] || { bg: 'var(--info-soft)', text: 'var(--info)', border: 'var(--info)' };

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        padding: '4px 8px',
        borderRadius: '4px',
        fontSize: '11px',
        fontWeight: 500,
        fontFamily: 'var(--font-mono)',
        background: style.bg,
        color: style.text,
        border: '1px solid transparent',
      }}
    >
      {status}
    </span>
  );
};
```

### 5.3 Lands Page
```typescript
// src/components/pages/Lands.tsx
const mockLands = [
  { id: 'LD001', name: 'ซอยลาดพร้าว 15', area: '320 ตร.ว.', invested: 8000000, valuation: 12000000, roi: 50, stage: 'Planning', progress: 20 },
  { id: 'LD002', name: 'ถนนพหลโยธิน 32', area: '560 ตร.ว.', invested: 15000000, valuation: 18000000, roi: 20, stage: 'Construction', progress: 65 },
];

export const Lands = () => {
  return (
    <div className="lands">
      <h1 style={{ marginBottom: '24px' }}>Land Development</h1>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '20px' }}>
        {mockLands.map((land) => (
          <div key={land.id} className="card" style={{ padding: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px' }}>
              <div style={{ fontSize: '12px', color: 'var(--muted)', fontFamily: 'var(--font-mono)' }}>{land.id}</div>
              <div style={{ fontSize: '12px', color: 'var(--accent)', fontWeight: 600 }}>ROI {land.roi}%</div>
            </div>
            <h3 style={{ fontSize: '18px', fontWeight: 600, marginBottom: '12px' }}>{land.name}</h3>
            <div style={{ fontSize: '14px', color: 'var(--muted)', marginBottom: '16px' }}>{land.area}</div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '16px' }}>
              <div>
                <div style={{ fontSize: '11px', color: 'var(--muted)', marginBottom: '4px' }}>Invested</div>
                <div style={{ fontSize: '16px', fontWeight: 500, fontFamily: 'var(--font-mono)' }}>฿{(land.invested / 1000000).toFixed(1)}M</div>
              </div>
              <div>
                <div style={{ fontSize: '11px', color: 'var(--muted)', marginBottom: '4px' }}>Valuation</div>
                <div style={{ fontSize: '16px', fontWeight: 500, fontFamily: 'var(--font-mono)' }}>฿{(land.valuation / 1000000).toFixed(1)}M</div>
              </div>
            </div>
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                <span style={{ fontSize: '12px' }}>{land.stage}</span>
                <span style={{ fontSize: '12px', fontFamily: 'var(--font-mono)' }}>{land.progress}%</span>
              </div>
              <div style={{ height: '6px', background: 'var(--surface-2)', borderRadius: '3px', overflow: 'hidden' }}>
                <div style={{ height: '100%', width: `${land.progress}%`, background: 'var(--accent)' }} />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
```

### 5.4 AI Panel Page (Showcases Neo-Brutalist Theme)
```typescript
// src/components/pages/AI.tsx
import { useState, useRef, useEffect } from 'react';

export const AI = () => {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'สวัสดีครับ ผมคือ AI Assistant สำหรับ Sunday Estate\n\nผมช่วยวิเคราะห์ข้อมูลสัญญา ที่ดิน และให้คำแนะนำได้ครับ',
      timestamp: new Date().toISOString(),
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const send = async () => {
    if (!input.trim() || loading) return;
    const userMsg = { role: 'user', content: input, timestamp: new Date().toISOString() };
    setMessages([...messages, userMsg]);
    setInput('');
    setLoading(true);

    // Simulate AI response
    setTimeout(() => {
      const assistantMsg = {
        role: 'assistant',
        content: `วิเคราะห์ข้อมูล "${input}" เรียบร้อยแล้ว\n\n[STATUS] วิเคราะห์สำเร็จ\n[DATA] ตรวจสอบ 12 สัญญา\n[RISK] ระดับความเสี่ยง: ต่ำ\n[RECOMMEND] แนะนำอนุมัติสัญญา L005, L012`,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
      setLoading(false);
    }, 1500);
  };

  return (
    <div className="ai" style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 121px)' }}>
      <h1 style={{ marginBottom: '16px' }}>AI Analysis</h1>
      <div
        ref={scrollRef}
        style={{
          flex: 1,
          overflow: 'auto',
          padding: '16px',
          background: 'var(--surface)',
          border: '1px solid var(--border)',
          marginBottom: '16px',
          borderRadius: 'var(--d-radius)',
        }}
      >
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`ai-message ${msg.role === 'user' ? 'user-message' : 'assistant-message'}`}
            style={{
              maxWidth: '80%',
              padding: '12px 16px',
              marginBottom: '12px',
              borderRadius: 'var(--d-radius)',
              background: msg.role === 'user' ? 'var(--surface-2)' : 'transparent',
            }}
          >
            <div style={{ fontSize: '11px', color: 'var(--muted)', marginBottom: '8px', fontFamily: 'var(--font-mono)' }}>
              {msg.role === 'user' ? '[USER]' : '[AI]'} {new Date(msg.timestamp).toLocaleTimeString('th-TH', { hour: '2-digit', minute: '2-digit' })}
            </div>
            <div style={{ whiteSpace: 'pre-wrap', lineHeight: '1.6' }}>
              {msg.content}
            </div>
          </div>
        ))}
        {loading && (
          <div className="ai-message" style={{ padding: '12px 16px', background: 'var(--surface-2)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span className="status-blink active" />
              <span style={{ fontSize: '14px', color: 'var(--muted)' }}>กำลังวิเคราะห์...</span>
            </div>
          </div>
        )}
      </div>
      <div style={{ display: 'flex', gap: '12px' }}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && send()}
          placeholder="ถามคำถามเกี่ยวกับสัญญาหรือที่ดิน..."
          style={{
            flex: 1,
            padding: '12px 16px',
            border: '1px solid var(--border)',
            borderRadius: 'var(--d-radius)',
            fontSize: '14px',
            background: 'var(--surface)',
          }}
        />
        <button
          onClick={send}
          disabled={loading}
          className="btn primary"
          style={{ padding: '12px 24px', fontWeight: 500 }}
        >
          ส่ง
        </button>
      </div>
    </div>
  );
};
```

---

## Phase 6: Main App Component

```typescript
// src/App.tsx
import { useState } from 'react';
import { AppShell } from './components/shell/AppShell';
import { Dashboard } from './components/pages/Dashboard';
import { Loans } from './components/pages/Loans';
import { Lands } from './components/pages/Lands';
import { AI } from './components/pages/AI';

type Page = 'dashboard' | 'loans' | 'lands' | 'ai';

export default function App() {
  const [currentPage, setCurrentPage] = useState<Page>('dashboard');
  const [theme, setTheme] = useState<'light' | 'dark' | 'modern' | 'neobrutalist'>('light');

  useEffect(() => {
    document.body.setAttribute('data-theme', theme);
  }, [theme]);

  return (
    <AppShell>
      <div style={{ display: 'flex', gap: '24px' }}>
        <nav style={{ minWidth: '200px' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <NavButton active={currentPage === 'dashboard'} onClick={() => setCurrentPage('dashboard')}>
              Dashboard
            </NavButton>
            <NavButton active={currentPage === 'loans'} onClick={() => setCurrentPage('loans')}>
              Loans
            </NavButton>
            <NavButton active={currentPage === 'lands'} onClick={() => setCurrentPage('lands')}>
              Lands
            </NavButton>
            <NavButton active={currentPage === 'ai'} onClick={() => setCurrentPage('ai')}>
              AI Analysis
            </NavButton>
          </div>
          <div style={{ marginTop: '32px', padding: '16px', border: '1px solid var(--border)', borderRadius: 'var(--d-radius)' }}>
            <h4 style={{ fontSize: '12px', marginBottom: '12px', color: 'var(--muted)' }}>THEME</h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {(['light', 'dark', 'modern', 'neobrutalist'] as const).map((t) => (
                <button
                  key={t}
                  onClick={() => setTheme(t)}
                  style={{
                    textAlign: 'left',
                    padding: '8px 12px',
                    border: theme === t ? '2px solid var(--accent)' : '1px solid var(--border)',
                    background: theme === t ? 'var(--accent-soft)' : 'transparent',
                    borderRadius: '4px',
                    fontSize: '14px',
                    fontWeight: theme === t ? 600 : 400,
                    cursor: 'pointer',
                  }}
                >
                  {t === 'neobrutalist' ? '🎨 Neo-Brutalist' : t.charAt(0).toUpperCase() + t.slice(1)}
                </button>
              ))}
            </div>
          </div>
        </nav>
        <main style={{ flex: 1 }}>
          {currentPage === 'dashboard' && <Dashboard />}
          {currentPage === 'loans' && <Loans />}
          {currentPage === 'lands' && <Lands />}
          {currentPage === 'ai' && <AI />}
        </main>
      </div>
    </AppShell>
  );
}

function NavButton({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      onClick={onClick}
      style={{
        textAlign: 'left',
        padding: '12px 16px',
        border: '1px solid transparent',
        background: active ? 'var(--surface-2)' : 'transparent',
        borderRadius: 'var(--d-radius)',
        fontSize: '14px',
        fontWeight: active ? 600 : 400,
        color: active ? 'var(--text)' : 'var(--muted)',
        cursor: 'pointer',
        transition: 'all 0.2s',
      }}
    >
      {children}
    </button>
  );
}
```

---

## Phase 7: Base CSS Styles

```css
/* src/styles/base.css */
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: var(--font-sans);
  background: var(--bg);
  color: var(--text);
  line-height: 1.6;
}

/* Components */
.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--d-radius);
  box-shadow: var(--shadow-sm);
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 10px 20px;
  border: none;
  border-radius: var(--d-radius);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn.primary {
  background: var(--accent);
  color: var(--accent-text);
}

.btn.primary:hover {
  background: var(--accent-text);
  color: var(--accent);
}

.iconbtn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 8px;
  border: 1px solid var(--border);
  border-radius: var(--d-radius);
  background: transparent;
  color: var(--text);
  cursor: pointer;
  transition: all 0.2s;
}

.iconbtn:hover {
  background: var(--surface-2);
}

/* Typography */
h1 {
  font-size: 28px;
  font-weight: 700;
  line-height: 1.3;
}

h2 {
  font-size: 22px;
  font-weight: 600;
  line-height: 1.4;
}

h3 {
  font-size: 18px;
  font-weight: 600;
  line-height: 1.4;
}

/* Responsive */
@media (max-width: 768px) {
  .dashboard {
    grid-template-columns: 1fr !important;
  }

  .card-grid {
    grid-template-columns: 1fr !important;
  }
}
```

---

## Phase 8: Implementation Instructions

### 8.1 Step-by-Step
1. **Initialize project**: Use Create React App or Vite with TypeScript
2. **Add fonts**: Import Google fonts in index.html
3. **Create CSS files**:
   - `src/styles/base.css` (basic reset, typography)
   - `src/styles/themes.css` (all 4 theme variables)
   - `src/styles/components.css` (component styles)
4. **Create components**:
   - UI primitives (Icon, Card, Button)
   - Shell components (Sidebar, Topbar, AppShell)
   - Page components (Dashboard, Loans, Lands, AI)
5. **Implement theme switching**:
   - Add theme state to App component
   - Apply `data-theme` attribute to body
   - Create theme selector UI
6. **Test theme switching**: Verify all 4 themes work correctly
7. **Refine Neo-Brutalist styles**: Focus on AI panel message display

### 8.2 Key Requirements
- **No build step**: Use CDN React/Babel or simple Create React App setup
- **All pages functional**: Dashboard, Loans, Lands, AI with mock data
- **Theme switching**: Working toggle between 4 themes
- **Neo-Brutalist highlights**:
  - AI message timestamps in monospace
  - Status badges with [ ] brackets
  - Blinking status indicator
  - Sharp borders (0px radius)
  - High-contrast colors

### 8.3 Testing Checklist
- [ ] All 4 themes switch correctly
- [ ] Dashboard displays KPI cards and widgets
- [ ] Loans page shows table with status tags
- [ ] Lands page shows property cards with progress bars
- [ ] AI panel shows chat interface with technical badges
- [ ] Neo-Brutalist theme shows sharp borders and monospace data
- [ ] Fonts render correctly (Inter + JetBrains Mono)
- [ ] Responsive design works on mobile

---

## Phase 9: Validation & Success Criteria

### 9.1 Must Have
- ✅ 4 selectable themes (light, dark, modern, neobrutalist)
- ✅ Full page navigation (Dashboard, Loans, Lands, AI)
- ✅ Theme switcher in sidebar or topbar
- ✅ Neo-Brutalist theme with specific styles (sharp borders, monospace data)
- ✅ AI panel with technical badges and blinking status

### 9.2 Nice to Have
- Sparkline charts for Dashboard widgets
- Animated theme transitions
- Save theme preference to localStorage
- Mock API calls for AI responses

---

## Phase 10: Deliverables

Provide the AI model with:
1. Complete React application code
2. All CSS theme files
3. Mock data files
4. Component files
5. Instructions for running the demo

The demo should be:
- **Runnable**: `npm install && npm start`
- **Functional**: All pages and theme switching work
- **Demonstrative**: Clearly shows Neo-Brutalist theme integration
- **Self-contained**: No external dependencies beyond React/Babel CDN or standard npm packages