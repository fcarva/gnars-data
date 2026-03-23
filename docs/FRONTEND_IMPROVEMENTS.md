# Frontend Improvements - Treasury & Auctions Visualization

## Dados Disponíveis

### 1. Treasury History Timeseries
**File**: `web/public/data/treasury_history.json`

```json
{
  "records": [
    {
      "date": "2024-03-01",
      "inflow_usd": 3518.16,
      "outflow_usd": 0,
      "balance_usd": 524860.63,
      "has_activity": true
    }
  ]
}
```

**Use Case**: Daily balance chart with inflows/outflows overlay

### 2. Auctions Daily Timeseries
**File**: `web/public/data/auctions_daily.json`

```json
{
  "records": [
    {
      "date": "2024-03-01",
      "chain": "base+ethereum",
      "daily_eth": 0.1042,
      "daily_usd": 366.57,
      "daily_auction_count": 7.3
    }
  ]
}
```

**Use Case**: Revenue timeseries, auction frequency visualization

### 3. Auctions Monthly Summary
**File**: `web/public/data/auctions_monthly.json`

```json
{
  "records": [
    {
      "month": "2024-03",
      "chain": "base+ethereum",
      "auction_count": 219,
      "total_eth": 3.1261,
      "avg_eth_price": 3518.16,
      "total_usd": 10988.93
    }
  ]
}
```

**Use Case**: Monthly comparison, trend analysis

---

## Recommended Components

### Component 1: Treasury Balance Chart (Priority 🔴)

**Path**: `web/src/components/TreasuryBalanceChart.tsx`

```typescript
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface TreasuryRecord {
  date: string;
  balance_usd: number;
  inflow_usd: number;
  outflow_usd: number;
}

export function TreasuryBalanceChart({ data }: { data: TreasuryRecord[] }) {
  // Filter to activity days only or monthly endpoints for performance
  const filtered = data.filter((d, i) => d.inflow_usd > 0 || i % 30 === 0);

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={filtered}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis 
          dataKey="date" 
          tick={{ fontSize: 12 }}
          interval={Math.floor(filtered.length / 6)}
        />
        <YAxis 
          label={{ value: 'Balance (USD)', angle: -90, position: 'insideLeft' }}
          formatter={(value) => `$${(value / 1000).toFixed(0)}k`}
        />
        <Tooltip 
          formatter={(value) => `$${value.toLocaleString('en-US', { maximumFractionDigits: 0 })}`}
          labelFormatter={(label) => `Date: ${label}`}
        />
        <Legend />
        <Line 
          type="monotone" 
          dataKey="balance_usd" 
          stroke="#3AA99F" 
          name="Balance"
          isAnimationActive={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
```

### Component 2: Auction Revenue Timeseries (Priority 🟡)

**Path**: `web/src/components/AuctionRevenueChart.tsx`

```typescript
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface AuctionsDailyRecord {
  date: string;
  daily_usd: number;
  daily_auction_count: number;
}

export function AuctionRevenueChart({ data }: { data: AuctionsDailyRecord[] }) {
  // Aggregate to monthly for visibility
  const monthly = aggregateMonthly(data);

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={monthly}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="month" />
        <YAxis label={{ value: 'Revenue (USD)', angle: -90, position: 'insideLeft' }} />
        <Tooltip formatter={(value) => `$${value.toFixed(2)}`} />
        <Bar dataKey="monthly_usd" fill="#4385BE" name="Auction Revenue" />
      </BarChart>
    </ResponsiveContainer>
  );
}

function aggregateMonthly(data: AuctionsDailyRecord[]) {
  const monthly: Record<string, number> = {};
  data.forEach((d) => {
    const month = d.date.substring(0, 7); // YYYY-MM
    monthly[month] = (monthly[month] || 0) + d.daily_usd;
  });
  return Object.entries(monthly).map(([month, usd]) => ({
    month,
    monthly_usd: usd,
  }));
}
```

### Component 3: Combined Treasury + Revenue Dual Axis (Priority 🟢)

**Path**: `web/src/components/TreasuryDashboard.tsx`

