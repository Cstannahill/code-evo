import React from "react";
import ReactWordcloud from "react-wordcloud";
import { motion } from "framer-motion";

interface PatternWordCloudProps {
  patterns: Record<string, any>;
}

export const PatternWordCloud: React.FC<PatternWordCloudProps> = ({
  patterns,
}) => {
  const words = React.useMemo(() => {
    return Object.entries(patterns).map(([pattern, stats]) => ({
      text: pattern,
      value: stats.occurrences * (stats.is_antipattern ? 0.5 : 1),
      category: stats.category,
    }));
  }, [patterns]);

  const options = {
    colors: ["#3b82f6", "#8b5cf6", "#10b981", "#f59e0b", "#ef4444", "#06b6d4"],
    enableTooltip: true,
    deterministic: true,
    fontFamily: "Inter, sans-serif",
    fontSizes: [20, 80],
    fontStyle: "normal",
    fontWeight: "bold",
    padding: 8,
    rotations: 0,
    scale: "sqrt",
    spiral: "archimedean",
    transitionDuration: 1000,
  };

  const callbacks = {
    onWordClick: (word: any) => {
      console.log(`Clicked on ${word.text}`);
    },
    onWordMouseOver: (word: any) => {
      console.log(`Mouse over ${word.text}`);
    },
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.8 }}
      className="w-full h-96"
    >
      <ReactWordcloud words={words} options={options} callbacks={callbacks} />
    </motion.div>
  );
};
