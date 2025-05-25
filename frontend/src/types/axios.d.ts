/**
 * @fileoverview Type extensions for Axios to support logging metadata
 */

declare module "axios" {
  export interface InternalAxiosRequestConfig {
    metadata?: {
      startTime: number;
      requestId: string;
    };
  }
}
