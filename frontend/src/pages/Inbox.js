import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Sparkles, Send, MessageSquare } from "lucide-react";

const channelStyle = {
  Airbnb: "text-[#FF5A5F] bg-[#FF5A5F]/10",
  VRBO: "text-[#0066FF] bg-[#0066FF]/10",
  SMS: "text-[#10B981] bg-[#10B981]/10",
  Email: "text-[#6B7280] bg-[#F3F4F6]",
};

export default function Inbox() {
  const [threads, setThreads] = useState([]);
  const [active, setActive] = useState(null);
  const [draft, setDraft] = useState("");
  const [aiLoading, setAiLoading] = useState(false);

  const loadThreads = () => api.get("/inbox").then((r) => {
    setThreads(r.data);
    if (!active && r.data.length) setActive(r.data[0]);
  });
  useEffect(() => {
    loadThreads();
  }, []);

  const openThread = async (t) => {
    const { data } = await api.get(`/inbox/${t.id}`);
    setActive(data);
    setDraft("");
  };

  const aiDraft = async () => {
    if (!active) return;
    setAiLoading(true);
    try {
      const { data } = await api.post("/ai/draft-reply", { thread_id: active.id });
      setDraft(data.draft);
    } catch (e) {
      setDraft("");
    } finally {
      setAiLoading(false);
    }
  };

  const send = async () => {
    if (!draft.trim() || !active) return;
    const { data } = await api.post(`/inbox/${active.id}/message`, { body: draft });
    setActive(data);
    setDraft("");
    loadThreads();
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="text-xs font-bold tracking-wider uppercase text-[#6B7280]">Communications</div>
      <h1 className="font-display text-3xl sm:text-4xl font-bold tracking-tight text-[#0A2540] mt-1">Unified Inbox</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 mt-6">
        {/* Thread list */}
        <div className="rounded-xl border border-[#E5E7EB] bg-white overflow-hidden">
          {threads.map((t) => (
            <button
              key={t.id}
              data-testid="thread-item"
              onClick={() => openThread(t)}
              className={`w-full text-left px-4 py-4 border-b border-[#F3F4F6] last:border-0 transition-colors ${
                active?.id === t.id ? "bg-[#0066FF]/5" : "hover:bg-[#F9FAFB]"
              }`}
            >
              <div className="flex items-center justify-between gap-2">
                <span className="text-sm font-semibold text-[#111827]">{t.guest}</span>
                <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${channelStyle[t.channel]}`}>{t.channel}</span>
              </div>
              <div className="text-xs text-[#6B7280] mt-0.5">{t.property_name}</div>
              <div className="text-sm text-[#4B5563] mt-1 truncate">{t.preview}</div>
            </button>
          ))}
        </div>

        {/* Thread view */}
        <div className="lg:col-span-2 rounded-xl border border-[#E5E7EB] bg-white flex flex-col min-h-[500px]">
          {active ? (
            <>
              <div className="px-6 py-4 border-b border-[#E5E7EB] flex items-center justify-between">
                <div>
                  <div className="font-semibold text-[#0A2540]">{active.guest}</div>
                  <div className="text-xs text-[#6B7280]">{active.property_name}</div>
                </div>
                <span className={`text-[11px] font-semibold px-2.5 py-1 rounded-full ${channelStyle[active.channel]}`}>{active.channel}</span>
              </div>

              <div className="flex-1 px-6 py-5 space-y-4 overflow-y-auto coastline-scroll">
                {active.messages?.map((m) => (
                  <div key={m.id} className={`flex ${m.from === "host" ? "justify-end" : "justify-start"}`}>
                    <div className={`max-w-[75%] rounded-2xl px-4 py-2.5 text-sm ${
                      m.from === "host" ? "bg-[#0A2540] text-white rounded-br-sm" : "bg-[#F3F4F6] text-[#111827] rounded-bl-sm"
                    }`}>
                      {m.body}
                    </div>
                  </div>
                ))}
              </div>

              <div className="px-6 py-4 border-t border-[#E5E7EB]">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold tracking-wider uppercase text-[#6B7280]">Reply</span>
                  <button
                    data-testid="ai-draft-btn"
                    onClick={aiDraft}
                    disabled={aiLoading}
                    className="flex items-center gap-1.5 text-xs font-semibold text-[#0066FF] bg-[#0066FF]/10 hover:bg-[#0066FF]/20 px-3 py-1.5 rounded-full transition-colors disabled:opacity-60"
                  >
                    <Sparkles className="h-3.5 w-3.5" /> {aiLoading ? "Drafting…" : "AI Draft"}
                  </button>
                </div>
                <div className="flex items-end gap-2">
                  <textarea
                    data-testid="reply-input"
                    value={draft}
                    onChange={(e) => setDraft(e.target.value)}
                    rows={2}
                    placeholder="Write or generate a reply…"
                    className="flex-1 rounded-lg border border-[#E5E7EB] px-3 py-2.5 text-sm outline-none focus:ring-2 focus:ring-[#0066FF] resize-none"
                  />
                  <button
                    data-testid="send-reply-btn"
                    onClick={send}
                    className="h-11 w-11 shrink-0 rounded-lg bg-[#0A2540] text-white flex items-center justify-center hover:bg-[#0e3358] transition-colors"
                  >
                    <Send className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-[#6B7280]">
              <MessageSquare className="h-10 w-10 mb-2" /> Select a conversation
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
