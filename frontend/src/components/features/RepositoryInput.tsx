import React, { useState } from "react";
import { Button } from "../ui/button";

interface RepositoryInputProps {
  onAnalyze: (url: string) => void;
  loading: boolean;
}

export const RepositoryInput: React.FC<RepositoryInputProps> = ({
  onAnalyze,
  loading,
}) => {
  const [url, setUrl] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (url.trim()) {
      onAnalyze(url);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-4">
      <input
        type="url"
        value={url}
        onChange={(e) => setUrl(e.target.value)}
        placeholder="https://github.com/username/repository"
        className="flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
        required
        disabled={loading}
      />
      <Button type="submit" disabled={loading}>
        {loading ? "Analyzing..." : "Analyze"}
      </Button>
    </form>
  );
};
