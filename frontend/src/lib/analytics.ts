export const trackModelSelection = (modelName: string) => {
  if (typeof gtag !== "undefined") {
    gtag("event", "model_selected", {
      model_name: modelName,
      custom_parameter: "single_analysis",
    });
  }
};

export const trackRepositoryAnalysis = (modelName: string, repoUrl: string) => {
  if (typeof gtag !== "undefined") {
    gtag("event", "repository_analysis_started", {
      model_name: modelName,
      repository_type: "github",
    });
  }
};
