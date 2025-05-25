export const PatternWordCloud: React.FC<PatternWordCloudProps> = ({
  patterns = [],
  height = 300,
  width = 600,
}) => {
  // Filter and validate patterns data
  const validPatterns = patterns.filter(
    (pattern) =>
      pattern &&
      pattern.text &&
      typeof pattern.text === "string" &&
      pattern.text.trim().length > 0 &&
      pattern.value &&
      typeof pattern.value === "number" &&
      pattern.value > 0
  );

  // If no valid data, render a placeholder
  if (!validPatterns.length) {
    return (
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          height,
          color: "#888",
          fontSize: "14px",
        }}
      >
        {patterns.length > 0
          ? "Processing pattern data..."
          : "No pattern data available"}
      </div>
    );
  }

  // WordCloud configuration with better error handling
  const options = {
    rotations: 2,
    rotationAngles: [-90, 0] as [number, number],
    fontSizes: [12, 60] as [number, number],
    enableTooltip: true,
    deterministic: true, // Makes rendering more stable
    fontFamily: "Arial, sans-serif",
    fontWeight: "normal",
    padding: 2,
    scale: "sqrt" as const,
    spiral: "archimedean" as const,
  };

  try {
    return (
      <div style={{ width, height }}>
        <ReactWordCloud words={validPatterns} options={options} />
      </div>
    );
  } catch (error) {
    console.warn("WordCloud render error:", error);
    return (
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          height,
          color: "#888",
          fontSize: "14px",
        }}
      >
        Pattern visualization temporarily unavailable
      </div>
    );
  }
};
