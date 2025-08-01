import React from "react";
import { motion } from "framer-motion";
import { Brain, TrendingUp, Shield, Zap } from "lucide-react";
import type { Analysis } from "../../../types/insights";

interface AISummaryCardProps {
    analysis: Analysis;
    firstPatternKey: string;
}

export const AISummaryCard: React.FC<AISummaryCardProps> = ({ analysis, firstPatternKey }) => {
    // Calculate additional metrics for enhanced summary
    const techCount = Object.values(analysis.technologies || {}).flat().length;
    const complexityLevel = analysis.summary.total_patterns > 15 ? "Advanced" : 
                           analysis.summary.total_patterns > 8 ? "Intermediate" : "Basic";
    
    // Enhanced analysis data if available
    const enhancedAnalysis = analysis as any;
    const hasEnhancedData = enhancedAnalysis.security_analysis || enhancedAnalysis.performance_analysis;

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-gradient-to-r from-blue-500/10 via-purple-500/10 to-green-500/10 rounded-lg border p-6"
        >
            <div className="flex items-start gap-4">
                <div className="p-3 rounded-lg bg-gradient-to-br from-blue-500 via-purple-500 to-green-500">
                    <Brain className="w-6 h-6 text-white" />
                </div>
                <div className="flex-1">
                    <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                        AI Analysis Summary
                        {hasEnhancedData && <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">Enhanced</span>}
                    </h3>
                    
                    <div className="space-y-3">
                        <p className="text-sm text-muted-foreground leading-relaxed">
                            Your repository demonstrates <span className="font-medium">{analysis.summary.total_patterns} distinct coding patterns</span> across <span className="font-medium">{analysis.analysis_session.commits_analyzed} commits</span>. 
                            The codebase shows <span className="font-medium">{techCount > 10 ? "high" : techCount > 5 ? "moderate" : "focused"} technological diversity</span> with a complexity level of <span className="font-medium">{complexityLevel}</span>.
                            {analysis.summary.antipatterns_detected > 0 && ` ${analysis.summary.antipatterns_detected} areas have been identified for potential improvement.`}
                        </p>

                        {/* Enhanced Metrics Grid */}
                        {hasEnhancedData && (
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
                                {enhancedAnalysis.security_analysis && (
                                    <div className="flex items-center gap-2 p-3 bg-card rounded-lg border">
                                        <Shield className="w-4 h-4 text-blue-500" />
                                        <div className="text-xs">
                                            <div className="font-medium">Security Score</div>
                                            <div className="text-muted-foreground">{enhancedAnalysis.security_analysis.overall_score}%</div>
                                        </div>
                                    </div>
                                )}
                                
                                {enhancedAnalysis.performance_analysis && (
                                    <div className="flex items-center gap-2 p-3 bg-card rounded-lg border">
                                        <Zap className="w-4 h-4 text-yellow-500" />
                                        <div className="text-xs">
                                            <div className="font-medium">Performance</div>
                                            <div className="text-muted-foreground">Grade {enhancedAnalysis.performance_analysis.performance_grade}</div>
                                        </div>
                                    </div>
                                )}
                                
                                {enhancedAnalysis.architectural_analysis && (
                                    <div className="flex items-center gap-2 p-3 bg-card rounded-lg border">
                                        <TrendingUp className="w-4 h-4 text-green-500" />
                                        <div className="text-xs">
                                            <div className="font-medium">Architecture</div>
                                            <div className="text-muted-foreground">{enhancedAnalysis.architectural_analysis.quality_metrics.grade}</div>
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </motion.div>
    );
};
