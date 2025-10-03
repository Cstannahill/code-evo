# What It Returns

## Analysis Summary

```json
{
  "repository_id": "c92fdf38-e709-4bc6-a479-2d3abb4008b2",
  "status": "completed",
  "analysis_session": {
    "id": "6c7eed23-10c7-4586-a94e-ded04166badb",
    "status": "completed",
    "commits_analyzed": 50,
    "patterns_found": 10,
    "started_at": "2025-05-24T07:19:24.548209",
    "completed_at": "2025-05-24T07:19:44.123593"
  },
  "technologies": {
    "language": [
      {
        "name": "JSON",
        "first_seen": "2017-10-28T22:13:02",
        "usage_count": 42
      },
      {
        "name": "Markdown",
        "first_seen": "2017-10-28T22:13:02",
        "usage_count": 75
      },
      {
        "name": "YAML",
        "first_seen": "2017-10-28T22:13:02",
        "usage_count": 7
      },
      {
        "name": "JavaScript",
        "first_seen": "2017-10-28T22:13:02",
        "usage_count": 268
      },
      {
        "name": "TypeScript",
        "first_seen": "2017-10-28T22:13:02",
        "usage_count": 10
      },
      {
        "name": "CSS",
        "first_seen": "2017-10-28T22:13:02",
        "usage_count": 12
      },
      {
        "name": "HTML",
        "first_seen": "2017-10-28T22:13:02",
        "usage_count": 4
      },
      {
        "name": "React TypeScript",
        "first_seen": "2017-10-28T22:13:02",
        "usage_count": 7
      },
      {
        "name": "SCSS",
        "first_seen": "2017-10-28T22:13:02",
        "usage_count": 5
      }
    ],
    "framework": [
      {
        "name": "React",
        "first_seen": "2017-10-28T22:13:02",
        "usage_count": 1
      }
    ],
    "tool": [
      {
        "name": "Webpack",
        "first_seen": "2017-10-28T22:13:02",
        "usage_count": 1
      },
      {
        "name": "Jest",
        "first_seen": "2017-10-28T22:13:02",
        "usage_count": 1
      }
    ]
  },
  "patterns": [
    {
      "pattern_name": "useState",
      "file_path": "docusaurus/website/src/pages/index.js",
      "confidence_score": 0.8,
      "detected_at": "2025-05-24T07:19:36.470262"
    },
    {
      "pattern_name": "class components",
      "file_path": "docusaurus/website/src/pages/index.js",
      "confidence_score": 0.8,
      "detected_at": "2025-05-24T07:19:36.476560"
    },
    {
      "pattern_name": "javascript_es6",
      "file_path": "docusaurus/website/src/pages/index.js",
      "confidence_score": 0.8,
      "detected_at": "2025-05-24T07:19:36.476564"
    },
    {
      "pattern_name": "useEffect",
      "file_path": "docusaurus/website/src/pages/index.js",
      "confidence_score": 0.8,
      "detected_at": "2025-05-24T07:19:40.495949"
    },
    {
      "pattern_name": "async_await",
      "file_path": "packages/create-react-app/createReactApp.js",
      "confidence_score": 0.8,
      "detected_at": "2025-05-24T07:19:40.495954"
    },
    {
      "pattern_name": "react_hooks",
      "file_path": "packages/create-react-app/createReactApp.js",
      "confidence_score": 0.8,
      "detected_at": "2025-05-24T07:19:40.495958"
    },
    {
      "pattern_name": "async_await",
      "file_path": "packages/create-react-app/createReactApp.js",
      "confidence_score": 0.8,
      "detected_at": "2025-05-24T07:19:40.495961"
    },
    {
      "pattern_name": "prompts",
      "file_path": "packages/create-react-app/createReactApp.js",
      "confidence_score": 0.8,
      "detected_at": "2025-05-24T07:19:44.072960"
    },
    {
      "pattern_name": "react_hooks",
      "file_path": "packages/create-react-app/createReactApp.js",
      "confidence_score": 0.8,
      "detected_at": "2025-05-24T07:19:44.072965"
    },
    {
      "pattern_name": "javascript_es6",
      "file_path": "packages/react-scripts/fixtures/kitchensink/template/src/features/config/BaseUrl.test.js",
      "confidence_score": 0.8,
      "detected_at": "2025-05-24T07:19:44.072969"
    }
  ],
  "insights": [
    {
      "type": "info",
      "title": "Repository Analysis Complete",
      "description": "Successfully analyzed 50 commits, detected 9 programming languages, and found 10 code patterns.",
      "data": {
        "technologies": {
          "languages": {
            "JSON": 42,
            "Markdown": 75,
            "YAML": 7,
            "JavaScript": 268,
            "TypeScript": 10,
            "CSS": 12,
            "HTML": 4,
            "React TypeScript": 7,
            "SCSS": 5
          },
          "frameworks": ["React"],
          "libraries": [],
          "tools": ["Webpack", "Jest"]
        },
        "patterns_detected": 10,
        "commits_analyzed": 50
      }
    }
  ]
}
```

## Insights

