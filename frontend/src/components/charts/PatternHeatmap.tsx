import React, { useMemo } from "react";
import { scaleLinear } from "@visx/scale";
import { HeatmapRect } from "@visx/heatmap";
import { motion } from "framer-motion";
import * as Tooltip from "@radix-ui/react-tooltip";

interface PatternHeatmapProps {
  data: any;
  width?: number;
  height?: number;
}

export const PatternHeatmap: React.FC<PatternHeatmapProps> = ({
  data,
  width = 800,
  height = 400,
}) => {
  const heatmapData = useMemo(() => {
    // Transform pattern timeline data into heatmap format
    const patterns = Object.keys(data.pattern_statistics);
    const timeline = data.pattern_timeline.timeline;

    return patterns.map((pattern, i) => ({
      bin: pattern,
      bins: timeline.map((t) => ({
        bin: t.date,
        count: t.patterns[pattern] || 0,
      })),
    }));
  }, [data]);

  const xScale = useMemo(
    () =>
      scaleLinear({
        domain: [0, heatmapData[0]?.bins.length || 0],
      }),
    [heatmapData]
  );

  const yScale = useMemo(
    () =>
      scaleLinear({
        domain: [0, heatmapData.length],
      }),
    [heatmapData]
  );

  const colorScale = scaleLinear({
    domain: [
      0,
      Math.max(...heatmapData.flatMap((d) => d.bins.map((b) => b.count))),
    ],
    range: ["#1a1a2e", "#3b82f6", "#8b5cf6"],
  });

  const binWidth = width / (heatmapData[0]?.bins.length || 1);
  const binHeight = height / heatmapData.length;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5 }}
      className="relative"
    >
      <svg width={width} height={height}>
        <HeatmapRect
          data={heatmapData}
          xScale={(d) => xScale(d) ?? 0}
          yScale={(d) => yScale(d) ?? 0}
          colorScale={colorScale}
          binWidth={binWidth}
          binHeight={binHeight}
          gap={2}
        >
          {(heatmap) =>
            heatmap.map((heatmapBins) =>
              heatmapBins.map((bin) => (
                <Tooltip.Provider key={`${bin.row}-${bin.column}`}>
                  <Tooltip.Root>
                    <Tooltip.Trigger asChild>
                      <rect
                        className="cursor-pointer transition-opacity hover:opacity-80"
                        width={bin.width}
                        height={bin.height}
                        x={bin.x}
                        y={bin.y}
                        fill={bin.color}
                        fillOpacity={bin.opacity}
                      />
                    </Tooltip.Trigger>
                    <Tooltip.Portal>
                      <Tooltip.Content
                        className="bg-popover px-3 py-2 rounded-md shadow-lg border text-sm"
                        sideOffset={5}
                      >
                        <div className="font-semibold">{bin.bin}</div>
                        <div className="text-muted-foreground">
                          Count: {bin.count}
                        </div>
                        <Tooltip.Arrow className="fill-popover" />
                      </Tooltip.Content>
                    </Tooltip.Portal>
                  </Tooltip.Root>
                </Tooltip.Provider>
              ))
            )
          }
        </HeatmapRect>
      </svg>
    </motion.div>
  );
};
