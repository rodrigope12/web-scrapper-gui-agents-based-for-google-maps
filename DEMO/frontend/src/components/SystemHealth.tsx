import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Activity, Cpu, Server } from 'lucide-react';
import { api } from '../services/api';

const SystemHealth: React.FC = () => {
    const [health, setHealth] = useState({
        cpu_percent: 0,
        ram_percent: 0,
        ram_available_gb: 0,
        ram_total_gb: 0
    });
    const [expanded, setExpanded] = useState(false);

    useEffect(() => {
        const check = async () => {
            try {
                const res = await api.getSystemHealth();
                setHealth(res.data);
            } catch (e) { }
        };
        check();
        const interval = setInterval(check, 5000);
        return () => clearInterval(interval);
    }, []);

    const isHighLoad = health.cpu_percent > 80 || health.ram_percent > 80;

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="absolute bottom-6 left-1/2 -translate-x-1/2 z-[500]"
            onMouseEnter={() => setExpanded(true)}
            onMouseLeave={() => setExpanded(false)}
        >
            <motion.div
                layout
                className="glass-panel rounded-full border border-white/10 shadow-2xl backdrop-blur-xl bg-[#1c1c1e]/80 flex items-center overflow-hidden"
                animate={{
                    padding: expanded ? "12px 24px" : "8px 16px",
                    gap: expanded ? "16px" : "8px"
                }}
            >
                {/* Status Dot */}
                <div className="flex items-center gap-2">
                    <div className="relative">
                        <div className={`w-2.5 h-2.5 rounded-full ${isHighLoad ? 'bg-apple-yellow animate-pulse' : 'bg-apple-green'}`} />
                        {isHighLoad && <div className="absolute inset-0 rounded-full bg-apple-yellow animate-ping opacity-50" />}
                    </div>
                    <span className="text-xs font-medium text-gray-300">System</span>
                </div>

                {/* Vertical Divider */}
                <div className="w-[1px] h-4 bg-white/10" />

                {/* Metrics */}
                <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2">
                        <Cpu size={14} className="text-gray-400" />
                        <span className="text-xs font-mono text-white">{health.cpu_percent.toFixed(0)}%</span>
                    </div>

                    <AnimatePresence>
                        {expanded && (
                            <motion.div
                                initial={{ width: 0, opacity: 0 }}
                                animate={{ width: 'auto', opacity: 1 }}
                                exit={{ width: 0, opacity: 0 }}
                                className="flex items-center gap-4 overflow-hidden whitespace-nowrap"
                            >
                                <div className="flex items-center gap-2">
                                    <Server size={14} className="text-gray-400" />
                                    <span className="text-xs font-mono text-white">{health.ram_percent.toFixed(0)}% RAM</span>
                                </div>
                                <span className="text-[10px] text-gray-500">
                                    {health.ram_available_gb}GB Free
                                </span>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>
            </motion.div>
        </motion.div>
    );
};

export default SystemHealth;
