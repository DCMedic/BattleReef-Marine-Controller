import { useState } from "react";

import { evaluateScheduleRules } from "../api/queries";

type ScheduleAutomationPanelProps = {
  onScheduleEvaluated?: () => void;
};

export function ScheduleAutomationPanel({
  onScheduleEvaluated,
}: ScheduleAutomationPanelProps) {
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("")

  async function runScheduleEvaluation() {
    try {
      setBusy(true);
      setMessage("");
      const result = await evaluateScheduleRules();
      setMessage(
        `Schedule evaluated at ${new Date(result.evaluated_at).toLocaleString()} (UTC hour ${result.schedule_hour_utc}).`
      );
      onScheduleEvaluated?.();
    } catch (error) {
      const text = error instanceof Error ? error.message : "Schedule evaluation failed";
      setMessage(text);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div
      style={{
        border: "1px solid #d0d7de",
        borderRadius: "12px",
        padding: "16px",
        background: "#ffffff",
        boxShadow: "0 1px 3px rgba(0,0,0,0.06)",
        marginBottom: "24px",
      }}
    >
      <div
        style={{
          fontSize: "1rem",
          fontWeight: 700,
          color: "#1f2328",
          marginBottom: "6px",
        }}
      >
        Scheduled Automation
      </div>

      <div
        style={{
          fontSize: "0.85rem",
          color: "#57606a",
          marginBottom: "12px",
        }}
      >
        Evaluate lighting, feeding, and wavemaker schedules using the current UTC time.
        Devices in manual mode are skipped.
      </div>

      <button
        type="button"
        disabled={busy}
        onClick={runScheduleEvaluation}
        style={{
          border: "1px solid #d0d7de",
          borderRadius: "8px",
          background: "#f6f8fa",
          color: "#1f2328",
          padding: "8px 12px",
          fontSize: "0.9rem",
          fontWeight: 600,
          cursor: "pointer",
        }}
      >
        Run Schedule Evaluation
      </button>

      <div
        style={{
          minHeight: "20px",
          marginTop: "12px",
          fontSize: "0.85rem",
          color:
            message.toLowerCase().includes("failed") || message.toLowerCase().includes("error")
              ? "#cf222e"
              : "#1a7f37",
          wordBreak: "break-word",
        }}
      >
        {message}
      </div>
    </div>
  );
}