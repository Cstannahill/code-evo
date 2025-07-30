import React, { useMemo } from "react";
import { motion } from "framer-motion";

interface PatternHeatmapProps {
  data: any;
  width?: number;
  height?: number;
}

interface HeatmapCell {
  pattern: string;
  month: string;
  value: number;
  color: string;
}

export const PatternHeatmap: React.FC<PatternHeatmapProps> = ({
  data,
  width = 800,
  height = 400,
}) => {
  const heatmapData = useMemo(() => {
    if (!data?.pattern_statistics || !data?.pattern_timeline) {
      return { cells: [], patterns: [], months: [] };
    }

    const patterns = Object.keys(data.pattern_statistics).slice(0, 8); // Limit for display
    
    // Normalize timeline data
    let timeline = [];
    if (data.pattern_timeline?.timeline && Array.isArray(data.pattern_timeline.timeline)) {
      timeline = data.pattern_timeline.timeline;
    } else if (Array.isArray(data.pattern_timeline)) {
      timeline = data.pattern_timeline;
    }

    if (patterns.length === 0 || timeline.length === 0) {
      return { cells: [], patterns: [], months: [] };
    }

    const months = timeline.map((t: any) => t.date);
    const cells: HeatmapCell[] = [];

    // Find max value for color scaling
    let maxValue = 0;
    patterns.forEach((pattern) => {
      timeline.forEach((timePoint: any) => {
        const value = timePoint.patterns[pattern] || 0;
        maxValue = Math.max(maxValue, value);
      });
    });

    // Create cells
    patterns.forEach((pattern) => {
      timeline.forEach((timePoint: any) => {
        const value = timePoint.patterns[pattern] || 0;
        const intensity = maxValue > 0 ? value / maxValue : 0;

        // Color based on intensity
        const getColor = (intensity: number) => {
          if (intensity === 0) return "#1F2937"; // gray-800
          if (intensity < 0.3) return "#1E3A8A"; // blue-800
          if (intensity < 0.6) return "#3B82F6"; // blue-500
          if (intensity < 0.8) return "#8B5CF6"; // violet-500
          return "#EC4899"; // pink-500
        };

        cells.push({
          pattern,
          month: timePoint.date,
          value,
          color: getColor(intensity),
        });
      });
    });

    return { cells, patterns, months };
  }, [data]);

  if (heatmapData.cells.length === 0) {
    return (
      <div
        style={{ width, height }}
        className="flex items-center justify-center bg-gray-800 rounded-lg border border-gray-700"
      >
        <div className="text-center text-gray-400">
          <div className="text-4xl mb-2">📊</div>
          <div className="text-sm">No heatmap data available</div>
          <div className="text-xs text-gray-500 mt-1">
            Pattern timeline data needed for heatmap
          </div>
        </div>
      </div>
    );
  }

  const { patterns, months } = heatmapData;
  const cellWidth = Math.max(40, (width - 120) / months.length);
  const cellHeight = Math.max(30, (height - 60) / patterns.length);

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5 }}
      className="bg-gray-800 rounded-lg border border-gray-700 p-4 overflow-auto"
      style={{ width, height }}
    >
      <div className="relative">
        {/* Pattern labels */}
        <div className="absolute left-0 top-12">
          {patterns.map((pattern) => (
            <div
              key={pattern}
              className="text-xs text-gray-300 font-medium truncate"
              style={{
                height: cellHeight,
                width: 100,
                lineHeight: `${cellHeight}px`,
                paddingRight: 8,
              }}
              title={pattern}
            >
              {pattern.replace(/_/g, " ")}
            </div>
          ))}
        </div>

        {/* Month labels */}
        <div className="absolute top-0 left-24">
          {months.map((month: any) => (
            <div
              key={month}
              className="text-xs text-gray-300 font-medium inline-block text-center"
              style={{
                width: cellWidth,
                transform: "rotate(-45deg)",
                transformOrigin: "center",
                marginTop: 16,
              }}
            >
              {month}
            </div>
          ))}
        </div>

        {/* Heatmap cells */}
        <div className="mt-12 ml-24 relative">
          {heatmapData.cells.map((cell, i) => {
            const patternIndex = patterns.indexOf(cell.pattern);
            const monthIndex = months.indexOf(cell.month);

            return (
              <motion.div
                key={`${cell.pattern}-${cell.month}`}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: i * 0.01 }}
                className="absolute border border-gray-600 cursor-pointer hover:border-gray-400 transition-colors"
                style={{
                  left: monthIndex * cellWidth,
                  top: patternIndex * cellHeight,
                  width: cellWidth - 1,
                  height: cellHeight - 1,
                  backgroundColor: cell.color,
                }}
                title={`${cell.pattern}: ${cell.value} occurrences in ${cell.month}`}
              />
            );
          })}
        </div>

        {/* Legend */}
        <div className="absolute bottom-0 right-0 flex items-center gap-2 text-xs text-gray-400">
          <span>Less</span>
          <div className="flex gap-1">
            {["#1F2937", "#1E3A8A", "#3B82F6", "#8B5CF6", "#EC4899"].map(
              (color, i) => (
                <div
                  key={i}
                  className="w-3 h-3 border border-gray-600"
                  style={{ backgroundColor: color }}
                />
              )
            )}
          </div>
          <span>More</span>
        </div>
      </div>
    </motion.div>
  );
};
