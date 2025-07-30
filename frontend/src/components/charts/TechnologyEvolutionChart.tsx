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
  timeline: Array<{ date: string; patterns: Record<string, number> }> | any;
}

export const TechnologyEvolutionChart: React.FC<
  TechnologyEvolutionChartProps
> = ({ technologies, timeline }) => {
  // Normalize timeline data with better error handling
  const normalizedTimeline = React.useMemo(() => {
    if (!timeline) {
      console.log("TechnologyEvolutionChart: No timeline data provided");
      return [];
    }

    // Handle nested timeline structure from backend
    if (timeline.timeline && Array.isArray(timeline.timeline)) {
      console.log("TechnologyEvolutionChart: Using nested timeline", timeline.timeline);
      return timeline.timeline;
    }

    // If timeline is already an array, use it directly
    if (Array.isArray(timeline)) {
      console.log("TechnologyEvolutionChart: Using direct timeline array", timeline);
      return timeline;
    }

    // Handle pattern_timeline structure
    if (timeline.pattern_timeline?.timeline && Array.isArray(timeline.pattern_timeline.timeline)) {
      console.log("TechnologyEvolutionChart: Using pattern_timeline.timeline", timeline.pattern_timeline.timeline);
      return timeline.pattern_timeline.timeline;
    }

    console.warn("TechnologyEvolutionChart: Unknown timeline structure", timeline);
    return [];
  }, [timeline]);

  const data = React.useMemo(() => {
    if (!normalizedTimeline || normalizedTimeline.length === 0) {
      // Generate sample data if no timeline provided
      const currentDate = new Date();
      return Array.from({ length: 6 }, (_, i) => {
        const date = new Date(currentDate);
        date.setMonth(date.getMonth() - (5 - i));

        const dataPoint: any = {
          month: date.toISOString().slice(0, 7),
        };

        // Safely handle technologies object
        if (technologies && typeof technologies === 'object') {
          const allTechs = Object.values(technologies).flat().filter(tech => tech && tech.name);
          allTechs.forEach((tech) => {
            dataPoint[tech.name] = Math.min(
              100,
              (i + 1) * 15 + Math.random() * 10
            );
          });
        }

        return dataPoint;
      });
    }

    // Use actual timeline if provided
    return normalizedTimeline.map((point: { date: string; patterns: Record<string, number> }) => ({
      month: point.date,
      ...point.patterns,
    }));
  }, [technologies, normalizedTimeline]);

  const colors = ["#3b82f6", "#8b5cf6", "#10b981", "#f59e0b", "#ef4444"];

  // Get top 5 technologies for display with better error handling
  const allTechs = React.useMemo(() => {
    if (!technologies || typeof technologies !== 'object') {
      console.warn("TechnologyEvolutionChart: Invalid technologies object", technologies);
      return [];
    }

    const techs = Object.values(technologies)
      .flat()
      .filter(tech => tech && tech.name && typeof tech.name === 'string')
      .slice(0, 5);
    
    console.log("TechnologyEvolutionChart: Displaying technologies", techs);
    return techs;
  }, [technologies]);

  // Show empty state if no data
  if (!data || data.length === 0 || allTechs.length === 0) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5 }}
        className="w-full h-96 flex items-center justify-center"
      >
        <div className="text-center text-muted-foreground">
          <div className="text-4xl mb-2">📈</div>
          <p className="text-lg mb-2">No Technology Evolution Data</p>
          <p className="text-sm">Evolution chart will show technology adoption over time</p>
          <div className="mt-4 text-xs bg-muted/50 p-3 rounded max-w-md">
            {!technologies && <p>• No technologies detected</p>}
            {normalizedTimeline.length === 0 && <p>• No timeline data available</p>}
            {allTechs.length === 0 && technologies && <p>• Technology format invalid</p>}
          </div>
        </div>
      </motion.div>
    );
  }

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
