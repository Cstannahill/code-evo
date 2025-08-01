import React from "react";
import type { Insight, InsightType } from "../../../types/insights";
import { InsightCard } from "./InsightCard";

interface InsightsCategorySectionProps {
    title: string;
    icon: React.ReactNode;
    count: number;
    insights: Insight[];
    getIcon: (type: InsightType) => React.ComponentType<React.SVGProps<SVGSVGElement>>;
    getColor: (type: InsightType) => string;
}

export const InsightsCategorySection: React.FC<InsightsCategorySectionProps> = ({
    title,
    icon,
    count,
    insights,
    getIcon,
    getColor,
}) => (
    <div className="space-y-4">
        <h4 className="text-sm font-medium text-muted-foreground flex items-center gap-2">
            {icon} {title} ({count})
        </h4>
        <div className="space-y-3">
            {insights.map((insight, idx) => (
                <InsightCard
                    key={idx}
                    insight={insight}
                    getIcon={getIcon}
                    getColor={getColor}
                />
            ))}
        </div>
    </div>
);