```json
{
  "repository_id": "c92fdf38-e709-4bc6-a479-2d3abb4008b2",
  "pattern_timeline": {
    "timeline": [],
    "summary": {}
  },
  "pattern_statistics": {
    "useState": {
      "category": "detected",
      "occurrences": 1,
      "complexity_level": "intermediate",
      "is_antipattern": false
    },
    "class components": {
      "category": "detected",
      "occurrences": 1,
      "complexity_level": "intermediate",
      "is_antipattern": false
    },
    "javascript_es6": {
      "category": "detected",
      "occurrences": 2,
      "complexity_level": "intermediate",
      "is_antipattern": false
    },
    "useEffect": {
      "category": "detected",
      "occurrences": 1,
      "complexity_level": "intermediate",
      "is_antipattern": false
    },
    "async_await": {
      "category": "detected",
      "occurrences": 2,
      "complexity_level": "intermediate",
      "is_antipattern": false
    },
    "react_hooks": {
      "category": "detected",
      "occurrences": 2,
      "complexity_level": "intermediate",
      "is_antipattern": false
    },
    "prompts": {
      "category": "detected",
      "occurrences": 1,
      "complexity_level": "intermediate",
      "is_antipattern": false
    }
  },
  "insights": [
    {
      "type": "info",
      "title": "Repository Overview",
      "description": "Analyzed 1520 commits with 7 patterns detected.",
      "data": {
        "repository_id": "c92fdf38-e709-4bc6-a479-2d3abb4008b2",
        "patterns": {
          "useState": {
            "category": "detected",
            "occurrences": 1,
            "complexity_level": "intermediate",
            "is_antipattern": false
          },
          "class components": {
            "category": "detected",
            "occurrences": 1,
            "complexity_level": "intermediate",
            "is_antipattern": false
          },
          "javascript_es6": {
            "category": "detected",
            "occurrences": 2,
            "complexity_level": "intermediate",
            "is_antipattern": false
          },
          "useEffect": {
            "category": "detected",
            "occurrences": 1,
            "complexity_level": "intermediate",
            "is_antipattern": false
          },
          "async_await": {
            "category": "detected",
            "occurrences": 2,
            "complexity_level": "intermediate",
            "is_antipattern": false
          },
          "react_hooks": {
            "category": "detected",
            "occurrences": 2,
            "complexity_level": "intermediate",
            "is_antipattern": false
          },
          "prompts": {
            "category": "detected",
            "occurrences": 1,
            "complexity_level": "intermediate",
            "is_antipattern": false
          }
        },
        "total_commits": 1520,
        "technologies": [
          "JSON",
          "Markdown",
          "YAML",
          "JavaScript",
          "TypeScript",
          "CSS",
          "HTML",
          "React TypeScript",
          "SCSS",
          "React",
          "Webpack",
          "Jest"
        ]
      }
    },
    {
      "type": "pattern_summary",
      "title": "Detected 7 Programming Patterns",
      "description": "Most common patterns: useState, class components, javascript_es6",
      "data": {
        "patterns": {
          "useState": {
            "category": "detected",
            "occurrences": 1,
            "complexity_level": "intermediate",
            "is_antipattern": false
          },
          "class components": {
            "category": "detected",
            "occurrences": 1,
            "complexity_level": "intermediate",
            "is_antipattern": false
          },
          "javascript_es6": {
            "category": "detected",
            "occurrences": 2,
            "complexity_level": "intermediate",
            "is_antipattern": false
          },
          "useEffect": {
            "category": "detected",
            "occurrences": 1,
            "complexity_level": "intermediate",
            "is_antipattern": false
          },
          "async_await": {
            "category": "detected",
            "occurrences": 2,
            "complexity_level": "intermediate",
            "is_antipattern": false
          },
          "react_hooks": {
            "category": "detected",
            "occurrences": 2,
            "complexity_level": "intermediate",
            "is_antipattern": false
          },
          "prompts": {
            "category": "detected",
            "occurrences": 1,
            "complexity_level": "intermediate",
            "is_antipattern": false
          }
        }
      }
    },
    {
      "type": "technology_adoption",
      "title": "Technology Stack Analysis",
      "description": "Primary technologies: JavaScript (1520 commits), React ecosystem detected",
      "data": {
        "technologies": [
          "JSON",
          "Markdown",
          "YAML",
          "JavaScript",
          "TypeScript",
          "CSS",
          "HTML",
          "React TypeScript",
          "SCSS",
          "React",
          "Webpack",
          "Jest"
        ]
      }
    },
    {
      "type": "ai_analysis",
      "title": "AI Architecture Analysis",
      "description": "AI-generated insights about your codebase architecture and technology choices",
      "data": {
        "architecture_insights": [
          "The use of JSON, Markdown, YAML, JavaScript, and TypeScript is a well-rounded technology stack that provides a strong foundation for building modern web applications. These technologies are widely used in the industry and have a large community of developers who contribute to their development and maintenance."
        ],
        "technology_trends": [
          "The use of JSON, Markdown, YAML, JavaScript, and TypeScript is becoming increasingly popular due to its versatility and ability to handle various tasks. The trend of using these technologies is driven by the need for efficient and scalable development processes that can handle complex data structures and large-scale applications."
        ],
        "recommendations": [
          "Consider using a more modern version of TypeScript, as it offers better support for modern web development features such as async/await, optional chaining, and nullish coalescing. Additionally, consider using a more robust build system such as Webpack or Rollup to optimize the performance of your application."
        ]
      }
    },
    {
      "type": "info",
      "title": "Analysis Complete",
      "description": "Repository analysis completed successfully. Analyzed 1520 commits across 12 technologies.",
      "data": {}
    }
  ],
  "ai_powered": true,
  "summary": {
    "total_patterns": 7,
    "antipatterns_detected": 0,
    "complexity_distribution": {
      "simple": 0,
      "intermediate": 7,
      "advanced": 0
    }
  }
}
```
