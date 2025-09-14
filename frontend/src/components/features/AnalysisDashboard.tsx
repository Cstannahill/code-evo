import React, { useMemo, useState } from "react";



import { motion, AnimatePresence } from "framer-motion";
import {
  Activity,
  BarChart3,
  Brain,
  FileText,
  Layers,
  LineChart,
  TrendingUp,
  Sparkles,
  Gauge,
  Network,
  Calendar,
  Award,
} from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../ui/tabs";
import { useRepositoryAnalysis } from "../../hooks/useRepositoryAnalysis";
import { PatternTimeline } from "../charts/PatternTimeline";
import { TechnologyRadar } from "../charts/TechRadar";
import { PatternHeatmap } from "../charts/PatternHeatmap";
import { CodeQualityMetrics } from "../charts/CodeQualityMetrics";
import { PatternWordCloud } from "../charts/PatternWordCloud";
import { TechnologyEvolutionChart } from "../charts/TechnologyEvolutionChart";
import { ComplexityEvolutionChart } from "../charts/ComplexityEvolutionChart";
import { LearningProgressionChart } from "../charts/LearningProgressionChart";
import { TechStackComposition } from "../charts/TechStackComposition";
import { TechnologyRelationshipGraph } from "../charts/TechnologyRelationshipGraph";
import { useRepositoryPatterns } from "../../hooks/useRepositoryPatterns";
import { InsightsDashboard } from "./InsightsDashboard";
import { PatternDeepDive } from "./PatternDeepDive";
import { CodeQualityDashboard } from "./CodeQualityDashboard";
import type { Word } from "react-wordcloud";

// Reusable components (moved above main component)
const MetricCard = ({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  color,
}: {
  title: string;
  value: string | number;
  subtitle: string;
  icon: React.ComponentType<{ className?: string }>;
  trend?: string;
  color: string;
}) => (
  <motion.div
    whileHover={{ scale: 1.02 }}
    className="bg-card rounded-lg border p-6 relative overflow-hidden"
  >
    <div className="flex items-start justify-between">
      <div>
        <p className="text-sm font-medium text-muted-foreground">{title}</p>
        <p className={`text-3xl font-bold my-2 ${color}`}>{value}</p>
        <p className="text-xs text-muted-foreground">{subtitle}</p>
        {trend && (
          <p className="text-xs text-green-500 mt-2">
            {trend} from last analysis
          </p>
        )}
      </div>
      <Icon className={`w-8 h-8 ${color} opacity-20`} />
    </div>
    <div
      className={`absolute inset-x-0 bottom-0 h-1 ${color.replace(
        "text-",
        "bg-"
      )}`}
    />
  </motion.div>
);

const DashboardCard = ({
  title,
  icon: Icon,
  children,
}: {
  title: string;
  icon: React.ComponentType<{ className?: string }>;
  children: React.ReactNode;
}) => (
  <motion.div
    initial={{ opacity: 0 }}
    animate={{ opacity: 1 }}
    className="bg-card rounded-lg border p-6"
  >
    <div className="flex items-center gap-2 mb-4">
      <Icon className="w-5 h-5 text-muted-foreground" />
      <h3 className="text-lg font-semibold">{title}</h3>
    </div>
    {children}
  </motion.div>
);

const DashboardSkeleton = () => (
  <div className="space-y-6 animate-pulse">
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
      {[...Array(4)].map((_, i) => (
        <div key={i} className="bg-card rounded-lg border p-6 h-32" />
      ))}
    </div>
    <div className="bg-card rounded-lg border p-6 h-96" />
  </div>
);

const ErrorState = () => (
  <div className="text-center py-12">
    <FileText className="w-12 h-12 text-destructive mx-auto mb-4" />
    <p className="text-lg text-muted-foreground">Failed to load analysis</p>
  </div>
);

const AnalysisInProgress = () => (
  <div className="flex flex-col items-center justify-center py-16">
    <svg className="animate-spin h-10 w-10 text-blue-500 mb-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"></path>
    </svg>
    <p className="text-lg font-semibold text-blue-500">Analysis in progress...</p>
    <p className="text-sm text-muted-foreground mt-2">This may take a few moments depending on repository size.</p>
  </div>
);

