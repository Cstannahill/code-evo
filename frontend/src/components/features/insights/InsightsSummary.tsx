import React from "react";
import { Brain } from "lucide-react";
import type { CategorizedInsights } from "../../../types/insights";
import { motion } from "framer-motion";

interface InsightsSummaryProps {
    categorizedInsights: CategorizedInsights;
}

export const InsightsSummary: React.FC<InsightsSummaryProps> = ({ categorizedInsights }) => (
    <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2 }}
        className="bg-card rounded-lg border p-6 "
    >
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Brain className="w-5 h-5" /> AI Insights Summary
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-blue-500/10 rounded-lg">
                <div className="text-2xl font-bold text-blue-500">
                    {categorizedInsights.recommendations.length}
                </div>
                <div className="text-sm text-muted-foreground">Recommendations</div>
            </div>
            <div className="text-center p-4 bg-green-500/10 rounded-lg">
                <div className="text-2xl font-bold text-green-500">
                    {categorizedInsights.achievements.length}
                </div>
                <div className="text-sm text-muted-foreground">Achievements</div>
            </div>
            <div className="text-center p-4 bg-orange-500/10 rounded-lg">
                <div className="text-2xl font-bold text-orange-500">
                    {categorizedInsights.warnings.length}
                </div>
                <div className="text-sm text-muted-foreground">Areas to Improve</div>
            </div>
            <div className="text-center p-4 bg-purple-500/10 rounded-lg">
                <div className="text-2xl font-bold text-purple-500">
                    {categorizedInsights.trends.length}
                </div>
                <div className="text-sm text-muted-foreground">Trends Identified</div>
            </div>
        </div>
    </motion.div>
);
