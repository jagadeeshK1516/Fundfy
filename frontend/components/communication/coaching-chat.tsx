"use client";

import { useState, useRef, useEffect } from "react";
import { useWorkspace } from "@/lib/workspace-context";
import { startCommunicationSession } from "@/lib/api";
import { useToast } from "@/components/ui/toast";
import { ChatInput } from "@/components/chat/chat-input";
import { LoadingSpinner } from "@/components/ui/loading-spinner";
import type { ChatMessage } from "@/lib/types";

type CoachingMode = "mock_interview" | "pitch_practice" | "qa_rehearsal";

const modes: { id: CoachingMode; label: string }[] = [
  { id: "mock_interview", label: "Mock Interview" },
  { id: "pitch_practice", label: "Pitch Practice" },
  { id: "qa_rehearsal", label: "Q&A Rehearsal" },
];

export function CoachingChat() {
  const { state } = useWorkspace();
  const { addToast } = useToast();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [mode, setMode] = useState<CoachingMode>("mock_interview");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async (content: string) => {
    if (!state.founderId) return;

    const userMessage: ChatMessage = {
      role: "user",
      content,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const res = await startCommunicationSession({
        founder_id: state.founderId,
        mode,
        message: content,
        business_id: state.businessId || undefined,
      });

      const assistantMessage: ChatMessage = {
        role: "assistant",
        content: res.response,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      addToast(
        err instanceof Error ? err.message : "Failed to get response",
        "error"
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Mode selector */}
      <div className="p-4 border-b border-slate-800">
        <div className="flex items-center gap-1 p-1 bg-slate-800/50 rounded-lg w-fit">
          {modes.map((m) => (
            <button
              key={m.id}
              onClick={() => setMode(m.id)}
              className={`
                px-3 py-1.5 text-sm font-medium rounded-md transition-all duration-200
                ${
                  mode === m.id
                    ? "bg-gradient-to-r from-brand-pink to-brand-purple text-white shadow-sm"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-700/50"
                }
              `}
            >
              {m.label}
            </button>
          ))}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center text-slate-500">
            <p className="text-lg font-medium text-slate-300">Ready to practice?</p>
            <p className="text-sm mt-1">Select a mode and start your coaching session.</p>
          </div>
        )}
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex animate-slide-in ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`
                max-w-[80%] md:max-w-[70%] rounded-2xl px-4 py-3 text-sm leading-relaxed
                ${
                  msg.role === "user"
                    ? "bg-gradient-to-r from-brand-pink to-brand-purple text-white"
                    : "bg-slate-800 text-slate-200 border-l-2 border-l-brand-purple border border-slate-700"
                }
              `}
            >
              <p className="whitespace-pre-wrap">{msg.content}</p>
              <p className={`text-xs mt-1 ${msg.role === "user" ? "text-white/60" : "text-slate-500"}`}>
                {msg.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
              </p>
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-slate-800 rounded-2xl px-4 py-3 border border-slate-700">
              <LoadingSpinner size="sm" />
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <ChatInput
        onSend={handleSend}
        disabled={isLoading}
        placeholder={`Practice your ${mode.replace(/_/g, " ")}...`}
      />
    </div>
  );
}
