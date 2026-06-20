import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate, Outlet } from "react-router-dom";
import { AuthProvider, useAuth } from "@/context/AuthContext";
import { I18nProvider } from "@/context/I18nContext";
import { Toaster } from "@/components/ui/sonner";
import Sidebar from "@/components/Sidebar";
import StormBanner from "@/components/StormBanner";
import Login from "@/pages/Login";
import ManagerDashboard from "@/pages/ManagerDashboard";
import Properties from "@/pages/Properties";
import Maintenance from "@/pages/Maintenance";
import Inbox from "@/pages/Inbox";
import Accounting from "@/pages/Accounting";
import OwnerPortal from "@/pages/OwnerPortal";
import FieldApp from "@/pages/FieldApp";
import { Waves } from "lucide-react";

const roleHome = { manager: "/dashboard", owner: "/owner", housekeeper: "/field", maintenance: "/field" };

function Loading() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-[#F9FAFB]">
      <div className="flex flex-col items-center gap-3 text-[#0A2540]">
        <div className="h-12 w-12 rounded-2xl bg-[#0A2540] flex items-center justify-center animate-pulse">
          <Waves className="h-6 w-6 text-white" />
        </div>
        <span className="text-sm text-[#6B7280]">Loading Coastline…</span>
      </div>
    </div>
  );
}

function Protected({ roles }) {
  const { user, loading } = useAuth();
  if (loading || user === null) return <Loading />;
  if (!user) return <Navigate to="/login" replace />;
  if (roles && !roles.includes(user.role)) return <Navigate to={roleHome[user.role] || "/login"} replace />;
  return <Outlet />;
}

function DashboardLayout() {
  return (
    <div className="flex min-h-screen bg-[#F9FAFB]">
      <Sidebar />
      <div className="flex-1 min-w-0">
        <StormBanner />
        <Outlet />
      </div>
    </div>
  );
}

function RootRedirect() {
  const { user, loading } = useAuth();
  if (loading || user === null) return <Loading />;
  if (!user) return <Navigate to="/login" replace />;
  return <Navigate to={roleHome[user.role] || "/login"} replace />;
}

function App() {
  return (
    <div className="App">
      <AuthProvider>
        <I18nProvider>
          <BrowserRouter>
            <Routes>
              <Route path="/" element={<RootRedirect />} />
              <Route path="/login" element={<Login />} />

              {/* Manager workspace */}
              <Route element={<Protected roles={["manager"]} />}>
                <Route element={<DashboardLayout />}>
                  <Route path="/dashboard" element={<ManagerDashboard />} />
                  <Route path="/properties" element={<Properties />} />
                  <Route path="/maintenance" element={<Maintenance />} />
                  <Route path="/inbox" element={<Inbox />} />
                  <Route path="/accounting" element={<Accounting />} />
                </Route>
              </Route>

              {/* Owner portal */}
              <Route element={<Protected roles={["owner", "manager"]} />}>
                <Route element={<DashboardLayout />}>
                  <Route path="/owner" element={<OwnerPortal />} />
                </Route>
              </Route>

              {/* Field app */}
              <Route element={<Protected roles={["housekeeper", "maintenance"]} />}>
                <Route path="/field" element={<FieldApp />} />
              </Route>

              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </BrowserRouter>
          <Toaster />
        </I18nProvider>
      </AuthProvider>
    </div>
  );
}

export default App;
