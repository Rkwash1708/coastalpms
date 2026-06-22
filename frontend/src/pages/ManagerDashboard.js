import { useEffect, useState } from "react";
import { api, fmtMoney } from "@/lib/api";
import {
  Home, Wrench, Sparkles, TrendingUp, AlertTriangle, Waves, ArrowUpRight, CalendarRange,
} from "lucide-react";
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from "recharts";

function StatCard({ icon: Icon, label, value, sub, tone = "default", testid }) {
  const tones = {
    default: "text-[#0A2540] bg-[#0A2540]/5",
    blue: "text-[#0066FF] bg-[#0066FF]/10",
    green: "text-[#10B981] bg-[#10B981]/10",
    storm: "text-[#FF5A5F] bg-[#FF5A5F]/10",
  };
  return (
    <div data-testid={testid} className="rounded-xl border border-[#E5E7EB] bg-white p-6 fade-up">
      <div className={`inline-flex h-10 w-10 items-center justify-center rounded-lg ${tones[tone]}`}>
        <Icon className="h-5 w-5" strokeWidth={2} />
      </div>
      <div className="mt-4 text-3xl font-display font-bold text-[#0A2540]">{value}</div>
      <div className="text-sm text-[#6B7280] mt-1">{label}</div>
      {sub && <div className="text-xs text-[#10B981] mt-2 flex items-center gap-1"><ArrowUpRight className="h-3 w-3" />{sub}</div>}
    </div>
  );
}

export default function ManagerDashboard() {
  const [summary, setSummary] = useState(null);
  const [financials, setFinancials] = useState(null);
  const [maint, setMaint] = useState([]);
  const [stormName, setStormName] = useState("Hurricane Idalia");

  const load = () => {
    api.get("/dashboard/summary").then((r) => setSummary(r.data));
    api.get("/owner/financials").then((r) => setFinancials(r.data));
    api.get("/maintenance").then((r) => setMaint(r.data.slice(0, 6)));
  };
  useEffect(() => {
    load();
  }, []);

  const activateStorm = async () => {
    await api.post("/storm/activate", { active: true, storm_name: stormName });
    load();
    window.location.reload();
  };

  const monthly = (financials?.monthly || []).map((m) => ({
    name: new Date(m.month + "-01").toLocaleDateString("en-US", { month: "short" }),
    revenue: Math.round(m.revenue),
  }));

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex items-end justify-between flex-wrap gap-4">
        <div>
          <div className="text-xs font-bold tracking-wider uppercase text-[#6B7280]">Operations</div>
          <h1 className="font-display text-3xl sm:text-4xl font-bold tracking-tight text-[#0A2540] mt-1">
            War Room
          </h1>
        </div>
        {!summary?.storm_active && (
          <div className="flex items-center gap-2">
            <input
              data-testid="storm-name-input"
              value={stormName}
              onChange={(e) => setStormName(e.target.value)}
              className="rounded-lg border border-[#E5E7EB] px-3 py-2.5 text-sm outline-none focus:ring-2 focus:ring-[#FF5A5F] w-40"
            />
            <button
              data-testid="activate-storm-btn"
              onClick={activateStorm}
              className="flex items-center gap-2 rounded-lg bg-[#FF5A5F] text-white font-semibold px-5 py-2.5 hover:bg-[#e5484d] transition-colors"
            >
              <AlertTriangle className="h-4 w-4" /> Activate Storm Mode
            </button>
          </div>
        )}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 mt-6">
        <StatCard testid="stat-revenue" icon={TrendingUp} tone="blue" label="Gross Revenue (6 mo)" value={fmtMoney(summary?.revenue)} sub="Trust-accounted" />
        <StatCard testid="stat-reservations" icon={CalendarRange} label="Upcoming Reservations" value={summary?.upcoming_bookings ?? "—"} />
        <StatCard testid="stat-maintenance" icon={Wrench} tone="storm" label="Open Maintenance" value={summary?.open_maintenance ?? "—"} />
        <StatCard testid="stat-housekeeping" icon={Sparkles} tone="green" label="Turnovers Pending" value={summary?.housekeeping_pending ?? "—"} />
      </div>

      {/* Chart + maintenance */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 mt-5">
        <div className="lg:col-span-2 rounded-xl border border-[#E5E7EB] bg-white p-6">
          <div className="flex items-center justify-between">
            <h3 className="font-display text-lg font-semibold text-[#0A2540]">Revenue Trend</h3>
            <span className="text-xs text-[#6B7280]">Last 6 months</span>
          </div>
          <div className="h-64 mt-4 -ml-2">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={monthly}>
                <defs>
                  <linearGradient id="rev" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#0066FF" stopOpacity={0.25} />
                    <stop offset="100%" stopColor="#0066FF" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" vertical={false} />
                <XAxis dataKey="name" tick={{ fontSize: 12, fill: "#6B7280" }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 12, fill: "#6B7280" }} axisLine={false} tickLine={false} tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} />
                <Tooltip formatter={(v) => fmtMoney(v)} />
                <Area type="monotone" dataKey="revenue" stroke="#0066FF" strokeWidth={2.5} fill="url(#rev)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="rounded-xl border border-[#E5E7EB] bg-white p-6">
          <h3 className="font-display text-lg font-semibold text-[#0A2540]">Maintenance Queue</h3>
          <div className="mt-4 space-y-3 coastline-scroll max-h-64 overflow-y-auto">
            {maint.map((m) => (
              <div key={m.id} data-testid="dash-maint-item" className="flex items-start gap-3 pb-3 border-b border-[#F3F4F6] last:border-0">
                <div className={`mt-1 h-2 w-2 rounded-full shrink-0 ${m.storm ? "bg-[#FF5A5F]" : m.predictive ? "bg-[#0066FF]" : "bg-[#10B981]"}`} />
                <div className="min-w-0">
                  <div className="text-sm font-medium text-[#111827] truncate">{m.title}</div>
                  <div className="text-xs text-[#6B7280]">{m.property_name}</div>
                </div>
                {m.predictive && <span className="ml-auto text-[10px] font-semibold text-[#0066FF] bg-[#0066FF]/10 px-2 py-0.5 rounded-full shrink-0">Auto</span>}
              </div>
            ))}
            {maint.length === 0 && <div className="text-sm text-[#6B7280]">All clear.</div>}
          </div>
        </div>
      </div>

      {/* Coastal note */}
      <div className="mt-5 rounded-xl border border-[#E5E7EB] bg-gradient-to-r from-[#0A2540] to-[#0e3a63] text-white p-6 flex items-center gap-4 overflow-hidden relative">
        <Waves className="h-10 w-10 text-white/40 shrink-0" />
        <div>
          <div className="font-display font-semibold">Coastal Maintenance Engine is on watch</div>
          <div className="text-sm text-white/80 mt-1">
            Salt-corrosion & HVAC checks auto-schedule every 60 days for coastal properties.
          </div>
        </div>
      </div>
    </div>
  );
}
