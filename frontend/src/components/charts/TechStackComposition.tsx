import React, { useMemo, useState } from "react";
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  Sector,
} from "recharts";
import type { Payload as RechartsTooltipPayload } from "recharts/types/component/DefaultTooltipContent";
import { motion } from "framer-motion";
import type {
  TechnologiesByCategory,
  TechStackPieData,
} from "../../types/analysis";

interface TechStackCompositionProps {
  technologies: TechnologiesByCategory;
}

// Props that Recharts passes to the activeShape function for a Pie.
interface PieActiveShapeProps {
  cx: number;
  cy: number;
  midAngle: number;
  innerRadius: number;
  outerRadius: number;
  startAngle: number;
  endAngle: number;
  fill: string;
  stroke?: string;
  payload: TechStackPieData;
  percent: number;
  value: number;
  name: string;
}

const renderActiveShape = (props: unknown): React.ReactElement => {
  // Type assertion inside the function
  const {
    cx,
    cy,
    innerRadius,
    outerRadius,
    startAngle,
    endAngle,
    fill,
    payload,
    percent,
  } = props as PieActiveShapeProps;

  return (
    <g>
      <text
        x={cx}
        y={cy - 18}
        textAnchor="middle"
        fill={fill}
        className="text-base font-bold drop-shadow-sm"
        dominantBaseline="central"
      >
        {payload.name}
      </text>
      <text
        x={cx}
        y={cy + 2}
        textAnchor="middle"
        fill={"#E5E7EB"}
        className="text-sm"
      >
        {`${(percent * 100).toFixed(0)}% of usage`}
      </text>
      <text
        x={cx}
        y={cy + 20}
        textAnchor="middle"
        fill={"#9CA3AF"}
        className="text-xs"
      >
        {`${payload.count} tech${payload.count !== 1 ? "s" : ""}`}
      </text>

      <Sector
        cx={cx}
        cy={cy}
        innerRadius={innerRadius}
        outerRadius={outerRadius}
        startAngle={startAngle}
        endAngle={endAngle}
        fill={fill}
        stroke={"#374151"}
        strokeWidth={1}
      />
      <Sector
        cx={cx}
        cy={cy}
        startAngle={startAngle}
        endAngle={endAngle}
        innerRadius={outerRadius + 4}
        outerRadius={outerRadius + 8}
        fill={fill}
        opacity={0.7}
      />
    </g>
  );
};

export const TechStackComposition: React.FC<TechStackCompositionProps> = ({
  technologies,
}) => {
  const [activeIndex, setActiveIndex] = useState(0);

  const data: TechStackPieData[] = useMemo(() => {
    const categories = [
      "language",
      "framework",
      "library",
      "tool",
      "database",
      "platform",
      "other",
    ];
    return categories
      .map((category) => {
        const techs = technologies[category] || [];
        return {
          name: category.charAt(0).toUpperCase() + category.slice(1),
          value: techs.reduce((sum, tech) => sum + tech.usage_count, 0),
          count: techs.length,
          technologies: techs,
        };
      })
      .filter((item) => item.value > 0);
  }, [technologies]);

  const COLORS = [
    "#3b82f6",
    "#8b5cf6",
    "#10b981",
    "#f59e0b",
    "#ef4444",
    "#6366f1",
    "#ec4899",
  ];

  const onPieEnter = (_: unknown, index: number): void => {
    setActiveIndex(index);
  };

  if (data.length === 0) {
    return (
      <div className="w-full h-80 flex items-center justify-center text-gray-500 bg-gray-800 rounded-lg shadow-xl border border-gray-700">
        No technology stack data available to display.
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5 }}
      className="w-full h-80 bg-gray-800 rounded-lg shadow-xl p-2 border border-gray-700"
    >
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            activeIndex={activeIndex}
            activeShape={
              renderActiveShape as (props: unknown) => React.ReactElement
            } // Cast here for Recharts compatibility
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={"65%"}
            outerRadius={"85%"}
            fill="#8884d8" // Default fill, overridden by Cell
            dataKey="value"
            nameKey="name"
            onMouseEnter={onPieEnter}
            paddingAngle={data.length > 1 ? 2 : 0}
          >
            {data.map((_entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={COLORS[index % COLORS.length]}
                stroke={"#374151"} // Dark theme stroke for cells
                strokeWidth={1}
              />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              backgroundColor: "#1F2937", // Dark theme background
              borderColor: "#374151", // Dark theme border
              borderRadius: "0.5rem",
              boxShadow: "0 4px 6px rgba(0,0,0,0.1)",
            }}
            itemStyle={{
              color: "#E5E7EB", // Dark theme text
            }}
            cursor={{ fill: "rgba(255, 255, 255, 0.1)" }}
            formatter={(
              _value: number, // This is entry.value
              _name: string, // This is entry.name
              entry: RechartsTooltipPayload<number, string>
            ): [React.ReactNode, React.ReactNode] => {
              const techDataPayload = entry.payload as TechStackPieData;
              const formattedName = techDataPayload.name; // e.g. "Language"
              const formattedValue = `${techDataPayload.count} tech${
                techDataPayload.count !== 1 ? "s" : ""
              } (${(
                ((entry.value || 0) /
                  (data.reduce((acc, d) => acc + d.value, 0) || 1)) *
                100
              ).toFixed(0)}%)`;

              // Display category name and then details about it
              return [formattedValue, formattedName];
            }}
          />
        </PieChart>
      </ResponsiveContainer>
    </motion.div>
  );
};

export default TechStackComposition;
