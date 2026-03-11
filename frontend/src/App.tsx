import { BrowserRouter, NavLink, Route, Routes } from "react-router-dom";

import DashboardHomePage from "./pages/DashboardHomePage";
import ManualControlPage from "./pages/ManualControlPage";
import OperationsPage from "./pages/OperationsPage";
import SchedulesPage from "./pages/SchedulesPage";

function SidebarNavLink({
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
        display: "block",
        textDecoration: "none",
        padding: "12px 14px",
        borderRadius: "10px",
        border: isActive ? "1px solid #0969da" : "1px solid transparent",
        background: isActive ? "#0969da" : "transparent",
        color: isActive ? "#ffffff" : "#1f2328",
        fontSize: "0.95rem",
        fontWeight: 700,
        transition: "all 0.15s ease",
      })}
    >
      {children}
    </NavLink>
  );
}

function Sidebar() {
  return (
    <aside
      style={{
        width: "260px",
        minWidth: "260px",
        borderRight: "1px solid #d0d7de",
        background: "#ffffff",
        minHeight: "100vh",
        position: "sticky",
        top: 0,
        alignSelf: "start",
      }}
    >
      <div
        style={{
          padding: "24px 18px 18px 18px",
          borderBottom: "1px solid #d8dee4",
        }}
      >
        <div
          style={{
            fontSize: "1.2rem",
            fontWeight: 800,
            color: "#1f2328",
            marginBottom: "6px",
          }}
        >
          BattleReef
        </div>

        <div
          style={{
            fontSize: "0.85rem",
            color: "#57606a",
            lineHeight: 1.5,
          }}
        >
          Operator Console for aquarium telemetry, automation, manual device control, and operations visibility.
        </div>
      </div>

      <div style={{ padding: "16px 12px" }}>
        <div
          style={{
            fontSize: "0.78rem",
            fontWeight: 800,
            color: "#57606a",
            letterSpacing: "0.04em",
            textTransform: "uppercase",
            marginBottom: "10px",
            paddingLeft: "6px",
          }}
        >
          Navigation
        </div>

        <nav
          style={{
            display: "grid",
            gap: "8px",
          }}
        >
          <SidebarNavLink to="/">Main Dashboard</SidebarNavLink>
          <SidebarNavLink to="/schedules">Schedules</SidebarNavLink>
          <SidebarNavLink to="/manual-control">Manual Control</SidebarNavLink>
          <SidebarNavLink to="/operations">Operations</SidebarNavLink>
        </nav>
      </div>

      <div
        style={{
          marginTop: "auto",
          padding: "18px 18px 24px 18px",
        }}
      >
        <div
          style={{
            border: "1px solid #d8dee4",
            borderRadius: "12px",
            background: "#f6f8fa",
            padding: "12px",
          }}
        >
          <div
            style={{
              fontSize: "0.82rem",
              fontWeight: 700,
              color: "#1f2328",
              marginBottom: "6px",
            }}
          >
            Operator View
          </div>

          <div
            style={{
              fontSize: "0.78rem",
              color: "#57606a",
              lineHeight: 1.5,
            }}
          >
            Use Main Dashboard for status, Schedules for automation, Manual Control for direct actions, and Operations for audit visibility.
          </div>
        </div>
      </div>
    </aside>
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
      <div
        style={{
          display: "flex",
          alignItems: "stretch",
          minHeight: "100vh",
        }}
      >
        <Sidebar />

        <div
          style={{
            flex: 1,
            minWidth: 0,
          }}
        >
          <header
            style={{
              background: "#ffffff",
              borderBottom: "1px solid #d0d7de",
              padding: "18px 24px",
              position: "sticky",
              top: 0,
              zIndex: 10,
            }}
          >
            <div
              style={{
                maxWidth: "1400px",
                margin: "0 auto",
              }}
            >
              <div
                style={{
                  fontSize: "1.05rem",
                  fontWeight: 800,
                  color: "#1f2328",
                }}
              >
                BattleReef Marine Controller
              </div>

              <div
                style={{
                  fontSize: "0.85rem",
                  color: "#57606a",
                  marginTop: "4px",
                }}
              >
                Aquarium telemetry, device orchestration, automation scheduling, and operational awareness.
              </div>
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
      </div>
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