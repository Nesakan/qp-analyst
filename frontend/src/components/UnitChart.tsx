"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

interface Props {
  unitDistribution: Record<string, number>;
  marksByUnit: Record<string, number>;
}

export default function UnitChart({ unitDistribution, marksByUnit }: Props) {
  const data = Object.keys(unitDistribution)
    .sort((a, b) => Number(a) - Number(b))
    .map((unit) => ({
      unit: `Unit ${unit}`,
      questions: unitDistribution[unit],
      marks: marksByUnit[unit] ?? 0,
    }));

  return (
    <div className="rounded-sm border border-ink-line bg-ink-raised p-6">
      <h3 className="font-serif text-base text-paper">
        Questions per unit
      </h3>
      <p className="mb-4 text-xs text-graphite">
        Where the question count concentrates across the syllabus
      </p>
      <ResponsiveContainer width="100%" height={240}>
        <BarChart data={data} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1f242f" vertical={false} />
          <XAxis
            dataKey="unit"
            tick={{ fill: "#7c8a99", fontSize: 12, fontFamily: "var(--font-jetbrains-mono)" }}
            axisLine={{ stroke: "#1f242f" }}
            tickLine={false}
          />
          <YAxis
            tick={{ fill: "#7c8a99", fontSize: 12, fontFamily: "var(--font-jetbrains-mono)" }}
            axisLine={false}
            tickLine={false}
            allowDecimals={false}
          />
          <Tooltip
            cursor={{ fill: "#1f242f", opacity: 0.4 }}
            contentStyle={{
              background: "#0b0d12",
              border: "1px solid #1f242f",
              borderRadius: 2,
              fontSize: 12,
              fontFamily: "var(--font-jetbrains-mono)",
            }}
            labelStyle={{ color: "#f5f2e8" }}
          />
          <Bar dataKey="questions" fill="#e8542e" radius={[2, 2, 0, 0]} maxBarSize={48} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
