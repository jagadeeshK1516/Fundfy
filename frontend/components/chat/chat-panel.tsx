"use client";

import { useState, useRef, useEffect } from "react";
import { useWorkspace } from "@/lib/workspace-context";
import { sendChat, startCommunicationSession } from "@/lib/api";
import { useToast } from "@/components/ui/toast";
import { MessageBubble } from "./message-bubble";
import { ChatInput } from "./chat-input";
import { ModeSwitcher, type ChatMode } from "./mode-switcher";
import { LoadingSpinner } from "@/components/ui/loading-spinner";
import type { ChatMessage } from "@/lib/types";

export function ChatPanel() {
  const { state } = useWorkspace();
  const { addToast } = useToast();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [mode, setMode] = useState<ChatMode>("chat");
  const [isLoading, setIsLoading] = useState(false);
  const [latestAssistantIdx, setLatestAssistantIdx] = useState<number | null>(null);
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
      let responseText: string;

      if (mode === "chat") {
        const res = await sendChat(
          state.founderId,
          content,
          state.businessId || undefined
        );
        responseText = res.response;
      } else {
        const res = await startCommunicationSession({
          founder_id: state.founderId,
          mode,
          message: content,
          business_id: state.businessId || undefined,
        });
        responseText = res.response;
      }

      const assistantMessage: ChatMessage = {
        role: "assistant",
        content: responseText,
        timestamp: new Date(),
      };
      setMessages((prev) => {
        setLatestAssistantIdx(prev.length);
        return [...prev, assistantMessage];
      });
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
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <h1 className="text-lg font-semibold text-slate-100">AI Chat</h1>
          <span className="px-2 py-0.5 text-xs rounded-full bg-slate-800 text-slate-400 border border-slate-700">
            {state.businessName || "No business set"}
          </span>
        </div>
        <ModeSwitcher activeMode={mode} onModeChange={setMode} />
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center text-slate-500">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-brand-pink/20 to-brand-purple/20 flex items-center justify-center mb-4">
              <svg className="w-8 h-8 text-brand-purple" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
            </div>
            <p className="text-lg font-medium text-slate-300">Start a conversation</p>
            <p className="text-sm mt-1">Ask about your business, get advice, or practice your pitch.</p>
          </div>
        )}
        {messages.map((msg, i) => (
          <MessageBubble
            key={i}
            message={msg}
            isLatestAssistant={i === latestAssistantIdx}
          />
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
        placeholder={
          mode === "chat"
            ? "Ask your AI business advisor..."
            : `Practice your ${mode.replace("_", " ")}...`
        }
      />
    </div>
  );
}
