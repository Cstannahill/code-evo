import { useMemo } from "react";
import type {
  RepositoryAnalysisResponse,
  RepositoryAnalysis,
  Technology,
} from "../types/api";

export const useTransformAnalysis = (
  rawData: RepositoryAnalysisResponse | null
): RepositoryAnalysis | null => {
  return useMemo(() => {
    if (!rawData) return null;

    // Extract unique patterns and build statistics
    const patternStats: Record<string, any> = {};
    const patternTimeline: Record<string, Record<string, number>> = {};

    rawData.patterns.forEach((occurrence) => {
      // Build pattern statistics
      if (!patternStats[occurrence.pattern_name]) {
        patternStats[occurrence.pattern_name] = {
          category: occurrence.pattern_name.includes("react")
            ? "react"
            : occurrence.pattern_name.includes("async")
            ? "async"
            : occurrence.pattern_name.includes("javascript")
            ? "javascript"
            : "other",
          occurrences: 0,
          complexity_level: "intermediate",
          is_antipattern: false,
        };
      }
      patternStats[occurrence.pattern_name].occurrences++;

      // Build timeline
      const month = occurrence.detected_at.substring(0, 7); // YYYY-MM
      if (!patternTimeline[month]) {
        patternTimeline[month] = {};
      }
      if (!patternTimeline[month][occurrence.pattern_name]) {
        patternTimeline[month][occurrence.pattern_name] = 0;
      }
      patternTimeline[month][occurrence.pattern_name]++;
    });

    // Convert timeline to array format
    const timelineArray = Object.entries(patternTimeline)
      .map(([date, patterns]) => ({ date, patterns }))
      .sort((a, b) => a.date.localeCompare(b.date));

    // Transform technologies - extract from language array
    const technologies: RepositoryAnalysis["technologies"] = {
      language: [],
      framework: [],
      library: [],
      tool: [],
    };

    // Parse technologies from the language array
    if (rawData.technologies?.language) {
      rawData.technologies.language.forEach((tech: any) => {
        const transformedTech: Technology = {
          id: tech.name,
          name: tech.name,
          category: "language",
          first_seen: "2024-01-01",
          last_seen: "2024-01-01",
          usage_count: tech.usage_count || 1,
          metadata: {},
        };

        // Categorize based on name
        if (
          ["JavaScript", "TypeScript", "Python", "Java", "Go"].includes(
            tech.name
          )
        ) {
          technologies.language.push(transformedTech);
        } else if (
          ["React", "Vue", "Angular", "Django", "Express"].includes(tech.name)
        ) {
          technologies.framework.push({
            ...transformedTech,
            category: "framework",
          });
        } else if (tech.name.includes("lib") || tech.name.includes("utils")) {
          technologies.library.push({
            ...transformedTech,
            category: "library",
          });
        } else {
          technologies.tool.push({ ...transformedTech, category: "tool" });
        }
      });
    }

    // Get insights from the separate insights endpoint data if available
    const insights = rawData.insights || [];

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
      insights,
      summary: {
        total_patterns: Object.keys(patternStats).length,
        antipatterns_detected: 0,
        complexity_distribution: {
          simple: 0,
          intermediate: Object.keys(patternStats).length,
          advanced: 0,
        },
      },
      ai_powered: true,
    };
  }, [rawData]);
};
