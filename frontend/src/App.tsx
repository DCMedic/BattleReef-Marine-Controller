import { BrowserRouter, NavLink, Route, Routes } from "react-router-dom";
import { useEffect, useState } from "react";

import { fetchSystemSummary } from "./api/queries";
import DashboardHomePage from "./pages/DashboardHomePage";
import ManualControlPage from "./pages/ManualControlPage";
import OperationsPage from "./pages/OperationsPage";
import SchedulesPage from "./pages/SchedulesPage";
import type { SystemSummaryResponse } from "./types";

function SidebarNavLink({
  to,
  children,
  badge,
  tone = "default",
}: {
  to: string;
  children: React.ReactNode;
  badge?: string;
  tone?: "default" | "warning" | "danger" | "success";
}) {
  const badgeColors =
    tone === "danger"
      ? { background: "#ffebe9", color: "#cf222e", border: "#ff818266" }
      : tone === "warning"
      ? { background: "#fff8c5", color: "#9a6700", border: "#d4a72c66" }
      : tone === "success"
      ? { background: "#dafbe1", color: "#1a7f37", border: "#4ac26b66" }
      : { background: "#f6f8fa", color: "#57606a", border: "#d0d7de" };

  return (
    <NavLink
      to={to}
      end={to === "/"}
      style={({ isActive }) => ({
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: "12px",
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
      <span>{children}</span>

      {badge ? (
        <span
          style={({} as React.CSSProperties)}
        >
          <span
            style={{
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center",
              minWidth: "26px",
              height: "22px",
              padding: "0 8px",
              borderRadius: "999px",
              fontSize: "0.75rem",
              fontWeight: 800,
              background: badgeColors.background,
              color: badgeColors.color,
              border: `1px solid ${badgeColors.border}`,
            }}
          >
            {badge}
          </span>
        </span>
      ) : null}
    </NavLink>
  );
}

function StatusPill({
  label,
  value,
  tone = "default",
}: {
  label: string;
  value: string;
  tone?: "default" | "warning" | "danger" | "success";
}) {
  const palette =
    tone === "danger"
      ? { bg: "#ffebe9", fg: "#cf222e", border: "#ff818266" }
      : tone === "warning"
      ? { bg: "#fff8c5", fg: "#9a6700", border: "#d4a72c66" }
      : tone === "success"
      ? { bg: "#dafbe1", fg: "#1a7f37", border: "#4ac26b66" }
      : { bg: "#f6f8fa", fg: "#57606a", border: "#d0d7de" };

  return (
    <div
      style={{
        border: `1px solid ${palette.border}`,
        borderRadius: "10px",
        background: palette.bg,
        color: palette.fg,
        padding: "10px 12px",
      }}
    >
      <div
        style={{
          fontSize: "0.74rem",
          fontWeight: 800,
          letterSpacing: "0.03em",
          textTransform: "uppercase",
          marginBottom: "4px",
        }}
      >
        {label}
      </div>
      <div
        style={{
          fontSize: "0.95rem",
          fontWeight: 800,
        }}
      >
        {value}
      </div>
    </div>
  );
}

function Sidebar() {
  const [summary, setSummary] = useState<SystemSummaryResponse | null>(null);
  const [error, setError] = useState(false);

  async function loadSidebarSummary() {
    try {
      const data = await fetchSystemSummary();
      setSummary(data);
      setError(false);
    } catch {
      setError(true);
    }
  }

  useEffect(() => {
    void loadSidebarSummary();
    const interval = window.setInterval(loadSidebarSummary, 5000);
    return () => window.clearInterval(interval);
  }, []);

  const counts = summary?.counts;
  const queued = counts?.commands_queued ?? 0;
  const failed = counts?.commands_failed ?? 0;
  const devices = counts?.device_states ?? 0;
  const telemetry = counts?.telemetry_readings ?? 0;
  const platformHealthy =
    summary?.timescale_status.extension_installed &&
    summary?.timescale_status.telemetry_is_hypertable;

  return (
    <aside
      style={{
        width: "280px",
        minWidth: "280px",
        borderRight: "1px solid #d0d7de",
        background: "#ffffff",
        minHeight: "100vh",
        position: "sticky",
        top: 0,
        alignSelf: "start",
        display: "flex",
        flexDirection: "column",
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
          <SidebarNavLink
            to="/manual-control"
            badge={String(devices)}
            tone={devices > 0 ? "success" : "default"}
          >
            Manual Control
          </SidebarNavLink>
          <SidebarNavLink
            to="/operations"
            badge={failed > 0 ? String(failed) : String(queued)}
            tone={failed > 0 ? "danger" : queued > 0 ? "warning" : "success"}
          >
            Operations
          </SidebarNavLink>
        </nav>
      </div>

      <div
        style={{
          padding: "0 18px 18px 18px",
        }}
      >
        <div
          style={{
            fontSize: "0.78rem",
            fontWeight: 800,
            color: "#57606a",
            letterSpacing: "0.04em",
            textTransform: "uppercase",
            marginBottom: "10px",
            paddingLeft: "2px",
          }}
        >
          Live Status
        </div>

        <div
          style={{
            display: "grid",
            gap: "10px",
          }}
        >
          <StatusPill
            label="Platform"
            value={error ? "Unreachable" : platformHealthy ? "Healthy" : "Degraded"}
            tone={error ? "danger" : platformHealthy ? "success" : "warning"}
          />
          <StatusPill
            label="Queued Commands"
            value={queued.toLocaleString()}
            tone={queued > 0 ? "warning" : "success"}
          />
          <StatusPill
            label="Failed Commands"
            value={failed.toLocaleString()}
            tone={failed > 0 ? "danger" : "success"}
          />
          <StatusPill
            label="Tracked Devices"
            value={devices.toLocaleString()}
            tone={devices > 0 ? "success" : "default"}
          />
          <StatusPill
            label="Telemetry Records"
            value={telemetry.toLocaleString()}
            tone="default"
          />
        </div>
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