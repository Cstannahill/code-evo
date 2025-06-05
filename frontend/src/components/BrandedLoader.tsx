import { Loader2 } from "lucide-react";

// components/BrandedLoader.tsx
export const BrandedLoader: React.FC<{ message?: string }> = ({ message }) => (
  <div className="flex flex-col items-center justify-center p-8">
    <div className="ctan-loading w-12 h-12 relative">
      <Loader2 className="w-12 h-12 animate-spin text-ctan-gold" />
    </div>
    {message && <p className="mt-4 text-ctan-text-secondary">{message}</p>}
  </div>
);
