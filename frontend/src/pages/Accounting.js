import { useEffect, useState } from "react";
import { api, fmtMoney, fmtDate } from "@/lib/api";
import { Wallet, ArrowDownRight, Receipt, Building2, Landmark, Percent } from "lucide-react";

function SplitCard({ icon: Icon, label, value, pct, tone, testid }) {
  return (
    <div data-testid={testid} className="rounded-xl border border-[#E5E7EB] bg-white p-5">
      <div className="flex items-center justify-between">
        <div className={`h-9 w-9 rounded-lg flex items-center justify-center ${tone}`}>
          <Icon className="h-4 w-4" />
        </div>
        {pct != null && <span className="text-xs font-semibold text-[#6B7280]">{pct}%</span>}
      </div>
      <div className="mt-3 text-2xl font-display font-bold text-[#0A2540]">{fmtMoney(value)}</div>
      <div className="text-sm text-[#6B7280] mt-0.5">{label}</div>
    </div>
  );
}

export default function Accounting() {
  const [data, setData] = useState(null);
  useEffect(() => {
    api.get("/accounting/ledger").then((r) => setData(r.data));
  }, []);

  const t = data?.totals || {};
  const gross = t.gross || 1;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="text-xs font-bold tracking-wider uppercase text-[#6B7280]">Finance</div>
      <h1 className="font-display text-3xl sm:text-4xl font-bold tracking-tight text-[#0A2540] mt-1">Trust Accounting</h1>
      <p className="text-[#6B7280] mt-2">Every cleared booking auto-splits into its ledger the second it lands.</p>

      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mt-6">
        <SplitCard testid="ledger-gross" icon={Wallet} label="Gross Revenue" value={t.gross} tone="bg-[#0A2540]/5 text-[#0A2540]" />
        <SplitCard testid="ledger-owner" icon={Building2} label="Owner Payouts" value={t.owner_payout} pct={Math.round((t.owner_payout / gross) * 100)} tone="bg-[#10B981]/10 text-[#10B981]" />
        <SplitCard testid="ledger-commission" icon={Percent} label="PMC Commission" value={t.commission} pct={Math.round((t.commission / gross) * 100)} tone="bg-[#0066FF]/10 text-[#0066FF]" />
        <SplitCard testid="ledger-cleaning" icon={Receipt} label="Cleaning Fees" value={t.cleaning_fee} tone="bg-[#FF5A5F]/10 text-[#FF5A5F]" />
        <SplitCard testid="ledger-tax" icon={Landmark} label="Occupancy Tax" value={t.occupancy_tax} pct={Math.round((t.occupancy_tax / gross) * 100)} tone="bg-[#6B7280]/10 text-[#6B7280]" />
      </div>

      <div className="mt-6 rounded-xl border border-[#E5E7EB] bg-white overflow-hidden">
        <div className="px-5 py-4 border-b border-[#E5E7EB]">
          <h3 className="font-display text-lg font-semibold text-[#0A2540]">Split Ledger</h3>
        </div>
        <div className="overflow-x-auto coastline-scroll">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs font-bold tracking-wider uppercase text-[#6B7280] border-b border-[#E5E7EB]">
                <th className="px-5 py-3">Property</th>
                <th className="px-5 py-3">Channel</th>
                <th className="px-5 py-3">Date</th>
                <th className="px-5 py-3 text-right">Gross</th>
                <th className="px-5 py-3 text-right">Commission</th>
                <th className="px-5 py-3 text-right">Tax</th>
                <th className="px-5 py-3 text-right">Owner</th>
              </tr>
            </thead>
            <tbody>
              {(data?.ledgers || []).slice(0, 40).map((l) => (
                <tr key={l.id} data-testid="ledger-row" className="border-b border-[#F3F4F6] hover:bg-[#F9FAFB]">
                  <td className="px-5 py-3.5 font-medium text-[#111827]">{l.property_name}</td>
                  <td className="px-5 py-3.5 text-[#6B7280]">{l.channel}</td>
                  <td className="px-5 py-3.5 text-[#6B7280]">{fmtDate(l.date)}</td>
                  <td className="px-5 py-3.5 text-right text-[#111827]">{fmtMoney(l.gross)}</td>
                  <td className="px-5 py-3.5 text-right text-[#0066FF]">{fmtMoney(l.commission)}</td>
                  <td className="px-5 py-3.5 text-right text-[#6B7280]">{fmtMoney(l.occupancy_tax)}</td>
                  <td className="px-5 py-3.5 text-right font-semibold text-[#10B981]">{fmtMoney(l.owner_payout)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
