import React from "react";
import { ChevronDown } from "lucide-react";
import { apiClient } from "../../api/client";

type RepoModelsResponse = {
    repository_id: string;
    models: Array<{
        model: string;
        analysis_types: string[];
        count: number;
        latest: string | null;
    }>;
};

export interface ModelSelectorProps {
    repositoryId: string;
    selectedModel?: string | null;
    onChange: (model: string | null) => void;
}

export const ModelSelector: React.FC<ModelSelectorProps> = ({
    repositoryId,
    selectedModel,
    onChange,
}) => {
    const [loading, setLoading] = React.useState(false);
    const [error, setError] = React.useState<string | null>(null);
    const [models, setModels] = React.useState<RepoModelsResponse["models"]>([]);
    const initializedRef = React.useRef(false);

    React.useEffect(() => {
        let cancelled = false;
        (async () => {
            try {
                setLoading(true);
                setError(null);
                const resp: RepoModelsResponse = await apiClient.getRepositoryModels(
                    repositoryId
                );
                if (!cancelled) {
                    setModels(resp.models || []);
                }
            } catch {
                if (!cancelled) setError("Failed to load models");
            } finally {
                if (!cancelled) setLoading(false);
            }
        })();
        return () => {
            cancelled = true;
        };
    }, [repositoryId]);

    // Auto-select the first available concrete model once models load
    React.useEffect(() => {
        if (initializedRef.current) return;
        if (!selectedModel && models && models.length > 0) {
            initializedRef.current = true;
            onChange(models[0].model || null);
        }
    }, [models, selectedModel, onChange]);

    const hasModels = models && models.length > 0;

    return (
        <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">Analysis model</span>
            <div className="relative inline-flex">
                <select
                    className="appearance-none bg-card border px-3 py-1.5 pr-8 rounded-md text-sm"
                    disabled={!hasModels || loading}
                    value={selectedModel || (hasModels ? models[0]?.model : "")}
                    onChange={(e) => onChange(e.target.value || null)}
                    aria-label="Select analysis model"
                >
                    {models.map((m) => (
                        <option key={m.model} value={m.model}>
                            {m.model} {m.analysis_types?.length ? `· ${m.analysis_types.join("/")}` : ""}
                        </option>
                    ))}
                </select>
                <ChevronDown className="pointer-events-none absolute right-2 top-2.5 h-4 w-4 opacity-60" />
            </div>
            {loading && <span className="text-xs text-muted-foreground">Loading…</span>}
            {error && <span className="text-xs text-destructive">{error}</span>}
        </div>
    );
};
