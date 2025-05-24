import React from "react";
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import { type Technology } from "../../types/api";
import { motion } from "framer-motion";

interface TechnologyRadarProps {
  technologies: {
    language: Technology[];
    framework: Technology[];
    library: Technology[];
    tool: Technology[];
  };
}

export const TechnologyRadar: React.FC<TechnologyRadarProps> = ({
  technologies,
}) => {
  const data = React.useMemo(() => {
    const categories = ["Languages", "Frameworks", "Libraries", "Tools"];
    return categories.map((category) => {
      const key = category
        .toLowerCase()
        .slice(0, -1) as keyof typeof technologies;
      const techs = technologies[key] || [];
      return {
        category,
        count: techs.length,
        usage: techs.reduce((sum, t) => sum + t.usage_count, 0),
      };
    });
  }, [technologies]);

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5, delay: 0.2 }}
      className="w-full h-80"
    >
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart data={data}>
          <PolarGrid className="stroke-muted" />
          <PolarAngleAxis dataKey="category" className="text-xs" />
          <PolarRadiusAxis className="text-xs" />
          <Tooltip />
          <Radar
            name="Technology Count"
            dataKey="count"
            stroke="#3b82f6"
            fill="#3b82f6"
            fillOpacity={0.6}
          />
          <Radar
            name="Total Usage"
            dataKey="usage"
            stroke="#8b5cf6"
            fill="#8b5cf6"
            fillOpacity={0.4}
          />
        </RadarChart>
      </ResponsiveContainer>
    </motion.div>
  );
};
