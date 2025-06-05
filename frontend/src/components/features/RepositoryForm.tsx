// src/components/RepositoryForm.tsx
import React, { useState } from "react";
import { Github, Plus, Loader } from "lucide-react";

interface RepositoryFormProps {
  onSubmit: (url: string, branch: string) => Promise<void>;
  loading: boolean;
}

const RepositoryForm: React.FC<RepositoryFormProps> = ({
  onSubmit,
  loading,
}) => {
  const [url, setUrl] = useState("");
  const [branch, setBranch] = useState("main");
  const [errors, setErrors] = useState<string[]>([]);

  const validateUrl = (url: string): string[] => {
    const errors: string[] = [];

    if (!url.trim()) {
      errors.push("Repository URL is required");
      return errors;
    }

    // Basic GitHub URL validation
    const githubPattern = /^https:\/\/github\.com\/[\w-.]+\/[\w-.]+/;
    if (!githubPattern.test(url)) {
      errors.push("Please enter a valid GitHub repository URL");
    }

    return errors;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const validationErrors = validateUrl(url);
    setErrors(validationErrors);

    if (validationErrors.length === 0) {
      await onSubmit(url.trim(), branch.trim());
    }
  };

  const handleUrlChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setUrl(e.target.value);
    if (errors.length > 0) {
      setErrors([]);
    }
  };

  const exampleUrls = [
    "https://github.com/facebook/react",
    "https://github.com/microsoft/vscode",
    "https://github.com/octocat/Hello-World",
  ];

  return (
    <div className="w-fit mx-auto">
      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label
            htmlFor="url"
            className="block text-sm font-medium text-gray-300 mb-1"
          >
            GitHub Repository URL
          </label>
          <div className="relative">
            <Github className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-500" />
            <input
              type="url"
              id="url"
              value={url}
              onChange={handleUrlChange}
              placeholder="https://github.com/username/repository"
              className={`w-full pl-10 pr-3 py-2.5 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-gray-700 text-gray-100 placeholder-gray-500 ${
                errors.length > 0 ? "border-red-500" : "border-gray-600"
              }`}
              disabled={loading}
            />
          </div>

          {errors.length > 0 && (
            <div className="mt-2">
              {errors.map((error, index) => (
                <p key={index} className="text-sm text-red-400">
                  {error}
                </p>
              ))}
            </div>
          )}

          <div className="mt-3 text-xs text-gray-400">
            <p className="font-medium mb-1">Examples:</p>
            <ul className="list-disc list-inside space-y-1 pl-1">
              {exampleUrls.map((exampleUrl, index) => (
                <li key={index}>
                  <code className="bg-gray-700 px-1.5 py-0.5 rounded-md text-light font-semibold text-[0.7rem]">
                    {exampleUrl.replace("https://github.com/", "")}
                  </code>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div>
          <label
            htmlFor="branch"
            className="block text-sm font-medium text-gray-300 mb-1"
          >
            Branch
          </label>
          <input
            type="text"
            id="branch"
            value={branch}
            onChange={(e) => setBranch(e.target.value)}
            placeholder="main"
            className="w-full px-3 py-2.5 border border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-gray-700 text-gray-100 placeholder-gray-500"
            disabled={loading}
          />
          <p className="mt-1.5 text-xs text-gray-400">
            Default branch to analyze (usually 'main' or 'master')
          </p>
        </div>

        <button
          type="submit"
          disabled={loading || !url.trim()}
          className="w-full flex items-center justify-center px-4 py-2.5 border border-transparent text-sm font-medium rounded-lg text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-800 focus:ring-blue-500 disabled:opacity-60 disabled:cursor-not-allowed transition-opacity"
        >
          {loading ? (
            <>
              <Loader className="h-5 w-5 mr-2 animate-spin" />
              Analyzing Repository...
            </>
          ) : (
            <>
              <Plus className="h-5 w-5 mr-2" />
              Analyze Repository
            </>
          )}
        </button>

        {loading && (
          <div className="bg-blue-900 bg-opacity-40 border border-blue-700 rounded-lg p-3.5">
            <div className="flex items-center text-sm text-blue-300">
              <Loader className="h-4 w-4 mr-2.5 animate-spin" />
              <div>
                <p className="font-medium">Analysis in progress</p>
                <p className="text-xs text-blue-400">
                  This typically takes 2-5 minutes depending on repository size
                </p>
              </div>
            </div>
          </div>
        )}
      </form>
    </div>
  );
};

export default RepositoryForm;
