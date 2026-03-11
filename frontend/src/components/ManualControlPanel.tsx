import { useState } from "react";

import { createManualCommand } from "../api/queries";
import type { CommandResponse, DeviceStateSummary } from "../types";

type ManualControlPanelProps = {
  deviceStates: DeviceStateSummary[];
  onCommandSent?: (command: CommandResponse) => void;
};

type DeviceStatePayload = Record<string, unknown> | undefined;

type PowerControlCardProps = {
  title: string;
  deviceKey: string;
  description: string;
  statePayload?: DeviceStatePayload;
  onPowerOn: () => Promise<void>;
  onPowerOff: () => Promise<void>;
};

type WavemakerControlCardProps = {
  title: string;
  deviceKey: string;
  description: string;
  statePayload?: DeviceStatePayload;
  onPowerOn: () => Promise<void>;
  onPowerOff: () => Promise<void>;
  onLow: () => Promise<void>;
  onMedium: () => Promise<void>;
  onHigh: () => Promise<void>;
};

type FeederControlCardProps = {
  title: string;
  deviceKey: string;
  description: string;
  statePayload?: DeviceStatePayload;
  onFeed5: () => Promise<void>;
  onFeed10: () => Promise<void>;
};

function formatBoolean(value: unknown): string {
  if (typeof value === "boolean") return value ? "On" : "Off";
  return "Unknown";
}

function formatText(value: unknown, fallback = "Unknown"): string {
  if (value === null || value === undefined) return fallback;
  return String(value);
}

function StatusRow({ label, value }: { label: string; value: string }) {
  return (
    <div
      style={{
        display: "flex",
        justifyContent: "space-between",
        gap: "12px",
        fontSize: "0.9rem",
        marginBottom: "6px",
      }}
    >
      <span style={{ color: "#57606a", fontWeight: 600 }}>{label}</span>
      <span style={{ color: "#1f2328" }}>{value}</span>
    </div>
  );
}

function useActionRunner() {
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");

  async function runAction(action: () => Promise<void>, successText: string) {
    try {
      setBusy(true);
      setMessage("");
      await action();
      setMessage(successText);
    } catch (error) {
      const text = error instanceof Error ? error.message : "Command failed";
      setMessage(text);
    } finally {
      setBusy(false);
    }
  }

  return { busy, message, runAction };
}

function PanelMessage({ message }: { message: string }) {
  return (
    <div
      style={{
        minHeight: "20px",
        marginTop: "12px",
        fontSize: "0.85rem",
        color:
          message.toLowerCase().includes("failed") ||
          message.toLowerCase().includes("error")
            ? "#cf222e"
            : "#1a7f37",
        wordBreak: "break-word",
      }}
    >
      {message}
    </div>
  );
}

function PowerControlCard({
  title,
  deviceKey,
  description,
  statePayload,
  onPowerOn,
  onPowerOff,
}: PowerControlCardProps) {
  const { busy, message, runAction } = useActionRunner();

  return (
    <div style={cardStyle}>
      <div style={titleStyle}>{title}</div>
      <div style={descriptionStyle}>{description}</div>

      <StatusRow label="Power" value={formatBoolean(statePayload?.power)} />
      <StatusRow label="Mode" value={formatText(statePayload?.mode)} />

      <div style={buttonRowStyle}>
        <button
          type="button"
          disabled={busy}
          onClick={() => runAction(onPowerOn, `${deviceKey} power-on command submitted.`)}
          style={buttonStyle}
        >
          Power On
        </button>

        <button
          type="button"
          disabled={busy}
          onClick={() => runAction(onPowerOff, `${deviceKey} power-off command submitted.`)}
          style={buttonStyle}
        >
          Power Off
        </button>
      </div>

      <PanelMessage message={message} />
    </div>
  );
}

