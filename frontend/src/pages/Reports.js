import { useEffect, useState } from "react";
import { api, fmtMoney } from "@/lib/api";
import { BarChart3, TrendingUp, Percent, DollarSign, CalendarClock } from "lucide-react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Cell,
  PieChart, Pie, Legend,
} from "recharts";

const CHANNEL_COLORS = { Airbnb: "#FF5A5F", VRBO: "#0066FF", Direct: "#10B981", "Booking.com": "#0A2540" };

function Kpi({ icon: Icon, label, value, tone, testid }) {
  return (
    <div data-testid={testid} className="rounded-xl border border-[#E5E7EB] bg-white p-5">
      <div className={`h-10 w-10 rounded-lg flex items-center justify-center ${tone}`}><Icon className="h-5 w-5" /></div>
      <div className="mt-3 text-2xl font-display font-bold text-[#0A2540]">{value}</div>
      <div className="text-sm text-[#6B7280] mt-0.5">{label}</div>
    </div>
  );
}

export default function Reports() {
  const [d, setD] = useState(null);
  useEffect(() => {
    api.get("/reports/analytics").then((r) => setD(r.data));
  }, []);

  const k = d?.kpis || {};
  const monthly = (d?.monthly || []).map((m) => ({ name: new Date(m.month + "-01").toLocaleDateString("en-US", { month: "short" }), revenue: Math.round(m.revenue) }));
  const channels = (d?.channels || []).map((c) => ({ ...c, fill: CHANNEL_COLORS[c.name] || "#0A2540" }));

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="text-xs font-bold tracking-wider uppercase text-[#6B7280]">Analytics</div>
      <h1 className="font-display text-3xl sm:text-4xl font-bold tracking-tight text-[#0A2540] mt-1">Performance Reports</h1>
      <p className="text-[#6B7280] mt-2">Portfolio metrics across the last 180 days.</p>

      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mt-6">
        <Kpi testid="kpi-occupancy" icon={Percent} label="Occupancy" value={`${k.occupancy ?? "—"}%`} tone="bg-[#0066FF]/10 text-[#0066FF]" />
        <Kpi testid="kpi-adr" icon={DollarSign} label="ADR (avg daily rate)" value={fmtMoney(k.adr)} tone="bg-[#10B981]/10 text-[#10B981]" />
        <Kpi testid="kpi-revpar" icon={TrendingUp} label="RevPAR" value={fmtMoney(k.revpar)} tone="bg-[#FF5A5F]/10 text-[#FF5A5F]" />
        <Kpi testid="kpi-los" icon={CalendarClock} label="Avg Length of Stay" value={`${k.avg_los ?? "—"} nts`} tone="bg-[#0A2540]/5 text-[#0A2540]" />
        <Kpi testid="kpi-revenue" icon={BarChart3} label="Total Revenue" value={fmtMoney(k.total_revenue)} tone="bg-[#6B7280]/10 text-[#6B7280]" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 mt-5">
        <div className="lg:col-span-2 rounded-xl border border-[#E5E7EB] bg-white p-6">
          <h3 className="font-display text-lg font-semibold text-[#0A2540]">Revenue by Month</h3>
          <div className="h-64 mt-4 -ml-2">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={monthly}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F3F4F6" vertical={false} />
                <XAxis dataKey="name" tick={{ fontSize: 12, fill: "#6B7280" }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 12, fill: "#6B7280" }} axisLine={false} tickLine={false} tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} />
                <Tooltip formatter={(v) => fmtMoney(v)} cursor={{ fill: "#F3F4F6" }} />
                <Bar dataKey="revenue" radius={[6, 6, 0, 0]} fill="#0A2540" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="rounded-xl border border-[#E5E7EB] bg-white p-6">
          <h3 className="font-display text-lg font-semibold text-[#0A2540]">Revenue by Channel</h3>
          <div className="h-64 mt-4">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={channels} dataKey="revenue" nameKey="name" cx="50%" cy="45%" innerRadius={50} outerRadius={80} paddingAngle={2}>
                  {channels.map((c, i) => <Cell key={i} fill={c.fill} />)}
                </Pie>
                <Tooltip formatter={(v) => fmtMoney(v)} />
                <Legend wrapperStyle={{ fontSize: 12 }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="mt-5 rounded-xl border border-[#E5E7EB] bg-white overflow-hidden">
        <div className="px-5 py-4 border-b border-[#E5E7EB] font-display text-lg font-semibold text-[#0A2540]">Property Leaderboard</div>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs font-bold uppercase tracking-wider text-[#6B7280] border-b border-[#E5E7EB]">
              <th className="px-5 py-3">Property</th>
              <th className="px-5 py-3 text-center">Occupancy</th>
              <th className="px-5 py-3 text-right">Revenue</th>
            </tr>
          </thead>
          <tbody>
            {(d?.properties || []).map((p, i) => (
              <tr key={i} data-testid="property-perf-row" className="border-b border-[#F3F4F6] last:border-0 hover:bg-[#F9FAFB]">
                <td className="px-5 py-3.5 font-medium text-[#111827]">{p.name}</td>
                <td className="px-5 py-3.5">
                  <div className="flex items-center gap-2 justify-center">
                    <div className="w-24 h-1.5 rounded-full bg-[#F3F4F6] overflow-hidden">
                      <div className="h-full bg-[#0066FF]" style={{ width: `${Math.min(100, p.occupancy)}%` }} />
                    </div>
                    <span className="text-xs text-[#6B7280] w-10">{p.occupancy}%</span>
                  </div>
                </td>
                <td className="px-5 py-3.5 text-right font-semibold text-[#0A2540]">{fmtMoney(p.revenue)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
