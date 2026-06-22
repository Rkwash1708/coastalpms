import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import {
  LayoutDashboard, Home, Wrench, Inbox, Wallet, Waves, LogOut, UserCircle2,
  CalendarRange, Users, BarChart3,
} from "lucide-react";

const navByRole = {
  manager: [
    { to: "/dashboard", label: "Operations", icon: LayoutDashboard, id: "ops" },
    { to: "/reservations", label: "Reservations", icon: CalendarRange, id: "reservations" },
    { to: "/properties", label: "Properties", icon: Home, id: "properties" },
    { to: "/guests", label: "Guests", icon: Users, id: "guests" },
    { to: "/maintenance", label: "Maintenance", icon: Wrench, id: "maintenance" },
    { to: "/inbox", label: "Inbox", icon: Inbox, id: "inbox" },
    { to: "/reports", label: "Reports", icon: BarChart3, id: "reports" },
    { to: "/accounting", label: "Trust Accounting", icon: Wallet, id: "accounting" },
  ],
  owner: [
    { to: "/owner", label: "My Portfolio", icon: LayoutDashboard, id: "owner" },
  ],
};

export default function Sidebar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const items = navByRole[user?.role] || [];

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <aside className="hidden lg:flex lg:flex-col w-64 shrink-0 border-r border-[#E5E7EB] bg-white h-screen sticky top-0">
      <div className="px-6 py-6 flex items-center gap-2.5 border-b border-[#E5E7EB]">
        <div className="h-9 w-9 rounded-xl bg-[#0A2540] flex items-center justify-center">
          <Waves className="h-5 w-5 text-white" strokeWidth={2} />
        </div>
        <div>
          <div className="font-display font-extrabold text-[#0A2540] leading-none text-lg">Coastline</div>
          <div className="text-[10px] tracking-[0.18em] text-[#6B7280] font-semibold uppercase mt-0.5">PMS</div>
        </div>
      </div>

      <nav className="flex-1 px-3 py-5 space-y-1">
        {items.map((it) => (
          <NavLink
            key={it.id}
            to={it.to}
            data-testid={`nav-${it.id}`}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive ? "bg-[#0A2540] text-white" : "text-[#4B5563] hover:bg-[#F3F4F6]"
              }`
            }
          >
            <it.icon className="h-[18px] w-[18px]" strokeWidth={2} />
            {it.label}
          </NavLink>
        ))}
      </nav>

      <div className="px-3 py-4 border-t border-[#E5E7EB]">
        <div className="flex items-center gap-3 px-3 py-2">
          <UserCircle2 className="h-8 w-8 text-[#0A2540]" strokeWidth={1.5} />
          <div className="min-w-0">
            <div className="text-sm font-semibold text-[#111827] truncate">{user?.name}</div>
            <div className="text-xs text-[#6B7280] capitalize">{user?.role}</div>
          </div>
        </div>
        <button
          onClick={handleLogout}
          data-testid="logout-btn"
          className="mt-1 w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-[#6B7280] hover:bg-[#F3F4F6] transition-colors"
        >
          <LogOut className="h-[18px] w-[18px]" /> Log out
        </button>
      </div>
    </aside>
  );
}
