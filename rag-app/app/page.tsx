"use client"

/**
 * Landing Page - AKASIA v2.0
 * Halaman pertama yang dilihat pengunjung
 */

import * as React from "react"
import Link from "next/link"
import { motion } from "framer-motion"
import {
    GraduationCap, MessageSquare, FileText, BarChart3,
    Sparkles, ArrowRight, BookOpen, Clock, Shield, Zap,
    ChevronRight
} from "lucide-react"

// Animation variants
const fadeUp = {
    hidden: { opacity: 0, y: 30 },
    visible: (i: number) => ({
        opacity: 1,
        y: 0,
        transition: { delay: i * 0.1, duration: 0.5, ease: [0.25, 0.46, 0.45, 0.94] }
    })
}

const features = [
    {
        icon: MessageSquare,
        title: "Chat AI Interaktif",
        description: "Tanyakan apa saja tentang peraturan akademik dan dapatkan jawaban instan",
        color: "from-blue-500 to-cyan-500"
    },
    {
        icon: BookOpen,
        title: "Knowledge Base",
        description: "Didukung oleh dokumen resmi Peraturan Rektor dan Kalender Akademik UHO",
        color: "from-purple-500 to-pink-500"
    },
    {
        icon: Zap,
        title: "Respons Cepat",
        description: "Jawaban akurat dalam hitungan detik dengan teknologi RAG terkini",
        color: "from-amber-500 to-orange-500"
    },
    {
        icon: Shield,
        title: "Akurat & Terpercaya",
        description: "Setiap jawaban dilengkapi sumber referensi Pasal yang jelas",
        color: "from-green-500 to-emerald-500"
    }
]

const stats = [
    { value: "2+", label: "Dokumen Akademik" },
    { value: "276", label: "Knowledge Chunks" },
    { value: "24/7", label: "Tersedia" },
    { value: "< 3s", label: "Waktu Respons" }
]

