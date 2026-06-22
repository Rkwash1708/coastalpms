import { useEffect, useState } from "react";
import { api, fmtMoney, fmtDate } from "@/lib/api";
import { Users, Mail, Phone, Star, X, Save } from "lucide-react";

export default function Guests() {
  const [guests, setGuests] = useState([]);
  const [active, setActive] = useState(null);
  const [notes, setNotes] = useState("");

  const load = () => api.get("/guests").then((r) => setGuests(r.data));
  useEffect(() => {
    load();
  }, []);

  const open = async (g) => {
    const { data } = await api.get(`/guests/${g.id}`);
    setActive(data);
    setNotes(data.notes || "");
  };

  const saveNotes = async () => {
    await api.patch(`/guests/${active.id}`, { notes });
    setActive({ ...active, notes });
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="text-xs font-bold tracking-wider uppercase text-[#6B7280]">CRM</div>
      <h1 className="font-display text-3xl sm:text-4xl font-bold tracking-tight text-[#0A2540] mt-1">Guests</h1>
      <p className="text-[#6B7280] mt-2">{guests.length} guests · ranked by lifetime value</p>

      <div className="mt-6 rounded-xl border border-[#E5E7EB] bg-white overflow-hidden">
        <div className="grid grid-cols-12 px-5 py-3 text-xs font-bold uppercase tracking-wider text-[#6B7280] border-b border-[#E5E7EB]">
          <div className="col-span-5 sm:col-span-4">Guest</div>
          <div className="col-span-4 sm:col-span-4 hidden sm:block">Contact</div>
          <div className="col-span-3 sm:col-span-2 text-center">Stays</div>
          <div className="col-span-4 sm:col-span-2 text-right">Lifetime</div>
        </div>
        {guests.map((g, i) => (
          <button key={g.id} data-testid="guest-row" onClick={() => open(g)} className="w-full grid grid-cols-12 items-center px-5 py-3.5 border-b border-[#F3F4F6] last:border-0 hover:bg-[#F9FAFB] text-left transition-colors">
            <div className="col-span-5 sm:col-span-4 flex items-center gap-3 min-w-0">
              <div className="h-9 w-9 rounded-full bg-[#0A2540] text-white flex items-center justify-center text-sm font-semibold shrink-0">{g.name[0]}</div>
              <div className="min-w-0">
                <div className="text-sm font-semibold text-[#111827] truncate flex items-center gap-1">
                  {g.name}
                  {i === 0 && <Star className="h-3.5 w-3.5 text-[#F59E0B] fill-[#F59E0B]" />}
                </div>
                {g.last_stay && <div className="text-xs text-[#6B7280]">Last: {fmtDate(g.last_stay)}</div>}
              </div>
            </div>
            <div className="col-span-4 hidden sm:block text-sm text-[#6B7280] truncate">{g.email}</div>
            <div className="col-span-3 sm:col-span-2 text-center text-sm font-medium text-[#111827]">{g.total_stays}</div>
            <div className="col-span-4 sm:col-span-2 text-right text-sm font-semibold text-[#10B981]">{fmtMoney(g.total_spent)}</div>
          </button>
        ))}
      </div>

      {active && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-end" onClick={() => setActive(null)}>
          <div className="bg-white h-full w-full max-w-md p-6 overflow-y-auto coastline-scroll" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between">
              <h3 className="font-display text-xl font-semibold text-[#0A2540]">Guest Profile</h3>
              <button data-testid="guest-close" onClick={() => setActive(null)}><X className="h-5 w-5 text-[#6B7280]" /></button>
            </div>
            <div className="flex items-center gap-3 mt-5">
              <div className="h-14 w-14 rounded-full bg-[#0A2540] text-white flex items-center justify-center text-xl font-bold">{active.name[0]}</div>
              <div>
                <div className="font-display text-lg font-semibold text-[#0A2540]">{active.name}</div>
                <div className="text-sm text-[#6B7280]">{active.total_stays} stays · {fmtMoney(active.total_spent)} lifetime</div>
              </div>
            </div>
            <div className="mt-4 space-y-2 text-sm">
              {active.email && <div className="flex items-center gap-2 text-[#4B5563]"><Mail className="h-4 w-4 text-[#6B7280]" /> {active.email}</div>}
              {active.phone && <div className="flex items-center gap-2 text-[#4B5563]"><Phone className="h-4 w-4 text-[#6B7280]" /> {active.phone}</div>}
            </div>

            <div className="mt-5">
              <div className="text-xs font-bold uppercase tracking-wider text-[#6B7280] mb-2">Internal Notes</div>
              <textarea data-testid="guest-notes" value={notes} onChange={(e) => setNotes(e.target.value)} rows={3} placeholder="VIP, allergies, preferences…" className="w-full rounded-lg border border-[#E5E7EB] px-3 py-2.5 text-sm outline-none focus:ring-2 focus:ring-[#0066FF] resize-none" />
              <button data-testid="guest-save-notes" onClick={saveNotes} className="mt-2 flex items-center gap-1.5 text-sm font-semibold text-[#0066FF] bg-[#0066FF]/10 px-3 py-1.5 rounded-lg hover:bg-[#0066FF]/20"><Save className="h-4 w-4" /> Save notes</button>
            </div>

            <div className="mt-6">
              <div className="text-xs font-bold uppercase tracking-wider text-[#6B7280] mb-2">Stay History</div>
              <div className="space-y-2">
                {active.stays?.map((s) => (
                  <div key={s.id} className="rounded-lg border border-[#E5E7EB] px-3 py-2.5">
                    <div className="flex items-center justify-between">
                      <div className="text-sm font-medium text-[#111827]">{s.property_name}</div>
                      <div className="text-sm font-semibold text-[#0A2540]">{fmtMoney(s.gross)}</div>
                    </div>
                    <div className="text-xs text-[#6B7280] mt-0.5">{fmtDate(s.check_in)} → {fmtDate(s.check_out)} · {s.channel} · {s.status}</div>
                  </div>
                ))}
                {(!active.stays || active.stays.length === 0) && <div className="text-sm text-[#6B7280]">No stays yet.</div>}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
