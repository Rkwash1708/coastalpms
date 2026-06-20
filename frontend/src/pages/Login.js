import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth, formatApiErrorDetail } from "@/context/AuthContext";
import { Waves, ArrowRight } from "lucide-react";

const demoAccounts = [
  { label: "Manager", email: "manager@coastline.com", password: "Manager123" },
  { label: "Housekeeper", email: "maria@coastline.com", password: "Field123" },
  { label: "Maintenance", email: "carlos@coastline.com", password: "Field123" },
  { label: "Owner", email: "owner@coastline.com", password: "Owner123" },
];

const roleHome = { manager: "/dashboard", owner: "/owner", housekeeper: "/field", maintenance: "/field" };

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e?.preventDefault();
    setError("");
    setLoading(true);
    try {
      const u = await login(email, password);
      navigate(roleHome[u.role] || "/dashboard");
    } catch (err) {
      setError(formatApiErrorDetail(err.response?.data?.detail) || err.message);
    } finally {
      setLoading(false);
    }
  };

  const quick = (acc) => {
    setEmail(acc.email);
    setPassword(acc.password);
  };

  return (
    <div className="min-h-screen grid lg:grid-cols-2">
      {/* Left — form */}
      <div className="flex flex-col justify-center px-6 sm:px-12 lg:px-20 py-12">
        <div className="max-w-md w-full mx-auto fade-up">
          <div className="flex items-center gap-2.5 mb-12">
            <div className="h-10 w-10 rounded-xl bg-[#0A2540] flex items-center justify-center">
              <Waves className="h-5 w-5 text-white" />
            </div>
            <div>
              <div className="font-display font-extrabold text-[#0A2540] text-xl leading-none">Coastline</div>
              <div className="text-[10px] tracking-[0.18em] text-[#6B7280] font-semibold uppercase mt-0.5">PMS</div>
            </div>
          </div>

          <h1 className="font-display text-4xl font-bold tracking-tight text-[#0A2540]">Welcome back</h1>
          <p className="text-[#6B7280] mt-3 text-base">
            Property management built for the Southeast coast.
          </p>

          <form onSubmit={submit} className="mt-8 space-y-4">
            <div>
              <label className="text-xs font-bold tracking-wider uppercase text-[#6B7280]">Email</label>
              <input
                data-testid="login-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@coastline.com"
                className="mt-1.5 w-full rounded-lg border border-[#E5E7EB] px-4 py-3 text-[#111827] outline-none focus:ring-2 focus:ring-[#0066FF] focus:border-transparent transition"
              />
            </div>
            <div>
              <label className="text-xs font-bold tracking-wider uppercase text-[#6B7280]">Password</label>
              <input
                data-testid="login-password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="mt-1.5 w-full rounded-lg border border-[#E5E7EB] px-4 py-3 text-[#111827] outline-none focus:ring-2 focus:ring-[#0066FF] focus:border-transparent transition"
              />
            </div>
            {error && (
              <div data-testid="login-error" className="text-sm text-[#FF5A5F] bg-[#FF5A5F]/10 rounded-lg px-3 py-2">
                {error}
              </div>
            )}
            <button
              data-testid="login-submit"
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 rounded-lg bg-[#0A2540] text-white font-semibold px-6 py-3 hover:bg-[#0e3358] transition-colors disabled:opacity-60"
            >
              {loading ? "Signing in…" : "Sign in"} <ArrowRight className="h-4 w-4" />
            </button>
          </form>

          <div className="mt-8">
            <div className="text-xs font-bold tracking-wider uppercase text-[#6B7280] mb-2">Demo accounts</div>
            <div className="grid grid-cols-2 gap-2">
              {demoAccounts.map((a) => (
                <button
                  key={a.email}
                  data-testid={`demo-${a.label.toLowerCase()}`}
                  onClick={() => quick(a)}
                  className="text-left rounded-lg border border-[#E5E7EB] px-3 py-2 hover:border-[#0066FF] hover:bg-[#0066FF]/5 transition-colors"
                >
                  <div className="text-sm font-semibold text-[#111827]">{a.label}</div>
                  <div className="text-xs text-[#6B7280] truncate">{a.email}</div>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Right — hero */}
      <div className="hidden lg:block relative">
        <img
          src="https://images.unsplash.com/photo-1730005523015-422bd53dda0b?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjAzMjd8MHwxfHNlYXJjaHwzfHxtb2Rlcm4lMjBjb2FzdGFsJTIwdmFjYXRpb24lMjBob21lJTIwZXh0ZXJpb3J8ZW58MHx8fHwxNzgxOTMyMzMxfDA&ixlib=rb-4.1.0&q=85"
          alt="Coastal property"
          className="absolute inset-0 h-full w-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-[#0A2540]/90 via-[#0A2540]/30 to-transparent" />
        <div className="absolute bottom-0 left-0 right-0 p-12 text-white">
          <h2 className="font-display text-3xl font-bold leading-tight max-w-md">
            From salt-air corrosion to hurricane prep — handled.
          </h2>
          <p className="text-white/80 mt-3 max-w-md">
            The zero-phone-call platform that finally adapts to your business, not the other way around.
          </p>
        </div>
      </div>
    </div>
  );
}
