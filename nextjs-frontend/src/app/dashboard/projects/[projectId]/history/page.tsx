'use client';

import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getProjectExecutions, getProjectById, ExecutionLog, deleteExecution } from '@/lib/api';
import { format } from 'date-fns';
import Link from 'next/link';
import { ArrowLeft, Clock, CheckCircle, XCircle, PlayCircle, Terminal, Calendar, Trash2 } from 'lucide-react';
import { SiteHeader } from "@/components/site-header";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import ReactMarkdown from 'react-markdown';

interface HistoryPageProps {
    params: Promise<{
        projectId: string;
    }>;
}

export default function HistoryPage({ params }: HistoryPageProps) {
    const { projectId } = React.use(params);

    const { data: project } = useQuery({
        queryKey: ['project', projectId],
        queryFn: () => getProjectById(projectId),
    });

    const { data: executions, isLoading, error } = useQuery({
        queryKey: ['executions', projectId],
        queryFn: () => getProjectExecutions(projectId),
    });

    const [selectedExecution, setSelectedExecution] = React.useState<ExecutionLog | null>(null);
    const [executionToDelete, setExecutionToDelete] = React.useState<number | null>(null);
    const queryClient = useQueryClient();

    const deleteMutation = useMutation({
        mutationFn: deleteExecution,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['executions', projectId] });
            if (selectedExecution && executionToDelete === selectedExecution.id) {
                setSelectedExecution(null);
            }
            setExecutionToDelete(null);
        },
    });

    const handleDeleteClick = (e: React.MouseEvent, id: number) => {
        e.stopPropagation();
        setExecutionToDelete(id);
    };

    const confirmDelete = () => {
        if (executionToDelete) {
            deleteMutation.mutate(executionToDelete);
        }
    };

    // Select the first execution by default when loaded
    React.useEffect(() => {
        if (executions && executions.length > 0 && !selectedExecution) {
            setSelectedExecution(executions[0]);
        }
    }, [executions, selectedExecution]);

    if (isLoading) {
        return (
            <div className="flex h-screen items-center justify-center bg-neutral-50">
                <div className="text-neutral-500">Loading history...</div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex h-screen items-center justify-center bg-neutral-50">
                <div className="text-red-500">Error loading history.</div>
            </div>
        );
    }

    return (
        <div className="flex h-screen w-screen flex-col bg-neutral-50 overflow-hidden">
            <SiteHeader name={`History: ${project?.name || 'Loading...'}`}>
                <Button variant="ghost" size="sm" asChild>
                    <Link href={`/dashboard/projects/${projectId}`}>
                        <ArrowLeft className="w-4 h-4 mr-2" />
                        Back to Canvas
                    </Link>
                </Button>
            </SiteHeader>

            <div className="flex-1 flex overflow-hidden">
                {/* Sidebar List */}
                <div className="w-80 border-r border-neutral-200 bg-white flex flex-col flex-shrink-0">
                    <div className="p-4 border-b border-neutral-200 bg-neutral-50/50">
                        <h2 className="font-semibold text-sm text-neutral-900">Past Executions</h2>
                        <p className="text-xs text-neutral-500 mt-1">Select a run to view details</p>
                    </div>
                    <div className="flex-1 overflow-y-auto">
                        {executions?.map((execution) => (
                            <div
                                key={execution.id}
                                onClick={() => setSelectedExecution(execution)}
                                className={`p-4 border-b border-neutral-100 cursor-pointer transition-colors hover:bg-neutral-50 ${selectedExecution?.id === execution.id ? 'bg-blue-50 border-l-4 border-l-blue-500' : 'border-l-4 border-l-transparent'
                                    }`}
                            >
                                <div className="flex justify-between items-start mb-2">
                                    <div className="flex items-center gap-2">
                                        {execution.status === 'completed' ? (
                                            <CheckCircle className="w-4 h-4 text-green-500" />
                                        ) : execution.status === 'failed' ? (
                                            <XCircle className="w-4 h-4 text-red-500" />
                                        ) : (
                                            <PlayCircle className="w-4 h-4 text-blue-500" />
                                        )}
                                        <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${execution.status === 'completed' ? 'bg-green-100 text-green-700' :
                                            execution.status === 'failed' ? 'bg-red-100 text-red-700' :
                                                'bg-blue-100 text-blue-700'
                                            }`}>
                                            {execution.status.toUpperCase()}
                                        </span>
                                    </div>
                                    <button
                                        onClick={(e) => handleDeleteClick(e, execution.id)}
                                        className="p-1 hover:bg-red-100 rounded text-neutral-400 hover:text-red-600 transition-colors"
                                        title="Delete Execution"
                                    >
                                        <Trash2 className="w-3 h-3" />
                                    </button>
                                </div>
                                <div className="flex items-center gap-2 text-xs text-neutral-500 mb-2">
                                    <Calendar className="w-3 h-3" />
                                    {format(new Date(execution.started_at), 'MMM d, yyyy HH:mm')}
                                </div>

                                <div className="text-xs text-neutral-600 line-clamp-2 font-mono bg-neutral-100 p-1.5 rounded">
                                    {JSON.stringify(execution.initial_input)}
                                </div>
                            </div>
                        ))}
                        {executions?.length === 0 && (
                            <div className="p-8 text-center text-neutral-500 text-sm">No executions found.</div>
                        )}
                    </div>
                </div>

                {/* Detail View */}
                <div className="flex-1 flex flex-col bg-neutral-50 overflow-hidden">
                    {selectedExecution ? (
                        <div className="flex-1 flex flex-col h-full overflow-hidden">
                            {/* Header */}
                            <div className="px-6 py-4 bg-white border-b border-neutral-200 flex justify-between items-center shadow-sm z-10">
                                <div>
                                    <h1 className="text-lg font-bold text-neutral-900 flex items-center gap-2">
                                        Execution #{selectedExecution.id}
                                        <span className={`text-xs px-2 py-1 rounded-full border ${selectedExecution.status === 'completed' ? 'bg-green-50 border-green-200 text-green-700' :
                                            selectedExecution.status === 'failed' ? 'bg-red-50 border-red-200 text-red-700' :
                                                'bg-blue-50 border-blue-200 text-blue-700'
                                            }`}>
                                            {selectedExecution.status}
                                        </span>
                                    </h1>
                                    <div className="flex items-center gap-4 mt-1 text-sm text-neutral-500">
                                        <span className="flex items-center gap-1">
                                            <PlayCircle className="w-3 h-3" />
                                            Started: {format(new Date(selectedExecution.started_at), 'PPpp')}
                                        </span>
                                        {selectedExecution.completed_at && (
                                            <span className="flex items-center gap-1">
                                                <CheckCircle className="w-3 h-3" />
                                                Completed: {format(new Date(selectedExecution.completed_at), 'PPpp')}
                                            </span>
                                        )}
                                    </div>
                                </div>
                            </div>

                            {/* Content */}
                            <div className="flex-1 overflow-y-auto p-6 space-y-6">
                                {/* Input Section */}
                                <div className="bg-white rounded-lg border border-neutral-200 shadow-sm overflow-hidden">
                                    <div className="px-4 py-2 bg-neutral-50 border-b border-neutral-200 flex items-center gap-2">
                                        <Terminal className="w-4 h-4 text-neutral-500" />
                                        <h3 className="text-sm font-semibold text-neutral-700">Initial Input</h3>
                                    </div>
                                    <div className="p-4 bg-neutral-900 overflow-x-auto">
                                        <pre className="text-sm font-mono text-green-400">
                                            {JSON.stringify(selectedExecution.initial_input, null, 2)}
                                        </pre>
                                    </div>
                                </div>

                                {/* Final Output Section */}
                                {selectedExecution.final_output && (
                                    <div className="bg-white rounded-lg border border-neutral-200 shadow-sm overflow-hidden">
                                        <div className="px-4 py-2 bg-green-50 border-b border-green-100 flex items-center gap-2">
                                            <CheckCircle className="w-4 h-4 text-green-600" />
                                            <h3 className="text-sm font-semibold text-green-800">Final Output</h3>
                                        </div>
                                        <div className="p-4 text-neutral-800 font-medium prose prose-sm max-w-none">
                                            <ReactMarkdown>{selectedExecution.final_output}</ReactMarkdown>
                                        </div>
                                    </div>
                                )}

                                {/* Logs Section */}
                                <div className="bg-white rounded-lg border border-neutral-200 shadow-sm overflow-hidden">
                                    <div className="px-4 py-2 bg-neutral-50 border-b border-neutral-200 flex items-center gap-2">
                                        <Clock className="w-4 h-4 text-neutral-500" />
                                        <h3 className="text-sm font-semibold text-neutral-700">Execution Logs</h3>
                                    </div>
                                    <div className="divide-y divide-neutral-100">
                                        {selectedExecution.logs.map((log, index) => (
                                            <div key={index} className="p-3 text-sm hover:bg-neutral-50 transition-colors">
                                                {log.type === 'tool_output' && (
                                                    <div className="space-y-1">
                                                        <div className="flex items-center gap-2 text-blue-600 font-medium text-xs uppercase tracking-wider">
                                                            <Terminal className="w-3 h-3" />
                                                            Tool Output: {log.node}
                                                        </div>
                                                        <div className="bg-neutral-50 border border-neutral-200 rounded p-2 text-neutral-700 text-xs prose prose-xs max-w-none">
                                                            <ReactMarkdown>{log.output}</ReactMarkdown>
                                                        </div>
                                                    </div>
                                                )}
                                                {log.type === 'agent_output' && (
                                                    <div className="space-y-1">
                                                        <div className="flex items-center gap-2 text-purple-600 font-medium text-xs uppercase tracking-wider">
                                                            <div className="w-2 h-2 rounded-full bg-purple-500" />
                                                            Agent: {log.node}
                                                        </div>
                                                        <div className="pl-4 text-neutral-800 prose prose-sm max-w-none">
                                                            <ReactMarkdown>{log.output}</ReactMarkdown>
                                                        </div>
                                                    </div>
                                                )}
                                                {log.type === 'update' && (
                                                    <div className="flex items-center gap-2 text-neutral-500 italic text-xs">
                                                        <Clock className="w-3 h-3" />
                                                        Running {log.node}...
                                                    </div>
                                                )}
                                                {log.type === 'error' && (
                                                    <div className="bg-red-50 border border-red-100 rounded p-3 text-red-600 flex items-start gap-2">
                                                        <XCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                                                        <div>
                                                            <div className="font-bold text-xs uppercase tracking-wider mb-1">Error</div>
                                                            {log.error}
                                                        </div>
                                                    </div>
                                                )}
                                                {log.type === 'complete' && (
                                                    <div className="flex items-center gap-2 text-green-600 font-medium bg-green-50 p-2 rounded border border-green-100">
                                                        <CheckCircle className="w-4 h-4" />
                                                        {log.message}
                                                    </div>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        </div>
                    ) : (
                        <div className="flex-1 flex flex-col items-center justify-center text-neutral-400 bg-neutral-50">
                            <Clock className="w-16 h-16 mb-4 opacity-20" />
                            <p className="text-lg font-medium text-neutral-500">Select an execution to view details</p>
                        </div>
                    )}
                </div>
            </div >

            <Dialog open={!!executionToDelete} onOpenChange={(open) => !open && setExecutionToDelete(null)}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Delete Execution</DialogTitle>
                        <DialogDescription>
                            Are you sure you want to delete this execution log? This action cannot be undone.
                        </DialogDescription>
                    </DialogHeader>
                    <DialogFooter>
                        <Button variant="outline" onClick={() => setExecutionToDelete(null)}>
                            Cancel
                        </Button>
                        <Button variant="destructive" onClick={confirmDelete} disabled={deleteMutation.isPending}>
                            {deleteMutation.isPending ? 'Deleting...' : 'Delete'}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div >
    );
}
