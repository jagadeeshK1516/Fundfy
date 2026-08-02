"use client";

import { useEffect, useRef, useState } from "react";
import type { ChatMessage } from "@/lib/types";

interface MessageBubbleProps {
  message: ChatMessage;
  isLatestAssistant?: boolean;
}

function useTypewriter(text: string, enabled: boolean) {
  const [displayed, setDisplayed] = useState(enabled ? "" : text);
  const [typing, setTyping] = useState(enabled);
  const indexRef = useRef(0);

  useEffect(() => {
    if (!enabled) {
      setDisplayed(text);
      setTyping(false);
      return;
    }

    indexRef.current = 0;
    setDisplayed("");
    setTyping(true);

    const interval = setInterval(() => {
      indexRef.current++;
      const next = text.slice(0, indexRef.current);
      setDisplayed(next);
      if (indexRef.current >= text.length) {
        clearInterval(interval);
        setTyping(false);
      }
    }, 10);

    return () => clearInterval(interval);
  }, [text, enabled]);

  return { displayed, typing };
}

export function MessageBubble({ message, isLatestAssistant }: MessageBubbleProps) {
  const isUser = message.role === "user";
  const { displayed, typing } = useTypewriter(
    message.content,
    !isUser && !!isLatestAssistant
  );

  return (
    <div
      className={`flex animate-slide-in ${isUser ? "justify-end" : "justify-start"}`}
    >
      <div
        className={`
          max-w-[80%] md:max-w-[70%] rounded-2xl px-4 py-3 text-sm leading-relaxed
          ${
            isUser
              ? "bg-gradient-to-r from-brand-pink to-brand-purple text-white"
              : "bg-slate-800 text-slate-200 border border-slate-700"
          }
        `}
      >
        <p className="whitespace-pre-wrap">
          {displayed}
          {typing && <span className="inline-block w-0.5 h-4 ml-0.5 bg-brand-pink animate-pulse" />}
        </p>
        <p className={`text-xs mt-1 ${isUser ? "text-white/60" : "text-slate-500"}`}>
          {message.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
        </p>
      </div>
    </div>
  );
}
