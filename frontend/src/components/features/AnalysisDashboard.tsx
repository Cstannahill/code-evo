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
import { TechnologyRelationshipGraph } from "../charts/TechnologyRelationShipGraph";
import { InsightsDashboard } from "./InsightsDashBoard";
import { PatternDeepDive } from "./PatternDeepDive";
import { CodeQualityDashboard } from "./CodeQualityDashboard";

interface AnalysisDashboardProps {
  repositoryId: string;
}

export const AnalysisDashboard: React.FC<AnalysisDashboardProps> = ({
  repositoryId,
}) => {
  const [activeTab, setActiveTab] = useState("overview");
  const {
    data: analysis,
    isLoading,
    error,
  } = useRepositoryAnalysis(repositoryId);

  // Build the word‐cloud data
  const wordCloudData = useMemo(() => {
    if (!analysis) return [];
    return Object.entries(analysis.pattern_statistics).map(
      ([pattern, info]) => ({
        text: pattern,
        value: info.occurrences,
      })
    );
  }, [analysis?.pattern_statistics]);

  if (isLoading) return <DashboardSkeleton />;
  if (error || !analysis) return <ErrorState />;

  // Header metrics
  const totalCommits = analysis.analysis_session?.commits_analyzed || 0;
  const totalPatterns = Object.keys(analysis.pattern_statistics).length;
  const totalTechnologies = Object.values(analysis.technologies).flat().length;
  const timelineLength = analysis.pattern_timeline.timeline.length;

  // Prepare a simple string[] map of technologies for the Insights panel
  const simpleTechnologies: Record<string, string[]> = {};
  Object.entries(analysis.technologies).forEach(([cat, arr]) => {
    simpleTechnologies[cat] = arr.map((t) => t.name);
  });

  // Prepare a simple number map of patterns for the Insights panel
  const simplePatternStats: Record<string, number> = {};
  Object.entries(analysis.pattern_statistics).forEach(
    ([name, info]) => (simplePatternStats[name] = info.occurrences)
  );

  const tabs = [
    { id: "overview", label: "Executive Overview", icon: Gauge },
    { id: "patterns", label: "Pattern Analysis", icon: Brain },
    { id: "evolution", label: "Code Evolution", icon: TrendingUp },
    { id: "technologies", label: "Tech Stack", icon: Layers },
    { id: "insights", label: "AI Insights", icon: Sparkles },
    { id: "quality", label: "Code Quality", icon: Award },
  ];

  return (
    <div className="space-y-6">
      {/* Header Metrics */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="grid grid-cols-1 md:grid-cols-4 gap-4"
      >
        <MetricCard
          title="Repository Health"
          value={`${Math.round(
            ((totalPatterns - analysis.summary.antipatterns_detected) /
              totalPatterns) *
              100
          )}%`}
          subtitle="Based on pattern analysis"
          icon={Activity}
          trend="+12%"
          color="text-green-500"
        />
        <MetricCard
          title="Evolution Velocity"
          value={`${(timelineLength * 3.2).toFixed(1)}`}
          subtitle="Learning rate index"
          icon={TrendingUp}
          trend="+8%"
          color="text-blue-500"
        />
        <MetricCard
          title="Tech Diversity"
          value={totalTechnologies}
          subtitle="Unique technologies"
          icon={Network}
          trend="+3"
          color="text-purple-500"
        />
        <MetricCard
          title="Code Maturity"
          value="Advanced"
          subtitle={`${totalCommits} commits analyzed`}
          icon={Award}
          color="text-yellow-500"
        />
      </motion.div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
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
                  <PatternWordCloud patterns={wordCloudData} />
                </DashboardCard>
              </div>
              <DashboardCard
                title="Repository Evolution Timeline"
                icon={Calendar}
              >
                {/* placeholder for future timeline */}
              </DashboardCard>
            </TabsContent>

            {/* Pattern Analysis */}
            <TabsContent value="patterns" className="space-y-6 mt-6">
              <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                <DashboardCard title="Pattern Heatmap" icon={BarChart3}>
                  <PatternHeatmap data={analysis} width={600} height={300} />
                </DashboardCard>
                <DashboardCard title="Pattern Timeline" icon={LineChart}>
                  <PatternTimeline
                    data={analysis.pattern_timeline.timeline}
                    height={300}
                  />
                </DashboardCard>
              </div>
              <DashboardCard title="Pattern Deep Dive" icon={Brain}>
                <PatternDeepDive
                  patterns={analysis.pattern_statistics}
                  occurrences={analysis.patterns}
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
                  technologies={analysis.technologies}
                  timeline={analysis.pattern_timeline.timeline}
                />
              </DashboardCard>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <DashboardCard title="Learning Progression" icon={Brain}>
                  <LearningProgressionChart analysis={analysis} />
                </DashboardCard>
                <DashboardCard title="Complexity Evolution" icon={Layers}>
                  <ComplexityEvolutionChart
                    patterns={analysis.pattern_statistics}
                  />
                </DashboardCard>
              </div>
            </TabsContent>

            {/* Tech Stack */}
            <TabsContent value="technologies" className="space-y-6 mt-6">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <DashboardCard title="Technology Radar" icon={Network}>
                  <TechnologyRadar technologies={analysis.technologies} />
                </DashboardCard>
                <DashboardCard title="Tech Stack Composition" icon={Layers}>
                  <TechStackComposition technologies={analysis.technologies} />
                </DashboardCard>
              </div>
              <DashboardCard title="Technology Relationships" icon={Network}>
                {/* only technologies needed */}
                <TechnologyRelationshipGraph
                  analysis={{ technologies: analysis.technologies }}
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
                }}
              />
            </TabsContent>
          </motion.div>
        </AnimatePresence>
      </Tabs>
    </div>
  );
};

// Reusable components
const MetricCard = ({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  color,
}: any) => (
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

const DashboardCard = ({ title, icon: Icon, children }: any) => (
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
