import { useState } from 'react';
import { createPortal } from 'react-dom';
import { AlertTriangle, ExternalLink, Shield, Activity, Lock, CheckCircle2 } from 'lucide-react';
import { Button } from '../ui/button';

interface RiskDisclosureDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onAccept: () => void;
}

/**
 * Full risk disclosure dialog with transparency features
 * Shows security risks, bandwidth concerns, and source code links
 */
export function RiskDisclosureDialog({ open, onOpenChange, onAccept }: RiskDisclosureDialogProps) {
    const [acknowledgedRisks, setAcknowledgedRisks] = useState({
        exposure: false,
        bandwidth: false,
        security: false,
    });

    if (!open) return null;

    const allAcknowledged = Object.values(acknowledgedRisks).every(Boolean);

    const handleAccept = () => {
        if (allAcknowledged) {
            onAccept();
            // Reset for next time
            setAcknowledgedRisks({
                exposure: false,
                bandwidth: false,
                security: false,
            });
        }
    };

    return createPortal(
        <div
            className="fixed inset-0 z-[9999] flex items-center justify-center p-4 text-white/85"
            style={{ isolation: 'isolate' }}
        >
            {/* Backdrop */}
            <div
                className="absolute inset-0 bg-black/70 backdrop-blur-sm"
                onClick={() => onOpenChange(false)}
            />

            {/* Dialog - scrollable container */}
            <div className="relative w-full max-w-2xl max-h-[90vh] overflow-y-auto">
                <div className="bg-gray-900 border border-gray-700 rounded-lg shadow-2xl my-8">
                    <div className="p-6 space-y-6">
                        {/* Header */}
                        <div className="flex items-start gap-4">
                            <div className="p-3 rounded-full bg-yellow-500/10">
                                <AlertTriangle className="h-6 w-6 text-yellow-500" />
                            </div>
                            <div>
                                <h2 className="text-xl font-bold">Security Disclosure</h2>
                                <p className="text-sm text-muted-foreground mt-1">
                                    Please read and acknowledge these important security considerations before enabling the tunnel.
                                </p>
                            </div>
                        </div>

                        {/* Risk Cards */}
                        <div className="space-y-4">
                            {/* Risk 1: Network Exposure */}
                            <div className="border border-border rounded-lg p-4">
                                <div className="flex items-start gap-3">
                                    <Shield className="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5" />
                                    <div className="flex-1 space-y-2">
                                        <h3 className="font-semibold text-sm">Network Exposure</h3>
                                        <p className="text-sm text-muted-foreground">
                                            Creating a tunnel exposes your local Ollama instance to the internet via a public URL.
                                            Anyone with the URL can potentially make requests to your local AI models during the
                                            tunnel session.
                                        </p>
                                        <label className="flex items-center gap-2 text-sm cursor-pointer">
                                            <input
                                                type="checkbox"
                                                checked={acknowledgedRisks.exposure}
                                                onChange={(e) =>
                                                    setAcknowledgedRisks({ ...acknowledgedRisks, exposure: e.target.checked })
                                                }
                                                className="rounded border-gray-300"
                                            />
                                            <span>I understand the network exposure risks</span>
                                        </label>
                                    </div>
                                </div>
                            </div>

                            {/* Risk 2: Bandwidth Usage */}
                            <div className="border border-border rounded-lg p-4">
                                <div className="flex items-start gap-3">
                                    <Activity className="h-5 w-5 text-orange-500 flex-shrink-0 mt-0.5" />
                                    <div className="flex-1 space-y-2">
                                        <h3 className="font-semibold text-sm">Bandwidth & Performance</h3>
                                        <p className="text-sm text-muted-foreground">
                                            AI model requests can use significant bandwidth and may impact your local network
                                            performance. Large model requests could take several minutes and consume considerable
                                            resources.
                                        </p>
                                        <label className="flex items-center gap-2 text-sm cursor-pointer">
                                            <input
                                                type="checkbox"
                                                checked={acknowledgedRisks.bandwidth}
                                                onChange={(e) =>
                                                    setAcknowledgedRisks({ ...acknowledgedRisks, bandwidth: e.target.checked })
                                                }
                                                className="rounded border-gray-300"
                                            />
                                            <span>I understand the bandwidth implications</span>
                                        </label>
                                    </div>
                                </div>
                            </div>

                            {/* Risk 3: Security Best Practices */}
                            <div className="border border-border rounded-lg p-4">
                                <div className="flex items-start gap-3">
                                    <Lock className="h-5 w-5 text-blue-500 flex-shrink-0 mt-0.5" />
                                    <div className="flex-1 space-y-2">
                                        <h3 className="font-semibold text-sm">Security Measures</h3>
                                        <p className="text-sm text-muted-foreground">
                                            We implement token-based authentication, rate limiting (60 requests/minute), and
                                            request logging. However, you remain responsible for monitoring tunnel usage and
                                            disabling it when not needed.
                                        </p>
                                        <label className="flex items-center gap-2 text-sm cursor-pointer">
                                            <input
                                                type="checkbox"
                                                checked={acknowledgedRisks.security}
                                                onChange={(e) =>
                                                    setAcknowledgedRisks({ ...acknowledgedRisks, security: e.target.checked })
                                                }
                                                className="rounded border-gray-300"
                                            />
                                            <span>I will monitor and disable the tunnel when not in use</span>
                                        </label>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Transparency Section */}
                        <div className="border-t pt-4">
                            <h3 className="font-semibold text-sm mb-3 flex items-center gap-2">
                                <CheckCircle2 className="h-4 w-4 text-green-500" />
                                Transparency & Source Code
                            </h3>
                            <div className="space-y-2 text-sm text-muted-foreground">
                                <p>This feature is fully open source. Review the implementation:</p>
                                <div className="flex flex-col gap-1">
                                    <a
                                        href="https://github.com/Cstannahill/code-evo/blob/main/backend/app/services/secure_tunnel_service.py"
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-primary hover:underline flex items-center gap-1"
                                    >
                                        <ExternalLink className="h-3 w-3" />
                                        Backend Service Implementation
                                    </a>
                                    <a
                                        href="https://github.com/Cstannahill/code-evo/blob/main/backend/app/api/tunnel.py"
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-primary hover:underline flex items-center gap-1"
                                    >
                                        <ExternalLink className="h-3 w-3" />
                                        API Endpoints
                                    </a>
                                    <a
                                        href="https://github.com/Cstannahill/code-evo/blob/main/frontend/src/hooks/useTunnelManager.ts"
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-primary hover:underline flex items-center gap-1"
                                    >
                                        <ExternalLink className="h-3 w-3" />
                                        Frontend Hook
                                    </a>
                                </div>
                            </div>
                        </div>

                        {/* Actions */}
                        <div className="flex gap-3 border-t pt-4">
                            <Button
                                variant="outline"
                                onClick={() => onOpenChange(false)}
                                className="flex-1"
                            >
                                Cancel
                            </Button>
                            <Button
                                onClick={handleAccept}
                                disabled={!allAcknowledged}
                                className="flex-1 hover:bg-[#FFA500]"
                                variant="outline"
                            >
                                I Understand, Continue
                            </Button>
                        </div>
                    </div>
                </div>
            </div>
        </div>,
        document.body
    );
}
