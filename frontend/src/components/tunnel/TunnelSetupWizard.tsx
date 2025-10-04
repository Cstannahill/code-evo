import { useState } from 'react';
import { createPortal } from 'react-dom';
import { Copy, Check, Loader2, ExternalLink, ArrowRight, ArrowLeft } from 'lucide-react';
import { Button } from '../ui/button';
import { useTunnelManager } from '../../hooks/useTunnelManager';
import type { TunnelProvider } from '../../types/tunnel';

interface TunnelSetupWizardProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
}

/**
 * Step-by-step tunnel setup wizard with Cloudflare and ngrok instructions
 */
export function TunnelSetupWizard({ open, onOpenChange }: TunnelSetupWizardProps) {
    const { registerTunnel, isLoading } = useTunnelManager();

    const [provider, setProvider] = useState<TunnelProvider | null>(null);
    const [step, setStep] = useState(0);
    const [tunnelUrl, setTunnelUrl] = useState('');
    const [copiedCommand, setCopiedCommand] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    if (!open) return null;

    // Copy command to clipboard
    const copyCommand = (command: string) => {
        navigator.clipboard.writeText(command);
        setCopiedCommand(command);
        setTimeout(() => setCopiedCommand(null), 2000);
    };

    // Handle provider selection
    const selectProvider = (selectedProvider: TunnelProvider) => {
        setProvider(selectedProvider);
        setStep(1);
        setError(null);
    };

    // Handle tunnel registration
    const handleRegister = async () => {
        if (!tunnelUrl.trim()) {
            setError('Please enter your tunnel URL');
            return;
        }

        if (!provider) {
            setError('Please select a tunnel provider');
            return;
        }

        // Only cloudflare and ngrok are supported by backend
        if (provider === 'custom') {
            setError('Custom tunnel method is not yet supported. Please use Cloudflare or ngrok.');
            return;
        }

        const success = await registerTunnel(tunnelUrl, provider);
        if (success) {
            onOpenChange(false);
            // Reset wizard for next time
            setProvider(null);
            setStep(0);
            setTunnelUrl('');
            setError(null);
        } else {
            setError('Failed to register tunnel. Please verify the URL is correct and accessible.');
        }
    };

    // Cloudflare Tunnel instructions
    const cloudflareSteps = [
        {
            title: 'Install Cloudflare Tunnel',
            content: (
                <div className="space-y-3 text-white/80">
                    <p className="text-sm text-muted-foreground">
                        Install cloudflared using one of these methods:
                    </p>
                    <div className="space-y-2">
                        <div className="flex items-start gap-2">
                            <span className="text-xs font-mono bg-muted px-2 py-1 rounded">macOS</span>
                            <code className="flex-1 text-xs bg-gray-600 bg-muted p-2 rounded font-mono">
                                brew install cloudflare/cloudflare/cloudflared
                            </code>
                            <button
                                onClick={() => copyCommand('brew install cloudflare/cloudflare/cloudflared')}
                                className="p-1 hover:bg-muted rounded"
                            >
                                {copiedCommand === 'brew install cloudflare/cloudflare/cloudflared' ? (
                                    <Check className="h-4 w-4 text-green-500" />
                                ) : (
                                    <Copy className="h-4 w-4" />
                                )}
                            </button>
                        </div>
                        <div className="flex items-start gap-2">
                            <span className="text-xs font-mono bg-muted px-2 py-1 rounded">Windows</span>
                            <code className="flex-1 text-xs bg-gray-600 p-2 rounded font-mono">
                                winget install --id Cloudflare.cloudflared
                            </code>
                            <button
                                onClick={() => copyCommand('winget install --id Cloudflare.cloudflared')}
                                className="p-1 hover:bg-muted rounded"
                            >
                                {copiedCommand === 'winget install --id Cloudflare.cloudflared' ? (
                                    <Check className="h-4 w-4 text-green-500" />
                                ) : (
                                    <Copy className="h-4 w-4" />
                                )}
                            </button>
                        </div>
                    </div>
                    <a
                        href="https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-primary hover:underline flex items-center gap-1"
                    >
                        <ExternalLink className="h-3 w-3" />
                        More installation options
                    </a>
                </div>
            ),
        },
        {
            title: 'Start Tunnel to Ollama',
            content: (
                <div className="space-y-3">
                    <p className="text-sm text-white/80">
                        Run this command to create a tunnel to your local Ollama instance:
                    </p>
                    <div className="flex items-start gap-2">
                        <code className="flex-1 text-xs bg-gray-600 p-3 rounded font-mono text-white/80">
                            cloudflared tunnel --url http://localhost:11434
                        </code>
                        <button
                            onClick={() => copyCommand('cloudflared tunnel --url http://localhost:11434')}
                            className="p-1 hover:bg-muted rounded align-middle"
                        >
                            {copiedCommand === 'cloudflared tunnel --url http://localhost:11434' ? (
                                <Check className="h-4 w-4 text-green-500" />
                            ) : (
                                <Copy className="h-4 w-4" />
                            )}
                        </button>
                    </div>

                    {/* Info box about certificate warnings */}
                    <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-3">
                        <p className="text-xs text-blue-400 mb-1">
                            <strong>ℹ️ Note:</strong> You may see certificate error messages in red - this is normal!
                        </p>
                        <p className="text-xs text-blue-300/80">
                            Quick tunnels don't require certificates. Look for "Your quick Tunnel has been created!"
                            and "Registered tunnel connection" messages - these confirm it's working.
                        </p>
                    </div>

                    <p className="text-xs text-yellow-600 dark:text-yellow-400">
                        ⚠️ Keep this terminal window open! The tunnel will stay active as long as the command is running.
                    </p>
                </div>
            ),
        },
        {
            title: 'Copy Tunnel URL',
            content: (
                <div className="space-y-3">
                    <p className="text-sm text-white/80">
                        Look for output like this in your terminal:
                    </p>
                    <code className="block text-xs bg-gray-600 text-white p-3 rounded font-mono whitespace-pre">
                        {`Your quick tunnel is https://abc123.trycloudflare.com`}
                    </code>
                    <p className="text-sm text-white/80">
                        Copy that URL and paste it below (including https://):
                    </p>
                    <input
                        type="text"
                        value={tunnelUrl}
                        onChange={(e) => {
                            setTunnelUrl(e.target.value);
                            setError(null);
                        }}
                        placeholder="https://abc123.trycloudflare.com"
                        className="w-full px-3 py-2 border border-border rounded-md bg-background text-sm text-white/80"
                    />
                    {error && (
                        <p className="text-xs text-red-500">{error}</p>
                    )}
                </div>
            ),
        },
    ];

    // ngrok instructions
    const ngrokSteps = [
        {
            title: 'Install ngrok',
            content: (
                <div className="space-y-3">
                    <p className="text-sm text-muted-foreground">
                        Sign up at ngrok.com (free) and install:
                    </p>
                    <div className="space-y-2">
                        <div className="flex items-start gap-2">
                            <span className="text-xs font-mono bg-muted px-2 py-1 rounded">macOS</span>
                            <code className="flex-1 text-xs bg-muted p-2 bg-gray-600 rounded font-mono">
                                brew install ngrok/ngrok/ngrok
                            </code>
                            <button
                                onClick={() => copyCommand('brew install ngrok/ngrok/ngrok')}
                                className="p-1 hover:bg-muted rounded"
                            >
                                {copiedCommand === 'brew install ngrok/ngrok/ngrok' ? (
                                    <Check className="h-4 w-4 text-green-500" />
                                ) : (
                                    <Copy className="h-4 w-4" />
                                )}
                            </button>
                        </div>
                        <div className="flex items-start gap-2">
                            <span className="text-xs font-mono bg-muted px-2 py-1 rounded">Windows</span>
                            <code className="flex-1 text-xs bg-gray-600 p-2 rounded font-mono">
                                choco install ngrok
                            </code>
                            <button
                                onClick={() => copyCommand('choco install ngrok')}
                                className="p-1 hover:bg-muted rounded"
                            >
                                {copiedCommand === 'choco install ngrok' ? (
                                    <Check className="h-4 w-4 text-green-500" />
                                ) : (
                                    <Copy className="h-4 w-4" />
                                )}
                            </button>
                        </div>
                    </div>
                    <a
                        href="https://ngrok.com/download"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-primary hover:underline flex items-center gap-1"
                    >
                        <ExternalLink className="h-3 w-3" />
                        Download from ngrok.com
                    </a>
                </div>
            ),
        },
        {
            title: 'Authenticate ngrok',
            content: (
                <div className="space-y-3">
                    <p className="text-sm text-muted-foreground">
                        Get your authtoken from the ngrok dashboard and run:
                    </p>
                    <code className="block bg-gray-600 text-xs bg-muted p-3 rounded font-mono">
                        ngrok config add-authtoken YOUR_TOKEN_HERE
                    </code>
                    <a
                        href="https://dashboard.ngrok.com/get-started/your-authtoken"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-primary hover:underline flex items-center gap-1"
                    >
                        <ExternalLink className="h-3 w-3" />
                        Get your authtoken
                    </a>
                </div>
            ),
        },
        {
            title: 'Start Tunnel to Ollama',
            content: (
                <div className="space-y-3">
                    <p className="text-sm text-muted-foreground">
                        Run this command to create a tunnel:
                    </p>
                    <div className="flex items-start gap-2">
                        <code className="flex-1 text-xs bg-gray-600 p-3 rounded font-mono">
                            ngrok http 11434
                        </code>
                        <button
                            onClick={() => copyCommand('ngrok http 11434')}
                            className="p-1 hover:bg-muted rounded"
                        >
                            {copiedCommand === 'ngrok http 11434' ? (
                                <Check className="h-4 w-4 text-green-500" />
                            ) : (
                                <Copy className="h-4 w-4" />
                            )}
                        </button>
                    </div>
                    <p className="text-xs text-yellow-600 dark:text-yellow-400">
                        ⚠️ Keep this terminal window open! The tunnel will stay active as long as ngrok is running.
                    </p>
                </div>
            ),
        },
        {
            title: 'Copy Tunnel URL',
            content: (
                <div className="space-y-3">
                    <p className="text-sm text-white/80">
                        Copy the Forwarding URL from the ngrok terminal (starts with https://):
                    </p>
                    <code className="block text-xs bg-gray-600 p-3 rounded font-mono whitespace-pre">
                        {`Forwarding  https://abc-123-def.ngrok-free.app -> http://localhost:11434`}
                    </code>
                    <p className="text-sm text-muted-foreground">
                        Paste the https:// URL below:
                    </p>
                    <input
                        type="text"
                        value={tunnelUrl}
                        onChange={(e) => {
                            setTunnelUrl(e.target.value);
                            setError(null);
                        }}
                        placeholder="https://abc-123-def.ngrok-free.app"
                        className="w-full px-3 py-2 border border-border rounded-md bg-background text-sm"
                    />
                    {error && (
                        <p className="text-xs text-red-500">{error}</p>
                    )}
                </div>
            ),
        },
    ];

    const currentSteps = provider === 'cloudflare' ? cloudflareSteps : ngrokSteps;

    if (!open) return null;

    return createPortal(
        <div
            className="fixed inset-0 z-[9999] flex items-center justify-center p-4"
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
                        <div>
                            <h2 className="text-xl font-bold text-[#FFA500]">Tunnel Setup Wizard</h2>
                            <p className="text-sm text-white/50 mt-1">
                                {!provider
                                    ? 'Choose a tunnel provider to get started'
                                    : `Step ${step} of ${currentSteps.length}`}
                            </p>
                        </div>

                        {/* Provider Selection */}
                        {!provider && (
                            <div className="grid grid-cols-2 gap-4">
                                <button
                                    onClick={() => selectProvider('cloudflare')}
                                    className="border-2 border-border hover:border-primary rounded-lg p-6 text-left transition-colors"
                                >
                                    <h3 className="font-semibold mb-2">Cloudflare Tunnel</h3>
                                    <p className="text-sm text-muted-foreground mb-4">
                                        Free, secure, and easy to set up. No account required for quick tunnels.
                                    </p>
                                    <span className="text-xs bg-green-500/10 text-green-500 px-2 py-1 rounded-full">
                                        Recommended
                                    </span>
                                </button>
                                <button
                                    onClick={() => selectProvider('ngrok')}
                                    className="border-2 border-border hover:border-primary rounded-lg p-6 text-left transition-colors"
                                >
                                    <h3 className="font-semibold mb-2">ngrok</h3>
                                    <p className="text-sm text-muted-foreground mb-4">
                                        Quick setup with persistent URLs. Free tier requires signup.
                                    </p>
                                    <span className="text-xs bg-blue-500/10 text-blue-500 px-2 py-1 rounded-full">
                                        Alternative
                                    </span>
                                </button>
                            </div>
                        )}

                        {/* Step Content */}
                        {provider && step > 0 && step <= currentSteps.length && (
                            <div className="border border-border rounded-lg p-6">
                                <h3 className="font-semibold mb-4 text-white/80">{currentSteps[step - 1].title}</h3>
                                {currentSteps[step - 1].content}
                            </div>
                        )}

                        {/* Actions */}
                        <div className="flex gap-3 border-t pt-4">
                            {!provider ? (
                                <Button
                                    variant="outline"
                                    onClick={() => onOpenChange(false)}
                                    className="flex-1"
                                >
                                    Cancel
                                </Button>
                            ) : (
                                <>
                                    {step > 1 && (
                                        <Button
                                            variant="outline"
                                            onClick={() => setStep(step - 1)}
                                            disabled={isLoading}
                                        >
                                            <ArrowLeft className="mr-2 h-4 w-4" />
                                            Back
                                        </Button>
                                    )}
                                    {step === 0 && (
                                        <Button
                                            variant="outline"
                                            onClick={() => {
                                                setProvider(null);
                                                setStep(0);
                                            }}
                                        >
                                            Change Provider
                                        </Button>
                                    )}
                                    {step < currentSteps.length && (
                                        <Button
                                            onClick={() => setStep(step + 1)}
                                            className="flex-1 text-[#FFA500] hover:bg-gray-800"
                                            variant="outline"

                                        >
                                            Next
                                            <ArrowRight className="ml-2 h-4 w-4" />
                                        </Button>
                                    )}
                                    {step === currentSteps.length && (
                                        <Button
                                            onClick={handleRegister}
                                            disabled={isLoading || !tunnelUrl}
                                            className="flex-1 hover:bg-gray-800 text-[#FFA500]"
                                            variant="outline"
                                        >
                                            {isLoading ? (
                                                <>
                                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                                    Registering...
                                                </>
                                            ) : (
                                                'Complete Setup'
                                            )}
                                        </Button>
                                    )}
                                </>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>,
        document.body
    );
}