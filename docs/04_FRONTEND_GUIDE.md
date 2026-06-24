# FinSense — Frontend Guide (React + Tailwind)
## Context File 04 for AI Coding Agents

---

## SETUP

```bash
npm create vite@latest frontend -- --template react
cd frontend
npm install tailwindcss @tailwindcss/vite recharts axios react-router-dom lucide-react
```

`vite.config.js`:
```js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: { proxy: { '/api': 'http://localhost:8000' } }
})
```

---

## COLOUR SYSTEM (Tier Colours)

Use these consistently everywhere:

```js
// src/utils/tiers.js
export const TIER_CONFIG = {
  green:  { bg: 'bg-green-100',  border: 'border-green-400',  text: 'text-green-700',  hex: '#16a34a', label: 'Healthy' },
  amber:  { bg: 'bg-yellow-100', border: 'border-yellow-400', text: 'text-yellow-700', hex: '#d97706', label: 'Early Stress' },
  orange: { bg: 'bg-orange-100', border: 'border-orange-400', text: 'text-orange-700', hex: '#ea580c', label: 'High Risk' },
  red:    { bg: 'bg-red-100',    border: 'border-red-400',    text: 'text-red-700',    hex: '#dc2626', label: 'Pre-Default' },
}

export function getTierConfig(tier) {
  return TIER_CONFIG[tier] || TIER_CONFIG.green
}
```

---

## API CLIENT

Save as `src/api/client.js`:

```js
import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export const getDashboardSummary = () => api.get('/dashboard/summary')
export const getHighRisk = (tiers = 'orange,red', limit = 20) =>
  api.get(`/dashboard/high-risk?tier=${tiers}&limit=${limit}`)

export const getLoanRisk = (loanId) => api.get(`/risk/${loanId}`)
export const rescoreLoan = (loanId) => api.post(`/risk/${loanId}/score`)

export const getLoanDetail = (loanId) => api.get(`/loans/${loanId}`)
export const getAlerts = () => api.get('/dashboard/alerts')
export const markAlertRead = (alertId) => api.patch(`/dashboard/alerts/${alertId}/read`)

export const startAgentConversation = (loanId, channel = 'in_app') =>
  api.post(`/agent/${loanId}/start`, { channel })
export const sendAgentMessage = (loanId, conversationId, message) =>
  api.post(`/agent/${loanId}/message`, { conversation_id: conversationId, message })
```

---

## PAGE: Dashboard.jsx

The main page. Shows portfolio summary + high-risk borrower table.

**Layout:** Sidebar + Main area

```
┌──────────────────────────────────────────────────────┐
│  🏦 FinSense         [Alerts 47]    Officer: Priya   │
├─────────┬────────────────────────────────────────────┤
│  Nav    │  Portfolio Overview                        │
│         │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐     │
│ Home    │  │ 3200 │ │  950 │ │  620 │ │  230 │     │
│ Alerts  │  │GREEN │ │AMBER │ │ORNG  │ │ RED  │     │
│ Search  │  └──────┘ └──────┘ └──────┘ └──────┘     │
│         │                                           │
│         │  Trend Graph (6 months avg risk)          │
│         │                                           │
│         │  High Risk Loans (sortable table)         │
│         │  [Name] [Type] [Balance] [Score] [Tier]   │
└─────────┴────────────────────────────────────────────┘
```

**Key components to render:**
- 4 stat cards (one per tier) using `TIER_CONFIG` colours
- `<TrendChart />` (Recharts LineChart of avg portfolio risk over 6 months)
- `<BorrowerTable />` (clickable rows → navigate to BorrowerDetail)

---

## PAGE: BorrowerDetail.jsx

The deep-dive page for one loan. Route: `/loan/:loanId`

```
┌─────────────────────────────────────────────────────────┐
│ ← Back   Rajesh Kumar (Personal Loan)      [Re-score]  │
├────────────────────┬────────────────────────────────────┤
│  RISK GAUGE        │  SHAP Explanation                  │
│                    │  ┌────────────────────────────┐    │
│   [ 78.4 ]         │  │ EMI missed (3m)    ████ +31│    │
│   🔴 PRE-DEFAULT   │  │ Cheque bounces     ███  +19│    │
│                    │  │ Balance trend      ██   -12│    │
│                    │  │ Credit/debit ratio ██   +9 │    │
│                    │  └────────────────────────────┘    │
├────────────────────┴────────────────────────────────────┤
│  Score History (6 months)                              │
│  [Recharts line chart showing score progression]       │
├─────────────────────────────────────────────────────────┤
│  Loan Details          │  Borrower Profile             │
│  Type: Personal        │  Income: ₹45,000/mo           │
│  EMI: ₹8,200/mo        │  Employment: Salaried         │
│  Outstanding: ₹2.8L    │  City: Mumbai                 │
├─────────────────────────────────────────────────────────┤
│  [🤖 Engage with AI Agent]   [📋 Escalate to Branch]  │
└─────────────────────────────────────────────────────────┘
```

---

## COMPONENT: RiskGauge.jsx

Animated semicircular gauge. Score 0–100, colour changes by tier.

