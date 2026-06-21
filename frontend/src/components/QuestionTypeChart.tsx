"use client";

import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

interface Props {
  questionTypeDistribution: Record<string, number>;
}

const COLORS = ["#e8542e", "#2a8c6e", "#7c8a99", "#c9a85c", "#8a5cc9"];

export default function QuestionTypeChart({ questionTypeDistribution }: Props) {
  const data = Object.entries(questionTypeDistribution).map(([type, count]) => ({
    name: type,
    value: count,
  }));

  return (
    <div className="rounded-sm border border-ink-line bg-ink-raised p-6">
      <h3 className="font-serif text-base text-paper">Question types</h3>
      <p className="mb-4 text-xs text-graphite">
        How questions are split by format
      </p>
      <div className="flex items-center gap-6">
        <ResponsiveContainer width="50%" height={180}>
          <PieChart>
            <Pie
              data={data}
              dataKey="value"
              nameKey="name"
              innerRadius={45}
              outerRadius={75}
              paddingAngle={2}
              stroke="none"
            >
              {data.map((_, i) => (
                <Cell key={i} fill={COLORS[i % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                background: "#0b0d12",
                border: "1px solid #1f242f",
                borderRadius: 2,
                fontSize: 12,
                fontFamily: "var(--font-jetbrains-mono)",
              }}
              labelStyle={{ color: "#f5f2e8" }}
            />
          </PieChart>
        </ResponsiveContainer>
        <ul className="flex flex-1 flex-col gap-2">
          {data.map((d, i) => (
            <li key={d.name} className="flex items-center justify-between gap-3 text-sm">
              <span className="flex items-center gap-2 text-graphite">
                <span
                  className="h-2 w-2 rounded-full"
                  style={{ background: COLORS[i % COLORS.length] }}
                />
                {d.name}
              </span>
              <span className="font-mono text-paper">{d.value}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
