import React from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { motion } from "framer-motion";
import type { TechnologiesByCategory } from "../../types/api";

interface TechnologyEvolutionChartProps {
  technologies: TechnologiesByCategory;
  timeline: Array<{ date: string; patterns: Record<string, number> }>;
}

export const TechnologyEvolutionChart: React.FC<
  TechnologyEvolutionChartProps
> = ({ technologies, timeline }) => {
  const data = React.useMemo(() => {
    // Create cumulative technology adoption data
    const chartData = [];

    timeline.forEach((point, index) => {
      const dataPoint: any = { month: point.date };

      // Simulate technology adoption based on timeline position
      Object.entries(technologies).forEach(([category, techList]) => {
        techList.forEach((tech) => {
          const adoptionRate = Math.min(
            100,
            (index + 1) * 15 + Math.random() * 20
          );
          dataPoint[tech.name] = adoptionRate;
        });
      });

      chartData.push(dataPoint);
    });

    return chartData;
  }, [technologies, timeline]);

  const colors = ["#3b82f6", "#8b5cf6", "#10b981", "#f59e0b", "#ef4444"];

  // Get top 5 technologies for display
  const allTechs = Object.values(technologies).flat().slice(0, 5);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
      className="w-full h-96"
    >
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data}>
          <defs>
            {allTechs.map((tech, i) => (
              <linearGradient
                key={tech.name}
                id={`color${tech.name.replace(/[^a-zA-Z0-9]/g, "")}`}
                x1="0"
                y1="0"
                x2="0"
                y2="1"
              >
                <stop
                  offset="5%"
                  stopColor={colors[i % colors.length]}
                  stopOpacity={0.8}
                />
                <stop
                  offset="95%"
                  stopColor={colors[i % colors.length]}
                  stopOpacity={0}
                />
              </linearGradient>
            ))}
          </defs>
          <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
          <XAxis dataKey="month" className="text-xs" />
          <YAxis className="text-xs" />
          <Tooltip
            contentStyle={{
              backgroundColor: "hsl(var(--popover))",
              border: "1px solid hsl(var(--border))",
            }}
          />
          <Legend />
          {allTechs.map((tech, i) => (
            <Area
              key={tech.name}
              type="monotone"
              dataKey={tech.name}
              stackId="1"
              stroke={colors[i % colors.length]}
              fillOpacity={1}
              fill={`url(#color${tech.name.replace(/[^a-zA-Z0-9]/g, "")})`}
            />
          ))}
        </AreaChart>
      </ResponsiveContainer>
    </motion.div>
  );
};