function WavemakerControlCard({
  title,
  deviceKey,
  description,
  statePayload,
  onPowerOn,
  onPowerOff,
  onLow,
  onMedium,
  onHigh,
}: WavemakerControlCardProps) {
  const { busy, message, runAction } = useActionRunner();

  return (
    <div style={cardStyle}>
      <div style={titleStyle}>{title}</div>
      <div style={descriptionStyle}>{description}</div>

      <StatusRow label="Power" value={formatBoolean(statePayload?.power)} />
      <StatusRow label="Intensity" value={formatText(statePayload?.intensity)} />
      <StatusRow label="Mode" value={formatText(statePayload?.mode)} />

      <div style={buttonRowStyle}>
        <button
          type="button"
          disabled={busy}
          onClick={() => runAction(onPowerOn, `${deviceKey} power-on command submitted.`)}
          style={buttonStyle}
        >
          Power On
        </button>

        <button
          type="button"
          disabled={busy}
          onClick={() => runAction(onPowerOff, `${deviceKey} power-off command submitted.`)}
          style={buttonStyle}
        >
          Power Off
        </button>
      </div>

      <div style={buttonRowStyle}>
        <button
          type="button"
          disabled={busy}
          onClick={() => runAction(onLow, `${deviceKey} low intensity command submitted.`)}
          style={buttonStyle}
        >
          Low
        </button>

        <button
          type="button"
          disabled={busy}
          onClick={() => runAction(onMedium, `${deviceKey} medium intensity command submitted.`)}
          style={buttonStyle}
        >
          Medium
        </button>

        <button
          type="button"
          disabled={busy}
          onClick={() => runAction(onHigh, `${deviceKey} high intensity command submitted.`)}
          style={buttonStyle}
        >
          High
        </button>
      </div>

      <PanelMessage message={message} />
    </div>
  );
}

function FeederControlCard({
  title,
  deviceKey,
  description,
  statePayload,
  onFeed5,
  onFeed10,
}: FeederControlCardProps) {
  const { busy, message, runAction } = useActionRunner();

  return (
    <div style={cardStyle}>
      <div style={titleStyle}>{title}</div>
      <div style={descriptionStyle}>{description}</div>

      <StatusRow
        label="Last Feed Duration"
        value={
          statePayload?.last_feed_seconds !== undefined
            ? `${statePayload.last_feed_seconds} sec`
            : "Never"
        }
      />
      <StatusRow label="Mode" value={formatText(statePayload?.mode)} />
      <StatusRow
        label="Last Feed At"
        value={formatText(statePayload?.last_feed_at, "Unknown")}
      />

      <div style={buttonRowStyle}>
        <button
          type="button"
          disabled={busy}
          onClick={() => runAction(onFeed5, `${deviceKey} 5-second feed command submitted.`)}
          style={buttonStyle}
        >
          Feed 5s
        </button>

        <button
          type="button"
          disabled={busy}
          onClick={() => runAction(onFeed10, `${deviceKey} 10-second feed command submitted.`)}
          style={buttonStyle}
        >
          Feed 10s
        </button>
      </div>

      <PanelMessage message={message} />
    </div>
  );
}

const cardStyle: React.CSSProperties = {
  border: "1px solid #d0d7de",
  borderRadius: "12px",
  padding: "16px",
  background: "#ffffff",
  boxShadow: "0 1px 3px rgba(0,0,0,0.06)",
};

const titleStyle: React.CSSProperties = {
  fontSize: "1rem",
  fontWeight: 700,
  color: "#1f2328",
  marginBottom: "6px",
};

const descriptionStyle: React.CSSProperties = {
  fontSize: "0.85rem",
  color: "#57606a",
  marginBottom: "12px",
};

const buttonRowStyle: React.CSSProperties = {
  display: "flex",
  gap: "10px",
  flexWrap: "wrap",
  marginTop: "12px",
};

const buttonStyle: React.CSSProperties = {
  border: "1px solid #d0d7de",
  borderRadius: "8px",
  background: "#f6f8fa",
  color: "#1f2328",
  padding: "8px 12px",
  fontSize: "0.9rem",
  fontWeight: 600,
  cursor: "pointer",
};

