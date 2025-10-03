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
  topPatterns?: string[];
}

// Normalized item coming from API before chart transformation
type NormalizedItem = {
  date?: string;
  fullDate?: string;
  patterns?: Record<string, number>;
} & {
  [k: string]: number | string | Record<string, number> | undefined;
};

// Datum passed to Recharts
type ChartDatum = {
  date: string; // e.g., "May 23"
  fullDate: string; // e.g., "2025-05-24"
} & Record<string, number | string>;

const CustomTooltip = ({
  active,
  payload,
  label,
}: TooltipProps<number, string>) => {
  if (active && payload && payload.length) {
    // Get the full date from the payload data
    const fullDate = payload[0]?.payload?.fullDate || label;
    return (
      <div className="bg-gray-900 text-white p-3 rounded-lg shadow-lg border border-gray-700">
        <p className="font-semibold">{fullDate}</p>
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
  topPatterns,
}) => {
  // Debug the incoming data
  React.useEffect(() => {
    console.log("PatternTimeline: Component received data:", data);
    console.log("PatternTimeline: Data type:", typeof data);
    console.log("PatternTimeline: Is array:", Array.isArray(data));
  }, [data]);

  // Normalize data to ensure it's an array with better debugging
  const normalizedData: NormalizedItem[] = React.useMemo<NormalizedItem[]>(() => {
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

  // Utility to create a canonical comparison key: lowercase + remove non-alphanumerics
  const canonicalize = React.useCallback((s: string | undefined): string => {
    if (!s) return "";
    return String(s)
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "");
  }, []);

  // Extract all available data keys from data
  const availableDataKeys = React.useMemo<string[]>(() => {
    const names = new Set<string>();
    normalizedData.forEach((item: NormalizedItem) => {
      if (item && typeof item === "object") {
        if (item.patterns && typeof item.patterns === "object") {
          Object.keys(item.patterns).forEach((pattern) => names.add(pattern));
        } else {
          Object.keys(item).forEach((key) => {
            if (key !== "date" && key !== "fullDate" && typeof item[key] === "number") {
              names.add(key);
            }
          });
        }
      }
    });
    const result = Array.from(names);
    console.log("PatternTimeline: Available data keys (raw)", result);
    return result;
  }, [normalizedData]);

  // Build series list with mapping between display name and actual dataKey
  const series = React.useMemo(() => {
    // Build lookup by canonical key
    const lookup = new Map<string, string>();
    availableDataKeys.forEach((k) => lookup.set(canonicalize(k), k));

    const toSnake = (s: string) => s.replace(/\s+/g, "_");

    const requested = (topPatterns && topPatterns.length > 0)
      ? topPatterns
      : availableDataKeys; // fall back to using keys as names

    const mapped = requested.map((name) => {
      const candidates = [
        name,
        toSnake(name),
        name.replace(/\s+/g, "-"),
        name.replace(/\s+/g, ""),
      ];

      let foundKey: string | undefined;
      for (const c of candidates) {
        const canonical = canonicalize(c);
        const maybe = lookup.get(canonical);
        if (maybe) {
          foundKey = maybe;
          break;
        }
      }

      if (!foundKey) {
        // As a last resort, try exact case-insensitive match
        foundKey = availableDataKeys.find((k) => k.toLowerCase() === name.toLowerCase());
      }

      if (!foundKey) {
        console.warn(`PatternTimeline: Could not map requested pattern "${name}" to any data key. Skipping.`);
        return null;
      }

      return { name, dataKey: foundKey };
    }).filter(Boolean) as Array<{ name: string; dataKey: string }>;

    console.log("PatternTimeline: Series mapping (display name -> dataKey)", mapped);
    return mapped;
  }, [availableDataKeys, topPatterns, canonicalize]);

  // Transform data for recharts - handle both nested and flattened structures
  const chartData = React.useMemo<ChartDatum[]>(() => {
    const transformed = normalizedData.map<ChartDatum | null>((item: NormalizedItem) => {
      // Convert date to a format that Recharts can handle better
      // Allow either ISO string or already formatted string
      const rawDate: string = (item?.date ?? item?.fullDate ?? "");
      const dateObj = new Date(rawDate);

      // Check if date is valid
      if (isNaN(dateObj.getTime())) {
        console.warn("PatternTimeline: Invalid date found:", rawDate, "on item:", item);
        return null;
      }

      const formattedDate = dateObj.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric'
      });

      // Handle both data structures
      if (item.patterns && typeof item.patterns === 'object') {
        // Structure: {date: "...", patterns: {...}}
        return {
          date: formattedDate,
          fullDate: rawDate,
          ...item.patterns,
        } as ChartDatum;
      } else {
        // Structure: {date: "...", pattern1: value1, pattern2: value2, ...}
        const result: ChartDatum = {
          date: formattedDate,
          fullDate: rawDate,
        };

        // Copy all pattern properties (excluding date fields)
        Object.keys(item).forEach((key) => {
          if (key !== 'date' && key !== 'fullDate' && typeof item[key] === 'number') {
            result[key] = item[key] as number;
          }
        });

        return result;
      }
    }).filter((d): d is ChartDatum => d !== null); // Remove any null entries with type guard

    console.log("PatternTimeline: Chart data transformed", transformed);
    console.log(
      "PatternTimeline: Original dates:",
      normalizedData.map((item: NormalizedItem) => (item.date ?? item.fullDate) as string)
    );
    console.log(
      "PatternTimeline: Transformed dates:",
      transformed.map((item: ChartDatum) => item.date)
    );
    console.log("PatternTimeline: Available data keys:", availableDataKeys);
    console.log("PatternTimeline: First transformed item:", transformed[0]);
    console.log("PatternTimeline: Date validation - checking each date:");
    normalizedData.forEach((item: NormalizedItem, index: number) => {
      const rawDate: string = (item.date ?? item.fullDate ?? "");
      const dateObj = new Date(rawDate);
      console.log(`Date ${index}: "${rawDate}" -> Valid: ${!isNaN(dateObj.getTime())}${!isNaN(dateObj.getTime()) ? ", Parsed: " + dateObj.toISOString() : ""}`);
    });

    return transformed;
  }, [normalizedData, availableDataKeys]);

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
          {series.map((s, index) => (
            <Line
              key={s.dataKey}
              type="monotone"
              dataKey={s.dataKey}
              name={s.name}
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
