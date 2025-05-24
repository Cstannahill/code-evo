# Code Evolution Tracker - Development Roadmap

## Executive Summary

This document outlines the comprehensive development roadmap for completing the Code Evolution Tracker frontend and achieving production readiness. The immediate focus is on building a sophisticated visualization dashboard that leverages the fully operational AI-powered backend.

## Phase 1: Frontend Visualization (Immediate Priority)

### 1.1 Modern Dependency Setup

#### Tailwind CSS v4.1 Integration (Critical)

**Step 1: Install Tailwind CSS v4.1**
```bash
cd frontend
npm install tailwindcss@^4 @tailwindcss/postcss tw-animate-css@^1.3.0 tailwind-merge@^3.3.0
```

**Step 2: Configure PostCSS (v4.1 Pattern)**
```javascript
// postcss.config.mjs (or postcss.config.js)
const config = {
  plugins: ["@tailwindcss/postcss"],
};

export default config;
```

**Step 3: Update Global CSS (v4.1 Syntax)**
```css
/* src/index.css - NEW v4.1 approach */
@tailwindcss;

/* Additional custom styles */
@layer components {
  .card {
    @apply rounded-lg border bg-card text-card-foreground shadow-sm;
  }
}

@layer utilities {
  .text-balance {
    text-wrap: balance;
  }
}
```

**Step 4: Configure Tailwind Theme**
```javascript
// tailwind.config.js
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
        pulse: "pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        bounce: "bounce 1s infinite",
      },
    },
  },
  plugins: [],
}
```

### 1.2 Core Visualization Dependencies

**Install Visualization Libraries**
```bash
npm install recharts@^2.12.0 react-flow@^11.11.0 d3@^7.9.0 
npm install lucide-react@^0.344.0 @radix-ui/react-slot@^1.0.2
npm install class-variance-authority@^0.7.0 clsx@^2.1.0
```

**TypeScript Support**
```bash
npm install -D @types/d3@^7.4.0
```

### 1.3 Project Structure Setup

**Create Component Architecture**
```bash
mkdir -p src/components/{ui,charts,layouts,features}
mkdir -p src/hooks
mkdir -p src/lib
mkdir -p src/types
mkdir -p src/api
```

**Directory Structure**
```
src/
├── components/
│   ├── ui/           # Reusable UI components
│   ├── charts/       # Visualization components
│   ├── layouts/      # Page layouts
│   └── features/     # Feature-specific components
├── hooks/            # Custom React hooks
├── lib/              # Utility functions
├── types/            # TypeScript definitions
├── api/              # API integration
└── pages/            # Page components
```

### 1.4 API Integration Layer

**Step 1: Create API Client**
```typescript
// src/api/client.ts
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8080';

export class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      ...options,
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }

    return response.json();
  }

  // Repository endpoints
  async createRepository(data: { url: string; branch?: string }) {
    return this.request('/api/repositories', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getRepository(id: string) {
    return this.request(`/api/repositories/${id}`);
  }

  async getRepositoryAnalysis(id: string) {
    return this.request(`/api/repositories/${id}/analysis`);
  }

  async getInsights(id: string) {
    return this.request(`/api/analysis/insights/${id}`);
  }

  async analyzeCode(code: string, language: string) {
    return this.request('/api/analysis/code', {
      method: 'POST',
      body: JSON.stringify({ code, language }),
    });
  }
}

export const apiClient = new ApiClient();
```

**Step 2: TypeScript Definitions**
```typescript
// src/types/api.ts
export interface Repository {
  id: string;
  url: string;
  name: string;
  status: 'pending' | 'analyzing' | 'completed' | 'failed';
  total_commits: number;
  created_at: string;
  first_commit_date?: string;
  last_commit_date?: string;
}

export interface PatternOccurrence {
  pattern_name: string;
  file_path: string;
  confidence_score: number;
  detected_at: string;
}

export interface Technology {
  name: string;
  first_seen: string;
  usage_count: number;
}

export interface AnalysisSession {
  id: string;
  status: string;
  commits_analyzed: number;
  patterns_found: number;
  started_at: string;
  completed_at?: string;
}

export interface RepositoryAnalysis {
  repository_id: string;
  status: string;
  analysis_session: AnalysisSession;
  technologies: {
    language: Technology[];
    framework: Technology[];
    tool: Technology[];
  };
  patterns: PatternOccurrence[];
  insights: Insight[];
}

export interface Insight {
  type: 'info' | 'pattern_summary' | 'technology_adoption' | 'ai_analysis';
  title: string;
  description: string;
  data: any;
}
```

