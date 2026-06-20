import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, fileToDataUrl } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { useI18n } from "@/context/I18nContext";
import {
  Waves, LogOut, Camera, Check, Sparkles, Wrench, CheckCircle2, AlertTriangle, Clock, Languages,
} from "lucide-react";

const statusBadge = {
  pending: "bg-[#F3F4F6] text-[#6B7280]",
  in_progress: "bg-[#0066FF]/10 text-[#0066FF]",
  open: "bg-[#F3F4F6] text-[#6B7280]",
  guest_ready: "bg-[#10B981]/10 text-[#10B981]",
  completed: "bg-[#10B981]/10 text-[#10B981]",
};

function HousekeepingCard({ task, onUpload, t }) {
  const fileRef = useRef();
  const [busy, setBusy] = useState(false);
  const handle = async (e) => {
    const f = e.target.files?.[0];
    if (!f) return;
    setBusy(true);
    const url = await fileToDataUrl(f);
    await onUpload(task.id, url);
    setBusy(false);
  };
  const ready = task.status === "guest_ready";
  return (
    <div data-testid="hk-card" className="rounded-2xl border border-[#E5E7EB] bg-white overflow-hidden">
      <div className="relative h-40">
        <img src={task.photos?.[0]?.url || task.image} alt={task.property_name} className="h-full w-full object-cover" />
        <span className={`absolute top-3 right-3 text-xs font-semibold px-2.5 py-1 rounded-full ${statusBadge[task.status]}`}>
          {ready ? t("ready") : t(task.status)}
        </span>
      </div>
      <div className="p-4">
        <div className="font-display text-lg font-semibold text-[#0A2540]">{task.property_name}</div>
        <div className="text-sm text-[#6B7280] mt-0.5">{task.checkout_guest}</div>
        {ready ? (
          <div data-testid="hk-ready-state" className="mt-4 flex items-center justify-center gap-2 rounded-xl bg-[#10B981]/10 text-[#10B981] font-semibold py-3.5">
            <CheckCircle2 className="h-5 w-5" /> {t("ready")}
          </div>
        ) : (
          <>
            <p className="text-xs text-[#6B7280] mt-3">{t("take_clean_photo")}</p>
            <input ref={fileRef} type="file" accept="image/*" capture="environment" onChange={handle} className="hidden" data-testid="hk-file-input" />
            <button
              data-testid="hk-upload-btn"
              onClick={() => fileRef.current?.click()}
              disabled={busy}
              className="mt-2 w-full flex items-center justify-center gap-2 rounded-xl bg-[#0A2540] text-white font-semibold py-4 text-base hover:bg-[#0e3358] transition-colors disabled:opacity-60"
            >
              <Camera className="h-5 w-5" /> {busy ? "…" : `${t("upload_photo")} · ${t("guest_ready")}`}
            </button>
          </>
        )}
      </div>
    </div>
  );
}

