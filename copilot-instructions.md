# Copilot Instructions

## Rules - Important

- @error Rule - Robust Error Handling: Always include comprehensive error handling with meaningful error messages and appropriate logging levels.
- @performance Rule - Performance Considerations: When generating code that processes large datasets or handles high traffic, include performance optimizations and scalability considerations.

- @accessibility Rule - Accessibility First: When generating UI components or frontend code, ensure WCAG compliance and keyboard navigation support.

- @documentation Rule - Self-Documenting Code: Generate code with clear variable names, comprehensive comments for complex logic, and include usage examples where appropriate.

- @typescript Rule - Strict Explicit Typing: When generating TypeScript code, follow these strict typing requirements:

  - All function parameters must have explicit type annotations
  - All functions must have explicit return type annotations (never rely on inference)
  - All variable declarations must have explicit types when not immediately obvious
  - Never use `any` type - use `unknown`, proper unions, or define specific interfaces
  - All object properties must be explicitly typed via interfaces or type aliases
  - Generic types must have explicit constraints where applicable
  - Array and Promise types must be explicitly parameterized
  - All exported functions and classes must have complete type definitions
  - Include JSDoc comments with @param and @returns type documentation

- @types Rule - Strict Type Organization: When generating TypeScript code, enforce clean type architecture:

  - All interfaces, types, and enums must be defined in `types/` directory
  - Organize types by domain/feature in separate files (e.g., `types/user.ts`, `types/product.ts`)
  - Never define types inline within component, service, or utility files
  - Use barrel exports in `types/index.ts` for centralized imports
  - Import types using `import type { }` syntax for type-only imports
  - Prefix type files with descriptive names reflecting their domain
  - Each type file should group related types and include comprehensive JSDoc
  - Use consistent naming: PascalCase for interfaces/types, SCREAMING_SNAKE_CASE for enums
  - Include a `types/common.ts` for shared utility types across domains

- @nextjs Rule - Next.js 15+ Dynamic Routes Compliance: When generating Next.js dynamic route code, enforce these requirements:

  - Always declare `params` prop as `Promise<{ [key]: type }>` type
  - Use `async/await` syntax to resolve params - never synchronous access
  - Apply correct TypeScript types: `[slug]` → `{ slug: string }`, `[...slug]` → `{ slug: string[] }`, `[[...slug]]` → `{ slug?: string[] }`
  - Make page/layout components async functions when using params
  - Include try/catch error handling for param resolution
  - Apply Promise pattern to pages, layouts, and API route handlers consistently
  - For client components, use React's `use()` hook instead of await
  - Always destructure params after awaiting: `const { slug } = await params;`
  - Generate proper generateStaticParams functions for static generation

- @componentization Rule - Strict Component Decomposition: When generating page or complex components, enforce modular architecture:

  - Break monolithic components into single-responsibility sections (max 50 lines per page component)
  - Use consistent naming: feature prefix + descriptive name (e.g., `HMHero`, `RMIntroduction`, `PDProductList`)
  - Organize in feature directories: `components/[feature]/ComponentName.tsx`
  - Extract reusable elements to `components/shared/` (e.g., `SectionDivider`, `LoadingSpinner`)
  - Make components self-contained - own their styling, content, and minimal data needs
  - Compose pages as clean semantic layouts with imported components
  - Use `SectionDivider` or similar shared components between major sections
  - Each component should handle one logical UI section or responsibility
  - Prefer composition over complex prop drilling - components should be independently functional

- @context Rule - Automated Project Context Management: Implement mandatory context tracking workflow:
  - **Before every action**: Check root directory for `project-context.md`
  - **If missing**: Create `project-context.md` with initial project assessment
  - **After every action**: Update `project-context.md` with two required sections:
    - **Overall State**: Current functionality, implemented features, working components, completed integrations
    - **Immediate Next Steps**: Specific actionable tasks (e.g., "complete user authentication flow", "implement project deletion", "add error handling to API routes")
  - Keep context concise but comprehensive - focus on what works and what needs immediate attention
  - Use consistent markdown formatting with clear section headers
  - Update context reflects actual code changes made, not just planned changes
  - Treat context file as project's living development roadmap
