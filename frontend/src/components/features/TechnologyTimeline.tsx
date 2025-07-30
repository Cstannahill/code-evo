// src/components/TechnologyTimeline.tsx
import React, { useState, useEffect } from "react";
import { apiClient } from "../../api/client";
import {
  Calendar,
  TrendingUp,
  BarChart2,
  GitCommit,
  FileText,
  Users,
  AlertCircle,
  Loader,
} from "lucide-react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  Bar,
  ComposedChart,
} from "recharts";

interface TimelineEntry {
  date: string; // YYYY-MM format
  commits: number;
  languages: string[];
  technologies: string[];
}

interface TechnologyTimelineProps {
  repositoryId: string;
}

const TechnologyTimeline: React.FC<TechnologyTimelineProps> = ({
  repositoryId,
}) => {
  const [timelineData, setTimelineData] = useState<TimelineEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadTimelineData();
  }, [repositoryId]);

  const loadTimelineData = async () => {
    setLoading(true);
    setError(null);

    try {
      await apiClient.checkHealth(); // Using a simple API call as placeholder
      // TODO: Replace with actual timeline endpoint when available
      // const response = await apiClient.getRepository(repositoryId);
      setTimelineData([]); // Temporary empty data
    } catch (err) {
      setError("Failed to load timeline data");
      console.error("Error loading timeline:", err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-gray-800 rounded-lg shadow-xl p-12 text-center">
        <Loader className="h-12 w-12 text-blue-500 mx-auto mb-4 animate-spin" />
        <p className="text-gray-300">Loading timeline data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-900 bg-opacity-40 border border-red-700 rounded-lg p-8 text-center">
        <AlertCircle className="h-12 w-12 text-red-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-red-200 mb-2">
          Error Loading Timeline
        </h3>
        <p className="text-red-300">{error}</p>
        <button
          onClick={loadTimelineData}
          className="mt-4 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm"
        >
          Try Again
        </button>
      </div>
    );
  }

  if (timelineData.length === 0) {
    return (
      <div className="bg-gray-800 rounded-lg shadow-xl p-12 text-center">
        <Calendar className="h-16 w-16 text-gray-500 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-white mb-2">
          No Timeline Data Available
        </h3>
        <p className="text-gray-400">
          There is no historical data to display for this repository yet.
        </p>
      </div>
    );
  }

  // Process data for charts
  const chartData = timelineData.map((entry) => ({
    date: entry.date,
    commits: entry.commits,
    languageCount: entry.languages.length,
    techCount: entry.technologies.length,
    languages: entry.languages.join(", "),
    technologies: entry.technologies.join(", "),
  }));

  // Get all unique languages and technologies
  const allLanguages = Array.from(
    new Set(timelineData.flatMap((entry) => entry.languages))
  ).sort(); // Sort for consistent color mapping
  const allTechnologies = Array.from(
    new Set(timelineData.flatMap((entry) => entry.technologies))
  ).sort(); // Sort for consistent color mapping

  // Create language adoption timeline
  const languageTimelineData = timelineData.map((entry) => {
    const result: any = { date: entry.date };
    allLanguages.forEach((lang) => {
      result[lang] = entry.languages.includes(lang) ? 1 : 0;
    });
    return result;
  });

  // Calculate language statistics
  const languageStats = allLanguages
    .map((lang) => {
      const appearances = timelineData.filter((entry) =>
        entry.languages.includes(lang)
      ).length;
      const firstAppearance = timelineData.find((entry) =>
        entry.languages.includes(lang)
      )?.date;
      return {
        name: lang,
        appearances,
        firstAppearance,
        percentage: Math.round((appearances / timelineData.length) * 100),
      };
    })
    .sort((a, b) => b.appearances - a.appearances);

  const colors = [
    "#3B82F6", // blue-500
    "#EF4444", // red-500
    "#10B981", // green-500
    "#F59E0B", // amber-500
    "#8B5CF6", // violet-500
    "#EC4899", // pink-500
    "#06B6D4", // cyan-500
    "#F97316", // orange-500
    "#6366F1", // indigo-500
    "#D946EF", // fuchsia-500
    "#14B8A6", // teal-500
    "#F43F5E", // rose-500
  ];

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-gray-700 p-3 rounded shadow-lg border border-gray-600">
          <p className="text-sm font-semibold text-gray-100">{label}</p>
          {payload.map((pld: any, index: number) => (
            <div key={index} style={{ color: pld.color }} className="text-xs">
              {pld.name}: {pld.value}
            </div>
          ))}
          {payload[0].payload.languages && (
            <p className="text-xs text-gray-400 mt-1">
              Languages: {payload[0].payload.languages}
            </p>
          )}
          {payload[0].payload.technologies && (
            <p className="text-xs text-gray-400">
              Technologies: {payload[0].payload.technologies}
            </p>
          )}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="space-y-8">
      {/* Overview Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-gray-800 p-5 rounded-lg shadow-lg">
          <div className="flex items-center">
            <Calendar className="h-6 w-6 text-blue-400 mr-3" />
            <div>
              <p className="text-2xl font-semibold text-white">
                {timelineData.length}
              </p>
              <p className="text-sm text-gray-400">Months Analyzed</p>
            </div>
          </div>
        </div>
        <div className="bg-gray-800 p-5 rounded-lg shadow-lg">
          <div className="flex items-center">
            <GitCommit className="h-6 w-6 text-green-400 mr-3" />
            <div>
              <p className="text-2xl font-semibold text-white">
                {timelineData.reduce((sum, e) => sum + e.commits, 0)}
              </p>
              <p className="text-sm text-gray-400">Total Commits</p>
            </div>
          </div>
        </div>
        <div className="bg-gray-800 p-5 rounded-lg shadow-lg">
          <div className="flex items-center">
            <FileText className="h-6 w-6 text-purple-400 mr-3" />
            <div>
              <p className="text-2xl font-semibold text-white">
                {allLanguages.length}
              </p>
              <p className="text-sm text-gray-400">Unique Languages</p>
            </div>
          </div>
        </div>
        <div className="bg-gray-800 p-5 rounded-lg shadow-lg">
          <div className="flex items-center">
            <Users className="h-6 w-6 text-yellow-400 mr-3" />
            <div>
              <p className="text-2xl font-semibold text-white">
                {allTechnologies.length}
              </p>
              <p className="text-sm text-gray-400">Unique Technologies</p>
            </div>
          </div>
        </div>
      </div>

      {/* Commit Activity Timeline */}
      <div className="bg-gray-800 rounded-lg shadow-xl p-6">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
          <TrendingUp className="h-5 w-5 mr-2 text-blue-400" /> Commit Activity
          Over Time
        </h3>
        <ResponsiveContainer width="100%" height={300}>
          <ComposedChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#4A5568" />
            <XAxis dataKey="date" tick={{ fontSize: 12, fill: "#A0AEC0" }} />
            <YAxis yAxisId="left" tick={{ fontSize: 12, fill: "#A0AEC0" }} />
            <YAxis
              yAxisId="right"
              orientation="right"
              tick={{ fontSize: 12, fill: "#A0AEC0" }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend wrapperStyle={{ fontSize: "12px", color: "#CBD5E0" }} />
            <Bar
              yAxisId="left"
              dataKey="commits"
              name="Commits"
              fill="#3B82F6"
              barSize={20}
            />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="languageCount"
              name="Languages Used"
              stroke="#10B981"
              strokeWidth={2}
              dot={{ r: 3 }}
            />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="techCount"
              name="Technologies Used"
              stroke="#8B5CF6"
              strokeWidth={2}
              dot={{ r: 3 }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* Language Adoption Timeline */}
      {allLanguages.length > 0 && (
        <div className="bg-gray-800 rounded-lg shadow-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
            <BarChart2 className="h-5 w-5 mr-2 text-green-400" /> Language
            Adoption Over Time
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={languageTimelineData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#4A5568" />
              <XAxis dataKey="date" tick={{ fontSize: 12, fill: "#A0AEC0" }} />
              <YAxis tick={{ fontSize: 12, fill: "#A0AEC0" }} />
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={{ fontSize: "12px", color: "#CBD5E0" }} />
              {allLanguages.map((lang, index) => (
                <Line
                  key={lang}
                  type="monotone"
                  dataKey={lang}
                  stroke={colors[index % colors.length]}
                  strokeWidth={2}
                  dot={{ r: 2 }}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Language Statistics Table */}
      {languageStats.length > 0 && (
        <div className="bg-gray-800 rounded-lg shadow-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">
            Language Statistics
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left text-gray-300">
              <thead className="text-xs text-gray-400 uppercase bg-gray-700">
                <tr>
                  <th scope="col" className="px-4 py-2">
                    Language
                  </th>
                  <th scope="col" className="px-4 py-2 text-center">
                    Months Active
                  </th>
                  <th scope="col" className="px-4 py-2 text-center">
                    Adoption %
                  </th>
                  <th scope="col" className="px-4 py-2">
                    First Seen
                  </th>
                </tr>
              </thead>
              <tbody>
                {languageStats.map((stat) => (
                  <tr
                    key={stat.name}
                    className="bg-gray-800 border-b border-gray-700 hover:bg-gray-700"
                  >
                    <td className="px-4 py-2 font-medium text-white whitespace-nowrap flex items-center">
                      <span
                        style={{
                          backgroundColor:
                            colors[
                              allLanguages.indexOf(stat.name) % colors.length
                            ],
                        }}
                        className="h-2.5 w-2.5 rounded-full mr-2"
                      ></span>
                      {stat.name}
                    </td>
                    <td className="px-4 py-2 text-center">
                      {stat.appearances}
                    </td>
                    <td className="px-4 py-2 text-center">
                      {stat.percentage}%
                    </td>
                    <td className="px-4 py-2">{stat.firstAppearance}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Technology Adoption (Similar to Languages, if desired) */}
      {/* Placeholder for technology adoption chart and stats - can be implemented similarly to languages */}
      {allTechnologies.length > 0 && (
        <div className="bg-gray-800 rounded-lg shadow-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center">
            <BarChart2 className="h-5 w-5 mr-2 text-purple-400" /> Technology
            Adoption Over Time (Example)
          </h3>
          <p className="text-gray-400 text-sm">
            Further implementation can show technology adoption similar to
            languages.
          </p>
          {/* Add chart here if needed */}
        </div>
      )}
    </div>
  );
};

export default TechnologyTimeline;
