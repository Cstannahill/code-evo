import { useMemo } from "react";
import type {
  RepositoryAnalysisResponse,
  RepositoryAnalysis,
  Technology,
} from "../types/api";
import logger, { type LogContext } from "../lib/logger";

export const useTransformAnalysis = (
  rawData: RepositoryAnalysisResponse | null
): RepositoryAnalysis | null =>
  useMemo<RepositoryAnalysis | null>(() => {
    if (!rawData) return null;
    logger.info("useTransformAnalysis – rawData", {
      rawData,
    } as unknown as LogContext);
    // Build pattern_stats with the required 'name' property
    const patternStats: Record<
      string,
      {
        name: string;
        category: string;
        occurrences: number;
        complexity_level: string;
        is_antipattern: boolean;
      }
    > = {};
    const timelineMap: Record<string, Record<string, number>> = {};

    rawData.patterns.forEach(({ pattern_name, detected_at }) => {
      if (!patternStats[pattern_name]) {
        patternStats[pattern_name] = {
          name: pattern_name,
          category: pattern_name.includes("react")
            ? "react"
            : pattern_name.includes("async")
            ? "async"
            : pattern_name.includes("javascript")
            ? "javascript"
            : "other",
          occurrences: 0,
          complexity_level: "intermediate",
          is_antipattern: false,
        };
      }
      patternStats[pattern_name].occurrences++;

      const month = detected_at.slice(0, 7); // YYYY-MM
      if (!timelineMap[month]) timelineMap[month] = {};
      timelineMap[month][pattern_name] =
        (timelineMap[month][pattern_name] || 0) + 1;
    });

    const timelineArray = Object.entries(timelineMap)
      .map(([date, patterns]) => ({ date, patterns }))
      .sort((a, b) => a.date.localeCompare(b.date));

    // Shape technologies to match TechnologiesByCategory
    const technologies: RepositoryAnalysis["technologies"] = {
      language: [],
      framework: [],
      library: [],
      tool: [],
    };

    if (rawData.technologies?.language) {
      rawData.technologies.language.forEach((tech: any) => {
        const base: Technology = {
          ...tech,
          category: "language",
        };
        if (
          ["JavaScript", "TypeScript", "Python", "Java", "Go"].includes(
            tech.name
          )
        ) {
          technologies.language.push(base);
        } else if (
          ["React", "Vue", "Angular", "Django", "Express"].includes(tech.name)
        ) {
          technologies.framework.push({ ...base, category: "framework" });
        } else if (tech.name.includes("lib") || tech.name.includes("utils")) {
          technologies.library.push({ ...base, category: "library" });
        } else {
          technologies.tool.push({ ...base, category: "tool" });
        }
      });
    }
    return {
      repository_id: rawData.repository_id,
      status: rawData.status,
      analysis_session: rawData.analysis_session,
      technologies,
      patterns: rawData.patterns,
      pattern_timeline: {
        timeline: timelineArray,
        summary: {},
      },
      pattern_statistics: patternStats,
      insights: rawData.insights ?? [],
      summary: {
        total_patterns: Object.keys(patternStats).length,
        antipatterns_detected: 0,
        complexity_distribution: {
          simple: 0,
          intermediate: Object.keys(patternStats).length,
          advanced: 0,
        },
      },
      ai_powered: rawData?.ai_powered,
    };
  }, [rawData]);