export function ManualControlPanel({
  deviceStates,
  onCommandSent,
}: ManualControlPanelProps) {
  const deviceStateMap = new Map(deviceStates.map((item) => [item.device_key, item]));

  async function sendPowerCommand(
    targetDevice: string,
    power: boolean,
    reason: string
  ) {
    const result = await createManualCommand({
      requested_by: "dashboard.manual_control",
      target_device: targetDevice,
      command_type: "set_power",
      command_payload: {
        power,
        mode: "manual",
        reason,
      },
    });

    onCommandSent?.(result);
  }

  async function sendIntensityCommand(
    targetDevice: string,
    intensity: string,
    reason: string
  ) {
    const result = await createManualCommand({
      requested_by: "dashboard.manual_control",
      target_device: targetDevice,
      command_type: "set_intensity",
      command_payload: {
        power: true,
        intensity,
        mode: "manual",
        reason,
      },
    });

    onCommandSent?.(result);
  }

  async function sendFeedCommand(
    targetDevice: string,
    durationSeconds: number,
    reason: string
  ) {
    const requestedAt = new Date().toISOString();

    const result = await createManualCommand({
      requested_by: "dashboard.manual_control",
      target_device: targetDevice,
      command_type: "trigger_feed",
      command_payload: {
        duration_seconds: durationSeconds,
        mode: "manual",
        reason,
        requested_at: requestedAt,
      },
    });

    onCommandSent?.(result);
  }

  return (
    <div>
      <div style={{ marginBottom: "12px" }}>
        <h2
          style={{
            margin: 0,
            fontSize: "1.25rem",
            fontWeight: 700,
          }}
        >
          Manual Controls
        </h2>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
          gap: "16px",
          marginBottom: "24px",
        }}
      >
        <PowerControlCard
          title="Heater"
          deviceKey="heater_main"
          description="Manual power control for the primary heater."
          statePayload={deviceStateMap.get("heater_main")?.state_payload}
          onPowerOn={() => sendPowerCommand("heater_main", true, "manual_heater_on")}
          onPowerOff={() => sendPowerCommand("heater_main", false, "manual_heater_off")}
        />

        <PowerControlCard
          title="Main Return Pump"
          deviceKey="return_pump_main"
          description="Manual power control for the primary return pump."
          statePayload={deviceStateMap.get("return_pump_main")?.state_payload}
          onPowerOn={() =>
            sendPowerCommand("return_pump_main", true, "manual_return_pump_on")
          }
          onPowerOff={() =>
            sendPowerCommand("return_pump_main", false, "manual_return_pump_off")
          }
        />

        <PowerControlCard
          title="Lights"
          deviceKey="lights_main"
          description="Manual power control for the lighting system."
          statePayload={deviceStateMap.get("lights_main")?.state_payload}
          onPowerOn={() => sendPowerCommand("lights_main", true, "manual_lights_on")}
          onPowerOff={() => sendPowerCommand("lights_main", false, "manual_lights_off")}
        />

        <FeederControlCard
          title="Automatic Fish Feeder"
          deviceKey="feeder_main"
          description="Trigger a manual feeding cycle for the automatic feeder."
          statePayload={deviceStateMap.get("feeder_main")?.state_payload}
          onFeed5={() => sendFeedCommand("feeder_main", 5, "manual_feed_5_seconds")}
          onFeed10={() => sendFeedCommand("feeder_main", 10, "manual_feed_10_seconds")}
        />

        <WavemakerControlCard
          title="Wavemaker Left"
          deviceKey="wavemaker_left"
          description="Manual power and intensity control for the left wavemaker."
          statePayload={deviceStateMap.get("wavemaker_left")?.state_payload}
          onPowerOn={() => sendPowerCommand("wavemaker_left", true, "manual_wavemaker_left_on")}
          onPowerOff={() =>
            sendPowerCommand("wavemaker_left", false, "manual_wavemaker_left_off")
          }
          onLow={() => sendIntensityCommand("wavemaker_left", "low", "manual_wavemaker_left_low")}
          onMedium={() =>
            sendIntensityCommand("wavemaker_left", "medium", "manual_wavemaker_left_medium")
          }
          onHigh={() =>
            sendIntensityCommand("wavemaker_left", "high", "manual_wavemaker_left_high")
          }
        />

        <WavemakerControlCard
          title="Wavemaker Right"
          deviceKey="wavemaker_right"
          description="Manual power and intensity control for the right wavemaker."
          statePayload={deviceStateMap.get("wavemaker_right")?.state_payload}
          onPowerOn={() => sendPowerCommand("wavemaker_right", true, "manual_wavemaker_right_on")}
          onPowerOff={() =>
            sendPowerCommand("wavemaker_right", false, "manual_wavemaker_right_off")
          }
          onLow={() =>
            sendIntensityCommand("wavemaker_right", "low", "manual_wavemaker_right_low")
          }
          onMedium={() =>
            sendIntensityCommand("wavemaker_right", "medium", "manual_wavemaker_right_medium")
          }
          onHigh={() =>
            sendIntensityCommand("wavemaker_right", "high", "manual_wavemaker_right_high")
          }
        />
      </div>
    </div>
  );
}