import { useEffect, useState } from "react";
import { api, fmtMoney, fmtDate } from "@/lib/api";
import { Wrench, Plus, Zap, AlertTriangle, Wind } from "lucide-react";

const catLabel = {
  salt_corrosion: "Salt Corrosion",
  hvac: "HVAC",
  storm_prep: "Storm Prep",
  plumbing: "Plumbing",
  general: "General",
};

const statusStyle = {
  open: "text-[#6B7280] bg-[#F3F4F6]",
  in_progress: "text-[#0066FF] bg-[#0066FF]/10",
  completed: "text-[#10B981] bg-[#10B981]/10",
};

export default function Maintenance() {
  const [tasks, setTasks] = useState([]);
  const [props, setProps] = useState([]);
  const [filter, setFilter] = useState("all");
  const [show, setShow] = useState(false);
  const [form, setForm] = useState({ property_id: "", title: "", category: "general", priority: "normal" });

  const load = () => api.get("/maintenance").then((r) => setTasks(r.data));
  useEffect(() => {
    load();
    api.get("/properties").then((r) => setProps(r.data));
  }, []);

  const create = async () => {
    if (!form.property_id || !form.title) return;
    await api.post("/maintenance", form);
    setShow(false);
    setForm({ property_id: "", title: "", category: "general", priority: "normal" });
    load();
  };

  const filtered = tasks.filter((t) => {
    if (filter === "all") return true;
    if (filter === "predictive") return t.predictive;
    if (filter === "storm") return t.storm;
    return t.status === filter;
  });

  const filters = [
    { id: "all", label: "All" },
    { id: "predictive", label: "Predictive", icon: Zap },
    { id: "storm", label: "Storm", icon: Wind },
    { id: "open", label: "Open" },
    { id: "completed", label: "Completed" },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex items-end justify-between flex-wrap gap-4">
        <div>
          <div className="text-xs font-bold tracking-wider uppercase text-[#6B7280]">Coastal Engine</div>
          <h1 className="font-display text-3xl sm:text-4xl font-bold tracking-tight text-[#0A2540] mt-1">Maintenance</h1>
        </div>
        <button
          data-testid="new-task-btn"
          onClick={() => setShow(true)}
          className="flex items-center gap-2 rounded-lg bg-[#0A2540] text-white font-semibold px-5 py-2.5 hover:bg-[#0e3358] transition-colors"
        >
          <Plus className="h-4 w-4" /> New Task
        </button>
      </div>

      <div className="flex items-center gap-2 mt-6 flex-wrap">
        {filters.map((f) => (
          <button
            key={f.id}
            data-testid={`filter-${f.id}`}
            onClick={() => setFilter(f.id)}
            className={`flex items-center gap-1.5 text-sm font-medium px-3.5 py-2 rounded-full transition-colors ${
              filter === f.id ? "bg-[#0A2540] text-white" : "bg-white border border-[#E5E7EB] text-[#4B5563] hover:border-[#0066FF]"
            }`}
          >
            {f.icon && <f.icon className="h-3.5 w-3.5" />} {f.label}
          </button>
        ))}
      </div>

      <div className="mt-5 rounded-xl border border-[#E5E7EB] bg-white overflow-hidden">
        {filtered.map((t) => (
          <div key={t.id} data-testid="maint-row" className="flex items-center gap-4 px-5 py-4 border-b border-[#F3F4F6] last:border-0 hover:bg-[#F9FAFB] transition-colors">
            <div className={`h-9 w-9 rounded-lg flex items-center justify-center shrink-0 ${t.storm ? "bg-[#FF5A5F]/10 text-[#FF5A5F]" : "bg-[#0A2540]/5 text-[#0A2540]"}`}>
              {t.storm ? <AlertTriangle className="h-4 w-4" /> : <Wrench className="h-4 w-4" />}
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <span className="text-sm font-semibold text-[#111827] truncate">{t.title}</span>
                {t.predictive && <span className="text-[10px] font-semibold text-[#0066FF] bg-[#0066FF]/10 px-2 py-0.5 rounded-full">Auto · 60d</span>}
              </div>
              <div className="text-xs text-[#6B7280] mt-0.5">{t.property_name} · {catLabel[t.category]}</div>
            </div>
            <div className="hidden sm:block text-xs text-[#6B7280]">{fmtDate(t.created_at)}</div>
            {t.cost > 0 && <div className="hidden sm:block text-sm font-medium text-[#111827]">{fmtMoney(t.cost)}</div>}
            <span className={`text-xs font-semibold px-2.5 py-1 rounded-full capitalize ${statusStyle[t.status] || statusStyle.open}`}>
              {t.status.replace("_", " ")}
            </span>
          </div>
        ))}
        {filtered.length === 0 && <div className="px-5 py-12 text-center text-[#6B7280]">No tasks in this view.</div>}
      </div>

      {show && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4" onClick={() => setShow(false)}>
          <div className="bg-white rounded-2xl p-6 w-full max-w-md" onClick={(e) => e.stopPropagation()}>
            <h3 className="font-display text-xl font-semibold text-[#0A2540]">New Maintenance Task</h3>
            <div className="space-y-3 mt-4">
              <select
                data-testid="task-property"
                value={form.property_id}
                onChange={(e) => setForm({ ...form, property_id: e.target.value })}
                className="w-full rounded-lg border border-[#E5E7EB] px-3 py-2.5 text-sm outline-none focus:ring-2 focus:ring-[#0066FF]"
              >
                <option value="">Select property…</option>
                {props.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
              </select>
              <input
                data-testid="task-title"
                placeholder="Task title"
                value={form.title}
                onChange={(e) => setForm({ ...form, title: e.target.value })}
                className="w-full rounded-lg border border-[#E5E7EB] px-3 py-2.5 text-sm outline-none focus:ring-2 focus:ring-[#0066FF]"
              />
              <div className="grid grid-cols-2 gap-3">
                <select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} className="rounded-lg border border-[#E5E7EB] px-3 py-2.5 text-sm">
                  {Object.entries(catLabel).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                </select>
                <select value={form.priority} onChange={(e) => setForm({ ...form, priority: e.target.value })} className="rounded-lg border border-[#E5E7EB] px-3 py-2.5 text-sm">
                  <option value="normal">Normal</option>
                  <option value="high">High</option>
                  <option value="urgent">Urgent</option>
                </select>
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-5">
              <button onClick={() => setShow(false)} className="px-4 py-2.5 rounded-lg text-sm font-medium text-[#6B7280] hover:bg-[#F3F4F6]">Cancel</button>
              <button data-testid="task-save" onClick={create} className="px-5 py-2.5 rounded-lg bg-[#0A2540] text-white text-sm font-semibold hover:bg-[#0e3358]">Create</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
