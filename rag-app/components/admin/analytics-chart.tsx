"use client"

import { GlassCard } from "@/components/ui/glass-card"
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"

const data = [
    { time: "09:00", queries: 12 },
    { time: "10:00", queries: 35 },
    { time: "11:00", queries: 48 },
    { time: "12:00", queries: 65 },
    { time: "13:00", queries: 55 },
    { time: "14:00", queries: 72 },
    { time: "15:00", queries: 89 },
]

export function AnalyticsChart() {
    return (
        <GlassCard className="h-[400px]">
            <h3 className="text-lg font-semibold text-white mb-6">User Activity</h3>
            <div className="h-[300px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={data}>
                        <defs>
                            <linearGradient id="colorQueries" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.8} />
                                <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                            </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.4} />
                        <XAxis dataKey="time" stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
                        <YAxis stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
                        <Tooltip
                            contentStyle={{ backgroundColor: "#1e293b", border: "none", borderRadius: "8px", color: "#fff" }}
                            itemStyle={{ color: "#a78bfa" }}
                        />
                        <Area
                            type="monotone"
                            dataKey="queries"
                            stroke="#8b5cf6"
                            strokeWidth={3}
                            fillOpacity={1}
                            fill="url(#colorQueries)"
                        />
                    </AreaChart>
                </ResponsiveContainer>
            </div>
        </GlassCard>
    )
}
