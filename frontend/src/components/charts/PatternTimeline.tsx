import React from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  type TooltipProps,
} from "recharts";
import { motion } from "framer-motion";

interface PatternTimelineProps {
  data: Array<{
    date: string;
    patterns: Record<string, number>;
  }> | any;
  height?: number;
}

const CustomTooltip = ({
  active,
  payload,
  label,
}: TooltipProps<number, string>) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-popover p-3 rounded-lg shadow-lg border">
        <p className="font-semibold">{label}</p>
        {payload.map((entry, index) => (
          <p key={index} style={{ color: entry.color }}>
            {entry.name}: {entry.value}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

export const PatternTimeline: React.FC<PatternTimelineProps> = ({
  data,
  height = 400,
}) => {
  // Normalize data to ensure it's an array with better debugging
  const normalizedData = React.useMemo(() => {
    if (!data) {
      console.log("PatternTimeline: No data provided");
      return [];
    }

    // If data has a timeline property, use that
    if (data.timeline && Array.isArray(data.timeline)) {
      console.log("PatternTimeline: Using data.timeline", data.timeline);
      return data.timeline;
    }

    // If data is already an array, use it directly
    if (Array.isArray(data)) {
      console.log("PatternTimeline: Using data as array", data);
      return data;
    }

    // Handle pattern_timeline nested structure
    if (data.pattern_timeline?.timeline && Array.isArray(data.pattern_timeline.timeline)) {
      console.log("PatternTimeline: Using data.pattern_timeline.timeline", data.pattern_timeline.timeline);
      return data.pattern_timeline.timeline;
    }

    console.warn("PatternTimeline: Unknown data structure", data);
    return [];
  }, [data]);

  // Extract all unique pattern names with better error handling
  const patternNames = React.useMemo(() => {
    const names = new Set<string>();
    normalizedData.forEach((item: { date: string; patterns: Record<string, number> }) => {
      if (item && item.patterns && typeof item.patterns === 'object') {
        Object.keys(item.patterns).forEach((pattern) => names.add(pattern));
      }
    });
    const patternArray = Array.from(names);
    console.log("PatternTimeline: Extracted pattern names", patternArray);
    return patternArray;
  }, [normalizedData]);

  // Transform data for recharts - flatten the nested patterns object
  const chartData = React.useMemo(() => {
    const transformed = normalizedData.map((item: { date: string; patterns: Record<string, number> }) => ({
      date: item.date,
      ...item.patterns, // Spread patterns directly into the data object
    }));
    console.log("PatternTimeline: Chart data transformed", transformed);
    return transformed;
  }, [normalizedData]);

  const colors = [
    "#3b82f6",
    "#8b5cf6",
    "#10b981",
    "#f59e0b",
    "#ef4444",
    "#06b6d4",
    "#ec4899",
    "#84cc16",
  ];

  // Show empty state if no data
  if (normalizedData.length === 0) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full flex items-center justify-center"
        style={{ height }}
      >
        <div className="text-center text-muted-foreground">
          <div className="text-4xl mb-2">📊</div>
          <p>No timeline data available</p>
          <p className="text-sm mt-1">Pattern timeline will appear after analysis</p>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="w-full"
    >
      <ResponsiveContainer width="100%" height={height}>
        <LineChart
          data={chartData}
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
          <XAxis
            dataKey="date"
            className="text-xs"
            tick={{ fill: "currentColor" }}
          />
          <YAxis className="text-xs" tick={{ fill: "currentColor" }} />
          <Tooltip content={<CustomTooltip />} />
          <Legend className="text-xs" />
          {patternNames.map((pattern, index) => (
            <Line
              key={pattern}
              type="monotone"
              dataKey={pattern}
              name={pattern}
              stroke={colors[index % colors.length]}
              strokeWidth={2}
              dot={{ r: 4 }}
              activeDot={{ r: 6 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </motion.div>
  );
};