### 1.5 Core UI Component Library

**Button Component (Tailwind v4.1)**
```typescript
// src/components/ui/button.tsx
import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "../../lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90",
        destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
        outline: "border border-input bg-background hover:bg-accent hover:text-accent-foreground",
        secondary: "bg-secondary text-secondary-foreground hover:bg-secondary/80",
        ghost: "hover:bg-accent hover:text-accent-foreground",
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-md px-3",
        lg: "h-11 rounded-md px-8",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }
```

**Utility Functions**
```typescript
// src/lib/utils.ts
import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(dateString: string) {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });
}

export function formatCommitCount(count: number) {
  if (count >= 1000) {
    return `${(count / 1000).toFixed(1)}k`;
  }
  return count.toString();
}
```

### 1.6 Chart Component Implementation

**Pattern Evolution Timeline**
```typescript
// src/components/charts/PatternTimeline.tsx
import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface PatternTimelineProps {
  patterns: PatternOccurrence[];
}

export const PatternTimeline: React.FC<PatternTimelineProps> = ({ patterns }) => {
  const timelineData = React.useMemo(() => {
    const grouped = patterns.reduce((acc, pattern) => {
      const month = new Date(pattern.detected_at).toISOString().slice(0, 7);
      if (!acc[month]) {
        acc[month] = { month, patterns: {} };
      }
      acc[month].patterns[pattern.pattern_name] = 
        (acc[month].patterns[pattern.pattern_name] || 0) + 1;
      return acc;
    }, {} as Record<string, any>);

    return Object.values(grouped).sort((a: any, b: any) => 
      a.month.localeCompare(b.month)
    );
  }, [patterns]);

  const patternNames = Array.from(
    new Set(patterns.map(p => p.pattern_name))
  );

  const colors = [
    '#8884d8', '#82ca9d', '#ffc658', '#ff7300', 
    '#00ff00', '#ff0000', '#0000ff', '#ffff00'
  ];

  return (
    <div className="w-full h-96">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={timelineData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="month" />
          <YAxis />
          <Tooltip />
          <Legend />
          {patternNames.map((pattern, index) => (
            <Line
              key={pattern}
              type="monotone"
              dataKey={`patterns.${pattern}`}
              stroke={colors[index % colors.length]}
              strokeWidth={2}
              dot={{ r: 4 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};
```

**Technology Stack Visualization**
```typescript
// src/components/charts/TechnologyStack.tsx
import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

interface TechnologyStackProps {
  technologies: {
    language: Technology[];
    framework: Technology[];
    tool: Technology[];
  };
}

export const TechnologyStack: React.FC<TechnologyStackProps> = ({ technologies }) => {
  const chartData = React.useMemo(() => {
    const allTech = [
      ...technologies.language.map(t => ({ ...t, category: 'Language' })),
      ...technologies.framework.map(t => ({ ...t, category: 'Framework' })),
      ...technologies.tool.map(t => ({ ...t, category: 'Tool' })),
    ].sort((a, b) => b.usage_count - a.usage_count).slice(0, 10);

    return allTech;
  }, [technologies]);

  const getBarColor = (category: string) => {
    switch (category) {
      case 'Language': return '#8884d8';
      case 'Framework': return '#82ca9d';
      case 'Tool': return '#ffc658';
      default: return '#ff7300';
    }
  };

  return (
    <div className="w-full h-96">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} layout="horizontal">
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis type="number" />
          <YAxis dataKey="name" type="category" width={120} />
          <Tooltip />
          <Bar dataKey="usage_count">
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={getBarColor(entry.category)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};
```

### 1.7 Dashboard Layout Components

