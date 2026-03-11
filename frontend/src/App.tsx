import { BrowserRouter, NavLink, Route, Routes } from "react-router-dom";

import DashboardHomePage from "./pages/DashboardHomePage";
import ManualControlPage from "./pages/ManualControlPage";
import OperationsPage from "./pages/OperationsPage";
import SchedulesPage from "./pages/SchedulesPage";

function TopNavLink({
  to,
  children,
}: {
  to: string;
  children: React.ReactNode;
}) {
  return (
    <NavLink
      to={to}
      end={to === "/"}
      style={({ isActive }) => ({
        textDecoration: "none",
        padding: "8px 12px",
        borderRadius: "8px",
        border: "1px solid #d0d7de",
        background: isActive ? "#0969da" : "#f6f8fa",
        color: isActive ? "#ffffff" : "#1f2328",
        fontSize: "0.9rem",
        fontWeight: 700,
      })}
    >
      {children}
    </NavLink>
  );
}

function AppShell() {
  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#f6f8fa",
        color: "#1f2328",
      }}
    >
      <header
        style={{
          borderBottom: "1px solid #d0d7de",
          background: "#ffffff",
          position: "sticky",
          top: 0,
          zIndex: 20,
        }}
      >
        <div
          style={{
            maxWidth: "1400px",
            margin: "0 auto",
            padding: "16px 24px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: "16px",
            flexWrap: "wrap",
          }}
        >
          <div>
            <div
              style={{
                fontSize: "1.1rem",
                fontWeight: 800,
              }}
            >
              BattleReef Operator Console
            </div>
            <div
              style={{
                fontSize: "0.85rem",
                color: "#57606a",
                marginTop: "4px",
              }}
            >
              Aquarium telemetry, automation, control, and operations
            </div>
          </div>

          <nav
            style={{
              display: "flex",
              gap: "10px",
              flexWrap: "wrap",
            }}
          >
            <TopNavLink to="/">Main Dashboard</TopNavLink>
            <TopNavLink to="/schedules">Schedules</TopNavLink>
            <TopNavLink to="/manual-control">Manual Control</TopNavLink>
            <TopNavLink to="/operations">Operations</TopNavLink>
          </nav>
        </div>
      </header>

      <main>
        <Routes>
          <Route path="/" element={<DashboardHomePage />} />
          <Route path="/schedules" element={<SchedulesPage />} />
          <Route path="/manual-control" element={<ManualControlPage />} />
          <Route path="/operations" element={<OperationsPage />} />
        </Routes>
      </main>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppShell />
    </BrowserRouter>
  );
}