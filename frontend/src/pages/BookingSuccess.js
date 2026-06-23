import { useEffect, useState, useRef } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api, fmtMoney, fmtDate } from "@/lib/api";
import { Waves, CheckCircle2, Loader2, XCircle, ArrowLeft } from "lucide-react";

const MAX_ATTEMPTS = 8;
const INTERVAL = 2000;

export default function BookingSuccess() {
  const [params] = useSearchParams();
  const sessionId = params.get("session_id");
  const [state, setState] = useState("polling"); // polling | success | failed | timeout
  const [info, setInfo] = useState(null);
  const attempts = useRef(0);

  useEffect(() => {
    if (!sessionId) {
      setState("failed");
      return;
    }
    let timer;
    const poll = async () => {
      try {
        const { data } = await api.get(`/public/checkout/status/${sessionId}`);
        if (data.payment_status === "paid") {
          setInfo(data);
          setState("success");
          return;
        }
        if (data.status === "expired") {
          setState("failed");
          return;
        }
        attempts.current += 1;
        if (attempts.current >= MAX_ATTEMPTS) {
          setState("timeout");
          return;
        }
        timer = setTimeout(poll, INTERVAL);
      } catch (e) {
        setState("failed");
      }
    };
    poll();
    return () => clearTimeout(timer);
  }, [sessionId]);

  return (
    <div className="min-h-screen bg-[#F9FAFB] flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl border border-[#E5E7EB] p-8 max-w-md w-full text-center fade-up">
        <div className="flex justify-center mb-2">
          <div className="h-10 w-10 rounded-xl bg-[#0A2540] flex items-center justify-center"><Waves className="h-5 w-5 text-white" /></div>
        </div>

        {state === "polling" && (
          <div data-testid="payment-polling" className="py-6">
            <Loader2 className="h-10 w-10 text-[#0066FF] animate-spin mx-auto" />
            <h2 className="font-display text-xl font-semibold text-[#0A2540] mt-4">Confirming your payment…</h2>
            <p className="text-sm text-[#6B7280] mt-1">Hang tight, this only takes a moment.</p>
          </div>
        )}

        {state === "success" && (
          <div data-testid="payment-success" className="py-4">
            <CheckCircle2 className="h-12 w-12 text-[#10B981] mx-auto" />
            <h2 className="font-display text-2xl font-bold text-[#0A2540] mt-4">You're booked!</h2>
            <p className="text-sm text-[#6B7280] mt-1">A confirmation is on its way to your inbox.</p>
            {info?.booking && (
              <div className="mt-5 rounded-xl bg-[#F9FAFB] border border-[#E5E7EB] p-4 text-left">
                <div className="font-semibold text-[#0A2540]">{info.booking.property_name}</div>
                <div className="text-sm text-[#6B7280] mt-1">{fmtDate(info.booking.check_in)} → {fmtDate(info.booking.check_out)} · {info.booking.nights} nights</div>
                <div className="text-sm text-[#6B7280]">Guest · {info.booking.guest_name}</div>
                <div className="mt-2 pt-2 border-t border-[#E5E7EB] flex justify-between font-semibold text-[#0A2540]"><span>Paid</span><span>{fmtMoney(info.amount)}</span></div>
              </div>
            )}
            <Link to="/book" className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-[#0066FF]"><ArrowLeft className="h-4 w-4" /> Back to homes</Link>
          </div>
        )}

        {(state === "failed" || state === "timeout") && (
          <div data-testid="payment-failed" className="py-4">
            <XCircle className="h-12 w-12 text-[#FF5A5F] mx-auto" />
            <h2 className="font-display text-xl font-semibold text-[#0A2540] mt-4">
              {state === "timeout" ? "Still processing" : "Payment not completed"}
            </h2>
            <p className="text-sm text-[#6B7280] mt-1">
              {state === "timeout" ? "Your payment is taking longer than expected. Check your email for confirmation." : "We couldn't confirm a successful payment. No charge was made."}
            </p>
            <Link to="/book" className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-[#0066FF]"><ArrowLeft className="h-4 w-4" /> Back to homes</Link>
          </div>
        )}
      </div>
    </div>
  );
}
