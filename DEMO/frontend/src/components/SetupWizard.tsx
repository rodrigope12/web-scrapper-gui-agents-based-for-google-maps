import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { CheckCircle, XCircle, ChevronRight, ChevronLeft, Server, Shield, Zap } from 'lucide-react';

interface SetupWizardProps {
    onComplete: () => void;
}

const SetupWizard: React.FC<SetupWizardProps> = ({ onComplete }) => {
    const [step, setStep] = useState(1);
    const [isLoading, setIsLoading] = useState(false);

    // State
    const [captchaKey, setCaptchaKey] = useState('');
    const [proxies, setProxies] = useState('');
    const [performance, setPerformance] = useState({ max_concurrency: 2, request_delay: 2.0, random_delay: true });

    const [checks, setChecks] = useState({ internet: false, chrome_driver: false });
    const [checksLoaded, setChecksLoaded] = useState(false);

    useEffect(() => {
        if (step === 2 && !checksLoaded) {
            runSystemCheck();
        }
    }, [step]);

    const runSystemCheck = async () => {
        try {
            const res = await api.systemCheck();
            setChecks(res.data);
            setChecksLoaded(true);
        } catch (e) { console.error(e); }
    };

    const handleSave = async () => {
        setIsLoading(true);
        try {
            const proxyList = proxies.split('\n').filter(p => p.trim() !== '');
            // 1. Save Services
            await api.setupSystem(captchaKey, proxyList);
            // 2. Save Performance
            await api.updatePerformance(performance.max_concurrency, performance.request_delay, performance.random_delay);

            onComplete();
        } catch (e) {
            alert("Failed to save configuration.");
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-xl">
            <div className="bg-[#1c1c1e] w-full max-w-2xl rounded-2xl border border-white/10 shadow-2xl p-8 flex flex-col h-[600px]">

                {/* Progress Header */}
                <div className="flex justify-between items-center mb-8">
                    {[1, 2, 3, 4].map(s => (
                        <div key={s} className="flex items-center gap-2">
                            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-all ${step >= s ? 'bg-apple-blue text-white shadow-glow' : 'bg-white/10 text-gray-500'}`}>
                                {s}
                            </div>
                            {s < 4 && <div className={`w-12 h-1 rounded-full ${step > s ? 'bg-apple-blue' : 'bg-white/5'}`} />}
                        </div>
                    ))}
                </div>

                <div className="flex-1 overflow-y-auto">
                    {/* STEP 1: WELCOME */}
                    {step === 1 && (
                        <div className="text-center space-y-6 pt-10">
                            <div className="w-20 h-20 bg-apple-blue/20 rounded-full flex items-center justify-center mx-auto text-apple-blue mb-4">
                                <Shield size={40} />
                            </div>
                            <h2 className="text-3xl font-bold text-white">Welcome to MapScraper</h2>
                            <p className="text-gray-400 max-w-md mx-auto">
                                This tool is designed for high-performance, stealthy data extraction.
                                We'll guide you through a quick setup to ensure maximum stability and evade detection.
                            </p>
                        </div>
                    )}

                    {/* STEP 2: SYSTEM CHECK */}
                    {step === 2 && (
                        <div className="space-y-6">
                            <h2 className="text-2xl font-bold text-white flex items-center gap-3">
                                <Server className="text-apple-blue" /> System Check
                            </h2>
                            <p className="text-gray-400 text-sm">Validating your environment for automated browsing.</p>

                            <div className="space-y-4 mt-4">
                                <div className="p-4 rounded-xl bg-white/5 border border-white/5 flex justify-between items-center">
                                    <span className="text-white">Internet Connection</span>
                                    {checksLoaded ? (
                                        checks.internet ? <span className="text-green-400 flex items-center gap-1"><CheckCircle size={16} /> Online</span> : <span className="text-red-400 flex items-center gap-1"><XCircle size={16} /> Offline</span>
                                    ) : <span className="text-gray-500 animate-pulse">Checking...</span>}
                                </div>

                                <div className="p-4 rounded-xl bg-white/5 border border-white/5 flex justify-between items-center">
                                    <span className="text-white">Undetected Chrome Driver</span>
                                    {checksLoaded ? (
                                        checks.chrome_driver ? <span className="text-green-400 flex items-center gap-1"><CheckCircle size={16} /> Installed</span> : <span className="text-red-400 flex items-center gap-1"><XCircle size={16} /> Missing</span>
                                    ) : <span className="text-gray-500 animate-pulse">Checking...</span>}
                                </div>

                                {!checks.chrome_driver && checksLoaded && (
                                    <div className="bg-red-500/10 text-red-400 p-3 rounded-lg text-xs mt-4">
                                        Warning: Missing dependencies may cause the scraper to fail. Ensure <code>undetected-chromedriver</code> is installed in the backend.
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    {/* STEP 3: SERVICES */}
                    {step === 3 && (
                        <div className="space-y-6">
                            <h2 className="text-2xl font-bold text-white flex items-center gap-3">
                                <Shield className="text-apple-blue" /> Services
                            </h2>

                            <div>
                                <label className="block text-xs font-semibold text-gray-400 mb-2 uppercase">Proxies (Required)</label>
                                <textarea
                                    value={proxies}
                                    onChange={e => setProxies(e.target.value)}
                                    placeholder="http://user:pass@ip:port (One per line)"
                                    className="w-full bg-white/5 border border-white/10 rounded-xl p-4 text-white text-sm font-mono h-32 focus:outline-none focus:border-apple-blue"
                                />
                                <p className="text-[10px] text-gray-500 mt-1">High-quality residential proxies are recommended to avoid IP bans.</p>
                            </div>

                            <div>
                                <label className="block text-xs font-semibold text-gray-400 mb-2 uppercase">2Captcha Key (Optional)</label>
                                <input
                                    type="text"
                                    value={captchaKey}
                                    onChange={e => setCaptchaKey(e.target.value)}
                                    placeholder="API Key"
                                    className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-white focus:outline-none focus:border-apple-blue"
                                />
                            </div>
                        </div>
                    )}

                    {/* STEP 4: PERFORMANCE */}
                    {step === 4 && (
                        <div className="space-y-6">
                            <h2 className="text-2xl font-bold text-white flex items-center gap-3">
                                <Zap className="text-apple-blue" /> Performance
                            </h2>

                            <div className="space-y-8">
                                <div>
                                    <div className="flex justify-between mb-2">
                                        <label className="text-sm font-medium text-white">Concurrent Agents</label>
                                        <span className="text-apple-blue font-mono">{performance.max_concurrency}</span>
                                    </div>
                                    <input
                                        type="range" min="1" max="10"
                                        value={performance.max_concurrency}
                                        onChange={e => setPerformance({ ...performance, max_concurrency: parseInt(e.target.value) })}
                                        className="w-full h-2 rounded-lg bg-white/10 appearance-none cursor-pointer accent-apple-blue"
                                    />
                                </div>

                                <div>
                                    <div className="flex justify-between mb-2">
                                        <label className="text-sm font-medium text-white">Request Delay (Seconds)</label>
                                        <span className="text-apple-blue font-mono">{performance.request_delay}s</span>
                                    </div>
                                    <input
                                        type="range" min="0.5" max="10" step="0.5"
                                        value={performance.request_delay}
                                        onChange={e => setPerformance({ ...performance, request_delay: parseFloat(e.target.value) })}
                                        className="w-full h-2 rounded-lg bg-white/10 appearance-none cursor-pointer accent-apple-blue"
                                    />
                                </div>

                                <div className="flex items-center gap-3 p-4 bg-white/5 rounded-xl border border-white/5">
                                    <input
                                        type="checkbox"
                                        checked={performance.random_delay}
                                        onChange={e => setPerformance({ ...performance, random_delay: e.target.checked })}
                                        className="w-5 h-5 accent-apple-blue"
                                    />
                                    <div>
                                        <label className="text-white text-sm font-medium">Randomize Delays</label>
                                        <p className="text-xs text-gray-500">Adds natural variance to delays to mimic human behavior.</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                {/* Footer Controls */}
                <div className="flex justify-between mt-8 pt-6 border-t border-white/5">
                    {step > 1 ? (
                        <button
                            onClick={() => setStep(step - 1)}
                            className="px-6 py-2.5 rounded-xl text-gray-400 hover:text-white hover:bg-white/5 transition-colors flex items-center gap-2"
                        >
                            <ChevronLeft size={18} /> Back
                        </button>
                    ) : <div></div>}

                    {step < 4 ? (
                        <button
                            onClick={() => setStep(step + 1)}
                            className="bg-apple-blue hover:bg-blue-600 text-white px-8 py-2.5 rounded-xl font-medium shadow-glow transition-all flex items-center gap-2"
                        >
                            Next <ChevronRight size={18} />
                        </button>
                    ) : (
                        <button
                            onClick={handleSave}
                            disabled={isLoading}
                            className="bg-green-500 hover:bg-green-600 text-white px-8 py-2.5 rounded-xl font-medium shadow-glow transition-all flex items-center gap-2 disabled:opacity-50"
                        >
                            {isLoading ? 'Saving...' : 'Finish Setup'}
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
};

export default SetupWizard;
