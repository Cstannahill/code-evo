import { useState } from 'react';
import { Wifi, WifiOff, Loader2, AlertCircle, X } from 'lucide-react';
import { Button } from '../ui/button';
import { useTunnelManager } from '../../hooks/useTunnelManager';
import { RiskDisclosureDialog } from './RiskDisclosureDialog';
import { TunnelSetupWizard } from './TunnelSetupWizard';

/**
 * Compact tunnel toggle for navigation bar
 * Shows connection status and provides quick access to setup/disable
 */
export function TunnelToggle() {
    const {
        connection,
        isLoading,
        error,
        isActive,
        statusText,
        statusColor,
        disableTunnel,
    } = useTunnelManager();

    const [showRiskDialog, setShowRiskDialog] = useState(false);
    const [showWizard, setShowWizard] = useState(false);
    const [showMenu, setShowMenu] = useState(false);
    const [isDisconnecting, setIsDisconnecting] = useState(false);

    // Handle disconnect
    const handleDisconnect = async () => {
        setIsDisconnecting(true);
        await disableTunnel();
        setIsDisconnecting(false);
        setShowMenu(false);
    };

    // Handle enable - show risk disclosure first
    const handleEnable = () => {
        setShowMenu(false);
        setShowRiskDialog(true);
    };

    // After risk disclosure is accepted, show wizard
    const handleRiskAccepted = () => {
        setShowRiskDialog(false);
        setShowWizard(true);
    };

    // Get status icon
    const StatusIcon = isLoading
        ? Loader2
        : isActive
            ? Wifi
            : WifiOff;

    // Get status color classes
    const getStatusColorClass = () => {
        switch (statusColor) {
            case 'green':
                return 'text-green-500';
            case 'yellow':
                return 'text-yellow-500';
            case 'red':
                return 'text-red-500';
            default:
                return 'text-gray-400';
        }
    };

    const getBadgeColor = () => {
        switch (statusColor) {
            case 'green':
                return 'bg-green-500/10 text-green-500 border-green-500/20';
            case 'yellow':
                return 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20';
            case 'red':
                return 'bg-red-500/10 text-red-500 border-red-500/20';
            default:
                return 'bg-gray-500/10 text-gray-400 border-gray-500/20';
        }
    };

    return (
        <>
            <div className="relative">
                {/* Tunnel Button */}
                <Button
                    variant="ghost"
                    size="sm"
                    className="relative gap-2 px-3"
                    aria-label="Ollama Tunnel Status"
                    onClick={() => setShowMenu(!showMenu)}
                >
                    <StatusIcon
                        className={`h-4 w-4 ${getStatusColorClass()} ${isLoading ? 'animate-spin' : ''
                            }`}
                    />
                    <span className="hidden sm:inline text-sm">Tunnel</span>
                    {isActive && (
                        <span className="absolute -top-1 -right-1 flex h-3 w-3">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                            <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
                        </span>
                    )}
                </Button>

                {/* Dropdown Menu */}
                {showMenu && (
                    <div className="absolute right-0 mt-2 w-80 bg-gray-900 border border-gray-700 text-white/70 rounded-lg shadow-lg z-50">
                        <div className="p-4 space-y-4">
                            {/* Header */}
                            <div className="flex items-start justify-between">
                                <div>
                                    <h4 className="font-semibold text-sm">Ollama Tunnel</h4>
                                    <p className="text-xs text-muted-foreground mt-1">
                                        Connect your local Ollama to deployed backend
                                    </p>
                                </div>
                                <div className="flex items-center gap-2">
                                    <span
                                        className={`text-xs font-medium px-2 py-1 rounded-md border ${getBadgeColor()}`}
                                    >
                                        {statusText}
                                    </span>
                                    <button
                                        onClick={() => setShowMenu(false)}
                                        className="text-muted-foreground hover:text-foreground btn"
                                    >
                                        <X className="h-4 w-4" />
                                    </button>
                                </div>
                            </div>

                            {/* Error message */}
                            {error && (
                                <div className="flex items-start gap-2 rounded-md bg-destructive/10 p-3 text-destructive">
                                    <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
                                    <p className="text-xs">{error}</p>
                                </div>
                            )}

                            {/* Connection info */}
                            {connection && (
                                <div className="space-y-2 rounded-md bg-muted p-3">
                                    <div className="flex items-center justify-between text-xs">
                                        <span className="text-muted-foreground">Provider:</span>
                                        <span className="font-mono font-medium capitalize">
                                            {connection.provider}
                                        </span>
                                    </div>
                                    <div className="flex items-center justify-between text-xs">
                                        <span className="text-muted-foreground">Requests:</span>
                                        <span className="font-mono font-medium">
                                            {connection.request_count}
                                        </span>
                                    </div>
                                    <div className="flex items-center justify-between text-xs">
                                        <span className="text-muted-foreground">Tunnel URL:</span>
                                        <span className="font-mono text-xs truncate max-w-[180px]">
                                            {connection.tunnel_url ? (() => {
                                                try {
                                                    return new URL(connection.tunnel_url).hostname;
                                                } catch {
                                                    return connection.tunnel_url;
                                                }
                                            })() : 'N/A'}
                                        </span>
                                    </div>
                                </div>
                            )}

                            {/* Actions */}
                            <div className="flex gap-2">
                                {isActive ? (
                                    <Button
                                        onClick={handleDisconnect}
                                        disabled={isDisconnecting}
                                        variant="destructive"
                                        size="sm"
                                        className="flex-1"
                                    >
                                        {isDisconnecting ? (
                                            <>
                                                <Loader2 className="mr-2 h-3 w-3 animate-spin" />
                                                Disconnecting...
                                            </>
                                        ) : (
                                            <>
                                                <WifiOff className="mr-2 h-3 w-3" />
                                                Disconnect
                                            </>
                                        )}
                                    </Button>
                                ) : (
                                    <Button
                                        onClick={handleEnable}
                                        variant="outline"
                                        disabled={isLoading}
                                        size="sm"
                                        className="flex-1 hover:bg-gray-800"
                                    >
                                        <Wifi className="mr-2 h-3 w-3" />
                                        Enable Tunnel
                                    </Button>
                                )}
                            </div>

                            {/* Info note */}
                            <p className="text-xs text-muted-foreground border-t pt-3">
                                <strong>Note:</strong> Tunnel required when using local Ollama
                                with deployed backend.
                            </p>
                        </div>
                    </div>
                )}
            </div>

            {/* Risk Disclosure Dialog */}
            <RiskDisclosureDialog
                open={showRiskDialog}
                onOpenChange={setShowRiskDialog}
                onAccept={handleRiskAccepted}
            />

            {/* Setup Wizard */}
            <TunnelSetupWizard

                open={showWizard}
                onOpenChange={setShowWizard}
            />
        </>
    );
}
