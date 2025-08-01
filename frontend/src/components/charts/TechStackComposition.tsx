import React, { useMemo, useState } from "react";
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  Sector,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
} from "recharts";
import type { Payload as RechartsTooltipPayload } from "recharts/types/component/DefaultTooltipContent";
import { motion, AnimatePresence } from "framer-motion";
import { X, ChevronRight, BarChart3, List } from "lucide-react";
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
  const [selectedCategory, setSelectedCategory] = useState<TechStackPieData | null>(null);
  const [drillDownView, setDrillDownView] = useState<'chart' | 'list'>('list');

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
        const techs = technologies[category as keyof TechnologiesByCategory] || [];
        return {
          name: category.charAt(0).toUpperCase() + category.slice(1),
          value: techs.reduce((sum: number, tech: any) => sum + tech.usage_count, 0),
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

  const onPieClick = (_: unknown, index: number): void => {
    setSelectedCategory(data[index]);
  };

  const closeDrillDown = (): void => {
    setSelectedCategory(null);
  };

  // Prepare drill-down data
  const drillDownData = useMemo(() => {
    if (!selectedCategory) return [];
    
    return selectedCategory.technologies
      .map((tech: any) => ({
        name: tech.name || tech,
        usage: tech.usage_count || 1,
        version: tech.version,
        firstSeen: tech.first_seen,
        lastSeen: tech.last_seen,
      }))
      .sort((a, b) => b.usage - a.usage)
      .slice(0, 15); // Limit to top 15 for readability
  }, [selectedCategory]);

  // Drill-down list component
  const DrillDownList = () => (
    <div className="space-y-2 max-h-64 overflow-y-auto">
      {drillDownData.map((tech, index) => (
        <motion.div
          key={tech.name}
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: index * 0.05 }}
          className="flex items-center justify-between p-2 bg-muted/50 rounded-lg hover:bg-muted/70 transition-colors"
        >
          <div className="flex-1">
            <div className="font-medium text-sm">{tech.name}</div>
            {tech.version && (
              <div className="text-xs text-muted-foreground">v{tech.version}</div>
            )}
          </div>
          <div className="text-right">
            <div className="text-sm font-medium">{tech.usage}</div>
            <div className="text-xs text-muted-foreground">uses</div>
          </div>
        </motion.div>
      ))}
    </div>
  );

  // Drill-down chart component
  const DrillDownChart = () => (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={drillDownData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-muted opacity-30" />
        <XAxis 
          dataKey="name" 
          tick={{ fontSize: 10 }}
          angle={-45}
          textAnchor="end"
          height={60}
        />
        <YAxis tick={{ fontSize: 10 }} />
        <Tooltip
          contentStyle={{
            backgroundColor: "hsl(var(--popover))",
            border: "1px solid hsl(var(--border))",
            borderRadius: "6px",
          }}
        />
        <Bar 
          dataKey="usage" 
          fill={COLORS[activeIndex % COLORS.length]}
          radius={[2, 2, 0, 0]}
        />
      </BarChart>
    </ResponsiveContainer>
  );

  if (data.length === 0) {
    return (
      <div className="w-full h-80 flex items-center justify-center text-muted-foreground bg-card rounded-lg shadow-xl border">
        No technology stack data available to display.
      </div>
    );
  }

  return (
    <div className="relative">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
        className="w-full h-80 bg-card rounded-lg shadow-xl p-2 border"
      >
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              activeIndex={activeIndex}
              activeShape={
                renderActiveShape as (props: unknown) => React.ReactElement
              }
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={"65%"}
              outerRadius={"85%"}
              fill="#8884d8"
              dataKey="value"
              nameKey="name"
              onMouseEnter={onPieEnter}
              onClick={onPieClick}
              paddingAngle={data.length > 1 ? 2 : 0}
              style={{ cursor: 'pointer' }}
            >
              {data.map((_entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={COLORS[index % COLORS.length]}
                  stroke={"hsl(var(--border))"}
                  strokeWidth={1}
                />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                backgroundColor: "hsl(var(--popover))",
                borderColor: "hsl(var(--border))",
                borderRadius: "0.5rem",
              }}
              itemStyle={{
                color: "hsl(var(--popover-foreground))",
              }}
              cursor={{ fill: "rgba(255, 255, 255, 0.1)" }}
              formatter={(
                _value: number,
                _name: string,
                entry: RechartsTooltipPayload<number, string>
              ): [React.ReactNode, React.ReactNode] => {
                const techDataPayload = entry.payload as TechStackPieData;
                const formattedName = techDataPayload.name;
                const formattedValue = `${techDataPayload.count} tech${
                  techDataPayload.count !== 1 ? "s" : ""
                } (${(
                  ((entry.value || 0) /
                    (data.reduce((acc, d) => acc + d.value, 0) || 1)) *
                  100
                ).toFixed(0)}%) - Click to explore`;

                return [formattedValue, formattedName];
              }}
            />
          </PieChart>
        </ResponsiveContainer>
      </motion.div>

      {/* Drill-down overlay */}
      <AnimatePresence>
        {selectedCategory && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-card/95 backdrop-blur-sm rounded-lg border flex flex-col"
          >
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b">
              <div className="flex items-center gap-2">
                <ChevronRight className="w-4 h-4 text-muted-foreground" />
                <h3 className="font-semibold">{selectedCategory.name} Technologies</h3>
                <span className="text-sm text-muted-foreground">
                  ({selectedCategory.count} items)
                </span>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setDrillDownView(drillDownView === 'list' ? 'chart' : 'list')}
                  className="p-1.5 hover:bg-muted rounded transition-colors"
                  title={`Switch to ${drillDownView === 'list' ? 'chart' : 'list'} view`}
                >
                  {drillDownView === 'list' ? (
                    <BarChart3 className="w-4 h-4" />
                  ) : (
                    <List className="w-4 h-4" />
                  )}
                </button>
                <button
                  onClick={closeDrillDown}
                  className="p-1.5 hover:bg-muted rounded transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Content */}
            <div className="flex-1 p-4 overflow-hidden">
              {drillDownView === 'list' ? <DrillDownList /> : <DrillDownChart />}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default TechStackComposition;
