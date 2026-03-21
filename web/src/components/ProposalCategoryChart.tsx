import type { DaoMetrics } from "@/lib/gnars-data";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";

interface ProposalCategoryChartProps {
  metrics: DaoMetrics;
}

const COLORS = [
  "#f73c1b", // gnars brand primary
  "#ff9800",
  "#ffeb3b",
  "#4caf50",
  "#8bc34a",
  "#00bcd4",
  "#009688",
  "#3f51b5",
  "#9c27b0",
  "#607d8b",
];

export function ProposalCategoryChart({ metrics }: ProposalCategoryChartProps) {
  const counts = metrics.overview.proposal_category_counts || {};
  // Filter out 'uncategorized' for better pie chart clarity, or optionally keep it. Let's keep it but put it at the end.
  const entries = Object.entries(counts)
    .sort((a, b) => b[1] - a[1]);

  const data = entries.map(([name, value]) => ({
    name: name.replace(/_/g, " ").toUpperCase(),
    value,
  }));

  if (data.length === 0) {
    return null;
  }

  return (
    <div>
      <h4 className="analytics-block-title">PROPOSAL CATEGORIES</h4>
      <div style={{ width: "100%", height: 300, marginTop: "1rem" }}>
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={100}
              paddingAngle={2}
              dataKey="value"
              stroke="none"
              label={({ cx, cy, midAngle, innerRadius, outerRadius, value, index }) => {
                const RADIAN = Math.PI / 180;
                const radius = outerRadius + 20;
                const x = cx + radius * Math.cos(-midAngle * RADIAN);
                const y = cy + radius * Math.sin(-midAngle * RADIAN);
                // Only show label for top 5, else too crowded
                if (index > 4) return null;
                return (
                  <text x={x} y={y} fill="var(--color-text)" textAnchor={x > cx ? 'start' : 'end'} dominantBaseline="central" fontSize={11}>
                    {data[index].name} ({value})
                  </text>
                );
              }}
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.name === "UNCATEGORIZED" ? "#333333" : COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip 
              contentStyle={{ backgroundColor: 'var(--color-bg-elevated)', border: '1px solid var(--color-border)' }}
              itemStyle={{ color: 'var(--color-text)' }}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}