```typescript
import { ComposedChart, Bar, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export function TreasuryDashboard() {
  const [treasuryHistory, setTreasuryHistory] = React.useState([]);
  const [auctionDaily, setAuctionDaily] = React.useState([]);

  React.useEffect(() => {
    Promise.all([
      fetch('/data/treasury_history.json').then(r => r.json()),
      fetch('/data/auctions_daily.json').then(r => r.json()),
    ]).then(([t, a]) => {
      setTreasuryHistory(t.records);
      setAuctionDaily(a.records);
    });
  }, []);

  // Merge on date
  const combined = mergeOnDate(treasuryHistory, auctionDaily);
  const monthly = aggregateToMonthly(combined);

  return (
    <div className="treasury-dashboard">
      <h2>Treasury & Revenue</h2>
      <ResponsiveContainer width="100%" height={400}>
        <ComposedChart data={monthly}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="month" />
          <YAxis 
            yAxisId="left"
            label={{ value: 'Balance (USD)', angle: -90, position: 'insideLeft' }}
            formatter={(v) => `$${(v/1000).toFixed(0)}k`}
          />
          <YAxis 
            yAxisId="right" 
            orientation="right"
            label={{ value: 'Revenue (USD)', angle: 90, position: 'insideRight' }}
            formatter={(v) => `$${(v/1000).toFixed(0)}k`}
          />
          <Tooltip formatter={(value) => `$${value.toLocaleString()}`} />
          <Legend />
          
          {/* Daily average spend */}
          <Bar yAxisId="left" dataKey="avg_spend_daily" fill="#D14D41" name="Avg Daily Spend" opacity={0.7} />
          
          {/* Monthly revenue */}
          <Bar yAxisId="right" dataKey="monthly_revenue" fill="#4385BE" name="Monthly Revenue" />
          
          {/* Balance trend */}
          <Line yAxisId="left" type="monotone" dataKey="balance_eom" stroke="#3AA99F" name="End of Month Balance" strokeWidth={2} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
```

---

## Integration Path

### Phase 1: Add to Existing Pages (Week 1)
1. Add `TreasuryBalanceChart` to `/treasury` page
2. Add `AuctionRevenueChart` to `/proposals` or new `/analytics` page
3. Display `treasury_history` stats (current balance, peak, opening)

### Phase 2: Create Analytics Dashboard (Week 2)
1. New route: `/analytics` or `/insights`
2. Embed `TreasuryDashboard` (dual axis)
3. Add key metrics:
   - **Treasury Runway**: `balance / avg_monthly_spend`
   - **Revenue Trend**: `current_month_revenue vs avg`
   - **Contributor Burn**: `monthly_spend / active_contributors`

### Phase 3: Proposal Execution Timeline (Week 3)
1. Create `ProposalTimeline.tsx`
2. Show: Created → Voted → Executed delays
3. Highlight outliers (stalled proposals)

---

## Data Loading Pattern

```typescript
// Recommended: Fetch in parent, pass to components

import { useEffect, useState } from 'react';

function Treasury() {
  const [metrics, setMetrics] = useState(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        const [treasury, auctions, monthly] = await Promise.all([
          fetch('/data/treasury_history.json').then(r => r.json()),
          fetch('/data/auctions_daily.json').then(r => r.json()),
          fetch('/data/auctions_monthly.json').then(r => r.json()),
        ]);
        setMetrics({ treasury, auctions, monthly });
      } catch (e) {
        console.error('Failed to load metrics:', e);
      }
    };
    loadData();
  }, []);

  if (!metrics) return <div>Loading...</div>;

  return (
    <>
      <TreasuryBalanceChart data={metrics.treasury.records} />
      <AuctionRevenueChart data={metrics.auctions.records} />
      <TreasuryDashboard data={metrics} />
    </>
  );
}
```

---

## Performance Considerations

- **Large datasets**: `auctions_daily` has 746 records
  - Downsampling: Show only activity days + monthly endpoints
  - Use `isAnimationActive={false}` on Recharts for speed
  - Consider `useMemo()` for aggregations

- **Loading**: Parallel fetch all three JSON files
  - Estimated size: ~200KB total
  - Cache in localStorage after first load

- **Mobile**: Use `ResponsiveContainer` height={`window.innerHeight * 0.4`} for responsive sizing

---

## Testing Checklist

- [ ] Data loads without errors
- [ ] Charts render on all screen sizes
- [ ] Tooltip shows correct values
- [ ] Performance acceptable (<1s render)
- [ ] Works on mobile (touch) devices
- [ ] Accessibility: ARIA labels for charts
- [ ] Dark mode compatible (if applicable)

---

## Files to Create

```
web/src/components/
  ├── TreasuryBalanceChart.tsx
  ├── AuctionRevenueChart.tsx
  ├── TreasuryDashboard.tsx
  └── hooks/
      └── useTreasuryMetrics.ts

web/src/pages/
  ├── treasury.tsx  (add TreasuryBalanceChart)
  └── analytics.tsx (new - TreasuryDashboard + insights)
```

---

## Next Steps

1. **Immediate** (this session):
   - Copy component code to React project
   - Add to `/treasury` page
   - Test with real data

2. **Follow-up** (next sprint):
   - Create `/analytics` dashboard
   - Add KPI cards (runway, retention, etc.)
   - Performance optimization

3. **Polish** (next quarter):
   - Proposal execution timeline
   - Custom date range filters
   - Export to PDF/PNG
