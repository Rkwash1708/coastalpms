import { useEffect, useMemo, useState } from "react";
import { api, fmtMoney, fmtDate } from "@/lib/api";
import { CalendarRange, Plus, X } from "lucide-react";

const channelColor = {
  Airbnb: "#FF5A5F",
  VRBO: "#0066FF",
  Direct: "#10B981",
  "Booking.com": "#0A2540",
};

function daysFrom(start, count) {
  const arr = [];
  for (let i = 0; i < count; i++) {
    const d = new Date(start);
    d.setDate(d.getDate() + i);
    arr.push(d);
  }
  return arr;
}
const toKey = (d) => d.toISOString().slice(0, 10);

export default function Reservations() {
  const [data, setData] = useState({ properties: [], bookings: [], holds: [] });
  const [show, setShow] = useState(false);
  const [err, setErr] = useState("");
  const [form, setForm] = useState({ property_id: "", guest_name: "", guest_email: "", check_in: "", check_out: "", channel: "Direct" });

  const load = () => api.get("/calendar").then((r) => setData(r.data));
  useEffect(() => {
    load();
  }, []);

  const start = useMemo(() => { const d = new Date(); d.setHours(0, 0, 0, 0); return d; }, []);
  const days = useMemo(() => daysFrom(start, 24), [start]);

  const cellFor = (propId, dayKey) => {
    const b = data.bookings.find((x) => x.property_id === propId && x.check_in <= dayKey && x.check_out > dayKey);
    if (b) return { type: "booking", color: channelColor[b.channel] || "#0A2540", b };
    const h = data.holds.find((x) => x.property_id === propId && x.start_date.slice(0, 10) <= dayKey && x.end_date.slice(0, 10) >= dayKey);
    if (h) return { type: "hold", color: "#9CA3AF" };
    return null;
  };

  const upcoming = [...data.bookings]
    .filter((b) => b.check_out >= toKey(start))
    .sort((a, b) => a.check_in.localeCompare(b.check_in))
    .slice(0, 8);

  const create = async () => {
    setErr("");
    try {
      await api.post("/bookings", form);
      setShow(false);
      setForm({ property_id: "", guest_name: "", guest_email: "", check_in: "", check_out: "", channel: "Direct" });
      load();
    } catch (e) {
      setErr(e.response?.data?.detail || "Could not create reservation");
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex items-end justify-between flex-wrap gap-4">
        <div>
          <div className="text-xs font-bold tracking-wider uppercase text-[#6B7280]">Central Calendar</div>
          <h1 className="font-display text-3xl sm:text-4xl font-bold tracking-tight text-[#0A2540] mt-1">Reservations</h1>
        </div>
        <button data-testid="new-booking-btn" onClick={() => setShow(true)} className="flex items-center gap-2 rounded-lg bg-[#0A2540] text-white font-semibold px-5 py-2.5 hover:bg-[#0e3358] transition-colors">
          <Plus className="h-4 w-4" /> New Reservation
        </button>
      </div>

      {/* Legend */}
      <div className="flex items-center gap-4 mt-5 flex-wrap text-xs text-[#6B7280]">
        {Object.entries(channelColor).map(([k, c]) => (
          <span key={k} className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-full" style={{ background: c }} /> {k}</span>
        ))}
        <span className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-full bg-[#9CA3AF]" /> Owner hold</span>
      </div>

      {/* Calendar grid */}
      <div className="mt-4 rounded-xl border border-[#E5E7EB] bg-white overflow-x-auto coastline-scroll">
        <div className="min-w-[900px]">
          <div className="grid" style={{ gridTemplateColumns: `200px repeat(${days.length}, minmax(34px, 1fr))` }}>
            <div className="px-4 py-3 text-xs font-bold uppercase tracking-wider text-[#6B7280] border-b border-r border-[#E5E7EB] sticky left-0 bg-white z-10">Property</div>
            {days.map((d, i) => (
              <div key={i} className={`py-2 text-center border-b border-[#F3F4F6] ${[0, 6].includes(d.getDay()) ? "bg-[#F9FAFB]" : ""}`}>
                <div className="text-[10px] text-[#9CA3AF] uppercase">{d.toLocaleDateString("en-US", { weekday: "narrow" })}</div>
                <div className="text-xs font-semibold text-[#111827]">{d.getDate()}</div>
              </div>
            ))}
            {data.properties.map((p) => (
              <RowFragment key={p.id} p={p} days={days} cellFor={cellFor} />
            ))}
          </div>
        </div>
      </div>

      {/* Upcoming list */}
      <div className="mt-6 rounded-xl border border-[#E5E7EB] bg-white overflow-hidden">
        <div className="px-5 py-4 border-b border-[#E5E7EB] font-display text-lg font-semibold text-[#0A2540]">Upcoming Arrivals</div>
        {upcoming.map((b) => (
          <div key={b.id} data-testid="upcoming-booking" className="flex items-center gap-4 px-5 py-3.5 border-b border-[#F3F4F6] last:border-0">
            <span className="h-2.5 w-2.5 rounded-full shrink-0" style={{ background: channelColor[b.channel] || "#0A2540" }} />
            <div className="min-w-0 flex-1">
              <div className="text-sm font-semibold text-[#111827] truncate">{b.guest_name}</div>
              <div className="text-xs text-[#6B7280]">{b.property_name} · {b.channel}</div>
            </div>
            <div className="text-xs text-[#6B7280] hidden sm:block">{fmtDate(b.check_in)} → {fmtDate(b.check_out)} · {b.nights}n</div>
            <div className="text-sm font-semibold text-[#0A2540]">{fmtMoney(b.gross)}</div>
          </div>
        ))}
        {upcoming.length === 0 && <div className="px-5 py-8 text-center text-[#6B7280]">No upcoming reservations.</div>}
      </div>

      {show && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4" onClick={() => setShow(false)}>
          <div className="bg-white rounded-2xl p-6 w-full max-w-md" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between">
              <h3 className="font-display text-xl font-semibold text-[#0A2540]">New Reservation</h3>
              <button onClick={() => setShow(false)}><X className="h-5 w-5 text-[#6B7280]" /></button>
            </div>
            <div className="space-y-3 mt-4">
              <select data-testid="booking-property" value={form.property_id} onChange={(e) => setForm({ ...form, property_id: e.target.value })} className="w-full rounded-lg border border-[#E5E7EB] px-3 py-2.5 text-sm">
                <option value="">Select property…</option>
                {data.properties.map((p) => <option key={p.id} value={p.id}>{p.name} · {fmtMoney(p.nightly)}/night</option>)}
              </select>
              <input data-testid="booking-guest" placeholder="Guest name" value={form.guest_name} onChange={(e) => setForm({ ...form, guest_name: e.target.value })} className="w-full rounded-lg border border-[#E5E7EB] px-3 py-2.5 text-sm" />
              <input data-testid="booking-email" placeholder="Guest email (optional)" value={form.guest_email} onChange={(e) => setForm({ ...form, guest_email: e.target.value })} className="w-full rounded-lg border border-[#E5E7EB] px-3 py-2.5 text-sm" />
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs text-[#6B7280]">Check-in</label>
                  <input data-testid="booking-checkin" type="date" value={form.check_in} onChange={(e) => setForm({ ...form, check_in: e.target.value })} className="w-full rounded-lg border border-[#E5E7EB] px-3 py-2.5 text-sm" />
                </div>
                <div>
                  <label className="text-xs text-[#6B7280]">Check-out</label>
                  <input data-testid="booking-checkout" type="date" value={form.check_out} onChange={(e) => setForm({ ...form, check_out: e.target.value })} className="w-full rounded-lg border border-[#E5E7EB] px-3 py-2.5 text-sm" />
                </div>
              </div>
              <select value={form.channel} onChange={(e) => setForm({ ...form, channel: e.target.value })} className="w-full rounded-lg border border-[#E5E7EB] px-3 py-2.5 text-sm">
                {Object.keys(channelColor).map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
              {err && <div data-testid="booking-error" className="text-sm text-[#FF5A5F] bg-[#FF5A5F]/10 rounded-lg px-3 py-2">{err}</div>}
            </div>
            <div className="flex justify-end gap-2 mt-5">
              <button onClick={() => setShow(false)} className="px-4 py-2.5 rounded-lg text-sm font-medium text-[#6B7280] hover:bg-[#F3F4F6]">Cancel</button>
              <button data-testid="booking-save" onClick={create} className="px-5 py-2.5 rounded-lg bg-[#0A2540] text-white text-sm font-semibold hover:bg-[#0e3358]">Create & auto-bill</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function RowFragment({ p, days, cellFor }) {
  return (
    <>
      <div className="px-4 py-3 border-b border-r border-[#F3F4F6] sticky left-0 bg-white z-10">
        <div className="text-sm font-semibold text-[#111827] truncate">{p.name}</div>
        <div className="text-[11px] text-[#6B7280] truncate">{p.address?.split(",").slice(-2).join(",")}</div>
      </div>
      {days.map((d, i) => {
        const key = d.toISOString().slice(0, 10);
        const cell = cellFor(p.id, key);
        const weekend = [0, 6].includes(d.getDay());
        return (
          <div key={i} className={`border-b border-[#F3F4F6] h-[52px] flex items-center justify-center ${weekend ? "bg-[#F9FAFB]" : ""}`} title={cell?.b ? `${cell.b.guest_name} · ${cell.b.channel}` : ""}>
            {cell && <div className="h-5 w-full mx-px rounded-sm" style={{ background: cell.color, opacity: cell.type === "hold" ? 0.6 : 0.85 }} />}
          </div>
        );
      })}
    </>
  );
}
