"use client"

import * as React from "react"
import { SendHorizontal, Loader2 } from "lucide-react"
import { useChat } from "@/components/chat-provider"

export function ChatInput({ onSend }: { onSend: (message: string) => void }) {
    const [value, setValue] = React.useState("")
    const { isTyping } = useChat()

    const handleSend = () => {
        if (value.trim() && !isTyping) {
            onSend(value)
            setValue("")
        }
    }

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault()
            handleSend()
        }
    }

    return (
        <div className="fixed bottom-8 left-0 right-0 flex justify-center px-4 z-40 md:pl-64">
            <div className="relative w-full max-w-3xl group">

                {/* Animated Glow Behind */}
                <div className="absolute -inset-0.5 bg-gradient-to-r from-blue-500 via-purple-500 to-cyan-500 rounded-2xl opacity-20 group-hover:opacity-40 blur transition duration-500" />

                {/* Glass Container */}
                <div className="relative flex items-center gap-2 p-2 rounded-2xl bg-slate-950/90 backdrop-blur-xl border border-white/10 shadow-2xl">

                    <input
                        type="text"
                        value={value}
                        onChange={(e) => setValue(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Tanyakan seputar dokumen akademik UHO..."
                        disabled={isTyping}
                        className="flex-1 bg-transparent border-none outline-none text-white placeholder-slate-500 px-4 py-3 disabled:opacity-50"
                    />

                    <button
                        onClick={handleSend}
                        disabled={isTyping || !value.trim()}
                        className="p-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl shadow-lg hover:shadow-blue-500/25 transition-all hover:scale-105 active:scale-95 disabled:opacity-50 disabled:hover:scale-100"
                    >
                        {isTyping ? (
                            <Loader2 className="w-5 h-5 animate-spin" />
                        ) : (
                            <SendHorizontal className="w-5 h-5" />
                        )}
                    </button>
                </div>
            </div>
        </div>
    )
}
