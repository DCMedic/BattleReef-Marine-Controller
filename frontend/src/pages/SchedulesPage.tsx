import { useState } from "react";

import { ScheduleAutomationPanel } from "../components/ScheduleAutomationPanel";
import { ScheduleManagerPanel } from "../components/ScheduleManagerPanel";
import { WeeklyScheduleTimeline } from "../components/WeeklyScheduleTimeline";

export default function SchedulesPage() {
  const [refreshToken, setRefreshToken] = useState(0);

  function handleScheduleEvaluated() {
    window.setTimeout(() => {
      setRefreshToken((prev) => prev + 1);
    }, 500);
  }

  return (
    <div style={{ padding: "24px" }}>
      <div style={{ maxWidth: "1400px", margin: "0 auto" }}>
        <div style={{ marginBottom: "24px" }}>
          <h1 style={{ margin: 0, fontSize: "2rem", fontWeight: 800 }}>
            Schedules
          </h1>
          <p style={{ marginTop: "8px", color: "#57606a", fontSize: "1rem" }}>
            Manage persistent automation schedules and visualize weekly timing at a glance.
          </p>
        </div>

        <ScheduleAutomationPanel onScheduleEvaluated={handleScheduleEvaluated} />
        <WeeklyScheduleTimeline refreshToken={refreshToken} />
        <ScheduleManagerPanel refreshToken={refreshToken} />
      </div>
    </div>
  );
}