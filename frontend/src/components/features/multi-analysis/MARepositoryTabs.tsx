import React from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../../ui/tabs";
import { Button } from "../../ui/button";
import { Loader2, Users, User, Sparkles } from "lucide-react";

/**
 * Repository display modes
 */
export type RepositoryScope = "user" | "global" | "relevant";

export interface Repository {
    id: string;
    name: string;
    status?: string;
    url?: string;
    description?: string;
    created_by_user?: string;
}

export interface MARepositoryTabsProps {
    userRepositories: Repository[];
    globalRepositories: Repository[];
    relevantRepositories?: Repository[];
    selectedRepoId: string | null;
    setSelectedRepoId: (id: string) => void;
    isLoadingUser?: boolean;
    isLoadingGlobal?: boolean;
    isLoadingRelevant?: boolean;
    currentScope: RepositoryScope;
    onScopeChange: (scope: RepositoryScope) => void;
}

export const MARepositoryTabs: React.FC<MARepositoryTabsProps> = ({
    userRepositories,
    globalRepositories,
    relevantRepositories = [],
    selectedRepoId,
    setSelectedRepoId,
    isLoadingUser = false,
    isLoadingGlobal = false,
    isLoadingRelevant = false,
    currentScope,
    onScopeChange,
}) => {
    const renderRepositoryList = (repositories: Repository[], isLoading: boolean) => {
        if (isLoading) {
            return (
                <div className="flex items-center justify-center py-8">
                    <Loader2 className="w-6 h-6 animate-spin mr-2 text-yellow-500" />
                    <span className="text-sm text-gray-400">Loading repositories...</span>
                </div>
            );
        }

        if (repositories.length === 0) {
            return (
                <div className="text-center py-8">
                    <div className="text-gray-500 mb-2">
                        <Users className="w-8 h-8 mx-auto mb-2 opacity-50" />
                    </div>
                    <p className="text-sm text-gray-400">No repositories found.</p>
                    <p className="text-xs text-gray-500 mt-1">
                        {currentScope === "user" ? "Create your first repository above" : "Check back later for community repositories"}
                    </p>
                </div>
            );
        }

        return (
            <div className="mt-4 flex flex-wrap gap-2">
                {repositories.map((repo) => (
                    <Button
                        key={repo.id}
                        variant={selectedRepoId === repo.id ? "default" : "outline"}
                        size="sm"
                        onClick={() => setSelectedRepoId(repo.id)}
                        className={`
                            repo-button ctan-button text-xs transition-all duration-200 hover:scale-105
                            ${selectedRepoId === repo.id
                                ? "bg-yellow-600 hover:bg-yellow-500 text-black border-yellow-500 shadow-lg shadow-yellow-500/20 active"
                                : "bg-gray-800/50 hover:bg-gray-700/70 text-gray-300 border-gray-600/50 hover:border-yellow-500/50"
                            }
                        `}
                        title={repo.url || repo.description}
                    >
                        {repo.name}
                        {repo.status === "analyzing" && (
                            <Loader2 className="w-3 h-3 ml-1 animate-spin text-yellow-400" />
                        )}
                        {repo.status === "pending" && (
                            <div className="w-3 h-3 ml-1 bg-yellow-400 rounded-full animate-pulse shadow-sm shadow-yellow-400/50" />
                        )}
                        {repo.status === "completed" && (
                            <div className="w-2 h-2 ml-1 bg-green-400 rounded-full" />
                        )}
                    </Button>
                ))}
            </div>
        );
    };

    return (
        <Tabs
            value={currentScope}
            onValueChange={(value) => onScopeChange(value as RepositoryScope)}
            className="w-full"
        >
            <TabsList className="grid w-full grid-cols-3 bg-gray-900/50 border border-gray-700/50 rounded-lg p-1">
                <TabsTrigger
                    value="user"
                    className="ctan-tab flex items-center gap-2 data-[state=active]:bg-yellow-600/20 data-[state=active]:text-yellow-300 data-[state=active]:border-yellow-500/50 text-gray-400 hover:text-gray-200 transition-all duration-200"
                >
                    <User className="w-4 h-4 ctan-icon" />
                    <span className="hidden sm:inline">My Repositories</span>
                    <span className="sm:hidden">Mine</span>
                    <span className="bg-gray-700/50 text-yellow-400 px-1.5 py-0.5 text-xs rounded-full min-w-[1.5rem] h-5 flex items-center justify-center">
                        {userRepositories.length}
                    </span>
                </TabsTrigger>
                <TabsTrigger
                    value="relevant"
                    className="ctan-tab flex items-center gap-2 data-[state=active]:bg-yellow-600/20 data-[state=active]:text-yellow-300 data-[state=active]:border-yellow-500/50 text-gray-400 hover:text-gray-200 transition-all duration-200"
                >
                    <Sparkles className="w-4 h-4 ctan-icon" />
                    <span className="hidden sm:inline">For You</span>
                    <span className="sm:hidden">For You</span>
                    <span className="bg-gray-700/50 text-yellow-400 px-1.5 py-0.5 text-xs rounded-full min-w-[1.5rem] h-5 flex items-center justify-center">
                        {relevantRepositories.length}
                    </span>
                </TabsTrigger>
                <TabsTrigger
                    value="global"
                    className="ctan-tab flex items-center gap-2 data-[state=active]:bg-yellow-600/20 data-[state=active]:text-yellow-300 data-[state=active]:border-yellow-500/50 text-gray-400 hover:text-gray-200 transition-all duration-200"
                >
                    <Users className="w-4 h-4 ctan-icon" />
                    <span className="hidden sm:inline">Global Pool</span>
                    <span className="sm:hidden">Global</span>
                    <span className="bg-gray-700/50 text-yellow-400 px-1.5 py-0.5 text-xs rounded-full min-w-[1.5rem] h-5 flex items-center justify-center">
                        {globalRepositories.length}
                    </span>
                </TabsTrigger>
            </TabsList>

            <TabsContent value="user" className="mt-4">
                <div className="ctan-card p-4 border border-gray-700/50 rounded-lg bg-gray-900/30 backdrop-blur-sm">
                    <div className="flex items-center gap-2 mb-3">
                        <div className="w-6 h-6 rounded-full bg-yellow-600/20 flex items-center justify-center">
                            <User className="w-3 h-3 text-yellow-400 ctan-icon" />
                        </div>
                        <h3 className="text-sm font-medium text-gray-200">Your Repositories</h3>
                        <div className="flex-1 h-px bg-gradient-to-r from-yellow-500/20 to-transparent"></div>
                    </div>
                    <p className="text-xs text-gray-400 mb-3">
                        Repositories you've created and analyzed
                    </p>
                    {renderRepositoryList(userRepositories, isLoadingUser)}
                </div>
            </TabsContent>

            <TabsContent value="relevant" className="mt-4">
                <div className="ctan-card p-4 border border-gray-700/50 rounded-lg bg-gray-900/30 backdrop-blur-sm">
                    <div className="flex items-center gap-2 mb-3">
                        <div className="w-6 h-6 rounded-full bg-yellow-600/20 flex items-center justify-center">
                            <Sparkles className="w-3 h-3 text-yellow-400 ctan-icon" />
                        </div>
                        <h3 className="text-sm font-medium text-gray-200">Recommended for You</h3>
                        <div className="flex-1 h-px bg-gradient-to-r from-yellow-500/20 to-transparent"></div>
                    </div>
                    <p className="text-xs text-gray-400 mb-3">
                        Repositories recommended based on your analysis history and preferences
                    </p>
                    {renderRepositoryList(relevantRepositories, isLoadingRelevant)}
                </div>
            </TabsContent>

            <TabsContent value="global" className="mt-4">
                <div className="ctan-card p-4 border border-gray-700/50 rounded-lg bg-gray-900/30 backdrop-blur-sm">
                    <div className="flex items-center gap-2 mb-3">
                        <div className="w-6 h-6 rounded-full bg-yellow-600/20 flex items-center justify-center">
                            <Users className="w-3 h-3 text-yellow-400 ctan-icon" />
                        </div>
                        <h3 className="text-sm font-medium text-gray-200">Global Repository Pool</h3>
                        <div className="flex-1 h-px bg-gradient-to-r from-yellow-500/20 to-transparent"></div>
                    </div>
                    <p className="text-xs text-gray-400 mb-3">
                        All public repositories analyzed by the community
                    </p>
                    {renderRepositoryList(globalRepositories, isLoadingGlobal)}
                </div>
            </TabsContent>
        </Tabs>
    );
};
