import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, fmtMoney } from "@/lib/api";
import {
  Waves, MapPin, BedDouble, Bath, CalendarRange, ArrowRight, X, Lock, ShieldCheck,
} from "lucide-react";

export default function BookingSite() {
  const [props, setProps] = useState([]);
  const [sel, setSel] = useState(null);
  const [form, setForm] = useState({ check_in: "", check_out: "", guest_name: "", guest_email: "" });
  const [quote, setQuote] = useState(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");

  useEffect(() => {
    api.get("/public/properties").then((r) => setProps(r.data));
  }, []);

  const open = (p) => {
    setSel(p);
    setForm({ check_in: "", check_out: "", guest_name: "", guest_email: "" });
    setQuote(null);
    setErr("");
  };

  useEffect(() => {
    if (sel && form.check_in && form.check_out && form.check_out > form.check_in) {
      api.get(`/public/quote?property_id=${sel.id}&check_in=${form.check_in}&check_out=${form.check_out}`)
        .then((r) => setQuote(r.data))
        .catch(() => setQuote(null));
    } else {
      setQuote(null);
    }
  }, [sel, form.check_in, form.check_out]);

  const pay = async () => {
    setErr("");
    if (!form.guest_name || !form.guest_email || !quote?.available) return;
    setLoading(true);
    try {
      const { data } = await api.post("/public/checkout", {
        property_id: sel.id,
        guest_name: form.guest_name,
        guest_email: form.guest_email,
        check_in: form.check_in,
        check_out: form.check_out,
        origin_url: window.location.origin,
      });
      window.location.href = data.url;
    } catch (e) {
      setErr(e.response?.data?.detail || "Could not start checkout");
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F9FAFB]">
      {/* Nav */}
      <header className="sticky top-0 z-30 bg-white/90 backdrop-blur border-b border-[#E5E7EB]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <Link to="/book" className="flex items-center gap-2">
            <div className="h-9 w-9 rounded-xl bg-[#0A2540] flex items-center justify-center"><Waves className="h-5 w-5 text-white" /></div>
            <div>
              <div className="font-display font-extrabold text-[#0A2540] leading-none text-lg">Coastline</div>
              <div className="text-[10px] tracking-[0.18em] text-[#6B7280] font-semibold uppercase mt-0.5">Stays</div>
            </div>
          </Link>
          <Link to="/login" data-testid="manager-login-link" className="text-sm font-semibold text-[#0A2540] hover:text-[#0066FF] transition-colors">Manager login →</Link>
        </div>
      </header>

      {/* Hero */}
      <section className="relative">
        <img src="https://images.unsplash.com/photo-1730005523015-422bd53dda0b?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjAzMjd8MHwxfHNlYXJjaHwzfHxtb2Rlcm4lMjBjb2FzdGFsJTIwdmFjYXRpb24lMjBob21lJTIwZXh0ZXJpb3J8ZW58MHx8fHwxNzgxOTMyMzMxfDA&ixlib=rb-4.1.0&q=85" alt="Coast" className="h-[42vh] w-full object-cover" />
        <div className="absolute inset-0 bg-gradient-to-t from-[#0A2540]/90 to-[#0A2540]/20" />
        <div className="absolute inset-0 flex items-center">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full">
            <div className="max-w-xl text-white fade-up">
              <h1 className="font-display text-4xl sm:text-5xl font-bold tracking-tight">Book your Southeast coast escape</h1>
              <p className="mt-3 text-white/85 text-base">Direct rates, no platform fees. Salt-air homes from Destin to Hilton Head — managed by people who know the coast.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Listings */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <h2 className="font-display text-2xl font-semibold text-[#0A2540]">Available homes</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 mt-6">
          {props.map((p) => (
            <div key={p.id} data-testid="public-property-card" className="rounded-xl border border-[#E5E7EB] bg-white overflow-hidden group fade-up">
              <div className="relative h-48 overflow-hidden">
                <img src={p.image} alt={p.name} className="h-full w-full object-cover group-hover:scale-105 transition-transform duration-500" />
                {p.coastal && <span className="absolute top-3 left-3 flex items-center gap-1 text-[11px] font-semibold text-white bg-[#0A2540]/80 backdrop-blur px-2.5 py-1 rounded-full"><Waves className="h-3 w-3" /> Coastal</span>}
              </div>
              <div className="p-5">
                <h3 className="font-display text-lg font-semibold text-[#0A2540]">{p.name}</h3>
                <div className="flex items-center gap-1 text-sm text-[#6B7280] mt-1"><MapPin className="h-3.5 w-3.5" /> {p.address}</div>
                <div className="flex items-center gap-4 mt-4 text-sm text-[#4B5563]">
                  <span className="flex items-center gap-1"><BedDouble className="h-4 w-4" /> {p.beds}</span>
                  <span className="flex items-center gap-1"><Bath className="h-4 w-4" /> {p.baths}</span>
                  <span className="ml-auto font-semibold text-[#0A2540]">{fmtMoney(p.nightly)}<span className="text-xs text-[#6B7280] font-normal">/night</span></span>
                </div>
                <button data-testid="book-now-btn" onClick={() => open(p)} className="mt-4 w-full flex items-center justify-center gap-2 rounded-lg bg-[#0A2540] text-white font-semibold py-3 hover:bg-[#0e3358] transition-colors">
                  Book now <ArrowRight className="h-4 w-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Booking drawer */}
      {sel && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-end" onClick={() => setSel(null)}>
          <div className="bg-white h-full w-full max-w-md p-6 overflow-y-auto coastline-scroll" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between">
              <h3 className="font-display text-xl font-semibold text-[#0A2540]">Reserve {sel.name}</h3>
              <button data-testid="booking-drawer-close" onClick={() => setSel(null)}><X className="h-5 w-5 text-[#6B7280]" /></button>
            </div>
            <img src={sel.image} alt={sel.name} className="mt-4 rounded-xl h-40 w-full object-cover" />

            <div className="mt-5 space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-bold uppercase tracking-wider text-[#6B7280]">Check-in</label>
                  <input data-testid="public-checkin" type="date" value={form.check_in} onChange={(e) => setForm({ ...form, check_in: e.target.value })} className="mt-1 w-full rounded-lg border border-[#E5E7EB] px-3 py-2.5 text-sm" />
                </div>
                <div>
                  <label className="text-xs font-bold uppercase tracking-wider text-[#6B7280]">Check-out</label>
                  <input data-testid="public-checkout" type="date" value={form.check_out} onChange={(e) => setForm({ ...form, check_out: e.target.value })} className="mt-1 w-full rounded-lg border border-[#E5E7EB] px-3 py-2.5 text-sm" />
                </div>
              </div>
              <input data-testid="public-guest-name" placeholder="Full name" value={form.guest_name} onChange={(e) => setForm({ ...form, guest_name: e.target.value })} className="w-full rounded-lg border border-[#E5E7EB] px-3 py-2.5 text-sm" />
              <input data-testid="public-guest-email" type="email" placeholder="Email" value={form.guest_email} onChange={(e) => setForm({ ...form, guest_email: e.target.value })} className="w-full rounded-lg border border-[#E5E7EB] px-3 py-2.5 text-sm" />
            </div>

            {/* Quote */}
            {quote && (
              <div data-testid="quote-breakdown" className="mt-5 rounded-xl border border-[#E5E7EB] p-4">
                {quote.available ? (
                  <>
                    <div className="flex justify-between text-sm py-1"><span className="text-[#6B7280]">{fmtMoney(quote.nightly)} × {quote.nights} nights</span><span className="text-[#111827]">{fmtMoney(quote.accommodation)}</span></div>
                    <div className="flex justify-between text-sm py-1"><span className="text-[#6B7280]">Cleaning fee</span><span className="text-[#111827]">{fmtMoney(quote.cleaning_fee)}</span></div>
                    <div className="flex justify-between text-sm py-1"><span className="text-[#6B7280]">Occupancy tax</span><span className="text-[#111827]">{fmtMoney(quote.occupancy_tax)}</span></div>
                    <div className="flex justify-between text-base font-semibold py-2 mt-1 border-t border-[#E5E7EB]"><span className="text-[#0A2540]">Total</span><span data-testid="quote-total" className="text-[#0A2540]">{fmtMoney(quote.total)}</span></div>
                  </>
                ) : (
                  <div data-testid="quote-unavailable" className="text-sm text-[#FF5A5F] flex items-center gap-2"><CalendarRange className="h-4 w-4" /> Those dates are not available. Try different dates.</div>
                )}
              </div>
            )}

            {err && <div data-testid="checkout-error" className="mt-3 text-sm text-[#FF5A5F] bg-[#FF5A5F]/10 rounded-lg px-3 py-2">{err}</div>}

            <button
              data-testid="pay-book-btn"
              onClick={pay}
              disabled={loading || !quote?.available || !form.guest_name || !form.guest_email}
              className="mt-5 w-full flex items-center justify-center gap-2 rounded-lg bg-[#0066FF] text-white font-semibold py-3.5 hover:bg-[#0052cc] transition-colors disabled:opacity-50"
            >
              <Lock className="h-4 w-4" /> {loading ? "Redirecting…" : quote ? `Pay ${fmtMoney(quote.total)} & Book` : "Pay & Book"}
            </button>
            <div className="mt-3 flex items-center justify-center gap-1.5 text-xs text-[#6B7280]"><ShieldCheck className="h-3.5 w-3.5" /> Secure checkout powered by Stripe</div>
          </div>
        </div>
      )}
    </div>
  );
}