**Main Dashboard**
```typescript
// src/components/features/Dashboard.tsx
import React, { useState, useEffect } from 'react';
import { Button } from '../ui/button';
import { PatternTimeline } from '../charts/PatternTimeline';
import { TechnologyStack } from '../charts/TechnologyStack';
import { apiClient } from '../../api/client';

export const Dashboard: React.FC = () => {
  const [repositories, setRepositories] = useState([]);
  const [selectedRepo, setSelectedRepo] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleAnalyzeRepository = async (url: string) => {
    setLoading(true);
    try {
      const repo = await apiClient.createRepository({ url });
      setRepositories(prev => [...prev, repo]);
      setSelectedRepo(repo.id);
      
      // Poll for analysis completion
      const pollAnalysis = async () => {
        const analysis = await apiClient.getRepositoryAnalysis(repo.id);
        if (analysis.status === 'completed') {
          setAnalysis(analysis);
          setLoading(false);
        } else if (analysis.status === 'failed') {
          setLoading(false);
        } else {
          setTimeout(pollAnalysis, 5000);
        }
      };
      
      pollAnalysis();
    } catch (error) {
      console.error('Analysis failed:', error);
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8">
        <header className="mb-8">
          <h1 className="text-4xl font-bold text-foreground mb-2">
            Code Evolution Tracker
          </h1>
          <p className="text-muted-foreground">
            AI-powered repository analysis and pattern detection
          </p>
        </header>

        {analysis ? (
          <div className="space-y-8">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="card p-6">
                <h3 className="text-lg font-semibold mb-2">Commits Analyzed</h3>
                <p className="text-3xl font-bold text-primary">
                  {analysis.analysis_session.commits_analyzed}
                </p>
              </div>
              <div className="card p-6">
                <h3 className="text-lg font-semibold mb-2">Patterns Found</h3>
                <p className="text-3xl font-bold text-primary">
                  {analysis.analysis_session.patterns_found}
                </p>
              </div>
              <div className="card p-6">
                <h3 className="text-lg font-semibold mb-2">Technologies</h3>
                <p className="text-3xl font-bold text-primary">
                  {Object.values(analysis.technologies).flat().length}
                </p>
              </div>
              <div className="card p-6">
                <h3 className="text-lg font-semibold mb-2">Status</h3>
                <p className="text-lg font-semibold text-green-600 capitalize">
                  {analysis.status}
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <div className="card p-6">
                <h3 className="text-xl font-semibold mb-4">Pattern Evolution</h3>
                <PatternTimeline patterns={analysis.patterns} />
              </div>
              <div className="card p-6">
                <h3 className="text-xl font-semibold mb-4">Technology Stack</h3>
                <TechnologyStack technologies={analysis.technologies} />
              </div>
            </div>
          </div>
        ) : (
          <div className="card p-8 text-center">
            <h2 className="text-2xl font-semibold mb-4">
              Analyze Your Repository
            </h2>
            <RepositoryInput onAnalyze={handleAnalyzeRepository} loading={loading} />
          </div>
        )}
      </div>
    </div>
  );
};
```

## Phase 2: Enhanced Visualization Features

### 2.1 Advanced Chart Components

**Pattern Network Graph (React Flow)**
```typescript
// src/components/charts/PatternNetwork.tsx
import React, { useMemo } from 'react';
import ReactFlow, { 
  Node, 
  Edge, 
  Background, 
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState
} from '@xyflow/react';

export const PatternNetwork: React.FC<{ patterns: PatternOccurrence[] }> = ({ patterns }) => {
  const { nodes: initialNodes, edges: initialEdges } = useMemo(() => {
    // Create nodes for each unique pattern
    const patternNodes = Array.from(new Set(patterns.map(p => p.pattern_name)))
      .map((pattern, index) => ({
        id: pattern,
        data: { label: pattern },
        position: { x: Math.cos(index * 2 * Math.PI / patterns.length) * 200, 
                   y: Math.sin(index * 2 * Math.PI / patterns.length) * 200 },
        type: 'default',
      }));

    // Create edges based on co-occurrence in files
    const edges: Edge[] = [];
    // Logic to connect patterns that appear in same files
    
    return { nodes: patternNodes, edges };
  }, [patterns]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  return (
    <div className="w-full h-96">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        fitView
      >
        <Background />
        <Controls />
        <MiniMap />
      </ReactFlow>
    </div>
  );
};
```