export default function LandingPage() {
    return (
        <div className="min-h-screen overflow-hidden">
            {/* Hero Section */}
            <section className="relative min-h-screen flex items-center justify-center px-6">
                {/* Animated Background Orbs */}
                <div className="absolute inset-0 overflow-hidden pointer-events-none">
                    <motion.div
                        className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-500/20 rounded-full blur-3xl"
                        animate={{
                            x: [0, 50, 0],
                            y: [0, 30, 0],
                            scale: [1, 1.1, 1]
                        }}
                        transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
                    />
                    <motion.div
                        className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-purple-500/20 rounded-full blur-3xl"
                        animate={{
                            x: [0, -40, 0],
                            y: [0, -20, 0],
                            scale: [1, 1.15, 1]
                        }}
                        transition={{ duration: 10, repeat: Infinity, ease: "easeInOut" }}
                    />
                </div>

                <div className="relative z-10 max-w-5xl mx-auto text-center">
                    {/* Badge */}
                    <motion.div
                        custom={0}
                        variants={fadeUp}
                        initial="hidden"
                        animate="visible"
                        className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-purple-500/10 border border-purple-500/20 text-purple-300 text-sm mb-8"
                    >
                        <Sparkles className="w-4 h-4" />
                        <span>Powered by AI & RAG Technology</span>
                    </motion.div>

                    {/* Main Title */}
                    <motion.h1
                        custom={1}
                        variants={fadeUp}
                        initial="hidden"
                        animate="visible"
                        className="text-5xl md:text-7xl font-bold mb-6"
                    >
                        <span className="gradient-text">AKASIA</span>
                    </motion.h1>

                    <motion.p
                        custom={2}
                        variants={fadeUp}
                        initial="hidden"
                        animate="visible"
                        className="text-xl md:text-2xl text-slate-300 mb-4"
                    >
                        Asisten Akademik Sistem Informasi Answering
                    </motion.p>

                    <motion.p
                        custom={3}
                        variants={fadeUp}
                        initial="hidden"
                        animate="visible"
                        className="text-lg text-slate-400 max-w-2xl mx-auto mb-10"
                    >
                        Chatbot AI untuk menjawab pertanyaan seputar peraturan akademik
                        Universitas Halu Oleo dengan cepat dan akurat
                    </motion.p>

                    {/* CTA Buttons */}
                    <motion.div
                        custom={4}
                        variants={fadeUp}
                        initial="hidden"
                        animate="visible"
                        className="flex flex-col sm:flex-row gap-4 justify-center"
                    >
                        <Link href="/chat">
                            <motion.button
                                className="group px-8 py-4 bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl text-white font-semibold shadow-lg shadow-purple-500/25 flex items-center gap-2 justify-center"
                                whileHover={{ scale: 1.02, boxShadow: "0 20px 40px rgba(139, 92, 246, 0.3)" }}
                                whileTap={{ scale: 0.98 }}
                            >
                                <MessageSquare className="w-5 h-5" />
                                Mulai Chat
                                <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                            </motion.button>
                        </Link>
                        <Link href="/admin">
                            <motion.button
                                className="px-8 py-4 bg-white/5 border border-white/10 rounded-xl text-white font-semibold flex items-center gap-2 justify-center hover:bg-white/10 transition-colors"
                                whileHover={{ scale: 1.02 }}
                                whileTap={{ scale: 0.98 }}
                            >
                                <BarChart3 className="w-5 h-5" />
                                Admin Dashboard
                            </motion.button>
                        </Link>
                    </motion.div>

                    {/* Stats */}
                    <motion.div
                        custom={5}
                        variants={fadeUp}
                        initial="hidden"
                        animate="visible"
                        className="grid grid-cols-2 md:grid-cols-4 gap-6 mt-16 max-w-3xl mx-auto"
                    >
                        {stats.map((stat, i) => (
                            <div key={i} className="text-center">
                                <div className="text-3xl md:text-4xl font-bold gradient-text">{stat.value}</div>
                                <div className="text-sm text-slate-400 mt-1">{stat.label}</div>
                            </div>
                        ))}
                    </motion.div>
                </div>

                {/* Scroll Indicator */}
                <motion.div
                    className="absolute bottom-8 left-1/2 -translate-x-1/2"
                    animate={{ y: [0, 10, 0] }}
                    transition={{ duration: 2, repeat: Infinity }}
                >
                    <ChevronRight className="w-6 h-6 rotate-90 text-slate-500" />
                </motion.div>
            </section>

            {/* Features Section */}
            <section className="py-24 px-6 relative">
                <div className="max-w-6xl mx-auto">
                    <motion.div
                        className="text-center mb-16"
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                    >
                        <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
                            Fitur Unggulan
                        </h2>
                        <p className="text-slate-400 max-w-2xl mx-auto">
                            AKASIA dilengkapi dengan teknologi AI terkini untuk membantu mahasiswa
                            mendapatkan informasi akademik dengan mudah
                        </p>
                    </motion.div>

                    <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
                        {features.map((feature, i) => (
                            <motion.div
                                key={i}
                                className="p-6 rounded-2xl bg-slate-900/50 border border-slate-800/50 backdrop-blur-sm group hover:border-slate-700/50 transition-colors"
                                initial={{ opacity: 0, y: 30 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                viewport={{ once: true }}
                                transition={{ delay: i * 0.1 }}
                                whileHover={{ y: -5 }}
                            >
                                <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${feature.color} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}>
                                    <feature.icon className="w-6 h-6 text-white" />
                                </div>
                                <h3 className="text-lg font-semibold text-white mb-2">{feature.title}</h3>
                                <p className="text-sm text-slate-400">{feature.description}</p>
                            </motion.div>
                        ))}
                    </div>
                </div>
            </section>

            {/* Demo Preview Section */}
            <section className="py-24 px-6 relative">
                <div className="max-w-5xl mx-auto">
                    <motion.div
                        className="rounded-3xl bg-gradient-to-br from-slate-900 to-slate-800 border border-slate-700/50 p-8 md:p-12 overflow-hidden relative"
                        initial={{ opacity: 0, scale: 0.95 }}
                        whileInView={{ opacity: 1, scale: 1 }}
                        viewport={{ once: true }}
                    >
                        {/* Glow Effect */}
                        <div className="absolute top-0 right-0 w-64 h-64 bg-purple-500/10 rounded-full blur-3xl" />

                        <div className="relative z-10 flex flex-col md:flex-row items-center gap-8">
                            <div className="flex-1">
                                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-green-500/10 border border-green-500/20 text-green-400 text-xs mb-4">
                                    <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                                    System Online
                                </div>
                                <h3 className="text-2xl md:text-3xl font-bold text-white mb-4">
                                    Siap Menjawab Pertanyaan Anda
                                </h3>
                                <p className="text-slate-400 mb-6">
                                    Coba tanyakan tentang masa studi, syarat kelulusan, prosedur cuti akademik,
                                    atau jadwal kalender akademik UHO.
                                </p>
                                <Link href="/chat">
                                    <motion.button
                                        className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl text-white font-medium flex items-center gap-2"
                                        whileHover={{ scale: 1.02 }}
                                        whileTap={{ scale: 0.98 }}
                                    >
                                        Coba Sekarang
                                        <ArrowRight className="w-4 h-4" />
                                    </motion.button>
                                </Link>
                            </div>

                            {/* Chat Preview */}
                            <div className="flex-1 w-full">
                                <div className="bg-slate-950/80 rounded-2xl border border-slate-700/50 p-4 space-y-4">
                                    <div className="flex gap-3">
                                        <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center shrink-0">
                                            <GraduationCap className="w-4 h-4 text-slate-400" />
                                        </div>
                                        <div className="bg-slate-800/50 rounded-xl rounded-tl-none px-4 py-3 text-sm text-slate-300">
                                            Berapa masa studi maksimal S1?
                                        </div>
                                    </div>
                                    <div className="flex gap-3">
                                        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center shrink-0">
                                            <Sparkles className="w-4 h-4 text-white" />
                                        </div>
                                        <div className="bg-slate-800/30 rounded-xl rounded-tl-none px-4 py-3 text-sm text-slate-200">
                                            Masa studi maksimal S1 adalah 7 tahun akademik dengan beban studi minimal 144 SKS.
                                            <span className="text-blue-400"> [Sumber: Pasal 44]</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </motion.div>
                </div>
            </section>

            {/* Footer */}
            <footer className="py-12 px-6 border-t border-slate-800/50">
                <div className="max-w-5xl mx-auto text-center">
                    <div className="flex items-center justify-center gap-2 mb-4">
                        <GraduationCap className="w-6 h-6 text-purple-400" />
                        <span className="text-xl font-bold gradient-text">AKASIA</span>
                    </div>
                    <p className="text-slate-500 text-sm mb-4">
                        Asisten Akademik Berbasis AI untuk Universitas Halu Oleo
                    </p>
                    <p className="text-slate-600 text-xs">
                        © 2025 AKASIA v2.0 • Built with Next.js, FastAPI & LangChain
                    </p>
                </div>
            </footer>
        </div>
    )
}