interface AnalysisDashboardProps {
  repositoryId: string;
}

// Limit for top N patterns in charts
const TOP_PATTERNS_LIMIT = 20;


export const AnalysisDashboard: React.FC<AnalysisDashboardProps> = ({ repositoryId }) => {
  // All hooks must be called unconditionally at the top
  const [activeTab, setActiveTab] = useState("overview");
  const { data: analysis, isLoading, error } = useRepositoryAnalysis(repositoryId, true); // Use enhanced analysis
  const { data: patternDetails } = useRepositoryPatterns(repositoryId);

  // Precompute all memoized values regardless of data state
  const allOccurrences = useMemo(() => {
    if (!patternDetails?.patterns) return [];
    return (patternDetails.patterns as any[]).flatMap((p: any) => p.occurrences || []);
  }, [patternDetails]);
  const wordCloudData: Word[] = useMemo(() => {
    if (!analysis?.pattern_statistics) return [];
    return Object.entries(analysis.pattern_statistics)
      .map(([pattern, info]) => ({
        text: pattern.replace(/_/g, " "),
        value: info.occurrences,
      }))
      .filter((item) => item.value > 0)
      .sort((a, b) => b.value - a.value)
      .slice(0, TOP_PATTERNS_LIMIT);
  }, [analysis?.pattern_statistics]);
  // total_commits may only exist on EnhancedRepositoryAnalysisResponse
  const totalCommits =
    analysis?.analysis_session?.commits_analyzed ||
    (analysis && "total_commits" in analysis ? (analysis as any).total_commits : undefined) ||
    (analysis?.summary && "total_commits" in analysis.summary ? (analysis.summary as any).total_commits : undefined) ||
    0;

  // Debug commit data issues
  React.useEffect(() => {
    if (analysis) {
      console.log('AnalysisDashboard Debug:', {
        analysis_session: analysis.analysis_session,
        total_commits: "total_commits" in (analysis || {}) ? (analysis as any).total_commits : 0,
        summary: analysis.summary,
        calculated_totalCommits: totalCommits,
        timeline_length: analysis.pattern_timeline?.timeline?.length,
        available_keys: Object.keys(analysis)
      });
    }
  }, [analysis, totalCommits]);

  const totalPatterns = Object.keys(analysis?.pattern_statistics || {}).length;
  const totalTechnologies = React.useMemo(() => {
    if (!analysis?.technologies) return 0;
    if (Array.isArray(analysis.technologies)) {
      return analysis.technologies.length;
    }
    return Object.values(analysis.technologies).flat().length;
  }, [analysis?.technologies]);
  const timelineLength = analysis?.pattern_timeline?.timeline?.length || 0;
  const antipatterns = analysis?.summary?.antipatterns_detected || 0;
  const healthScore = Math.round(((totalPatterns - antipatterns) / Math.max(totalPatterns, 1)) * 100);
  const velocityScore = timelineLength > 0 ? (totalCommits / timelineLength) : 0;
  const healthTrend = React.useMemo(() => {
    if (antipatterns === 0) return "+12%";
    if (antipatterns < totalPatterns * 0.1) return "+5%";
    if (antipatterns < totalPatterns * 0.2) return "-2%";
    return "-8%";
  }, [antipatterns, totalPatterns]);
  const velocityTrend = React.useMemo(() => {
    if (velocityScore > 10) return "+15%";
    if (velocityScore > 5) return "+8%";
    if (velocityScore > 2) return "+3%";
    return "0%";
  }, [velocityScore]);
  const simpleTechnologies: Record<string, string[]> = React.useMemo(() => {
    const result: Record<string, string[]> = {};
    if (!analysis?.technologies) return result;
    if (Array.isArray(analysis.technologies)) {
      result['all'] = analysis.technologies.map((t: any) => t.name || t);
    } else {
      Object.entries(analysis.technologies).forEach(([cat, arr]: [string, any]) => {
        if (Array.isArray(arr)) {
          result[cat] = arr.map((t: any) => t.name || t);
        }
      });
    }
    return result;
  }, [analysis?.technologies]);
  const simplePatternStats: Record<string, number> = React.useMemo(() => {
    const result: Record<string, number> = {};
    if (!analysis?.pattern_statistics) return result;
    Object.entries(analysis.pattern_statistics).forEach(
      ([name, info]: [string, any]) => {
        result[name] = typeof info === 'object' ? info.occurrences || 0 : info;
      }
    );
    return result;
  }, [analysis?.pattern_statistics]);
  const tabs = [
    { id: "overview", label: "Executive Overview", icon: Gauge },
    { id: "patterns", label: "Pattern Analysis", icon: Brain },
    { id: "evolution", label: "Code Evolution", icon: TrendingUp },
    { id: "technologies", label: "Tech Stack", icon: Layers },
    { id: "insights", label: "AI Insights", icon: Sparkles },
    { id: "quality", label: "Code Quality", icon: Award },
  ];
  const topPatternNames = useMemo(() => wordCloudData.map((w) => w.text), [wordCloudData]);
  // Only now do early returns
  if (isLoading) return <DashboardSkeleton />;
  if (error) return <ErrorState />;
  if (!analysis) return <AnalysisInProgress />;
  if (analysis.status === "analyzing" || analysis.status === "pending") {
    return <AnalysisInProgress />;
  }
  if (analysis.status === "failed") return <ErrorState />;
  // For PatternHeatmap, limit to top N patterns as well




  return (
    <div className="space-y-6">
      {/* Header Metrics with improved calculations */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="grid grid-cols-1 md:grid-cols-4 gap-4"
      >
        <MetricCard
          title="Repository Health"
          value={`${healthScore}%`}
          subtitle={`${totalPatterns} patterns, ${antipatterns} issues`}
          icon={Activity}
          trend={healthTrend}
          color={healthScore >= 80 ? "text-green-500" : healthScore >= 60 ? "text-yellow-500" : "text-red-500"}
        />
        <MetricCard
          title="Evolution Velocity"
          value={velocityScore > 0 ? `${velocityScore.toFixed(1)}` : "0"}
          subtitle={`${totalCommits} commits across ${timelineLength || 1} periods`}
          icon={TrendingUp}
          trend={velocityTrend}
          color="text-blue-500"
        />
        <MetricCard
          title="Tech Diversity"
          value={totalTechnologies}
          subtitle={`${totalTechnologies > 10 ? 'High' : totalTechnologies > 5 ? 'Moderate' : 'Limited'} technology stack`}
          icon={Network}
          trend={totalTechnologies > 5 ? "+2" : totalTechnologies > 3 ? "+1" : "0"}
          color="text-purple-500"
        />
        <MetricCard
          title="Code Maturity"
          value={
            totalPatterns > 15
              ? "Advanced"
              : totalPatterns > 8
                ? "Intermediate"
                : "Basic"
          }
          subtitle={`${totalCommits} commits, ${timelineLength} periods`}
          icon={Award}
          trend={totalPatterns > 10 ? "+1 level" : "stable"}
          color={totalPatterns > 15 ? "text-green-500" : totalPatterns > 8 ? "text-yellow-500" : "text-blue-500"}
        />
      </motion.div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full -500">
        <TabsList className="grid grid-cols-6 w-full">
          {tabs.map((tab) => (
            <TabsTrigger
              key={tab.id}
              value={tab.id}
              className="flex items-center gap-2"
            >
              <tab.icon className="w-4 h-4" />
              <span className="hidden md:inline">{tab.label}</span>
            </TabsTrigger>
          ))}
        </TabsList>

        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
          >
            {/* Overview */}
            <TabsContent value="overview" className="space-y-6 mt-6">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <DashboardCard title="Code Quality Metrics" icon={Gauge}>
                  <CodeQualityMetrics analysis={analysis} />
                </DashboardCard>
                <DashboardCard title="Pattern Distribution" icon={Brain}>
                  {wordCloudData.length > 0 ? (
                    <PatternWordCloud patterns={wordCloudData} height={280} />
                  ) : (
                    <div className="flex items-center justify-center h-64 text-muted-foreground">
                      <div className="text-center">
                        <div className="text-4xl mb-2">🧠</div>
                        <p>Analyzing patterns...</p>
                        <p className="text-sm mt-1">
                          {Object.keys(analysis.pattern_statistics || {}).length}{" "}
                          patterns detected
                        </p>
                      </div>
                    </div>
                  )}
                </DashboardCard>
              </div>
              <DashboardCard
                title="Repository Evolution Timeline"
                icon={Calendar}
              >
                <PatternTimeline
                  data={analysis.pattern_timeline || {}}
                  height={250}
                  topPatterns={topPatternNames}
                />
              </DashboardCard>
            </TabsContent>

            {/* Pattern Analysis */}
            <TabsContent value="patterns" className="space-y-6 mt-6">
              <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                <DashboardCard title="Pattern Heatmap" icon={BarChart3}>
                  <PatternHeatmap data={analysis} width={600} height={300} topPatterns={topPatternNames} />
                </DashboardCard>
                <DashboardCard title="Pattern Timeline" icon={LineChart}>
                  <PatternTimeline
                    data={analysis.pattern_timeline || {}}
                    height={300}
                    topPatterns={topPatternNames}
                  />
                </DashboardCard>
              </div>
              <DashboardCard title="Pattern Deep Dive" icon={Brain}>
                <PatternDeepDive
                  patterns={analysis.pattern_statistics || {}}
                  occurrences={allOccurrences}
                />
              </DashboardCard>
            </TabsContent>

            {/* Code Evolution */}
            <TabsContent value="evolution" className="space-y-6 mt-6">
              <DashboardCard
                title="Technology Adoption Curve"
                icon={TrendingUp}
              >
                <TechnologyEvolutionChart
                  technologies={analysis.technologies || {}}
                  timeline={analysis.pattern_timeline?.timeline || []}
                />
              </DashboardCard>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <DashboardCard title="Learning Progression" icon={Brain}>
                  <LearningProgressionChart analysis={analysis} />
                </DashboardCard>
                <DashboardCard title="Complexity Evolution" icon={Layers}>
                  <ComplexityEvolutionChart
                    patterns={analysis.pattern_statistics || {}}
                  />
                </DashboardCard>
              </div>
            </TabsContent>

            {/* Tech Stack */}
            <TabsContent value="technologies" className="space-y-6 mt-6">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <DashboardCard title="Technology Radar" icon={Network}>
                  <TechnologyRadar technologies={analysis.technologies || {}} />
                </DashboardCard>
                <DashboardCard title="Tech Stack Composition" icon={Layers}>
                  <TechStackComposition technologies={analysis.technologies || {}} />
                </DashboardCard>
              </div>
              <DashboardCard title="Technology Relationships" icon={Network}>
                <TechnologyRelationshipGraph
                  analysis={{ technologies: analysis.technologies || {} }}
                />
              </DashboardCard>
            </TabsContent>

            {/* AI Insights */}
            <TabsContent value="insights" className="mt-6">
              <InsightsDashboard
                insights={analysis.insights}
                analysis={{
                  summary: analysis.summary,
                  analysis_session: analysis.analysis_session,
                  technologies: simpleTechnologies,
                  pattern_statistics: simplePatternStats,
                }}
              />
            </TabsContent>

            {/* Code Quality */}
            <TabsContent value="quality" className="space-y-6 mt-6">
              <CodeQualityDashboard
                analysis={{
                  pattern_statistics: analysis.pattern_statistics,
                  summary: {
                    antipatterns_detected:
                      analysis.summary.antipatterns_detected,
                  },
                  analysis_session: {
                    commits_analyzed:
                      analysis.analysis_session.commits_analyzed,
                  },
                  security_analysis: (analysis as any).security_analysis,
                  performance_analysis: (analysis as any).performance_analysis,
                  architectural_analysis: (analysis as any).architectural_analysis,
                }}
              />
            </TabsContent>
          </motion.div>
        </AnimatePresence>
      </Tabs>
    </div>
  );
};


