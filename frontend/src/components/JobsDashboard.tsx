import React, { useEffect, useState } from 'react';
import { Pause, Trash2, Clock, AlertCircle, CheckCircle2 } from 'lucide-react';
import clsx from 'clsx';
import { motion } from 'framer-motion';
import { api } from '../services/api';
import ExportModal from './ExportModal';

interface Job {
    id: number;
    name: string;
    status: 'RUNNING' | 'PAUSED' | 'COMPLETED' | 'FAILED' | 'PENDING' | 'PROCESSING';
    created_at: string;
    total_grids: number;
    completed_grids: number;
    results_count: number;
}

const StatusBadge = ({ status }: { status: Job['status'] }) => {
    const config = {
        RUNNING: { color: 'text-apple-blue', bg: 'bg-apple-blue/10', border: 'border-apple-blue/20', icon: ActivityIcon, label: 'Running' },
        PROCESSING: { color: 'text-apple-blue', bg: 'bg-apple-blue/10', border: 'border-apple-blue/20', icon: ActivityIcon, label: 'Proccessing' },
        PAUSED: { color: 'text-apple-yellow', bg: 'bg-apple-yellow/10', border: 'border-apple-yellow/20', icon: Pause, label: 'Paused' },
        COMPLETED: { color: 'text-apple-green', bg: 'bg-apple-green/10', border: 'border-apple-green/20', icon: CheckCircle2, label: 'Completed' },
        FAILED: { color: 'text-apple-red', bg: 'bg-apple-red/10', border: 'border-apple-red/20', icon: AlertCircle, label: 'Failed' },
        PENDING: { color: 'text-gray-400', bg: 'bg-gray-500/10', border: 'border-gray-500/20', icon: Clock, label: 'Pending' },
    };

    const style = config[status] || config.PENDING;
    const Icon = style.icon;

    return (
        <span className={clsx("flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium border backdrop-blur-md shadow-sm", style.color, style.bg, style.border)}>
            <Icon size={12} strokeWidth={2.5} className={status === 'RUNNING' || status === 'PROCESSING' ? 'animate-pulse' : ''} />
            {style.label}
        </span>
    );
};

// Custom tiny activity icon
const ActivityIcon = (props: any) => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
        <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
    </svg>
);

