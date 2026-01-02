"use client"

/**
 * ChatBubble Component - AKASIA v2.0
 * Komponen gelembung chat dengan animasi halus
 * Menggunakan Framer Motion untuk GPU-accelerated animations
 */

import * as React from "react"
import { motion, AnimatePresence } from "framer-motion"
import { User, Sparkles, BookOpen } from "lucide-react"
import { cn } from "@/lib/utils"

interface ChatBubbleProps {
    role: "user" | "ai"
    content: string
    citations?: string[]
    isTyping?: boolean
}

// Animation variants untuk performa optimal
const bubbleVariants = {
    hidden: {
        opacity: 0,
        y: 20,
        scale: 0.95
    },
    visible: {
        opacity: 1,
        y: 0,
        scale: 1,
        transition: {
            type: "spring",
            stiffness: 400,
            damping: 30,
            mass: 0.8
        }
    }
}

const avatarVariants = {
    hidden: { scale: 0, opacity: 0 },
    visible: {
        scale: 1,
        opacity: 1,
        transition: {
            type: "spring",
            stiffness: 500,
            damping: 25,
            delay: 0.1
        }
    }
}

const citationVariants = {
    hidden: { opacity: 0, y: 10 },
    visible: (i: number) => ({
        opacity: 1,
        y: 0,
        transition: {
            delay: 0.3 + (i * 0.1),
            duration: 0.3,
            ease: [0.4, 0, 0.2, 1]
        }
    })
}

// Komponen Typing Indicator dengan animasi halus
function TypingIndicator() {
    return (
        <div className="flex gap-1.5 items-center h-6 px-1">
            {[0, 1, 2].map((i) => (
                <motion.div
                    key={i}
                    className="w-2 h-2 rounded-full bg-gradient-to-r from-blue-400 via-purple-400 to-cyan-400"
                    animate={{
                        y: [0, -8, 0],
                        opacity: [0.5, 1, 0.5],
                    }}
                    transition={{
                        duration: 0.8,
                        repeat: Infinity,
                        delay: i * 0.15,
                        ease: "easeInOut"
                    }}
                />
            ))}
        </div>
    )
}

export function ChatBubble({ role, content, citations, isTyping }: ChatBubbleProps) {
    const isAI = role === "ai"

    return (
        <motion.div
            variants={bubbleVariants}
            initial="hidden"
            animate="visible"
            className={cn(
                "flex w-full mb-6",
                isAI ? "justify-start" : "justify-end"
            )}
        >
            <div className={cn(
                "flex max-w-[85%] md:max-w-[75%] gap-3",
                isAI ? "flex-row" : "flex-row-reverse"
            )}>
                {/* Avatar dengan animasi pop-in */}
                <motion.div
                    variants={avatarVariants}
                    initial="hidden"
                    animate="visible"
                    className={cn(
                        "w-10 h-10 rounded-full flex items-center justify-center shrink-0 shadow-lg",
                        "transform-gpu", // GPU acceleration hint
                        isAI
                            ? "bg-gradient-to-br from-blue-500 via-purple-500 to-cyan-500"
                            : "bg-gradient-to-br from-slate-700 to-slate-800 border border-slate-600"
                    )}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                >
                    {isAI ? (
                        <Sparkles className="w-5 h-5 text-white" />
                    ) : (
                        <User className="w-5 h-5 text-slate-300" />
                    )}
                </motion.div>

                {/* Message Content */}
                <div className="flex flex-col gap-2">
                    <motion.div
                        className={cn(
                            "px-5 py-4 rounded-2xl backdrop-blur-sm",
                            "shadow-lg transform-gpu",
                            "border text-sm md:text-base leading-relaxed",
                            isAI
                                ? "bg-slate-900/60 border-slate-700/50 text-slate-100 rounded-tl-sm"
                                : "bg-gradient-to-br from-blue-600/80 to-purple-600/80 border-white/10 text-white rounded-tr-sm"
                        )}
                        whileHover={{
                            scale: 1.01,
                            transition: { duration: 0.2 }
                        }}
                    >
                        <AnimatePresence mode="wait">
                            {isTyping ? (
                                <motion.div
                                    key="typing"
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    exit={{ opacity: 0 }}
                                >
                                    <TypingIndicator />
                                </motion.div>
                            ) : (
                                <motion.p
                                    key="content"
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    className="whitespace-pre-wrap"
                                >
                                    {content}
                                </motion.p>
                            )}
                        </AnimatePresence>
                    </motion.div>

                    {/* Citations dengan stagger animation */}
                    {isAI && citations && citations.length > 0 && !isTyping && (
                        <motion.div
                            initial="hidden"
                            animate="visible"
                            className="flex flex-wrap gap-2 mt-1 ml-1"
                        >
                            {citations.map((cite, i) => (
                                <motion.div
                                    key={i}
                                    custom={i}
                                    variants={citationVariants}
                                    className={cn(
                                        "flex items-center gap-1.5 px-3 py-1.5 rounded-full",
                                        "bg-blue-500/10 border border-blue-500/20",
                                        "text-blue-300 text-xs",
                                        "hover:bg-blue-500/20 hover:border-blue-400/30",
                                        "transition-colors duration-200 cursor-pointer",
                                        "transform-gpu"
                                    )}
                                    whileHover={{ scale: 1.02, y: -1 }}
                                    whileTap={{ scale: 0.98 }}
                                >
                                    <BookOpen className="w-3 h-3" />
                                    <span className="truncate max-w-[150px]">{cite}</span>
                                </motion.div>
                            ))}
                        </motion.div>
                    )}
                </div>
            </div>
        </motion.div>
    )
}
