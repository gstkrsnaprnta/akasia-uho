"use client"

import * as React from "react"
import { motion } from "framer-motion"
import { User, Sparkles, BookOpen } from "lucide-react"
import { cn } from "@/lib/utils"

interface ChatBubbleProps {
    role: "user" | "ai"
    content: string
    citations?: string[]
    isTyping?: boolean
}

export function ChatBubble({ role, content, citations, isTyping }: ChatBubbleProps) {
    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className={cn(
                "flex w-full mb-8",
                role === "user" ? "justify-end" : "justify-start"
            )}
        >
            <div className={cn(
                "flex max-w-[80%] md:max-w-[70%] gap-4",
                role === "user" ? "flex-row-reverse" : "flex-row"
            )}>
                {/* Avatar */}
                <div className={cn(
                    "w-10 h-10 rounded-full flex items-center justify-center shrink-0 border shadow-lg",
                    role === "user"
                        ? "bg-slate-800 border-slate-700"
                        : "bg-gradient-to-br from-blue-500 to-purple-600 border-transparent"
                )}>
                    {role === "user" ? <User className="w-5 h-5 text-slate-400" /> : <Sparkles className="w-5 h-5 text-white" />}
                </div>

                {/* Message Content */}
                <div className="flex flex-col gap-2">
                    <div className={cn(
                        "p-5 rounded-2xl backdrop-blur-md shadow-sm border text-sm md:text-base leading-relaxed",
                        role === "user"
                            ? "bg-white/10 border-white/10 text-white rounded-tr-none"
                            : "bg-slate-900/40 border-slate-800/60 text-slate-200 rounded-tl-none ring-1 ring-white/5"
                    )}>
                        {isTyping ? (
                            <div className="flex gap-1.5 items-center h-6">
                                <motion.div
                                    className="w-2.5 h-2.5 rounded-full bg-gradient-to-r from-blue-400 to-cyan-400"
                                    animate={{
                                        y: [0, -8, 0],
                                        scale: [1, 1.1, 1]
                                    }}
                                    transition={{
                                        duration: 0.6,
                                        repeat: Infinity,
                                        delay: 0,
                                        ease: "easeInOut"
                                    }}
                                />
                                <motion.div
                                    className="w-2.5 h-2.5 rounded-full bg-gradient-to-r from-purple-400 to-pink-400"
                                    animate={{
                                        y: [0, -8, 0],
                                        scale: [1, 1.1, 1]
                                    }}
                                    transition={{
                                        duration: 0.6,
                                        repeat: Infinity,
                                        delay: 0.15,
                                        ease: "easeInOut"
                                    }}
                                />
                                <motion.div
                                    className="w-2.5 h-2.5 rounded-full bg-gradient-to-r from-cyan-400 to-blue-400"
                                    animate={{
                                        y: [0, -8, 0],
                                        scale: [1, 1.1, 1]
                                    }}
                                    transition={{
                                        duration: 0.6,
                                        repeat: Infinity,
                                        delay: 0.3,
                                        ease: "easeInOut"
                                    }}
                                />
                            </div>
                        ) : (
                            <p className="whitespace-pre-wrap">{content}</p>
                        )}
                    </div>

                    {/* Citations (AI Only) */}
                    {role === "ai" && citations && citations.length > 0 && !isTyping && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ delay: 0.5 }}
                            className="flex flex-wrap gap-2 mt-1"
                        >
                            {citations.map((cite, i) => (
                                <div key={i} className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-300 text-xs hover:bg-blue-500/20 transition-colors cursor-pointer">
                                    <BookOpen className="w-3 h-3" />
                                    <span>{cite}</span>
                                </div>
                            ))}
                        </motion.div>
                    )}
                </div>
            </div>
        </motion.div>
    )
}
