import React from "react";
import { BookOpen } from "lucide-react";
import { motion } from "framer-motion";
import type { PathStep } from "../../../types/insights";

interface LearningPathSectionProps {
    analysis: import("../../../types/insights").Analysis;
}

export const generateLearningPath = (analysis: import("../../../types/insights").Analysis): PathStep[] => {
    const paths: PathStep[] = [];
    if (analysis.security_analysis) {
        paths.push({
            title: "Security Best Practices",
            description: "Implement security patterns and address vulnerabilities",
            difficulty: "Intermediate",
            estimatedTime: "3-4 weeks",
        });
    }
    if (analysis.summary.antipatterns_detected > 0) {
        paths.push({
            title: "Refactoring Anti-patterns",
            description: "Focus on eliminating detected anti-patterns to improve code quality",
            difficulty: "Intermediate",
            estimatedTime: "2-3 weeks",
        });
    }
    const techCount = Object.values(analysis.technologies || {}).flat().length;
    if (techCount < 5) {
        paths.push({
            title: "Explore Modern Frameworks",
            description: "Expand your technology stack with modern frameworks and tools",
            difficulty: "Beginner",
            estimatedTime: "4-6 weeks",
        });
    }
    if (analysis.performance_analysis) {
        paths.push({
            title: "Performance Optimization",
            description: "Optimize code performance and efficiency",
            difficulty: "Advanced",
            estimatedTime: "4-5 weeks",
        });
    }
    paths.push({
        title: "Advanced Pattern Implementation",
        description: "Master advanced design patterns for scalable architecture",
        difficulty: "Advanced",
        estimatedTime: "6-8 weeks",
    });
    return paths;
};

export const LearningPathSection: React.FC<LearningPathSectionProps> = ({ analysis }) => {
    const steps = generateLearningPath(analysis);
    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="bg-card rounded-lg border p-6"
        >
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <BookOpen className="w-5 h-5" /> Recommended Learning Path
            </h3>
            <div className="space-y-4">
                {steps.map((step, idx) => (
                    <div key={idx} className="flex items-start gap-4">
                        <div
                            className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${idx === 0
                                ? "bg-primary text-primary-foreground"
                                : "bg-muted text-muted-foreground"
                                }`}
                        >
                            {idx + 1}
                        </div>
                        <div className="flex-1">
                            <h4 className="font-medium">{step.title}</h4>
                            <p className="text-sm text-muted-foreground mt-1">
                                {step.description}
                            </p>
                            <div className="flex items-center gap-4 mt-2">
                                <span className="text-xs text-muted-foreground">
                                    Difficulty: {step.difficulty}
                                </span>
                                <span className="text-xs text-muted-foreground">
                                    Time: {step.estimatedTime}
                                </span>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </motion.div>
    );
};