```jsx
// Simplest implementation using SVG arc
import { getTierConfig } from '../utils/tiers'

export default function RiskGauge({ score, tier }) {
  const config = getTierConfig(tier)
  const angle = (score / 100) * 180  // 0 = left, 180 = right
  
  // SVG arc from -90deg to (angle - 90) deg
  const rad = (a) => (a * Math.PI) / 180
  const cx = 100, cy = 100, r = 80
  
  const startX = cx + r * Math.cos(rad(180))
  const startY = cy + r * Math.sin(rad(180))
  const endAngle = 180 + angle
  const endX = cx + r * Math.cos(rad(endAngle))
  const endY = cy + r * Math.sin(rad(endAngle))
  const largeArc = angle > 180 ? 1 : 0
  
  return (
    <div className="flex flex-col items-center">
      <svg viewBox="0 0 200 120" width={220}>
        {/* Background arc */}
        <path
          d={`M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}`}
          fill="none" stroke="#e5e7eb" strokeWidth={16} strokeLinecap="round"
        />
        {/* Score arc */}
        <path
          d={`M ${startX} ${startY} A ${r} ${r} 0 ${largeArc} 1 ${endX} ${endY}`}
          fill="none" stroke={config.hex} strokeWidth={16} strokeLinecap="round"
        />
        {/* Score text */}
        <text x={cx} y={cy + 15} textAnchor="middle"
          fontSize={32} fontWeight="bold" fill={config.hex}>
          {score.toFixed(1)}
        </text>
      </svg>
      <span className={`text-sm font-semibold px-3 py-1 rounded-full ${config.bg} ${config.text}`}>
        {config.label}
      </span>
    </div>
  )
}
```

---

## COMPONENT: ShapBar.jsx

Horizontal bar chart showing SHAP risk factors.

```jsx
export default function ShapBar({ factors }) {
  const maxImpact = Math.max(...factors.map(f => f.impact))
  
  return (
    <div className="space-y-2">
      {factors.map((f) => (
        <div key={f.feature} className="flex items-center gap-2">
          <span className="text-xs text-gray-600 w-44 truncate">{f.human_label}</span>
          <div className="flex-1 bg-gray-100 rounded-full h-3 relative">
            <div
              className={`h-3 rounded-full transition-all ${
                f.direction === 'increasing_risk' ? 'bg-red-400' : 'bg-green-400'
              }`}
              style={{ width: `${(f.impact / maxImpact) * 100}%` }}
            />
          </div>
          <span className={`text-xs font-mono w-10 text-right ${
            f.direction === 'increasing_risk' ? 'text-red-600' : 'text-green-600'
          }`}>
            {f.direction === 'increasing_risk' ? '+' : '-'}
            {(f.impact * 100).toFixed(0)}
          </span>
        </div>
      ))}
    </div>
  )
}
```

---

## COMPONENT: TrendChart.jsx

```jsx
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine } from 'recharts'

export default function TrendChart({ history }) {
  return (
    <LineChart width={480} height={200} data={history}>
      <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
      <XAxis dataKey="scored_at" tickFormatter={d => d.slice(0,7)} />
      <YAxis domain={[0, 100]} />
      <Tooltip formatter={(v) => [`${v.toFixed(1)}`, 'Risk Score']} />
      <ReferenceLine y={30} stroke="#16a34a" strokeDasharray="4 2" label="Green" />
      <ReferenceLine y={55} stroke="#d97706" strokeDasharray="4 2" label="Amber" />
      <ReferenceLine y={75} stroke="#ea580c" strokeDasharray="4 2" label="Orange" />
      <Line type="monotone" dataKey="score" stroke="#3b82f6" strokeWidth={2} dot={{ r: 4 }} />
    </LineChart>
  )
}
```

---

## PAGE: AgentChat.jsx

```
┌──────────────────────────────────────┐
│ 🤖 FinSense Agent — Rajesh Kumar    │
├──────────────────────────────────────┤
│                                      │
│  [Agent]: Namaste Rajesh ji, I'm    │
│  reaching out regarding your SBI    │
│  personal loan...                   │
│                                      │
│          [Borrower]: I had some     │
│          medical expenses...        │
│                                      │
│  [Agent]: I understand. SBI has a  │
│  restructuring option that can...   │
│                                      │
│  ┌────────────────────────────────┐  │
│  │ Type response...          [→] │  │
│  └────────────────────────────────┘  │
│                                      │
│  Quick replies: [Restructuring?]    │
│  [Speak to officer] [Not interested]│
└──────────────────────────────────────┘
```

The message bubbles should be styled:
- Agent: left-aligned, light blue background
- Borrower: right-aligned, white with border

---

## ROUTING (App.jsx)

```jsx
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import BorrowerDetail from './pages/BorrowerDetail'
import AgentChat from './pages/AgentChat'
import Alerts from './pages/Alerts'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/loan/:loanId" element={<BorrowerDetail />} />
        <Route path="/loan/:loanId/agent" element={<AgentChat />} />
        <Route path="/alerts" element={<Alerts />} />
      </Routes>
    </BrowserRouter>
  )
}
```

---

## RUNNING FRONTEND

```bash
cd frontend/
npm install
npm run dev
# Opens at http://localhost:5173
```

---
