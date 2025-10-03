import React, { useState } from "react";
import { motion } from "framer-motion";
import { AlertTriangle, Info } from "lucide-react";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";

interface PatternDeepDiveProps {
  patterns: Record<string, any>;
  occurrences: any[];
}

export const PatternDeepDive: React.FC<PatternDeepDiveProps> = ({
  patterns,
  occurrences,
}) => {
  const [selectedPattern, setSelectedPattern] = useState<string | null>(null);

  const patternList = Object.entries(patterns).map(([name, stats]) => ({
    name,
    ...stats,
    examples: occurrences.filter((o) => o.pattern_name === name),
  }));

  const getPatternInsights = (pattern: any) => {
    const insights = [];

    if (pattern.occurrences > 10) {
      insights.push({
        type: "info",
        message: "This pattern is heavily used throughout the codebase",
      });
    }

    if (pattern.is_antipattern) {
      insights.push({
        type: "warning",
        message: "This is identified as an anti-pattern. Consider refactoring.",
      });
    }

    if (pattern.complexity_level === "advanced") {
      insights.push({
        type: "info",
        message:
          "Advanced pattern usage indicates sophisticated code architecture",
      });
    }

    return insights;
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Pattern List */}
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-muted-foreground mb-3">
            Select a pattern to analyze
          </h4>
          <div className="space-y-2">
            {patternList.map((pattern) => (
              <motion.button
                key={pattern.name}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => setSelectedPattern(pattern.name)}
                className={`w-full text-left p-3 rounded-lg border transition-colors ${selectedPattern === pattern.name
                    ? "bg-primary/10 border-primary"
                    : "bg-card hover:bg-accent/50"
                  }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-medium">{pattern.name}</span>
                  <span className="text-sm text-muted-foreground">
                    {pattern.occurrences}x
                  </span>
                </div>
                <div className="flex items-center gap-2 mt-1">
                  <span
                    className={`text-xs px-2 py-0.5 rounded-full ${pattern.is_antipattern
                        ? "bg-orange-500/20 text-orange-500"
                        : "bg-green-500/20 text-green-500"
                      }`}
                  >
                    {pattern.category}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    {pattern.complexity_level}
                  </span>
                </div>
              </motion.button>
            ))}
          </div>
        </div>

        {/* Pattern Details */}
        {selectedPattern && (
          <div className="lg:col-span-2 space-y-4">
            <div className="bg-accent/50 rounded-lg p-4">
              <h3 className="text-lg font-semibold mb-2">{selectedPattern}</h3>
              <div className="grid grid-cols-3 gap-4 mt-4">
                <div>
                  <p className="text-sm text-muted-foreground">Category</p>
                  <p className="font-medium">
                    {patterns[selectedPattern].category}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Complexity</p>
                  <p className="font-medium">
                    {patterns[selectedPattern].complexity_level}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Occurrences</p>
                  <p className="font-medium">
                    {patterns[selectedPattern].occurrences}
                  </p>
                </div>
              </div>
            </div>

            {/* Insights */}
            <div className="space-y-2">
              {getPatternInsights(patterns[selectedPattern]).map(
                (insight, i) => (
                  <div
                    key={i}
                    className={`flex items-start gap-3 p-3 rounded-lg ${insight.type === "warning"
                        ? "bg-orange-500/10 text-orange-500"
                        : "bg-blue-500/10 text-blue-500"
                      }`}
                  >
                    {insight.type === "warning" ? (
                      <AlertTriangle className="w-4 h-4 mt-0.5" />
                    ) : (
                      <Info className="w-4 h-4 mt-0.5" />
                    )}
                    <p className="text-sm">{insight.message}</p>
                  </div>
                )
              )}
            </div>

            {/* Code Examples */}
            <div className="space-y-4">
              <h4 className="text-sm font-medium text-muted-foreground">
                Example Occurrences
              </h4>
              {patternList
                .find((p) => p.name === selectedPattern)
                ?.examples.slice(0, 3)
                .map((example: any, i: number) => (
                  <div key={i} className="bg-card rounded-lg border p-4">
                    <div className="flex items-center justify-between mb-2">
                      <code className="text-xs text-muted-foreground">
                        {example.file_path}
                      </code>
                      <span className="text-xs text-muted-foreground">
                        Confidence:{" "}
                        {(example.confidence_score * 100).toFixed(0)}%
                      </span>
                    </div>
                    {example.code_snippet && (
                      <SyntaxHighlighter
                        language="javascript"
                        style={oneDark}
                        customStyle={{
                          margin: 0,
                          borderRadius: "0.5rem",
                          fontSize: "0.75rem",
                        }}
                      >
                        {example.code_snippet}
                      </SyntaxHighlighter>
                    )}
                  </div>
                ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
