"use client"

import * as React from "react"
import { ChatInput } from "@/components/chat/chat-input";
import { ChatBubble } from "@/components/chat/chat-bubble";
import { MessageSquare, Sparkles } from "lucide-react";

import { useChat } from "@/components/chat-provider"

export default function Home() {
  const { messages, isTyping, sendMessage } = useChat()
  const messagesEndRef = React.useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  React.useEffect(() => {
    scrollToBottom()
  }, [messages, isTyping])

  const handleSend = (content: string) => {
    sendMessage(content)
  }

  const suggestedQuestions = [
    "Kapan jadwal pendaftaran mahasiswa baru?",
    "Bagaimana prosedur cuti akademik?",
    "Apa syarat kelulusan wisuda?",
    "Bagaimana cara mengurus KRS?"
  ]

  return (
    <div className="flex flex-col h-screen max-w-4xl mx-auto px-4 pt-20 md:pt-8 pb-32">
      <div className="flex-1 overflow-y-auto space-y-6 scrollbar-hide py-4">
        {messages.length === 0 ? (
          /* Empty State */
          <div className="flex flex-col items-center justify-center h-full text-center space-y-8 py-20">
            <div className="p-5 rounded-full bg-gradient-to-br from-blue-500/20 to-purple-500/20 border border-white/10">
              <Sparkles className="w-12 h-12 text-blue-400" />
            </div>

            <div className="space-y-3">
              <h1 className="text-3xl md:text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-br from-white via-blue-100 to-blue-300">
                Halo, Mahasiswa UHO
              </h1>
              <p className="text-slate-400 text-lg max-w-md">
                Saya asisten akademik AI Anda. Tanyakan seputar dokumen akademik yang telah diupload.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 w-full max-w-2xl">
              {suggestedQuestions.map((question, i) => (
                <button
                  key={i}
                  onClick={() => sendMessage(question)}
                  className="p-4 text-left text-sm bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl text-slate-300 hover:text-white transition-colors group"
                >
                  <MessageSquare className="w-4 h-4 text-blue-400 mb-2 group-hover:text-blue-300" />
                  {question}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <>
            {/* Welcome Message */}
            <div className="text-center mb-8 mt-4 space-y-2">
              <h1 className="text-2xl md:text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-br from-white via-blue-100 to-blue-300">
                AKASIA
              </h1>
              <p className="text-slate-500 text-sm">
                Asisten Akademik Berbasis AI - v1.0
              </p>
            </div>

            {messages.map((msg, i) => (
              <ChatBubble
                key={i}
                role={msg.role}
                content={msg.content}
                citations={msg.citations}
              />
            ))}
          </>
        )}

        {isTyping && (
          <ChatBubble role="ai" content="" isTyping={true} />
        )}

        <div ref={messagesEndRef} />
      </div>

      <ChatInput onSend={handleSend} />
    </div>
  );
}
