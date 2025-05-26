import React, { useState, useEffect } from "react";

interface Word {
  text: string;
  value: number;
}

interface PatternWordCloudProps {
  patterns?: Word[];
  height?: number;
  width?: number;
}

// Custom word cloud implementation that's more reliable
export const PatternWordCloud: React.FC<PatternWordCloudProps> = ({
  patterns = [],
  height = 300,
  width = 600,
}) => {
  const [processedPatterns, setProcessedPatterns] = useState<Word[]>([]);
  const [useReactWordCloud, setUseReactWordCloud] = useState(true);

  // Process and validate the data
  useEffect(() => {
    if (!Array.isArray(patterns) || patterns.length === 0) {
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
        className="flex flex-wrap items-center justify-center gap-2 p-4"
        style={{ height, width }}
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

  // Try to use react-wordcloud, fall back to custom implementation
  if (useReactWordCloud && processedPatterns.length > 0) {
    try {
      // Dynamic import to avoid build issues
      const ReactWordCloud = React.lazy(() => import("react-wordcloud"));

      return (
        <div
          style={{ width, height }}
          className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden"
        >
          <React.Suspense
            fallback={<CustomWordCloud words={processedPatterns} />}
          >
            <ErrorBoundary
              fallback={<CustomWordCloud words={processedPatterns} />}
              onError={() => setUseReactWordCloud(false)}
            >
              <ReactWordCloud
                words={processedPatterns}
                options={{
                  rotations: 2,
                  rotationAngles: [-45, 0] as [number, number],
                  fontSizes: [14, 64] as [number, number],
                  fontFamily: "Inter, system-ui, sans-serif",
                  fontWeight: "600",
                  padding: 4,
                  spiral: "archimedean" as const,
                  scale: "sqrt" as const,
                  transitionDuration: 1000,
                  colors: [
                    "#3B82F6",
                    "#8B5CF6",
                    "#10B981",
                    "#F59E0B",
                    "#EF4444",
                    "#06B6D4",
                    "#EC4899",
                    "#84CC16",
                  ],
                }}
                callbacks={{
                  onWordClick: (word: Word) => {
                    console.log(
                      `Clicked pattern: ${word.text} (${word.value} occurrences)`
                    );
                  },
                }}
              />
            </ErrorBoundary>
          </React.Suspense>
        </div>
      );
    } catch (error) {
      console.error("Failed to load react-wordcloud:", error);
      setUseReactWordCloud(false);
    }
  }

  // Use custom implementation
  return (
    <div
      style={{ width, height }}
      className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden"
    >
      <CustomWordCloud words={processedPatterns} />
    </div>
  );
};

// Simple error boundary component
class ErrorBoundary extends React.Component<
  {
    children: React.ReactNode;
    fallback: React.ReactNode;
    onError?: () => void;
  },
  { hasError: boolean }
> {
  constructor(props: any) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(_: Error) {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("WordCloud Error:", error, errorInfo);
    this.props.onError?.();
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback;
    }

    return this.props.children;
  }
}
