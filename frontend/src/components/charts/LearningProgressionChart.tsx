import React from "react";
import type { RepositoryAnalysis } from "../../types/api";

interface LearningProgressionChartProps {
  analysis: RepositoryAnalysis;
}

export const LearningProgressionChart: React.FC<
  LearningProgressionChartProps
> = ({ analysis }) => {
  return (
    <div className="flex items-center justify-center h-64 text-muted-foreground">
      <div className="text-center">
        <p>Learning Progression Chart</p>
        <p className="text-sm">Coming soon...</p>
      </div>
    </div>
  );
};
