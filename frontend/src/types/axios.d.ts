import "axios";

declare module "axios" {
  export interface AxiosRequestConfig {
    metadata?: {
      // Make it optional if it's not always present
      startTime?: number;
      requestId?: string;
    };
  }
}
