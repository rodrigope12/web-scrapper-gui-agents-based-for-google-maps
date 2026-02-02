import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { X, Check, Trash2, Edit2, Plus, Database, Globe } from 'lucide-react';

interface Profile {
    id: string;
    name: string;
    is_default: boolean;
    fields: string[];
}

interface SettingsProps {
    onClose: () => void;
}

const AVAILABLE_FIELDS = [
    "name", "address", "phone", "rating", "reviews",
    "website", "category", "opening_hours", "images",
    "price_level", "coordinates"
];

const Settings: React.FC<SettingsProps> = ({ onClose }) => {
    const [profiles, setProfiles] = useState<Profile[]>([]);
    const [activeTab, setActiveTab] = useState<'profiles' | 'performance' | 'intelligence'>('profiles');
    const [editingProfile, setEditingProfile] = useState<Profile | null>(null); // Null = List mode, Object = Edit mode
    const [performance, setPerformance] = useState({ max_concurrency: 2, request_delay: 2.0, random_delay: true });
    const [selectors, setSelectors] = useState<any>({});
    const [updatingSelectors, setUpdatingSelectors] = useState(false);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const [pRes, perfRes, selRes] = await Promise.all([
                api.getProfiles(),
                api.getPerformance(),
                api.getSelectors()
            ]);
            setProfiles(pRes.data);
            setPerformance(perfRes.data);
            setSelectors(selRes.data);
        } catch (e) { console.error(e); }
    };

    // --- Profile Handlers ---
    const handleSaveProfile = async () => {
        if (!editingProfile) return;
        try {
            if (profiles.find(p => p.id === editingProfile.id)) {
                // Update
                await api.updateProfile(editingProfile.id, { name: editingProfile.name, fields: editingProfile.fields });
            } else {
                // Create
                await api.createProfile(editingProfile.name, editingProfile.fields);
            }
            loadData();
            setEditingProfile(null);
        } catch (e) {
            console.error("Failed to save profile", e);
        }
    };

    const handleDeleteProfile = async (id: string) => {
        if (confirm("Are you sure?")) {
            await api.deleteProfile(id);
            loadData();
        }
    };

    const handleSetDefault = async (id: string) => {
        await api.setProfileDefault(id);
        loadData();
    };

    const toggleField = (field: string) => {
        if (!editingProfile) return;
        const newFields = editingProfile.fields.includes(field)
            ? editingProfile.fields.filter(f => f !== field)
            : [...editingProfile.fields, field];
        setEditingProfile({ ...editingProfile, fields: newFields });
    };

    // --- Performance Handlers ---
    const savePerformance = async () => {
        try {
            await api.updatePerformance(performance.max_concurrency, performance.request_delay, performance.random_delay);
            alert("Performance settings saved.");
        } catch (e) { console.error(e); }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-md">
            <div className="bg-[#1c1c1e] w-full max-w-4xl h-[80vh] rounded-2xl border border-white/10 shadow-2xl flex flex-col overflow-hidden">
                {/* Header */}
                <div className="flex justify-between items-center p-6 border-b border-white/5 bg-[#252527]">
                    <h2 className="text-2xl font-bold text-white">Settings</h2>
                    <button onClick={onClose} className="text-gray-400 hover:text-white transition-colors">
                        <X size={24} />
                    </button>
                </div>

                {/* Tabs */}
                <div className="flex border-b border-white/5 bg-[#1c1c1e]">
                    <button
                        onClick={() => setActiveTab('profiles')}
                        className={`flex-1 py-4 text-sm font-medium transition-colors ${activeTab === 'profiles' ? 'text-apple-blue border-b-2 border-apple-blue bg-white/5' : 'text-gray-400 hover:text-white'}`}
                    >
                        Data Profiles
                    </button>
                    <button
                        onClick={() => setActiveTab('performance')}
                        className={`flex-1 py-4 text-sm font-medium transition-colors ${activeTab === 'performance' ? 'text-apple-blue border-b-2 border-apple-blue bg-white/5' : 'text-gray-400 hover:text-white'}`}
                    >
                        Success & Performance
                    </button>
                    <button
                        onClick={() => setActiveTab('intelligence')}
                        className={`px-6 py-4 text-sm font-medium transition-colors border-b-2 ${activeTab === 'intelligence' ? 'border-apple-blue text-white' : 'border-transparent text-gray-400 hover:text-white'}`}
                    >
                        System Intelligence
                    </button>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-6 relative">
                    {activeTab === 'profiles' && (
                        <div>
                            {editingProfile ? (
                                // --- EDITOR MODE ---
                                <div className="space-y-6">
                                    <div className="flex justify-between items-center">
                                        <h3 className="text-lg font-semibold text-white">
                                            {profiles.find(p => p.id === editingProfile.id) ? 'Edit Profile' : 'New Profile'}
                                        </h3>
                                        <button onClick={() => setEditingProfile(null)} className="text-sm text-gray-400 hover:text-white">Cancel</button>
                                    </div>

                                    <div>
                                        <label className="block text-xs text-gray-400 mb-1">Profile Name</label>
                                        <input
                                            type="text"
                                            value={editingProfile.name}
                                            onChange={e => setEditingProfile({ ...editingProfile, name: e.target.value })}
                                            className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-apple-blue"
                                        />
                                    </div>

                                    <div>
                                        <label className="block text-xs text-gray-400 mb-3">Fields to Extract</label>
                                        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                                            {AVAILABLE_FIELDS.map(field => (
                                                <button
                                                    key={field}
                                                    onClick={() => toggleField(field)}
                                                    className={`p-3 rounded-xl border text-sm text-left transition-all ${editingProfile.fields.includes(field) ? 'bg-apple-blue/20 border-apple-blue text-white' : 'bg-white/5 border-white/5 text-gray-400 hover:bg-white/10'}`}
                                                >
                                                    <div className="flex items-center gap-2">
                                                        <div className={`w-4 h-4 rounded border flex items-center justify-center ${editingProfile.fields.includes(field) ? 'bg-apple-blue border-apple-blue' : 'border-gray-500'}`}>
                                                            {editingProfile.fields.includes(field) && <Check size={10} className="text-white" />}
                                                        </div>
                                                        <span className="capitalize">{field.replace('_', ' ')}</span>
                                                    </div>
                                                </button>
                                            ))}
                                        </div>
                                    </div>

                                    <button
                                        onClick={handleSaveProfile}
                                        className="bg-apple-blue hover:bg-blue-600 text-white px-6 py-3 rounded-xl font-medium w-full transition-colors"
                                    >
                                        Save Profile
                                    </button>
                                </div>
                            ) : (
                                // --- LIST MODE ---
                                <div className="space-y-4">
                                    <div className="flex justify-between items-center mb-6">
                                        <p className="text-gray-400 text-sm">Select a profile to edit or create a new one.</p>
                                        <button
                                            onClick={() => setEditingProfile({ id: 'new', name: 'My New Profile', is_default: false, fields: ['name', 'address'] })}
                                            className="bg-white/10 hover:bg-white/20 text-white px-4 py-2 rounded-lg text-sm flex items-center gap-2 transition-colors"
                                        >
                                            <Plus size={16} /> New Profile
                                        </button>
                                    </div>

                                    <div className="grid gap-4">
                                        {profiles.map(p => (
                                            <div key={p.id} className={`p-4 rounded-xl border transition-all ${p.is_default ? 'bg-apple-blue/10 border-apple-blue/30' : 'bg-white/5 border-white/5 hover:bg-white/10'}`}>
                                                <div className="flex justify-between items-start">
                                                    <div>
                                                        <h4 className="font-semibold text-white flex items-center gap-2">
                                                            {p.name}
                                                            {p.is_default && <span className="bg-apple-blue text-white text-[10px] px-2 py-0.5 rounded-full">Active</span>}
                                                        </h4>
                                                        <p className="text-xs text-gray-400 mt-1 line-clamp-1">
                                                            {p.fields.join(", ")}
                                                        </p>
                                                    </div>
                                                    <div className="flex items-center gap-2">
                                                        {!p.is_default && (
                                                            <button
                                                                onClick={() => handleSetDefault(p.id)}
                                                                title="Set as Default"
                                                                className="p-2 text-gray-400 hover:text-green-400 transition-colors"
                                                            >
                                                                <Check size={16} />
                                                            </button>
                                                        )}
                                                        <button
                                                            onClick={() => setEditingProfile(p)}
                                                            className="p-2 text-gray-400 hover:text-white transition-colors"
                                                        >
                                                            <Edit2 size={16} />
                                                        </button>
                                                        {!p.is_default && (
                                                            <button
                                                                onClick={() => handleDeleteProfile(p.id)}
                                                                className="p-2 text-gray-400 hover:text-red-400 transition-colors"
                                                            >
                                                                <Trash2 size={16} />
                                                            </button>
                                                        )}
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    )}

                    {activeTab === 'performance' && (
                        <div className="max-w-xl mx-auto space-y-8 py-4">
                            <div>
                                <h3 className="text-lg font-semibold text-white mb-4">Scraping Behavior</h3>
                                <div className="space-y-6">
                                    <div>
                                        <div className="flex justify-between mb-2">
                                            <label className="text-sm text-gray-300">Concurrent Agents</label>
                                            <span className="text-sm font-mono text-apple-blue">{performance.max_concurrency} browsers</span>
                                        </div>
                                        <input
                                            type="range"
                                            min="1"
                                            max="10"
                                            value={performance.max_concurrency}
                                            onChange={e => setPerformance({ ...performance, max_concurrency: parseInt(e.target.value) })}
                                            className="w-full h-2 bg-white/10 rounded-lg appearance-none cursor-pointer accent-apple-blue"
                                        />
                                        <p className="text-xs text-gray-500 mt-2">
                                            Recommended: 2-3 for standard laptops. High values (5+) increase detection risk.
                                        </p>
                                    </div>

                                    <div>
                                        <div className="flex justify-between mb-2">
                                            <label className="text-sm text-gray-300">Request Speed (approx delay)</label>
                                            <span className="text-sm font-mono text-apple-blue">{performance.request_delay}s</span>
                                        </div>
                                        <input
                                            type="range"
                                            min="0.5"
                                            max="10"
                                            step="0.5"
                                            value={performance.request_delay}
                                            onChange={e => setPerformance({ ...performance, request_delay: parseFloat(e.target.value) })}
                                            className="w-full h-2 bg-white/10 rounded-lg appearance-none cursor-pointer accent-apple-blue"
                                        />
                                    </div>

                                    <div className="flex items-center gap-3">
                                        <input
                                            type="checkbox"
                                            id="randomDelay"
                                            checked={performance.random_delay}
                                            onChange={e => setPerformance({ ...performance, random_delay: e.target.checked })}
                                            className="w-5 h-5 rounded border-gray-600 bg-black/20 text-apple-blue focus:ring-0"
                                        />
                                        <div>
                                            <label htmlFor="randomDelay" className="text-sm text-white block">Humanize Delays</label>
                                            <p className="text-xs text-gray-500">Adds random noise (±30%) to delays to look more human.</p>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <button
                                onClick={savePerformance}
                                className="bg-apple-blue hover:bg-blue-600 text-white px-8 py-3 rounded-xl font-medium shadow-glow transition-all w-full"
                            >
                                Save Performance Settings
                            </button>
                        </div>
                    )}

                    {activeTab === 'intelligence' && (
                        <div className="max-w-2xl mx-auto space-y-8 py-8">
                            {/* Hero */}
                            <div className="flex items-center gap-4 mb-8">
                                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-purple-500/20">
                                    <Globe className="text-white" size={24} />
                                </div>
                                <div>
                                    <h3 className="text-xl font-bold text-white">Scraping Intelligence</h3>
                                    <p className="text-sm text-gray-400">Manage how the system interacts with target websites.</p>
                                </div>
                            </div>

                            {/* Selectors Status */}
                            <div className="bg-[#1c1c1e] rounded-xl border border-white/5 p-6 overflow-hidden relative group">
                                <div className="absolute top-0 right-0 p-4 opacity-50">
                                    <Database size={100} className="text-white/5" strokeWidth={1} />
                                </div>

                                <div className="relative z-10">
                                    <div className="flex justify-between items-start mb-6">
                                        <div>
                                            <h4 className="text-base font-medium text-white">Selectors Configuration</h4>
                                            <p className="text-xs text-gray-500 mt-1">Definitions used to locate elements on Google Maps.</p>
                                        </div>
                                        <div className="px-2 py-1 bg-green-500/10 text-green-400 border border-green-500/20 rounded-md text-[10px] font-mono">
                                            ACTIVE
                                        </div>
                                    </div>

                                    <div className="bg-black/40 rounded-lg p-4 font-mono text-xs text-gray-300 border border-white/5 max-h-48 overflow-y-auto custom-scrollbar">
                                        <pre>{JSON.stringify(selectors, null, 2)}</pre>
                                    </div>

                                    <div className="mt-6 flex gap-3">
                                        <button
                                            disabled={updatingSelectors}
                                            onClick={() => {
                                                setUpdatingSelectors(true);
                                                setTimeout(() => {
                                                    setUpdatingSelectors(false);
                                                    api.getSelectors().then(res => setSelectors(res.data));
                                                    alert("Selectors definitions reloaded");
                                                }, 1000);
                                            }}
                                            className="flex-1 py-2 bg-white/5 hover:bg-white/10 text-white rounded-lg text-sm font-medium transition-colors border border-white/5 flex items-center justify-center gap-2"
                                        >
                                            {updatingSelectors ? (
                                                <div className="w-4 h-4 border-2 border-white/50 border-t-transparent rounded-full animate-spin" />
                                            ) : (
                                                <Globe size={16} />
                                            )}
                                            <span>Check for Updates</span>
                                        </button>
                                    </div>
                                </div>
                            </div>

                            {/* Info Box */}
                            <div className="bg-blue-500/5 border border-blue-500/10 rounded-xl p-4 flex gap-3">
                                <div className="mt-1">
                                    <div className="w-1.5 h-1.5 rounded-full bg-blue-500" />
                                </div>
                                <div className="text-xs text-blue-200/80 leading-relaxed">
                                    This system uses externalized selectors. When Google updates their layout, you can simply update the
                                    <code className="bg-blue-500/20 px-1 py-0.5 rounded mx-1 text-blue-100">selectors.json</code>
                                    file or click "Check for Updates" to pull the latest definitions without reinstalling the software.
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default Settings;
