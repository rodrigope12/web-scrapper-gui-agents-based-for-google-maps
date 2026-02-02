import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Download, FileJson, FileSpreadsheet, Table, Check } from 'lucide-react';
import { api } from '../services/api';
import clsx from 'clsx';

interface ExportModalProps {
    jobId: number | null;
    jobName: string;
    onClose: () => void;
}

const ExportModal: React.FC<ExportModalProps> = ({ jobId, jobName, onClose }) => {
    const [format, setFormat] = useState<'json' | 'csv' | 'excel'>('excel');
    const [normalizePhones, setNormalizePhones] = useState(true);
    const [isExporting, setIsExporting] = useState(false);

    const handleExport = async () => {
        if (!jobId) return;
        setIsExporting(true);
        try {
            const res = await api.exportJob(jobId, format, normalizePhones);

            // Create download link
            const url = window.URL.createObjectURL(new Blob([res.data]));
            const link = document.createElement('a');
            link.href = url;

            const ext = format === 'excel' ? 'xlsx' : format;
            link.setAttribute('download', `${jobName.replace(/\s+/g, '_')}_results.${ext}`);

            document.body.appendChild(link);
            link.click();
            link.parentNode?.removeChild(link);

            setTimeout(() => {
                onClose();
            }, 500);
        } catch (e) {
            console.error("Export failed", e);
            alert("Export failed. Please try again.");
            setIsExporting(false);
        }
    };

    return (
        <AnimatePresence>
            <div className="fixed inset-0 z-[1000] flex items-center justify-center p-4">
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    onClick={onClose}
                    className="absolute inset-0 bg-black/40 backdrop-blur-sm"
                />

                <motion.div
                    initial={{ scale: 0.95, opacity: 0, y: 10 }}
                    animate={{ scale: 1, opacity: 1, y: 0 }}
                    exit={{ scale: 0.95, opacity: 0, y: 10 }}
                    transition={{ type: "spring", duration: 0.5 }}
                    className="w-full max-w-md bg-[#1c1c1e] border border-white/10 rounded-2xl shadow-2xl overflow-hidden relative z-10"
                >
                    {/* Header */}
                    <div className="flex justify-between items-center p-5 border-b border-white/5 bg-white/5">
                        <h3 className="text-lg font-semibold text-white">Export Data</h3>
                        <button onClick={onClose} className="p-2 hover:bg-white/10 rounded-full transition-colors text-gray-400 hover:text-white">
                            <X size={18} />
                        </button>
                    </div>

                    <div className="p-6 space-y-6">
                        {/* Format Selection */}
                        <div className="space-y-3">
                            <label className="text-xs font-medium text-gray-400 uppercase tracking-wider">Format</label>
                            <div className="grid grid-cols-3 gap-3">
                                {[
                                    { id: 'json', label: 'JSON', icon: FileJson },
                                    { id: 'csv', label: 'CSV', icon: Table },
                                    { id: 'excel', label: 'Excel', icon: FileSpreadsheet },
                                ].map((opt) => (
                                    <button
                                        key={opt.id}
                                        onClick={() => setFormat(opt.id as any)}
                                        className={clsx(
                                            "flex flex-col items-center justify-center gap-2 p-3 rounded-xl border transition-all duration-200",
                                            format === opt.id
                                                ? "bg-apple-blue/20 border-apple-blue/50 text-white shadow-[0_0_15px_rgba(59,130,246,0.2)]"
                                                : "bg-white/5 border-transparent text-gray-400 hover:bg-white/10 hover:text-white"
                                        )}
                                    >
                                        <opt.icon size={20} className={format === opt.id ? "text-apple-blue" : ""} />
                                        <span className="text-xs font-medium">{opt.label}</span>
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Options */}
                        <div className="space-y-3">
                            <label className="text-xs font-medium text-gray-400 uppercase tracking-wider">Smart Cleaning</label>

                            <button
                                onClick={() => setNormalizePhones(!normalizePhones)}
                                className="w-full flex items-center justify-between p-4 bg-white/5 rounded-xl border border-white/5 hover:bg-white/10 transition-colors"
                            >
                                <div className="text-left">
                                    <div className="text-sm font-medium text-white">Normalize Phone Numbers</div>
                                    <div className="text-xs text-gray-500 mt-1">Converts to E.164 format (e.g. +1 555-0123)</div>
                                </div>
                                <div className={clsx(
                                    "w-6 h-6 rounded-full border flex items-center justify-center transition-colors",
                                    normalizePhones ? "bg-apple-blue border-apple-blue" : "border-gray-600"
                                )}>
                                    {normalizePhones && <Check size={14} className="text-white" />}
                                </div>
                            </button>
                        </div>
                    </div>

                    {/* Footer */}
                    <div className="p-5 border-t border-white/5 bg-white/5 flex justify-end gap-3">
                        <button
                            onClick={onClose}
                            className="px-4 py-2 text-sm font-medium text-gray-400 hover:text-white transition-colors"
                        >
                            Cancel
                        </button>
                        <button
                            onClick={handleExport}
                            disabled={isExporting}
                            className="flex items-center gap-2 px-6 py-2 bg-apple-blue hover:bg-blue-600 text-white rounded-full text-sm font-medium transition-all shadow-lg shadow-blue-500/30 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {isExporting ? (
                                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                            ) : (
                                <Download size={16} />
                            )}
                            {isExporting ? 'Exporting...' : 'Export File'}
                        </button>
                    </div>
                </motion.div>
            </div>
        </AnimatePresence>
    );
};

export default ExportModal;
