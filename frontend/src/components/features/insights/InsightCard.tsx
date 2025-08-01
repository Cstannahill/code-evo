import React from "react";
import { motion } from "framer-motion";
import type { Insight, InsightType } from "../../../types/insights";

interface InsightCardProps {
    insight: Insight;
    getIcon: (
        type: InsightType
    ) => React.ComponentType<React.SVGProps<SVGSVGElement>>;
    getColor: (type: InsightType) => string;
}

const safeStringify = (data: unknown): string => {
    try {
        if (typeof data === "object" && data !== null) {
            return JSON.stringify(data, null, 2);
        }
        return String(data);
    } catch {
        return "Unable to display data";
    }
};

export const InsightCard: React.FC<InsightCardProps> = ({
    insight,
    getIcon,
    getColor,
}) => {
    const Icon = getIcon(insight.type);
    const colorClass = getColor(insight.type);
    const [, bgClass] = colorClass.split(" ");

    return (
        <motion.div
            whileHover={{ scale: 1.02 }}
            className={`rounded-lg p-4 ${bgClass}`}
        >
            <div className="flex items-start gap-3">
                <Icon className={`w-5 h-5 mt-0.5 ${colorClass.split(" ")[0]}`} />
                <div className="flex-1">
                    <h4 className="font-medium text-sm">{insight.title}</h4>
                    <p className="text-sm text-muted-foreground mt-1">
                        {insight.description}
                    </p>
                    {insight.data !== undefined && (
                        <div className="mt-3 p-2 bg-background/50 rounded text-xs">
                            <pre>{safeStringify(insight.data)}</pre>
                        </div>
                    )}
                </div>
            </div>
        </motion.div>
    );
};