function MaintenanceCard({ task, onPhoto, onComplete, t }) {
  const beforeRef = useRef();
  const afterRef = useRef();
  const done = task.status === "completed";
  const upload = async (kind, e) => {
    const f = e.target.files?.[0];
    if (!f) return;
    const url = await fileToDataUrl(f);
    onPhoto(task.id, kind, url);
  };
  return (
    <div data-testid="mt-card" className={`rounded-2xl border bg-white overflow-hidden ${task.storm ? "border-[#FF5A5F]" : "border-[#E5E7EB]"}`}>
      <div className="p-4">
        <div className="flex items-start gap-3">
          <div className={`h-10 w-10 rounded-xl flex items-center justify-center shrink-0 ${task.storm ? "bg-[#FF5A5F]/10 text-[#FF5A5F]" : "bg-[#0A2540]/5 text-[#0A2540]"}`}>
            {task.storm ? <AlertTriangle className="h-5 w-5" /> : <Wrench className="h-5 w-5" />}
          </div>
          <div className="min-w-0 flex-1">
            <div className="font-semibold text-[#111827]">{task.title}</div>
            <div className="text-xs text-[#6B7280]">{task.property_name}</div>
          </div>
          <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${statusBadge[task.status]}`}>{t(task.status) || task.status}</span>
        </div>

        {task.checklist && (
          <div className="mt-3 space-y-1.5">
            {task.checklist.slice(0, 4).map((c, i) => (
              <div key={i} className="flex items-center gap-2 text-sm text-[#4B5563]">
                <Check className="h-3.5 w-3.5 text-[#10B981]" /> {c.text}
              </div>
            ))}
          </div>
        )}

        {!done && (
          <div className="grid grid-cols-2 gap-2 mt-4">
            <input ref={beforeRef} type="file" accept="image/*" capture="environment" onChange={(e) => upload("before", e)} className="hidden" />
            <input ref={afterRef} type="file" accept="image/*" capture="environment" onChange={(e) => upload("after", e)} className="hidden" />
            <button data-testid="mt-before-btn" onClick={() => beforeRef.current?.click()} className={`flex flex-col items-center justify-center gap-1 rounded-xl border py-3 text-sm font-medium ${task.before_photo ? "border-[#10B981] text-[#10B981] bg-[#10B981]/5" : "border-[#E5E7EB] text-[#4B5563]"}`}>
              {task.before_photo ? <Check className="h-4 w-4" /> : <Camera className="h-4 w-4" />} {t("before")}
            </button>
            <button data-testid="mt-after-btn" onClick={() => afterRef.current?.click()} className={`flex flex-col items-center justify-center gap-1 rounded-xl border py-3 text-sm font-medium ${task.after_photo ? "border-[#10B981] text-[#10B981] bg-[#10B981]/5" : "border-[#E5E7EB] text-[#4B5563]"}`}>
              {task.after_photo ? <Check className="h-4 w-4" /> : <Camera className="h-4 w-4" />} {t("after")}
            </button>
          </div>
        )}

        {(task.before_photo || task.after_photo) && (
          <div className="grid grid-cols-2 gap-2 mt-2">
            {[task.before_photo, task.after_photo].map((src, i) => src && (
              <img key={i} src={src} alt="" className="rounded-lg aspect-[4/3] object-cover w-full" />
            ))}
          </div>
        )}

        {!done && (
          <button
            data-testid="mt-complete-btn"
            onClick={() => onComplete(task.id)}
            className={`mt-3 w-full flex items-center justify-center gap-2 rounded-xl font-semibold py-3.5 text-white transition-colors ${task.storm ? "bg-[#FF5A5F] hover:bg-[#e5484d]" : "bg-[#0A2540] hover:bg-[#0e3358]"}`}
          >
            <CheckCircle2 className="h-5 w-5" /> {t("complete")}
          </button>
        )}
      </div>
    </div>
  );
}

export default function FieldApp() {
  const { user, logout } = useAuth();
  const { lang, toggle, t } = useI18n();
  const navigate = useNavigate();
  const [hk, setHk] = useState([]);
  const [mt, setMt] = useState([]);
  const [storm, setStorm] = useState(null);
  const isHK = user?.role === "housekeeper";

  const load = () => {
    api.get("/storm/status").then((r) => setStorm(r.data));
    if (isHK) api.get("/housekeeping").then((r) => setHk(r.data));
    else api.get("/maintenance").then((r) => setMt(r.data));
  };
  useEffect(() => {
    load();
  }, []);

  const guestReady = async (id, url) => {
    await api.post(`/housekeeping/${id}/guest-ready`, { photo: url });
    load();
  };
  const setPhoto = async (id, kind, url) => {
    await api.patch(`/maintenance/${id}`, { [kind]: url, status: "in_progress" });
    load();
  };
  const complete = async (id) => {
    await api.patch(`/maintenance/${id}`, { status: "completed" });
    load();
  };

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div className="min-h-screen bg-[#F9FAFB] pb-12">
      {/* Top bar */}
      <header className="sticky top-0 z-40 bg-white border-b border-[#E5E7EB]">
        <div className="px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-lg bg-[#0A2540] flex items-center justify-center"><Waves className="h-4 w-4 text-white" /></div>
            <div>
              <div className="font-display font-bold text-[#0A2540] leading-none">{t("field_app")}</div>
              <div className="text-[10px] text-[#6B7280]">{user?.name}</div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              data-testid="lang-toggle"
              onClick={toggle}
              className="flex items-center gap-1.5 text-sm font-bold rounded-full border border-[#E5E7EB] px-3 py-2 text-[#0A2540] hover:border-[#0066FF] transition-colors"
            >
              <Languages className="h-4 w-4" /> {lang === "en" ? "EN" : "ES"}
            </button>
            <button onClick={handleLogout} data-testid="field-logout" className="h-9 w-9 rounded-full border border-[#E5E7EB] flex items-center justify-center text-[#6B7280] hover:text-[#FF5A5F]">
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </div>
      </header>

      {storm?.active && (
        <div data-testid="field-storm-banner" className="bg-[#FF5A5F] text-white px-4 py-3 flex items-center gap-2">
          <AlertTriangle className="h-5 w-5 storm-pulse rounded-full" />
          <span className="font-display font-bold text-sm">{t("storm_mode")} — {storm.storm_name}</span>
        </div>
      )}

      <div className="px-4 pt-5">
        <div className="flex items-center gap-2 text-[#0A2540]">
          {isHK ? <Sparkles className="h-5 w-5" /> : <Wrench className="h-5 w-5" />}
          <h1 className="font-display text-2xl font-bold">{t("my_tasks")}</h1>
        </div>
      </div>

      <div className="px-4 mt-4 space-y-4 max-w-lg mx-auto">
        {isHK
          ? hk.map((task) => <HousekeepingCard key={task.id} task={task} onUpload={guestReady} t={t} />)
          : mt.map((task) => <MaintenanceCard key={task.id} task={task} onPhoto={setPhoto} onComplete={complete} t={t} />)}
        {((isHK && hk.length === 0) || (!isHK && mt.length === 0)) && (
          <div className="text-center text-[#6B7280] py-16 flex flex-col items-center gap-2">
            <Clock className="h-8 w-8" /> {t("no_tasks")}
          </div>
        )}
      </div>
    </div>
  );
}
