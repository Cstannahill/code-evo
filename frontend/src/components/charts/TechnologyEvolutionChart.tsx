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

interface TechnologyEvolutionChartProps {
  technologies: any;
  timeline: any[];
}

export const TechnologyEvolutionChart: React.FC<
  TechnologyEvolutionChartProps
> = ({ technologies, timeline }) => {
  const data = React.useMemo(() => {
    // Create cumulative technology adoption data
    const techAdoption: Record<string, number> = {};
    const chartData = [];

    timeline.forEach((point, index) => {
      const dataPoint: any = { month: point.date };

      // Simulate technology adoption based on timeline position
      Object.values(technologies)
        .flat()
        .forEach((tech: any) => {
          const adoptionRate = Math.min(100, (index + 1) * 10 * Math.random());
          dataPoint[tech.name] = adoptionRate;
        });

      chartData.push(dataPoint);
    });

    return chartData;
  }, [technologies, timeline]);

  const colors = ["#3b82f6", "#8b5cf6", "#10b981", "#f59e0b", "#ef4444"];

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
            {Object.values(technologies)
              .flat()
              .map((tech: any, i: number) => (
                <linearGradient
                  key={tech.name}
                  id={`color${tech.name}`}
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
          {Object.values(technologies)
            .flat()
            .slice(0, 5)
            .map((tech: any, i: number) => (
              <Area
                key={tech.name}
                type="monotone"
                dataKey={tech.name}
                stackId="1"
                stroke={colors[i % colors.length]}
                fillOpacity={1}
                fill={`url(#color${tech.name})`}
              />
            ))}
        </AreaChart>
      </ResponsiveContainer>
    </motion.div>
  );
};
