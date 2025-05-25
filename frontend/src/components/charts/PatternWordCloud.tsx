import React from "react";
import ReactWordCloud, { type Word } from "react-wordcloud";

interface PatternWordCloudProps {
  /**
   * Array of words with `text` and `value`.
   * Example: [{ text: "react_hooks", value: 10 }, …]
   */
  patterns?: Word[];
  /** Height of the cloud container (px) */
  height?: number;
  /** Width of the cloud container (px) */
  width?: number;
}

export const PatternWordCloud: React.FC<PatternWordCloudProps> = ({
  patterns = [],
  height = 300,
  width = 600,
}) => {
  // If no data, render a placeholder
  if (!patterns.length) {
    return (
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          height,
          color: "#888",
        }}
      >
        No pattern data available
      </div>
    );
  }

  // WordCloud configuration
  const options = {
    rotations: 2,
    rotationAngles: [-90, 0] as [number, number],
    fontSizes: [12, 60] as [number, number],
    // You can add more options here if needed
  };

  return (
    <div style={{ width, height }}>
      <ReactWordCloud words={patterns} options={options} />
    </div>
  );
};
