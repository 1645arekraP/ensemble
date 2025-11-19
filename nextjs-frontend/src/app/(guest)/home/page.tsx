"use client"

import React from 'react';
import Link from 'next/link';
import { ArrowRight, Box, Cpu, GitBranch, Layers, Play, Zap } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function Home() {
    return (
        <div className="min-h-screen bg-white text-neutral-900 font-sans selection:bg-blue-100">

            {/* Navigation */}
            <nav className="fixed top-0 w-full bg-white/80 backdrop-blur-md border-b border-neutral-100 z-50">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center text-white">
                            <Layers className="w-5 h-5" />
                        </div>
                        <span className="text-xl font-bold tracking-tight">Ensemble</span>
                    </div>
                    <div className="flex items-center gap-4">
                        <Link href="/login" className="text-sm font-medium text-neutral-600 hover:text-neutral-900 transition-colors">
                            Log in
                        </Link>
                        <Link href="/signup">
                            <Button className="bg-blue-600 hover:bg-blue-700 text-white rounded-full px-6">
                                Get Started
                            </Button>
                        </Link>
                    </div>
                </div>
            </nav>

            {/* Hero Section */}
            <section className="pt-32 pb-20 lg:pt-40 lg:pb-28 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto text-center">
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-50 text-blue-600 text-sm font-medium mb-8 animate-fade-in-up">
                    <span className="relative flex h-2 w-2">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500"></span>
                    </span>
                    under development
                </div>
                <h1 className="text-5xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight text-neutral-900 mb-6 max-w-4xl mx-auto leading-[1.1]">
                    Orchestrate AI Agents with <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-600">Visual Clarity</span>
                </h1>
                <p className="text-xl text-neutral-600 mb-10 max-w-2xl mx-auto leading-relaxed">
                    Build, test, and deploy complex multi-agent workflows without writing code. The most intuitive drag-and-drop platform for the age of AI.
                </p>
                <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                    <Link href="/register">
                        <Button size="lg" className="h-12 px-8 text-lg rounded-full bg-neutral-900 hover:bg-neutral-800 text-white shadow-lg hover:shadow-xl transition-all transform hover:-translate-y-0.5">
                            Start Building Free
                            <ArrowRight className="ml-2 w-5 h-5" />
                        </Button>
                    </Link>
                </div>

                {/* Hero Visual / Placeholder */}
                <div className="mt-16 relative rounded-2xl border border-neutral-200 shadow-2xl overflow-hidden bg-neutral-50 aspect-[16/9] max-w-5xl mx-auto group">
                    <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-purple-500/5"></div>
                    <div className="absolute inset-0 flex items-center justify-center">
                        {/* Abstract UI representation */}
                        <div className="relative w-3/4 h-3/4 bg-white rounded-xl shadow-lg border border-neutral-100 p-4 flex gap-4">
                            <div className="w-1/4 h-full bg-neutral-50 rounded-lg border border-neutral-100 p-2 space-y-2">
                                <div className="h-8 bg-neutral-200 rounded w-full animate-pulse"></div>
                                <div className="h-8 bg-neutral-100 rounded w-3/4"></div>
                                <div className="h-8 bg-neutral-100 rounded w-5/6"></div>
                            </div>
                            <div className="flex-1 h-full bg-neutral-50 rounded-lg border border-neutral-100 relative overflow-hidden">
                                <div className="absolute top-1/4 left-1/4 w-12 h-12 bg-blue-100 rounded-lg border-2 border-blue-500 shadow-sm z-10"></div>
                                <div className="absolute top-1/2 left-1/2 w-12 h-12 bg-purple-100 rounded-lg border-2 border-purple-500 shadow-sm z-10"></div>
                                <svg className="absolute inset-0 w-full h-full pointer-events-none">
                                    <path d="M 200 150 Q 300 200 400 250" stroke="#cbd5e1" strokeWidth="2" fill="none" strokeDasharray="4 4" />
                                </svg>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            {/* Features Grid */}
            <section className="py-24 bg-neutral-50">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="text-center mb-16">
                        <h2 className="text-3xl font-bold text-neutral-900 mb-4">Everything you need to build agents</h2>
                        <p className="text-lg text-neutral-600 max-w-2xl mx-auto">
                            From simple chatbots to complex autonomous swarms, Ensemble gives you the tools to build faster.
                        </p>
                    </div>

                    <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
                        {[
                            {
                                icon: <Box className="w-6 h-6 text-blue-600" />,
                                title: "Visual Builder",
                                desc: "Drag, drop, and connect nodes to create workflows. No spaghetti code, just clear logic."
                            },
                            {
                                icon: <Cpu className="w-6 h-6 text-purple-600" />,
                                title: "Multi-Agent Orchestration",
                                desc: "Coordinate multiple specialized agents to solve complex tasks collaboratively."
                            },
                            {
                                icon: <Zap className="w-6 h-6 text-amber-600" />,
                                title: "Real-time Streaming",
                                desc: "Watch your agents think and act in real-time with live execution logs and state updates."
                            },
                            {
                                icon: <Layers className="w-6 h-6 text-indigo-600" />,
                                title: "Extensible Tools",
                                desc: "Connect to any API, database, or service. If it has an API, your agents can use it."
                            }
                        ].map((feature, i) => (
                            <div key={i} className="bg-white p-8 rounded-2xl border border-neutral-100 shadow-sm hover:shadow-md transition-shadow">
                                <div className="w-12 h-12 bg-neutral-50 rounded-xl flex items-center justify-center mb-6">
                                    {feature.icon}
                                </div>
                                <h3 className="text-xl font-semibold text-neutral-900 mb-3">{feature.title}</h3>
                                <p className="text-neutral-600 leading-relaxed">{feature.desc}</p>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* CTA Section */}
            <section className="py-24 px-4 sm:px-6 lg:px-8">
                <div className="max-w-5xl mx-auto bg-neutral-900 rounded-3xl p-12 sm:p-16 text-center text-white relative overflow-hidden">
                    <div className="absolute top-0 left-0 w-full h-full opacity-10 bg-[radial-gradient(circle_at_top_right,_var(--tw-gradient-stops))] from-blue-500 via-purple-500 to-transparent"></div>

                    <h2 className="text-3xl sm:text-4xl font-bold mb-6 relative z-10">Ready to build your first agent?</h2>
                    <p className="text-lg text-neutral-400 mb-10 max-w-2xl mx-auto relative z-10">
                        Start building the future of AI automation with Ensemble.
                    </p>
                    <div className="relative z-10">
                        <Link href="/register">
                            <Button size="lg" className="h-14 px-10 text-lg rounded-full bg-white text-neutral-900 hover:bg-neutral-100 font-semibold">
                                Get Started for Free
                            </Button>
                        </Link>
                    </div>
                </div>
            </section>

            {/* Footer */}
            <footer className="border-t border-neutral-100 py-12 bg-white">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row justify-between items-center gap-6">
                    <div className="flex items-center gap-2">
                        <div className="w-6 h-6 bg-neutral-900 rounded-md flex items-center justify-center text-white">
                            <Layers className="w-3 h-3" />
                        </div>
                        <span className="font-bold text-neutral-900">Ensemble</span>
                    </div>
                    <div className="text-sm text-neutral-500">
                        © {new Date().getFullYear()} Ensemble AI. All rights reserved.
                    </div>
                </div>
            </footer>
        </div>
    );
}