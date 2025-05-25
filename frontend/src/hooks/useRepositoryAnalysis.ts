// src/hooks/useRepositoryAnalysis.ts

import type { UseQueryResult } from "@tanstack/react-query";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../api/client";
import { useTransformAnalysis } from "./useTransformAnalysis";

//
// 1) Mirror exactly what your backend returns for TS
//
interface PatternStats {
  category: string;
  occurrences: number;
  complexity_level: string; // <--- widened to `string`
  is_antipattern: boolean;
}

interface RawAnalysisResponse {
  pattern_statistics: Record<string, PatternStats>;
  insights?: any[];
  // add any other top-level fields your backend returns
}

//
// 2) The “flat” pattern type your UI actually consumes
//
export interface FlatPattern {
  pattern_name: string;
  category: string;
  occurrences: number;
  complexity_level: string;
  is_antipattern: boolean;
  file_path: string;
  confidence_score: number;
  detected_at: string;
}

//
// 3) Compute the transformed type once so we can reuse it
//
type Transformed = ReturnType<typeof useTransformAnalysis>;

//
// 4) Override only the `data` field on UseQueryResult<RawAnalysisResponse,Error>
//    so that we can swap in our `Transformed` payload without type errors.
//
type UseRepositoryAnalysisResult = Omit<
  UseQueryResult<RawAnalysisResponse, Error>,
  "data"
> & {
  data: Transformed;
};

export const useRepositoryAnalysis = (
  repoId: string | null
): UseRepositoryAnalysisResult => {
  // fetch the raw analysis from your API
  const analysisQuery = useQuery<RawAnalysisResponse, Error>({
    queryKey: ["repositoryAnalysis", repoId],
    queryFn: () => apiClient.getRepositoryAnalysis(repoId!),
    enabled: !!repoId,
  });

  // make sure we always have an object to destructure
  const raw = analysisQuery.data ?? {
    pattern_statistics: {},
    insights: [],
  };

  // build a guaranteed array of flat patterns
  const patternsArray: FlatPattern[] = Object.entries(
    raw.pattern_statistics
  ).map(([pattern_name, stats]) => ({
    pattern_name,
    category: stats.category,
    occurrences: stats.occurrences,
    complexity_level: stats.complexity_level,
    is_antipattern: stats.is_antipattern,
    file_path: "",
    confidence_score: stats.complexity_level === "advanced" ? 1 : 0,
    detected_at: new Date().toISOString(),
  }));

  // feed into your existing transformer
  const transformed = useTransformAnalysis({
    ...raw,
    insights: raw.insights ?? [],
    patterns: patternsArray,
  } as any);

  // return everything react-query gives you, but with `data` swapped out
  return {
    ...analysisQuery,
    data: transformed,
  };
};
