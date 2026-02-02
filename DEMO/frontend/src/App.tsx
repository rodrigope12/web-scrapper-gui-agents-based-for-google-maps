import { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import MapInterface from './components/MapInterface';
import JobsDashboard from './components/JobsDashboard';
import SetupWizard from './components/SetupWizard';
import { motion, AnimatePresence } from 'framer-motion';

function App() {
  const [activeTab, setActiveTab] = useState('map');
  const [isConfigured, setIsConfigured] = useState<boolean | null>(null);

  useEffect(() => {
    checkConfiguration();
  }, []);

  const checkConfiguration = async () => {
    try {
      const response = await fetch('http://localhost:8000/system/status');
      const data = await response.json();
      setIsConfigured(data.configured);
    } catch (e) {
      console.error("Failed to check config:", e);
      // Assume configured or show error? For now assume false to force retry or manual check
      setIsConfigured(false);
    }
  };

  const handleSetupComplete = () => {
    setIsConfigured(true);
    // Optionally refresh anything else
  };

  if (isConfigured === null) {
    return <div className="h-screen w-screen bg-[#1e1e1e] flex items-center justify-center text-white">Loading...</div>;
  }

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#1e1e1e] text-white">
      {/* Setup Wizard Overlay */}
      {!isConfigured && <SetupWizard onComplete={handleSetupComplete} />}

      {/* Draggable Title Bar Area (Invisible but handles drag) */}
      <div className="fixed top-0 left-0 w-full h-10 -webkit-app-region-drag z-50" />

      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

      <main className="flex-1 h-full relative overflow-hidden flex flex-col">
        <div className="h-14 w-full border-b border-apple-gray-700 flex items-center px-6 pt-4 bg-[#1e1e1e]/90 backdrop-blur">
          <h1 className="text-lg font-semibold capitalize text-gray-200">{activeTab.replace('-', ' ')}</h1>
        </div>

        <div className="flex-1 relative p-4">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
              className="h-full w-full"
            >
              {activeTab === 'map' && <div className="h-full w-full"><MapInterface /></div>}
              {activeTab === 'jobs' && <JobsDashboard />}
              {activeTab === 'results' && <div className="p-4 border border-dashed border-gray-700 h-full rounded-xl flex items-center justify-center text-gray-500">Results Table Placeholder</div>}
              {activeTab === 'settings' && <div className="p-4 border border-dashed border-gray-700 h-full rounded-xl flex items-center justify-center text-gray-500">Settings Placeholder</div>}
            </motion.div>
          </AnimatePresence>
        </div>
      </main>
    </div>
  );
}

export default App;
