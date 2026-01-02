"use client"

import { GlassCard } from "@/components/ui/glass-card"
import { LucideIcon, TrendingUp, TrendingDown } from "lucide-react"

interface StatsCardProps {
    title: string
    value: string
    change: string
    icon: LucideIcon
    positive?: boolean
}

export function StatsCard({ title, value, change, icon: Icon, positive = true }: StatsCardProps) {
    return (
        <GlassCard hoverEffect className="p-6">
            <div className="flex justify-between items-start">
                <div className="flex-1">
                    <p className="text-sm font-medium text-slate-400">{title}</p>
                    <h3 className="text-3xl font-bold mt-2 text-white">{value}</h3>
                    <p className="text-xs mt-2 text-slate-500">
                        {change}
                    </p>
                </div>
                <div className="p-3 rounded-xl bg-gradient-to-br from-blue-500/20 to-purple-500/20 border border-white/10 text-blue-400">
                    <Icon className="w-6 h-6" />
                </div>
            </div>
        </GlassCard>
    )
}
