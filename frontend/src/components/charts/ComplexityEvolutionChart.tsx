import React, { useMemo } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  Legend,
} from "recharts";
import { motion } from "framer-motion";
import type { PatternInfo, ComplexityChartData } from "../../types/analysis";

interface ComplexityEvolutionChartProps {
  patterns: Record<string, PatternInfo>; // Use PatternInfo for stats
}

export const ComplexityEvolutionChart: React.FC<
  ComplexityEvolutionChartProps
> = ({ patterns }) => {
  const data: ComplexityChartData[] = useMemo(() => {
    const complexityGroups: Record<string, PatternInfo[]> = {
      simple: [],
      intermediate: [],
      advanced: [],
    };

    Object.entries(patterns).forEach(([name, stats]) => {
      const level = stats.complexity_level || "intermediate";
      // Ensure 'name' is part of stats before pushing, or add it if it's not.
      // Assuming PatternInfo might not have 'name' but it's the key.
      const patternWithName: PatternInfo = { ...stats, name };
      complexityGroups[level as keyof typeof complexityGroups].push(
        patternWithName
      );
    });

    return Object.entries(complexityGroups).map(([level, groupPatterns]) => ({
      complexity: level,
      count: groupPatterns.length,
      totalOccurrences: groupPatterns.reduce(
        (sum, p) => sum + (p.occurrences || 0),
        0
      ),
      patterns: groupPatterns, // Now 'patterns' here is PatternInfo[]
    }));
  }, [patterns]);

  const getComplexityColor = (level: string): string => {
    switch (level) {
      case "simple":
        return "#10b981"; // Emerald 500
      case "intermediate":
        return "#f59e0b"; // Amber 500
      case "advanced":
        return "#ef4444"; // Red 500
      default:
        return "#6b7280"; // Gray 500
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5 }}
      className="w-full h-80 bg-gray-800 rounded-lg shadow-xl p-4 border border-gray-700"
    >
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          margin={{ top: 20, right: 30, left: 20, bottom: 20 }}
        >
          <CartesianGrid
            strokeDasharray="3 3"
            className="stroke-gray-700 opacity-50"
          />
          <XAxis
            dataKey="complexity"
            className="text-xs"
            tick={{ fill: "#9CA3AF" }} // Dark theme tick color
            tickFormatter={(value: string) =>
              value.charAt(0).toUpperCase() + value.slice(1)
            }
          />
          <YAxis className="text-xs" tick={{ fill: "#9CA3AF" }} />
          <Tooltip
            contentStyle={{
              backgroundColor: "#1F2937", // Dark theme background
              borderColor: "#374151", // Dark theme border
              borderRadius: "0.5rem",
              color: "#E5E7EB", // Dark theme text
            }}
            cursor={{ fill: "rgba(255, 255, 255, 0.1)" }}
            content={({ active, payload }) => {
              if (active && payload && payload.length) {
                const tooltipData = payload[0].payload as ComplexityChartData;
                return (
                  <div className="p-3 space-y-1 bg-gray-700 rounded-md shadow-lg border border-gray-600">
                    <p className="font-semibold capitalize text-gray-100">
                      {tooltipData.complexity} Complexity
                    </p>
                    <p className="text-sm text-gray-300">
                      Patterns: {tooltipData.count}
                    </p>
                    <p className="text-sm text-gray-300">
                      Total Occurrences: {tooltipData.totalOccurrences}
                    </p>
                    {tooltipData.patterns &&
                      tooltipData.patterns.length > 0 && (
                        <div className="text-xs text-gray-400 mt-2 pt-1 border-t border-gray-600">
                          <p className="font-medium text-gray-300 mb-1">
                            Top Patterns:
                          </p>
                          {tooltipData.patterns
                            .slice(0, 3)
                            .map((p: PatternInfo) => (
                              <div key={p.name} className="truncate">
                                {p.name} ({p.occurrences})
                              </div>
                            ))}
                          {tooltipData.patterns.length > 3 && (
                            <div className="italic">
                              ...and {tooltipData.patterns.length - 3} more
                            </div>
                          )}
                        </div>
                      )}
                  </div>
                );
              }
              return null;
            }}
          />
          <Legend wrapperStyle={{ color: "#9CA3AF", paddingTop: "10px" }} />
          <Bar dataKey="count" name="Pattern Count">
            {data.map((entry, index) => (
              <Cell
                key={`cell-count-${index}`}
                fill={getComplexityColor(entry.complexity)}
              />
            ))}
          </Bar>
          <Bar
            dataKey="totalOccurrences"
            name="Total Occurrences"
            opacity={0.7}
          >
            {data.map((entry, index) => (
              <Cell
                key={`cell-occurrences-${index}`}
                fill={getComplexityColor(entry.complexity)}
                // Slightly different shade or pattern for the second bar if desired
                // For now, using the same color but with overall bar opacity set
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </motion.div>
  );
};
