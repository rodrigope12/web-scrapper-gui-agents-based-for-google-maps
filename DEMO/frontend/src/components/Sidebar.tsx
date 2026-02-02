import React from 'react';
import { Map, Settings, Activity, FileText, Hexagon } from 'lucide-react';
import clsx from 'clsx';
import { motion } from 'framer-motion';

interface SidebarProps {
    activeTab: string;
    setActiveTab: (tab: string) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ activeTab, setActiveTab }) => {
    const menuItems = [
        { id: 'map', icon: Map, label: 'Search' },
        { id: 'jobs', icon: Activity, label: 'Jobs' },
        { id: 'results', icon: FileText, label: 'Data' },
        { id: 'settings', icon: Settings, label: 'Settings' },
    ];

    return (
        <div className="w-20 h-full flex flex-col items-center py-6 border-r border-white/5 bg-[#2c2c2e]/30 backdrop-blur-xl z-20 pt-[50px]">
            {/* Logo Mark */}
            <div className="mb-10 p-2 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl shadow-lg shadow-blue-500/20">
                <Hexagon className="text-white w-6 h-6" strokeWidth={2.5} />
            </div>

            <div className="space-y-4 w-full px-2">
                {menuItems.map((item) => {
                    const isActive = activeTab === item.id;
                    return (
                        <button
                            key={item.id}
                            onClick={() => setActiveTab(item.id)}
                            className={clsx(
                                "relative flex flex-col items-center justify-center w-full py-3 rounded-xl transition-all duration-300 group",
                                isActive ? "bg-white/10 text-white shadow-inner" : "text-gray-400 hover:text-white hover:bg-white/5"
                            )}
                        >
                            {isActive && (
                                <motion.div
                                    layoutId="activeTabIndicator"
                                    className="absolute inset-0 border border-white/10 rounded-xl"
                                    initial={false}
                                    transition={{ type: "spring", stiffness: 300, damping: 30 }}
                                />
                            )}
                            <item.icon className={clsx("w-6 h-6 mb-1.5 transition-transform duration-300", isActive && "scale-110 drop-shadow-md")} strokeWidth={isActive ? 2.5 : 2} />
                            <span className="text-[10px] font-medium tracking-wide">{item.label}</span>
                        </button>
                    );
                })}
            </div>
        </div>
    );
};

export default Sidebar;
