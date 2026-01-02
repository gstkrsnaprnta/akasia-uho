"use client"

import * as React from "react"

interface Message {
    role: "user" | "ai"
    content: string
    citations?: string[]
}

interface ChatRoom {
    id: string
    title: string
    messages: Message[]
    createdAt: number
}

interface ChatContextType {
    rooms: ChatRoom[]
    currentRoomId: string | null
    messages: Message[]
    isTyping: boolean
    sendMessage: (content: string) => void
    createNewRoom: () => void
    switchRoom: (roomId: string) => void
    deleteRoom: (roomId: string) => void
}

const ChatContext = React.createContext<ChatContextType | undefined>(undefined)

function generateId(): string {
    return Date.now().toString(36) + Math.random().toString(36).substr(2)
}

export function ChatProvider({ children }: { children: React.ReactNode }) {
    const [rooms, setRooms] = React.useState<ChatRoom[]>([])
    const [currentRoomId, setCurrentRoomId] = React.useState<string | null>(null)
    const [isTyping, setIsTyping] = React.useState(false)

    // Load rooms from localStorage on mount
    React.useEffect(() => {
        if (typeof window !== 'undefined') {
            const saved = localStorage.getItem('chat_rooms')
            if (saved) {
                try {
                    const parsed = JSON.parse(saved)
                    if (Array.isArray(parsed) && parsed.length > 0) {
                        setRooms(parsed)
                        // Set current room to most recent
                        const sortedRooms = [...parsed].sort((a, b) => b.createdAt - a.createdAt)
                        setCurrentRoomId(sortedRooms[0].id)
                    }
                } catch {
                    // Invalid JSON, ignore
                }
            }
        }
    }, [])

    // Save to localStorage whenever rooms change
    React.useEffect(() => {
        if (typeof window !== 'undefined' && rooms.length > 0) {
            localStorage.setItem('chat_rooms', JSON.stringify(rooms))
        }
    }, [rooms])

    // Get current room's messages
    const currentRoom = rooms.find(r => r.id === currentRoomId)
    const messages = currentRoom?.messages || []

    const createNewRoom = () => {
        const newRoom: ChatRoom = {
            id: generateId(),
            title: "Chat Baru",
            messages: [],
            createdAt: Date.now()
        }
        setRooms(prev => [newRoom, ...prev])
        setCurrentRoomId(newRoom.id)
    }

    const switchRoom = (roomId: string) => {
        setCurrentRoomId(roomId)
    }

    const deleteRoom = (roomId: string) => {
        setRooms(prev => {
            const filtered = prev.filter(r => r.id !== roomId)
            // If we deleted current room, switch to another
            if (roomId === currentRoomId && filtered.length > 0) {
                setCurrentRoomId(filtered[0].id)
            } else if (filtered.length === 0) {
                setCurrentRoomId(null)
            }
            // Update localStorage
            if (typeof window !== 'undefined') {
                if (filtered.length === 0) {
                    localStorage.removeItem('chat_rooms')
                } else {
                    localStorage.setItem('chat_rooms', JSON.stringify(filtered))
                }
            }
            return filtered
        })
    }

    const sendMessage = async (content: string) => {
        if (isTyping) return

        // Create new room if none exists
        let roomId = currentRoomId
        if (!roomId) {
            const newRoom: ChatRoom = {
                id: generateId(),
                title: content.slice(0, 30) + (content.length > 30 ? "..." : ""),
                messages: [],
                createdAt: Date.now()
            }
            setRooms(prev => [newRoom, ...prev])
            setCurrentRoomId(newRoom.id)
            roomId = newRoom.id
        }

        // Add user message
        const userMessage: Message = { role: "user", content }
        setRooms(prev => prev.map(room => {
            if (room.id === roomId) {
                // Update title from first message
                const newTitle = room.messages.length === 0
                    ? content.slice(0, 30) + (content.length > 30 ? "..." : "")
                    : room.title
                return { ...room, title: newTitle, messages: [...room.messages, userMessage] }
            }
            return room
        }))

        setIsTyping(true)

        try {
            const response = await fetch("http://localhost:8000/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: content })
            })

            if (!response.ok) throw new Error("Network response was not ok")
            if (!response.body) throw new Error("No response body")

            const reader = response.body.getReader()
            const decoder = new TextDecoder()

            let fullText = ""
            let citationsReceived: string[] = []

            // Add empty AI message
            setRooms(prev => prev.map(room => {
                if (room.id === roomId) {
                    return {
                        ...room,
                        messages: [...room.messages, { role: "ai", content: "", citations: [] }]
                    }
                }
                return room
            }))

            while (true) {
                const { done, value } = await reader.read()
                if (done) break

                const chunk = decoder.decode(value)
                const lines = chunk.split("\n")

                for (const line of lines) {
                    if (!line.trim()) continue
                    try {
                        const data = JSON.parse(line)

                        if (data.response) {
                            fullText += data.response
                            setRooms(prev => prev.map(room => {
                                if (room.id === roomId) {
                                    const updated = [...room.messages]
                                    updated[updated.length - 1] = {
                                        role: "ai",
                                        content: fullText,
                                        citations: citationsReceived
                                    }
                                    return { ...room, messages: updated }
                                }
                                return room
                            }))
                        }

                        if (data.citations) {
                            citationsReceived = data.citations
                        }
                    } catch {
                        // Skip invalid JSON chunks
                    }
                }
            }

        } catch (error) {
            setRooms(prev => prev.map(room => {
                if (room.id === roomId) {
                    return {
                        ...room,
                        messages: [...room.messages, {
                            role: "ai",
                            content: "Maaf, terjadi kesalahan saat menghubungi server. Pastikan backend Python berjalan di http://localhost:8000",
                            citations: []
                        }]
                    }
                }
                return room
            }))
        } finally {
            setIsTyping(false)
        }
    }

    return (
        <ChatContext.Provider value={{
            rooms,
            currentRoomId,
            messages,
            isTyping,
            sendMessage,
            createNewRoom,
            switchRoom,
            deleteRoom
        }}>
            {children}
        </ChatContext.Provider>
    )
}

export function useChat() {
    const context = React.useContext(ChatContext)
    if (context === undefined) {
        throw new Error("useChat must be used within a ChatProvider")
    }
    return context
}
