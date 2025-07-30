import React from "react";
import { Button } from "../../ui/button";
import { Loader2 } from "lucide-react";

/**
 * MARepositoryList - Renders a list of repositories for selection
 * @param repositories Array of repository objects
 * @param selectedRepoId Currently selected repository ID
 * @param setSelectedRepoId Setter for selected repository ID
 */
export interface MARepositoryListProps {
    repositories: Array<{ id: string; name: string; status?: string }>;
    selectedRepoId: string | null;
    setSelectedRepoId: (id: string) => void;
}

export const MARepositoryList: React.FC<MARepositoryListProps> = ({
    repositories,
    selectedRepoId,
    setSelectedRepoId,
}) => (
    <div className="mt-4 flex flex-wrap gap-2">
        {repositories.map((repo) => (
            <Button
                key={repo.id}
                variant={selectedRepoId === repo.id ? "default" : "outline"}
                size="sm"
                onClick={() => setSelectedRepoId(repo.id)}
                className={`repo-button text-xs ${selectedRepoId === repo.id ? "active" : ""}`}
            >
                {repo.name}
                {repo.status === "analyzing" && (
                    <Loader2 className="w-3 h-3 ml-1 animate-spin" />
                )}
            </Button>
        ))}
    </div>
);