### 2.2 Real-time Updates (WebSocket Integration)

**WebSocket Hook**
```typescript
// src/hooks/useRealtimeAnalysis.ts
import { useState, useEffect } from 'react';

export const useRealtimeAnalysis = (repositoryId: string) => {
  const [analysisProgress, setAnalysisProgress] = useState(null);
  
  useEffect(() => {
    const ws = new WebSocket(`ws://localhost:8080/ws/analysis/${repositoryId}`);
    
    ws.onmessage = (event) => {
      const update = JSON.parse(event.data);
      setAnalysisProgress(update);
    };
    
    return () => ws.close();
  }, [repositoryId]);
  
  return analysisProgress;
};
```

## Phase 3: Missing MVP Features & Backend Enhancements

### 3.1 Backend Features to Add

#### Repository Comparison Engine
```python
# New endpoint: GET /api/analysis/compare-multiple
# Compare 3+ repositories simultaneously
# Generate similarity matrices and clustering
```

#### Pattern Evolution Timeline API
```python
# New endpoint: GET /api/repositories/{id}/pattern-evolution
# Return time-series data for pattern adoption
# Include complexity progression over time
```

#### Learning Path Generation
```python
# New endpoint: POST /api/analysis/learning-path
# Generate personalized learning recommendations
# Based on current patterns and skill gaps
```

### 3.2 Advanced AI Features

#### Anti-pattern Detection
- Extend pattern detection to identify code smells
- Implement severity scoring for anti-patterns
- Generate refactoring suggestions

#### Code Quality Trends
- Track quality metrics over time
- Identify regression patterns
- Suggest quality improvement strategies

#### Technology Migration Analysis
- Detect technology stack migrations
- Analyze migration success patterns
- Recommend optimal migration paths

## Phase 4: Production Optimization

### 4.1 Performance Enhancements

#### Caching Strategy
```typescript
// Implement React Query for API caching
npm install @tanstack/react-query
```

#### Lazy Loading
```typescript
// Implement component lazy loading
const PatternTimeline = React.lazy(() => import('./PatternTimeline'));
```

### 4.2 Error Handling & UX

#### Error Boundary Implementation
```typescript
// src/components/ErrorBoundary.tsx
class ErrorBoundary extends React.Component {
  // Comprehensive error handling for chart failures
}
```

#### Loading States
```typescript
// Skeleton components for chart loading
const ChartSkeleton: React.FC = () => (
  <div className="animate-pulse">
    {/* Loading skeleton */}
  </div>
);
```

## Implementation Timeline

### Week 1: Core Setup
- Days 1-2: Tailwind v4.1 integration and basic UI components
- Days 3-4: API integration layer and TypeScript definitions
- Days 5-7: Basic dashboard with repository input and analysis display

### Week 2: Visualization
- Days 1-3: Chart component implementation (Recharts integration)
- Days 4-5: Advanced visualizations (React Flow network graphs)
- Days 6-7: Dashboard layout and responsive design

### Week 3: Enhanced Features
- Days 1-2: Real-time updates and WebSocket integration
- Days 3-4: Advanced pattern analysis views
- Days 5-7: Performance optimization and error handling

### Week 4: Polish & Testing
- Days 1-3: UI/UX refinements and accessibility
- Days 4-5: End-to-end testing and bug fixes
- Days 6-7: Documentation and deployment preparation

## Success Metrics

### Technical Metrics
- ✓ All backend APIs integrated and functional
- ✓ Real-time chart updates working
- ✓ Responsive design on mobile/desktop
- ✓ <3 second initial load time
- ✓ Error rate <1% for chart rendering

### User Experience Metrics
- ✓ Intuitive repository analysis workflow
- ✓ Clear visual pattern identification
- ✓ Actionable insights presentation
- ✓ Smooth navigation between views
- ✓ Professional visual design quality

This roadmap provides a comprehensive path from the current backend-complete state to a production-ready application with sophisticated AI-powered code analysis visualization.