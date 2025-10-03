import React, { useState, useEffect } from "react";

interface Word {
  text: string;
  value: number;
}

interface PatternWordCloudProps {
  patterns?: Word[];
  height?: number;
  width?: number | string;
}

// Custom word cloud implementation that's more reliable
export const PatternWordCloud: React.FC<PatternWordCloudProps> = ({
  patterns = [],
  height = 300,
  width = "100%",
}) => {
  const [processedPatterns, setProcessedPatterns] = useState<Word[]>([]);

  // Process and validate the data
  useEffect(() => {
    console.log("PatternWordCloud: Received patterns:", patterns);

    if (!Array.isArray(patterns) || patterns.length === 0) {
      console.log("PatternWordCloud: No patterns or empty array");
      setProcessedPatterns([]);
      return;
    }

    const processed = patterns
      .filter((p) => p && p.text && typeof p.value === "number" && p.value > 0)
      .map((p) => ({
        text: p.text.replace(/_/g, " "), // Make more readable
        value: p.value,
      }))
      .sort((a, b) => b.value - a.value) // Sort by frequency
      .slice(0, 50); // Limit to top 50 patterns

    console.log("PatternWordCloud: Processed patterns:", processed);
    setProcessedPatterns(processed);
  }, [patterns]);

  // Fallback to custom implementation if react-wordcloud fails
  const CustomWordCloud = ({ words }: { words: Word[] }) => {
    if (words.length === 0) {
      return (
        <div className="flex items-center justify-center h-full text-gray-400">
          <div className="text-center">
            <div className="text-4xl mb-2">🔍</div>
            <div className="text-sm">No pattern data available</div>
          </div>
        </div>
      );
    }

    const maxValue = Math.max(...words.map((w) => w.value));
    const minValue = Math.min(...words.map((w) => w.value));

    const getFontSize = (value: number) => {
      const ratio = (value - minValue) / (maxValue - minValue || 1);
      return Math.max(12, Math.min(48, 12 + ratio * 36));
    };

    const getColor = (index: number) => {
      const colors = [
        "#3B82F6",
        "#8B5CF6",
        "#10B981",
        "#F59E0B",
        "#EF4444",
        "#06B6D4",
        "#EC4899",
        "#84CC16",
      ];
      return colors[index % colors.length];
    };

    return (
      <div
        className="flex flex-wrap items-center justify-center gap-3 p-6"
        style={{ height, width: "100%", minHeight: height }}
      >
        {words.map((word, index) => (
          <span
            key={word.text}
            className="font-semibold cursor-pointer hover:opacity-80 transition-opacity"
            style={{
              fontSize: `${getFontSize(word.value)}px`,
              color: getColor(index),
              lineHeight: 1.2,
            }}
            title={`${word.text}: ${word.value} occurrences`}
          >
            {word.text}
          </span>
        ))}
      </div>
    );
  };

  // Use custom implementation only - react-wordcloud is causing crashes
  // The custom implementation is more reliable and provides better control

  // Use custom implementation
  return (
    <div
      style={{ width, height, minHeight: height }}
      className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden"
    >
      <CustomWordCloud words={processedPatterns} />
    </div>
  );
};

