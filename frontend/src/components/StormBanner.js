import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { AlertTriangle, Waves, X } from "lucide-react";

export default function StormBanner() {
  const { user } = useAuth();
  const [storm, setStorm] = useState(null);

  const load = () => api.get("/storm/status").then((r) => setStorm(r.data)).catch(() => {});
  useEffect(() => {
    load();
  }, []);

  const deactivate = async () => {
    await api.post("/storm/activate", { active: false });
    load();
  };

  if (!storm?.active) return null;

  return (
    <div
      data-testid="storm-banner"
      className="bg-[#FF5A5F] text-white px-4 sm:px-6 py-3 flex items-center justify-between gap-4 flex-wrap"
    >
      <div className="flex items-center gap-3">
        <span className="storm-pulse rounded-full bg-white/20 p-1.5">
          <AlertTriangle className="h-5 w-5" />
        </span>
        <div>
          <div className="font-display font-bold text-sm sm:text-base leading-tight">
            STORM MODE ACTIVE — {storm.storm_name}
          </div>
          <div className="text-xs text-white/90">Hurricane prep checklists dispatched to all field staff.</div>
        </div>
      </div>
      {user?.role === "manager" && (
        <button
          onClick={deactivate}
          data-testid="storm-deactivate-btn"
          className="flex items-center gap-1.5 text-sm font-semibold bg-white/15 hover:bg-white/25 px-3 py-1.5 rounded-lg transition-colors"
        >
          <X className="h-4 w-4" /> Stand down
        </button>
      )}
    </div>
  );
}
