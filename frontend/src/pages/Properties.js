import { useEffect, useState } from "react";
import { api, fmtMoney } from "@/lib/api";
import { MapPin, BedDouble, Bath, Waves } from "lucide-react";

export default function Properties() {
  const [props, setProps] = useState([]);
  useEffect(() => {
    api.get("/properties").then((r) => setProps(r.data));
  }, []);

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
              <div className="mt-4 pt-4 border-t border-[#F3F4F6] text-xs text-[#6B7280]">
                Owner · <span className="font-medium text-[#111827]">{p.owner_name}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