const JobsDashboard: React.FC = () => {
    const [jobs, setJobs] = useState<Job[]>([]);
    const [loading, setLoading] = useState(true);
    const [exportJob, setExportJob] = useState<{ id: number; name: string } | null>(null);

    const fetchJobs = async () => {
        try {
            const res = await api.getJobs();
            // Sort by newest first
            const sorted = res.data.sort((a: Job, b: Job) => b.id - a.id);
            setJobs(sorted);
        } catch (error) {
            console.error("Failed to fetch jobs", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchJobs();
        const interval = setInterval(fetchJobs, 2000);
        return () => clearInterval(interval);
    }, []);

    const container = {
        hidden: { opacity: 0 },
        show: {
            opacity: 1,
            transition: {
                staggerChildren: 0.05
            }
        }
    };

    const itemAnim: any = {
        hidden: { opacity: 0, y: 15, scale: 0.98 },
        show: { opacity: 1, y: 0, scale: 1, transition: { type: "spring", stiffness: 350, damping: 25 } }
    };

    if (loading && jobs.length === 0) return (
        <div className="flex flex-col items-center justify-center h-full text-gray-500 font-light tracking-wide space-y-4">
            <div className="w-6 h-6 border-2 border-apple-blue border-t-transparent rounded-full animate-spin" />
            <span className="text-xs uppercase tracking-widest text-gray-600">Loading Workspace</span>
        </div>
    );

    return (
        <>
            <motion.div
                className="h-full w-full overflow-y-auto pr-2 custom-scrollbar pb-20"
                variants={container}
                initial="hidden"
                animate="show"
            >
                <div className="grid gap-4">
                    {jobs.map((job) => {
                        const progress = job.total_grids > 0
                            ? (job.completed_grids / job.total_grids) * 100
                            : 0;

                        const isRunning = job.status === 'RUNNING' || job.status === 'PROCESSING';

                        return (
                            <motion.div
                                key={job.id}
                                variants={itemAnim}
                                layoutId={`job-${job.id}`}
                                className="glass-card rounded-2xl p-6 relative overflow-hidden group border border-white/5 hover:border-white/10 transition-colors"
                            >
                                {/* Ambient Background Glow for Active Jobs */}
                                {isRunning && (
                                    <div className="absolute -right-20 -top-20 w-64 h-64 bg-apple-blue/5 blur-[80px] rounded-full pointer-events-none" />
                                )}

                                <div className="flex justify-between items-start mb-5 relative z-10">
                                    <div>
                                        <h3 className="text-[15px] font-semibold text-white tracking-wide">{job.name}</h3>
                                        <div className="flex items-center gap-2 mt-1.5 text-xs text-gray-400 font-medium">
                                            <Clock size={12} strokeWidth={2} />
                                            <span>{new Date(job.created_at).toLocaleString(undefined, {
                                                month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
                                            })}</span>
                                        </div>
                                    </div>
                                    <StatusBadge status={job.status} />
                                </div>

                                {/* Refined Progress Bar */}
                                <div className="w-full h-1.5 bg-gray-700/30 rounded-full mb-4 overflow-hidden backdrop-blur-sm relative z-10 ring-1 ring-white/5">
                                    <motion.div
                                        className={clsx("h-full rounded-full shadow-[0_0_12px_rgba(59,130,246,0.6)]",
                                            job.status === 'FAILED' ? 'bg-apple-red shadow-apple-red/50' :
                                                job.status === 'COMPLETED' ? 'bg-apple-green shadow-apple-green/50' : 'bg-apple-blue shadow-apple-blue/50'
                                        )}
                                        initial={{ width: 0 }}
                                        animate={{ width: `${progress}%` }}
                                        transition={{ duration: 1.2, ease: "circOut" }}
                                    />
                                </div>

                                <div className="flex justify-between items-center text-xs text-gray-400 mb-2 relative z-10">
                                    <span className="font-medium flex items-center gap-1.5">
                                        <div className={clsx("w-1.5 h-1.5 rounded-full", isRunning ? "bg-apple-blue animate-pulse" : "bg-gray-600")} />
                                        {job.completed_grids} <span className="text-gray-600">/</span> {job.total_grids} Zones
                                    </span>
                                    <span className="text-white font-semibold tracking-wide bg-white/5 px-2 py-0.5 rounded-md border border-white/5">
                                        {job.results_count} <span className="text-gray-500 font-normal ml-1">Places</span>
                                    </span>
                                </div>

                                {/* Actions */}
                                <div className="flex gap-2 justify-end relative z-10 opacity-0 group-hover:opacity-100 transition-all duration-300 translate-y-2 group-hover:translate-y-0">
                                    <button
                                        onClick={() => setExportJob({ id: job.id, name: job.name })}
                                        className="px-3 py-1.5 hover:bg-apple-blue/10 rounded-lg text-[10px] font-medium text-apple-blue transition-all border border-transparent hover:border-apple-blue/20 flex items-center gap-1.5"
                                    >
                                        Download
                                    </button>
                                </div>
                            </motion.div>
                        );
                    })}

                    {jobs.length === 0 && (
                        <motion.div
                            variants={itemAnim}
                            className="text-center py-32 flex flex-col items-center justify-center"
                        >
                            <div className="w-20 h-20 bg-gradient-to-br from-gray-800 to-gray-900 rounded-3xl flex items-center justify-center mb-6 shadow-inner border border-white/5">
                                <Clock className="text-gray-600" size={32} strokeWidth={1.5} />
                            </div>
                            <h3 className="text-gray-300 font-medium text-lg">No active jobs</h3>
                            <p className="text-gray-500 text-sm mt-2 max-w-xs mx-auto">Select an area on the map to start your first scraping agent.</p>
                        </motion.div>
                    )}
                </div>
            </motion.div>

            {/* Export Modal */}
            {exportJob && (
                <ExportModal
                    jobId={exportJob.id}
                    jobName={exportJob.name}
                    onClose={() => setExportJob(null)}
                />
            )}
        </>
    );
};

export default JobsDashboard;
