import React, { useState } from "react";
import { Brain, Search, ChevronDown, ChevronUp, Filter } from "lucide-react";
import type { RepositoryAnalysis } from "../../types/api";

interface PatternViewerProps {
  data: RepositoryAnalysis;
}

const PatternViewer: React.FC<PatternViewerProps> = ({ data }) => {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [expandedPatterns, setExpandedPatterns] = useState<Set<string>>(
    new Set()
  );

  // Convert pattern statistics to array format for display
  const patterns = Object.entries(data.pattern_statistics).map(
    ([name, stats]) => ({
      name,
      category: stats.category,
      occurrences: stats.occurrences,
      complexity: stats.complexity_level,
      is_antipattern: stats.is_antipattern,
      description: `Pattern detected ${stats.occurrences} times in the codebase`,
      details: {
        occurrences: stats.occurrences,
        first_seen: data.patterns.find((p) => p?.pattern_name === name)
          ?.detected_at,
      },
    })
  );

  // Get unique categories
  const categories = Array.from(
    new Set(patterns.map((p) => p.category || "Uncategorized"))
  ).sort();

  // Filter patterns
  const filteredPatterns = patterns.filter((pattern) => {
    const matchesSearch =
      !searchTerm ||
      pattern.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      pattern.category?.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesCategory =
      selectedCategory === "all" || pattern.category === selectedCategory;

    return matchesSearch && matchesCategory;
  });

  // Group patterns by category
  const groupedPatterns = filteredPatterns.reduce((acc, pattern) => {
    const category = pattern.category || "Uncategorized";
    if (!acc[category]) {
      acc[category] = [];
    }
    acc[category].push(pattern);
    return acc;
  }, {} as Record<string, typeof patterns>);

  const togglePatternExpansion = (patternName: string) => {
    const newExpanded = new Set(expandedPatterns);
    if (newExpanded.has(patternName)) {
      newExpanded.delete(patternName);
    } else {
      newExpanded.add(patternName);
    }
    setExpandedPatterns(newExpanded);
  };

  const getPatternIcon = (category: string) => {
    switch (category?.toLowerCase()) {
      case "react":
        return "⚛️";
      case "async":
        return "⏱️";
      case "javascript":
        return "📜";
      case "error_handling":
        return "🛡️";
      default:
        return "🔧";
    }
  };

  const getComplexityColor = (level: string) => {
    switch (level?.toLowerCase()) {
      case "simple":
        return "bg-green-700 text-green-100";
      case "intermediate":
        return "bg-yellow-700 text-yellow-100";
      case "advanced":
        return "bg-red-700 text-red-100";
      default:
        return "bg-gray-600 text-gray-200";
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Stats & Filters */}
      <div className="bg-gray-800 rounded-lg shadow-xl p-6 mb-6">
        <div className="flex flex-col md:flex-row justify-between items-center gap-4">
          <div className="flex items-center text-gray-300">
            <Brain className="h-6 w-6 mr-2 text-blue-400" />
            <h2 className="text-xl font-semibold text-white">
              Coding Patterns ({filteredPatterns.length} / {patterns.length})
            </h2>
          </div>
          <div className="flex flex-col sm:flex-row gap-3 w-full md:w-auto">
            <div className="relative w-full sm:w-auto">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-500" />
              <input
                type="text"
                placeholder="Search patterns..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full sm:w-64 pl-10 pr-3 py-2 border border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-gray-700 text-gray-100 placeholder-gray-500"
              />
            </div>
            <div className="relative w-full sm:w-auto">
              <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-500" />
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="w-full sm:w-48 pl-10 pr-3 py-2 border border-gray-600 rounded-lg appearance-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-gray-700 text-gray-100"
              >
                <option value="all">All Categories</option>
                {categories.map((cat) => (
                  <option key={cat} value={cat}>
                    {cat}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Pattern Cards */}
      {filteredPatterns.length === 0 ? (
        <div className="bg-gray-800 rounded-lg shadow-xl p-12 text-center">
          <Search className="h-16 w-16 text-gray-500 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-white mb-2">
            No Patterns Match Your Search
          </h3>
          <p className="text-gray-400">
            Try adjusting your search term or category filter.
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          {Object.entries(groupedPatterns).map(
            ([category, categoryPatterns]) => (
              <div key={category}>
                <h3 className="text-xl font-semibold text-gray-200 mb-3 flex items-center">
                  <span className="text-2xl mr-2">
                    {getPatternIcon(category)}
                  </span>
                  {category} ({categoryPatterns.length})
                </h3>
                <div className="grid grid-cols-1 gap-4">
                  {categoryPatterns.map((pattern) => {
                    const isExpanded = expandedPatterns.has(pattern.name);

                    return (
                      <div
                        key={pattern.name}
                        className="bg-gray-700 border border-gray-600 rounded-lg shadow-md"
                      >
                        <button
                          onClick={() => togglePatternExpansion(pattern.name)}
                          className="w-full flex items-center justify-between p-4 text-left hover:bg-gray-600 rounded-t-lg focus:outline-none"
                        >
                          <div className="flex items-center">
                            <span className="text-xl mr-3">
                              {getPatternIcon(pattern.category)}
                            </span>
                            <div>
                              <h3 className="text-lg font-semibold text-gray-100">
                                {pattern.name}
                              </h3>
                              <p className="text-sm text-gray-400">
                                {pattern.occurrences} occurrences
                              </p>
                            </div>
                          </div>
                          <div className="flex items-center">
                            <span
                              className={`px-2 py-0.5 rounded-full text-xs font-medium mr-3 ${getComplexityColor(
                                pattern.complexity
                              )}`}
                            >
                              {pattern.complexity}
                            </span>
                            {isExpanded ? (
                              <ChevronUp className="h-5 w-5 text-gray-400" />
                            ) : (
                              <ChevronDown className="h-5 w-5 text-gray-400" />
                            )}
                          </div>
                        </button>

                        {isExpanded && (
                          <div className="p-4 border-t border-gray-600">
                            <p className="text-sm text-gray-300 mb-2">
                              {pattern.description}
                            </p>
                            {pattern.details && (
                              <div className="mt-2">
                                <h4 className="text-xs font-semibold text-gray-400 uppercase mb-1">
                                  Details:
                                </h4>
                                <pre className="bg-gray-800 p-3 rounded-md text-xs text-gray-200 overflow-x-auto">
                                  <code>
                                    {JSON.stringify(pattern.details, null, 2)}
                                  </code>
                                </pre>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )
          )}
        </div>
      )}
    </div>
  );
};

export default PatternViewer;
