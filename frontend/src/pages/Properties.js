import { useEffect, useState } from "react";
import { api, fmtMoney } from "@/lib/api";
import { MapPin, BedDouble, Bath, Waves, SlidersHorizontal, X } from "lucide-react";

export default function Properties() {
  const [props, setProps] = useState([]);
  const [edit, setEdit] = useState(null);
  const [form, setForm] = useState({});

  const load = () => api.get("/properties").then((r) => setProps(r.data));
  useEffect(() => {
    load();
  }, []);

  const openEdit = (p) => {
    setEdit(p);
    setForm({ nightly: p.nightly, weekend_nightly: p.weekend_nightly, min_nights: p.min_nights, cleaning_fee: p.cleaning_fee });
  };

  const save = async () => {
    await api.patch(`/properties/${edit.id}/rates`, {
      nightly: Number(form.nightly), weekend_nightly: Number(form.weekend_nightly),
      min_nights: Number(form.min_nights), cleaning_fee: Number(form.cleaning_fee),
    });
    setEdit(null);
    load();
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="text-xs font-bold tracking-wider uppercase text-[#6B7280]">Portfolio</div>
      <h1 className="font-display text-3xl sm:text-4xl font-bold tracking-tight text-[#0A2540] mt-1">Properties</h1>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 mt-6">
        {props.map((p) => (
          <div key={p.id} data-testid="property-card" className="rounded-xl border border-[#E5E7EB] bg-white overflow-hidden fade-up group">
            <div className="relative h-44 overflow-hidden">
              <img src={p.image} alt={p.name} className="h-full w-full object-cover group-hover:scale-105 transition-transform duration-500" />
              {p.coastal && (
                <span className="absolute top-3 left-3 flex items-center gap-1 text-[11px] font-semibold text-white bg-[#0A2540]/80 backdrop-blur px-2.5 py-1 rounded-full">
                  <Waves className="h-3 w-3" /> Coastal
                </span>
              )}
              <span className="absolute top-3 right-3 text-[11px] font-semibold text-[#0A2540] bg-white/90 px-2.5 py-1 rounded-full">
                {p.occupancy}% occ.
              </span>
            </div>
            <div className="p-5">
              <h3 className="font-display text-lg font-semibold text-[#0A2540]">{p.name}</h3>
              <div className="flex items-center gap-1 text-sm text-[#6B7280] mt-1">
                <MapPin className="h-3.5 w-3.5" /> {p.address}
              </div>
              <div className="flex items-center gap-4 mt-4 text-sm text-[#4B5563]">
                <span className="flex items-center gap-1"><BedDouble className="h-4 w-4" /> {p.beds}</span>
                <span className="flex items-center gap-1"><Bath className="h-4 w-4" /> {p.baths}</span>
                <span className="ml-auto font-semibold text-[#0A2540]">{fmtMoney(p.nightly)}<span className="text-xs text-[#6B7280] font-normal">/night</span></span>
              </div>
              <div className="mt-4 pt-4 border-t border-[#F3F4F6] flex items-center justify-between">
                <div className="text-xs text-[#6B7280]">Owner · <span className="font-medium text-[#111827]">{p.owner_name}</span></div>
                <button data-testid="edit-rates-btn" onClick={() => openEdit(p)} className="flex items-center gap-1.5 text-xs font-semibold text-[#0066FF] bg-[#0066FF]/10 px-2.5 py-1.5 rounded-full hover:bg-[#0066FF]/20">
                  <SlidersHorizontal className="h-3.5 w-3.5" /> Rates
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {edit && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4" onClick={() => setEdit(null)}>
          <div className="bg-white rounded-2xl p-6 w-full max-w-md" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between">
              <h3 className="font-display text-xl font-semibold text-[#0A2540]">Rates · {edit.name}</h3>
              <button onClick={() => setEdit(null)}><X className="h-5 w-5 text-[#6B7280]" /></button>
            </div>
            <div className="grid grid-cols-2 gap-3 mt-4">
              <div>
                <label className="text-xs font-bold uppercase tracking-wider text-[#6B7280]">Weekday $/night</label>
                <input data-testid="rate-nightly" type="number" value={form.nightly} onChange={(e) => setForm({ ...form, nightly: e.target.value })} className="mt-1 w-full rounded-lg border border-[#E5E7EB] px-3 py-2.5 text-sm" />
              </div>
              <div>
                <label className="text-xs font-bold uppercase tracking-wider text-[#6B7280]">Weekend $/night</label>
                <input data-testid="rate-weekend" type="number" value={form.weekend_nightly} onChange={(e) => setForm({ ...form, weekend_nightly: e.target.value })} className="mt-1 w-full rounded-lg border border-[#E5E7EB] px-3 py-2.5 text-sm" />
              </div>
              <div>
                <label className="text-xs font-bold uppercase tracking-wider text-[#6B7280]">Min nights</label>
                <input data-testid="rate-minnights" type="number" value={form.min_nights} onChange={(e) => setForm({ ...form, min_nights: e.target.value })} className="mt-1 w-full rounded-lg border border-[#E5E7EB] px-3 py-2.5 text-sm" />
              </div>
              <div>
                <label className="text-xs font-bold uppercase tracking-wider text-[#6B7280]">Cleaning fee</label>
                <input data-testid="rate-cleaning" type="number" value={form.cleaning_fee} onChange={(e) => setForm({ ...form, cleaning_fee: e.target.value })} className="mt-1 w-full rounded-lg border border-[#E5E7EB] px-3 py-2.5 text-sm" />
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-5">
              <button onClick={() => setEdit(null)} className="px-4 py-2.5 rounded-lg text-sm font-medium text-[#6B7280] hover:bg-[#F3F4F6]">Cancel</button>
              <button data-testid="rate-save" onClick={save} className="px-5 py-2.5 rounded-lg bg-[#0A2540] text-white text-sm font-semibold hover:bg-[#0e3358]">Save Rates</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
