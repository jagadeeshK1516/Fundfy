"use client";

export type ChatMode = "chat" | "mock_interview" | "pitch_practice" | "qa_rehearsal";

const modes: { id: ChatMode; label: string }[] = [
  { id: "chat", label: "Chat" },
  { id: "mock_interview", label: "Mock Interview" },
  { id: "pitch_practice", label: "Pitch Practice" },
  { id: "qa_rehearsal", label: "Q&A Rehearsal" },
];

interface ModeSwitcherProps {
  activeMode: ChatMode;
  onModeChange: (mode: ChatMode) => void;
}

export function ModeSwitcher({ activeMode, onModeChange }: ModeSwitcherProps) {
  return (
    <div className="flex items-center gap-1 p-1 bg-slate-800/50 rounded-lg">
      {modes.map((mode) => (
        <button
          key={mode.id}
          onClick={() => onModeChange(mode.id)}
          className={`
            px-3 py-1.5 text-sm font-medium rounded-md transition-all duration-200
            ${
              activeMode === mode.id
                ? "bg-gradient-to-r from-brand-pink to-brand-purple text-white shadow-sm"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-700/50"
            }
          `}
        >
          {mode.label}
        </button>
      ))}
    </div>
  );
}
