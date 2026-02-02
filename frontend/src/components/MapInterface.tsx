import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, FeatureGroup } from 'react-leaflet';
import { EditControl } from 'react-leaflet-draw';
import { api } from '../services/api';
import 'leaflet/dist/leaflet.css';
import 'leaflet-draw/dist/leaflet.draw.css';
import { Layers, Play, X, Plus, Globe, Settings as SettingsIcon, Search, List as ListIcon, Trash2, Crosshair } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import L from 'leaflet';
import markerIcon from 'leaflet/dist/images/marker-icon.png';
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png';
import markerShadow from 'leaflet/dist/images/marker-shadow.png';
import SetupWizard from './SetupWizard';
import Settings from './Settings';
import SystemHealth from './SystemHealth';
import clsx from 'clsx';

delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
    iconUrl: markerIcon,
    iconRetinaUrl: markerIcon2x,
    shadowUrl: markerShadow,
});

const MapInterface: React.FC = () => {
    // --- State ---
    const [polygons, setPolygons] = useState<any[]>([]);
    const [isCreating, setIsCreating] = useState(false);

    // UI Modals
    const [showManualInput, setShowManualInput] = useState(false);
    const [showSetupWizard, setShowSetupWizard] = useState(false);
    const [showSettings, setShowSettings] = useState(false);
    const [showSearchPanel, setShowSearchPanel] = useState(false);

    // Data
    const [manualCoords, setManualCoords] = useState({ lat: '', lon: '', radius: '1' });
    const [savedQueries, setSavedQueries] = useState<any[]>([]);
    const [selectedQueries, setSelectedQueries] = useState<string[]>([]); // Multi-select ID or Term
    const [newSearchTerm, setNewSearchTerm] = useState('');

    // --- Init ---
    useEffect(() => {
        checkDocs();
        loadSavedQueries();
    }, []);

    const checkDocs = async () => {
        try {
            const res = await api.systemCheck();
        } catch (e) { }
    };

    const loadSavedQueries = async () => {
        try {
            const res = await api.getSavedQueries();
            setSavedQueries(res.data);
        } catch (e) { console.error("Failed to load queries", e); }
    };

    // --- Handlers ---
    const handleSaveQuery = async () => {
        if (!newSearchTerm.trim()) return;
        try {
            await api.addSavedQuery(newSearchTerm);
            setNewSearchTerm('');
            loadSavedQueries();
        } catch (e) { console.error(e); }
    };

    const deleteQuery = async (id: string) => {
        try {
            await api.removeSavedQuery(id);
            loadSavedQueries();
            setSelectedQueries(prev => prev.filter(q => q !== id));
        } catch (e) { console.error(e); }
    };

    const toggleQuerySelection = (term: string) => {
        setSelectedQueries(prev =>
            prev.includes(term) ? prev.filter(t => t !== term) : [...prev, term]
        );
    };

    const _onCreated = (e: any) => {
        const { layerType, layer } = e;
        if (layerType === 'polygon' || layerType === 'rectangle') {
            const geoJSON = layer.toGeoJSON();
            setPolygons((prev) => [...prev, geoJSON]);
        }
    }

    const _onDeleted = (e: any) => {
        setPolygons([]);
    }

    const handleCreateJob = async () => {
        if (polygons.length === 0 || selectedQueries.length === 0) {
            alert("Please select at least one area and one search term.");
            return;
        }
        setIsCreating(true);

        try {
            const featureCollection = {
                type: "FeatureCollection",
                features: polygons.map(p => ({
                    type: "Feature",
                    geometry: p.geometry,
                    properties: {}
                }))
            };

            await api.createJob(
                `Job ${new Date().toLocaleTimeString()} (${selectedQueries.length} terms)`,
                selectedQueries,
                featureCollection
            );

            new Notification("Job Created", { body: "Background scraping active." });
            setPolygons([]);
            setSelectedQueries([]);
        } catch (error) {
            console.error(error);
            alert("Failed to create job.");
        } finally {
            setIsCreating(false);
        }
    };

    const handleManualSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        const lat = parseFloat(manualCoords.lat);
        const lon = parseFloat(manualCoords.lon);
        const radiusKm = parseFloat(manualCoords.radius);

        if (isNaN(lat) || isNaN(lon) || isNaN(radiusKm)) return;

        const latOffset = (radiusKm * 0.009);
        const lonOffset = (radiusKm * 0.009) / Math.cos(lat * (Math.PI / 180));

        const minLon = lon - lonOffset, maxLon = lon + lonOffset;
        const minLat = lat - latOffset, maxLat = lat + latOffset;

        const polygon = {
            type: "Polygon",
            coordinates: [[[minLon, minLat], [minLon, maxLat], [maxLon, maxLat], [maxLon, minLat], [minLon, minLat]]]
        };

        setPolygons(prev => [...prev, { type: "Feature", properties: {}, geometry: polygon }]);
        setShowManualInput(false);
        setManualCoords({ lat: '', lon: '', radius: '1' });
    };

    return (
        <div className="h-full w-full rounded-2xl overflow-hidden shadow-2xl border border-white/5 relative group bg-[#000]">
            {/* Map */}
            <MapContainer center={[40.7128, -74.0060]} zoom={13} style={{ height: "100%", width: "100%" }} className="z-0 bg-[#1c1c1e]">
                <TileLayer
                    url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
                />
                <FeatureGroup>
                    <EditControl
                        position='topright'
                        onCreated={_onCreated}
                        onDeleted={_onDeleted}
                        draw={{
                            rectangle: true,
                            polygon: { allowIntersection: false, shapeOptions: { color: '#0A84FF', fillOpacity: 0.2, weight: 1 } },
                            circle: false, circlemarker: false, marker: false, polyline: false
                        }}
                    />
                </FeatureGroup>
            </MapContainer>

            {/* --- TOP LEFT CONTROLS --- */}
            <div className="absolute top-6 left-6 z-[400] flex flex-col gap-3">
                <button
                    onClick={() => setShowSearchPanel(!showSearchPanel)}
                    className={clsx(
                        "rounded-xl p-3 flex items-center gap-3 transition-all duration-300 shadow-xl border backdrop-blur-md w-48 group/btn",
                        showSearchPanel || selectedQueries.length > 0
                            ? "bg-apple-blue text-white border-apple-blue shadow-blue-900/20"
                            : "bg-[#1c1c1e]/80 text-gray-300 border-white/10 hover:bg-[#2c2c2e]/90 hover:text-white hover:border-white/20"
                    )}
                >
                    <div className={clsx("p-1.5 rounded-lg transition-colors", showSearchPanel ? "bg-white/20" : "bg-white/5")}>
                        <Search size={16} />
                    </div>
                    <div className="flex flex-col items-start">
                        <span className="text-xs font-bold tracking-wide">Targets</span>
                        <span className="text-[10px] opacity-70 font-medium">
                            {selectedQueries.length > 0 ? `${selectedQueries.length} Selected` : "Select categories"}
                        </span>
                    </div>
                </button>

                <div className="flex gap-2">
                    <button
                        onClick={() => setShowManualInput(true)}
                        className="glass-panel p-3 rounded-xl text-gray-400 hover:text-white hover:bg-white/10 transition-all flex items-center justify-center border border-white/5 shadow-lg w-12 h-12"
                        title="Input Coordinates"
                    >
                        <Crosshair size={20} />
                    </button>
                    <button
                        onClick={() => setShowSetupWizard(true)}
                        className="glass-panel p-3 rounded-xl text-gray-400 hover:text-white hover:bg-white/10 transition-all flex items-center justify-center border border-white/5 shadow-lg w-12 h-12"
                        title="Setup Wizard"
                    >
                        <SettingsIcon size={20} />
                    </button>
                </div>
            </div>

            {/* --- FLOATING SEARCH PANEL --- */}
            <AnimatePresence>
                {showSearchPanel && (
                    <motion.div
                        initial={{ opacity: 0, x: -20, scale: 0.95 }}
                        animate={{ opacity: 1, x: 0, scale: 1 }}
                        exit={{ opacity: 0, x: -20, scale: 0.95 }}
                        transition={{ type: "spring", stiffness: 400, damping: 30 }}
                        className="absolute top-6 left-56 z-[1000] w-80 glass-panel rounded-2xl p-5 border border-white/10 shadow-2xl backdrop-blur-2xl bg-[#1c1c1e]/90"
                    >
                        <div className="flex justify-between items-center mb-5">
                            <h3 className="text-sm font-bold text-white tracking-wide uppercase">Search Categories</h3>
                            <button onClick={() => setShowSearchPanel(false)} className="text-gray-500 hover:text-white transition-colors">
                                <X size={16} />
                            </button>
                        </div>

                        {/* Input */}
                        <div className="flex gap-2 mb-4">
                            <input
                                type="text"
                                value={newSearchTerm}
                                onChange={(e) => setNewSearchTerm(e.target.value)}
                                placeholder="e.g. 'Coffee Shops'"
                                className="flex-1 bg-black/20 border border-white/10 rounded-xl px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-apple-blue/50 focus:ring-1 focus:ring-apple-blue/50 transition-all"
                                onKeyDown={(e) => e.key === 'Enter' && handleSaveQuery()}
                            />
                            <button
                                onClick={handleSaveQuery}
                                className="bg-white/5 hover:bg-white/10 text-white p-2 rounded-xl transition-all border border-white/5"
                            >
                                <Plus size={18} />
                            </button>
                        </div>

                        {/* Saved List */}
                        <div className="space-y-1.5 max-h-[300px] overflow-y-auto custom-scrollbar pr-1">
                            {savedQueries.map(q => {
                                const isSelected = selectedQueries.includes(q.query);
                                return (
                                    <motion.button
                                        key={q.id}
                                        layout
                                        onClick={() => toggleQuerySelection(q.query)}
                                        className={clsx(
                                            "w-full flex justify-between items-center p-2.5 rounded-lg border text-xs font-medium transition-all group",
                                            isSelected
                                                ? "bg-apple-blue text-white border-apple-blue shadow-md shadow-blue-900/20"
                                                : "bg-white/5 border-transparent text-gray-400 hover:bg-white/10 hover:text-white"
                                        )}
                                    >
                                        <span>{q.query}</span>
                                        {isSelected && <CheckBadge />}
                                        <div
                                            onClick={(e) => { e.stopPropagation(); deleteQuery(q.id); }}
                                            className={clsx("p-1 rounded hover:bg-white/10 opacity-0 group-hover:opacity-100 transition-opacity", isSelected ? "text-white hover:text-red-200" : "text-gray-500 hover:text-red-400")}
                                        >
                                            <Trash2 size={12} />
                                        </div>
                                    </motion.button>
                                );
                            })}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>


            {/* --- BOTTOM FLOATING BAR (ACTIONS) --- */}
            <AnimatePresence>
                {polygons.length > 0 && (
                    <motion.div
                        initial={{ opacity: 0, y: 50 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: 50 }}
                        className="absolute bottom-8 left-1/2 -translate-x-1/2 z-[400] flex items-center gap-3 p-2 pr-2 pl-4 rounded-2xl glass-panel bg-[#1c1c1e]/80 border-white/10"
                    >
                        <div className="flex items-center gap-3 mr-4">
                            <span className="flex h-2 w-2 relative">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                                <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                            </span>
                            <div className="flex flex-col">
                                <span className="text-xs font-bold text-white">{polygons.length} Active Zones</span>
                                <span className="text-[10px] text-gray-400">{selectedQueries.length} Search Terms</span>
                            </div>
                        </div>

                        <div className="h-8 w-px bg-white/10 mx-1" />

                        <button
                            onClick={() => setPolygons([])}
                            className="p-2.5 hover:bg-white/10 rounded-xl text-gray-400 hover:text-red-400 transition-colors"
                            title="Clear Zones"
                        >
                            <Trash2 size={16} />
                        </button>

                        <button
                            onClick={handleCreateJob}
                            disabled={selectedQueries.length === 0}
                            className="bg-apple-blue hover:bg-blue-500 disabled:opacity-50 disabled:grayscale text-white px-5 py-2.5 rounded-xl font-semibold shadow-lg shadow-blue-600/20 flex items-center gap-2 transition-all active:scale-95"
                        >
                            <Play size={16} fill="currentColor" />
                            <span className="text-xs tracking-wide">START EXTRACTION</span>
                        </button>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Modals */}
            <AnimatePresence>
                {showManualInput && (
                    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="absolute inset-0 z-[500] bg-black/60 backdrop-blur-sm flex items-center justify-center">
                        <div className="bg-[#1c1c1e] p-6 rounded-2xl w-80 border border-white/10 shadow-2xl">
                            <h3 className="text-white font-bold mb-4">Input Coordinates</h3>
                            <div className="space-y-3">
                                <input placeholder="Lat" value={manualCoords.lat} onChange={e => setManualCoords({ ...manualCoords, lat: e.target.value })} className="w-full bg-white/5 p-3 rounded-xl text-white text-sm border border-white/10 focus:border-apple-blue outline-none transition-colors" />
                                <input placeholder="Lon" value={manualCoords.lon} onChange={e => setManualCoords({ ...manualCoords, lon: e.target.value })} className="w-full bg-white/5 p-3 rounded-xl text-white text-sm border border-white/10 focus:border-apple-blue outline-none transition-colors" />
                                <input placeholder="Radius (km)" value={manualCoords.radius} onChange={e => setManualCoords({ ...manualCoords, radius: e.target.value })} className="w-full bg-white/5 p-3 rounded-xl text-white text-sm border border-white/10 focus:border-apple-blue outline-none transition-colors" />
                            </div>
                            <div className="flex gap-2 mt-6">
                                <button onClick={() => setShowManualInput(false)} className="flex-1 py-2.5 text-gray-400 hover:text-white text-sm font-medium">Cancel</button>
                                <button onClick={handleManualSubmit} className="flex-1 py-2.5 bg-apple-blue text-white rounded-xl text-sm font-semibold shadow-lg shadow-blue-500/20">Add Zone</button>
                            </div>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            {showSettings && <Settings onClose={() => setShowSettings(false)} />}
            {showSetupWizard && <SetupWizard onComplete={() => setShowSetupWizard(false)} />}

            <SystemHealth />

            {/* Empty State Hint */}
            {polygons.length === 0 && (
                <div className="absolute top-6 left-1/2 -translate-x-1/2 glass-panel px-6 py-2 rounded-full z-[400] text-sm text-gray-400 font-medium border border-white/5 shadow-lg pointer-events-none flex items-center gap-2">
                    <Globe size={14} className="text-apple-blue" />
                    <span>Use draw tools to define area</span>
                </div>
            )}
        </div>
    );
};

const CheckBadge = () => (
    <div className="w-4 h-4 rounded-full bg-white/20 flex items-center justify-center">
        <svg viewBox="0 0 24 24" fill="none" className="w-3 h-3 text-white" stroke="currentColor" strokeWidth="3">
            <polyline points="20 6 9 17 4 12" />
        </svg>
    </div>
);

export default MapInterface;
