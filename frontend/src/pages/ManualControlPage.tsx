import { useMemo, useState } from "react";

import { createManualCommand, setDeviceMode } from "../api/queries";
import { useLiveDeviceState } from "../hooks/useLiveDeviceState";
import type { CommandCreateRequest } from "../types";

type DeviceDefinition = {
  deviceKey: string;
  title: string;
  description: string;
  kind: "power" | "feeder" | "wavemaker";
};

const DEVICES: DeviceDefinition[] = [
  {
    deviceKey: "heater_main",
    title: "Heater",
    description: "Primary aquarium heater control and mode management.",
    kind: "power",
  },
  {
    deviceKey: "return_pump_main",
    title: "Main Return Pump",
    description: "Controls return flow from sump to display tank.",
    kind: "power",
  },
  {
    deviceKey: "lights_main",
    title: "Lights",
    description: "Primary lighting channel for the aquarium display.",
    kind: "power",
  },
  {
    deviceKey: "feeder_main",
    title: "Automatic Fish Feeder",
    description: "Manual feeding trigger with live state monitoring.",
    kind: "feeder",
  },
  {
    deviceKey: "wavemaker_left",
    title: "Wavemaker Left",
    description: "Left-side flow device with intensity control.",
    kind: "wavemaker",
  },
  {
    deviceKey: "wavemaker_right",
    title: "Wavemaker Right",
    description: "Right-side flow device with intensity control.",
    kind: "wavemaker",
  },
];

function sectionCard(children: React.ReactNode): JSX.Element {
  return (
    <section
      style={{
        background: "#ffffff",
        border: "1px solid #e5e7eb",
        borderRadius: 16,
        padding: 20,
        boxShadow: "0 1px 3px rgba(0,0,0,0.06)",
      }}
    >
      {children}
    </section>
  );
}

function pillStyle(tone: "default" | "success" | "warning" | "danger"): React.CSSProperties {
  if (tone === "success") {
    return {
      background: "#dafbe1",
      color: "#1a7f37",
      border: "1px solid #4ac26b66",
    };
  }

  if (tone === "warning") {
    return {
      background: "#fff8c5",
      color: "#9a6700",
      border: "1px solid #d4a72c66",
    };
  }

  if (tone === "danger") {
    return {
      background: "#ffebe9",
      color: "#cf222e",
      border: "1px solid #ff818266",
    };
  }

  return {
    background: "#f6f8fa",
    color: "#57606a",
    border: "1px solid #d0d7de",
  };
}

function StatusPill({
  label,
  tone,
}: {
  label: string;
  tone: "default" | "success" | "warning" | "danger";
}) {
  return (
    <span
      style={{
        ...pillStyle(tone),
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        borderRadius: 999,
        padding: "4px 10px",
        fontSize: 12,
        fontWeight: 800,
      }}
    >
      {label}
    </span>
  );
}

function ActionButton({
  label,
  onClick,
  disabled,
  tone = "default",
}: {
  label: string;
  onClick: () => void;
  disabled?: boolean;
  tone?: "default" | "primary" | "danger";
}) {
  const styles =
    tone === "primary"
      ? {
          background: "#0969da",
          color: "#ffffff",
          border: "1px solid #0969da",
        }
      : tone === "danger"
      ? {
          background: "#cf222e",
          color: "#ffffff",
          border: "1px solid #cf222e",
        }
      : {
          background: "#ffffff",
          color: "#1f2328",
          border: "1px solid #d0d7de",
        };

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      style={{
        ...styles,
        borderRadius: 10,
        padding: "10px 14px",
        fontWeight: 700,
        cursor: disabled ? "not-allowed" : "pointer",
        opacity: disabled ? 0.6 : 1,
      }}
    >
      {label}
    </button>
  );
}

function boolFromPayload(value: unknown): boolean | null {
  if (typeof value === "boolean") {
    return value;
  }

  if (typeof value === "string") {
    if (value.toLowerCase() === "true" || value.toLowerCase() === "on") {
      return true;
    }
    if (value.toLowerCase() === "false" || value.toLowerCase() === "off") {
      return false;
    }
  }

  return null;
}

function DeviceControlCard({ device }: { device: DeviceDefinition }) {
  const { state, loading, error, refresh, pulseRefresh } = useLiveDeviceState(device.deviceKey);

  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [intensityInput, setIntensityInput] = useState("50");

  const payload = state?.state_payload ?? {};
  const mode = (payload["mode"] as string | undefined) ?? "auto";
  const powerValue = boolFromPayload(payload["power"]);
  const applied = payload["applied"];
  const lastCommandId = payload["last_command_id"];
  const intensity = payload["intensity"];
  const updatedAt = state?.updated_at ? new Date(state.updated_at).toLocaleString() : "—";

  const onlineTone = error ? "danger" : loading ? "warning" : "success";
  const powerTone =
    powerValue === true ? "success" : powerValue === false ? "default" : "warning";

  const modeTone = mode === "manual" ? "warning" : "success";

  async function execute(payload: CommandCreateRequest, successMessage: string) {
    setBusy(true);
    setMessage(null);

    try {
      await createManualCommand(payload);
      setMessage(successMessage);
      await refresh();
      pulseRefresh();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Command failed");
    } finally {
      setBusy(false);
    }
  }

  async function changeMode(nextMode: "auto" | "manual") {
    setBusy(true);
    setMessage(null);

    try {
      await setDeviceMode(device.deviceKey, nextMode);
      setMessage(`Mode set to ${nextMode}.`);
      await refresh();
      pulseRefresh();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Failed to update mode");
    } finally {
      setBusy(false);
    }
  }

  const isManual = mode === "manual";

  const details = useMemo(() => {
    return Object.entries(payload)
      .filter(([key]) => !["mode", "power", "applied", "last_command_id"].includes(key))
      .map(([key, value]) => `${key}: ${String(value)}`);
  }, [payload]);

  return sectionCard(
    <div style={{ display: "grid", gap: 16 }}>
      <div style={{ display: "grid", gap: 6 }}>
        <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
          <div>
            <div style={{ fontSize: 20, fontWeight: 800 }}>{device.title}</div>
            <div style={{ color: "#57606a", marginTop: 4 }}>{device.description}</div>
          </div>

          <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "flex-start" }}>
            <StatusPill label={error ? "Unreachable" : loading ? "Syncing" : "Live"} tone={onlineTone} />
            <StatusPill label={`Mode: ${mode}`} tone={modeTone} />
            <StatusPill
              label={
                powerValue === true ? "Power: On" : powerValue === false ? "Power: Off" : "Power: Unknown"
              }
              tone={powerTone}
            />
          </div>
        </div>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(4, minmax(0, 1fr))",
          gap: 12,
        }}
      >
        <div
          style={{
            border: "1px solid #d8dee4",
            borderRadius: 12,
            padding: 12,
            background: "#f6f8fa",
          }}
        >
          <div style={{ fontSize: 12, color: "#57606a", fontWeight: 700 }}>Updated</div>
          <div style={{ marginTop: 6, fontWeight: 700 }}>{updatedAt}</div>
        </div>

        <div
          style={{
            border: "1px solid #d8dee4",
            borderRadius: 12,
            padding: 12,
            background: "#f6f8fa",
          }}
        >
          <div style={{ fontSize: 12, color: "#57606a", fontWeight: 700 }}>Applied</div>
          <div style={{ marginTop: 6, fontWeight: 700 }}>{String(applied ?? "—")}</div>
        </div>

        <div
          style={{
            border: "1px solid #d8dee4",
            borderRadius: 12,
            padding: 12,
            background: "#f6f8fa",
          }}
        >
          <div style={{ fontSize: 12, color: "#57606a", fontWeight: 700 }}>Last Command ID</div>
          <div style={{ marginTop: 6, fontWeight: 700 }}>{String(lastCommandId ?? "—")}</div>
        </div>

        <div
          style={{
            border: "1px solid #d8dee4",
            borderRadius: 12,
            padding: 12,
            background: "#f6f8fa",
          }}
        >
          <div style={{ fontSize: 12, color: "#57606a", fontWeight: 700 }}>
            {device.kind === "wavemaker" ? "Intensity" : "Device Key"}
          </div>
          <div style={{ marginTop: 6, fontWeight: 700 }}>
            {device.kind === "wavemaker" ? String(intensity ?? "—") : device.deviceKey}
          </div>
        </div>
      </div>

      {details.length > 0 ? (
        <div
          style={{
            border: "1px solid #d8dee4",
            borderRadius: 12,
            padding: 12,
            background: "#f6f8fa",
          }}
        >
          <div style={{ fontSize: 12, color: "#57606a", fontWeight: 700, marginBottom: 8 }}>
            Additional State
          </div>
          <div style={{ display: "grid", gap: 6, color: "#1f2328", fontSize: 14 }}>
            {details.map((item) => (
              <div key={item}>{item}</div>
            ))}
          </div>
        </div>
      ) : null}

      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          gap: 12,
          flexWrap: "wrap",
          alignItems: "center",
        }}
      >
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          <ActionButton
            label="Set Auto"
            onClick={() => void changeMode("auto")}
            disabled={busy || mode === "auto"}
          />
          <ActionButton
            label="Set Manual"
            onClick={() => void changeMode("manual")}
            disabled={busy || mode === "manual"}
            tone="primary"
          />
        </div>

        <div style={{ color: "#57606a", fontSize: 13 }}>
          Live backend state refreshes every 4 seconds. Command actions temporarily increase refresh speed.
        </div>
      </div>

      {device.kind === "power" ? (
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          <ActionButton
            label="Power On"
            tone="primary"
            disabled={busy || !isManual}
            onClick={() =>
              void execute(
                {
                  requested_by: "ui.manual_control",
                  target_device: device.deviceKey,
                  command_type: "set_power",
                  command_payload: { power: true },
                },
                `${device.title} power-on command queued.`
              )
            }
          />
          <ActionButton
            label="Power Off"
            tone="danger"
            disabled={busy || !isManual}
            onClick={() =>
              void execute(
                {
                  requested_by: "ui.manual_control",
                  target_device: device.deviceKey,
                  command_type: "set_power",
                  command_payload: { power: false },
                },
                `${device.title} power-off command queued.`
              )
            }
          />
        </div>
      ) : null}

      {device.kind === "feeder" ? (
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          <ActionButton
            label="Feed Now"
            tone="primary"
            disabled={busy || !isManual}
            onClick={() =>
              void execute(
                {
                  requested_by: "ui.manual_control",
                  target_device: device.deviceKey,
                  command_type: "trigger",
                  command_payload: { action: "feed", duration_seconds: 3 },
                },
                "Feeding command queued."
              )
            }
          />
        </div>
      ) : null}

      {device.kind === "wavemaker" ? (
        <div style={{ display: "grid", gap: 12 }}>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
            <label style={{ fontWeight: 700, color: "#1f2328" }}>Intensity %</label>
            <input
              type="number"
              min={0}
              max={100}
              value={intensityInput}
              onChange={(event) => setIntensityInput(event.target.value)}
              style={{
                width: 100,
                border: "1px solid #d0d7de",
                borderRadius: 10,
                padding: "10px 12px",
                font: "inherit",
              }}
            />
            <ActionButton
              label="Apply Intensity"
              tone="primary"
              disabled={busy || !isManual}
              onClick={() =>
                void execute(
                  {
                    requested_by: "ui.manual_control",
                    target_device: device.deviceKey,
                    command_type: "set_intensity",
                    command_payload: {
                      intensity: Number(intensityInput),
                      power: Number(intensityInput) > 0,
                    },
                  },
                  `${device.title} intensity command queued.`
                )
              }
            />
          </div>

          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            <ActionButton
              label="Stop"
              tone="danger"
              disabled={busy || !isManual}
              onClick={() =>
                void execute(
                  {
                    requested_by: "ui.manual_control",
                    target_device: device.deviceKey,
                    command_type: "set_intensity",
                    command_payload: { intensity: 0, power: false },
                  },
                  `${device.title} stop command queued.`
                )
              }
            />
            <ActionButton
              label="Low Flow"
              disabled={busy || !isManual}
              onClick={() => {
                setIntensityInput("30");
                void execute(
                  {
                    requested_by: "ui.manual_control",
                    target_device: device.deviceKey,
                    command_type: "set_intensity",
                    command_payload: { intensity: 30, power: true },
                  },
                  `${device.title} low-flow command queued.`
                );
              }}
            />
            <ActionButton
              label="Medium Flow"
              disabled={busy || !isManual}
              onClick={() => {
                setIntensityInput("60");
                void execute(
                  {
                    requested_by: "ui.manual_control",
                    target_device: device.deviceKey,
                    command_type: "set_intensity",
                    command_payload: { intensity: 60, power: true },
                  },
                  `${device.title} medium-flow command queued.`
                );
              }}
            />
            <ActionButton
              label="High Flow"
              disabled={busy || !isManual}
              onClick={() => {
                setIntensityInput("90");
                void execute(
                  {
                    requested_by: "ui.manual_control",
                    target_device: device.deviceKey,
                    command_type: "set_intensity",
                    command_payload: { intensity: 90, power: true },
                  },
                  `${device.title} high-flow command queued.`
                );
              }}
            />
          </div>
        </div>
      ) : null}

      {!isManual ? (
        <div
          style={{
            border: "1px solid #d4a72c66",
            borderRadius: 12,
            background: "#fff8c5",
            color: "#9a6700",
            padding: 12,
            fontWeight: 700,
          }}
        >
          Manual action buttons are disabled while this device remains in auto mode.
        </div>
      ) : null}

      {message ? (
        <div
          style={{
            border: "1px solid #d8dee4",
            borderRadius: 12,
            background: "#f6f8fa",
            color: "#1f2328",
            padding: 12,
            fontWeight: 600,
          }}
        >
          {message}
        </div>
      ) : null}

      {error ? (
        <div
          style={{
            border: "1px solid #ff818266",
            borderRadius: 12,
            background: "#ffebe9",
            color: "#cf222e",
            padding: 12,
            fontWeight: 700,
          }}
        >
          {error}
        </div>
      ) : null}
    </div>
  );
}

export default function ManualControlPage() {
  return (
    <div style={{ display: "grid", gap: 16, padding: 24, maxWidth: 1400, margin: "0 auto" }}>
      {sectionCard(
        <div>
          <h1 style={{ margin: 0, fontSize: 28 }}>Manual Control</h1>
          <p style={{ margin: "8px 0 0 0", color: "#57606a", lineHeight: 1.6 }}>
            Directly control aquarium devices and observe live backend device-state feedback.
            Switch devices between auto and manual mode, issue commands, and watch state updates
            synchronize in near real time.
          </p>
        </div>
      )}

      <div style={{ display: "grid", gap: 16 }}>
        {DEVICES.map((device) => (
          <DeviceControlCard key={device.deviceKey} device={device} />
        ))}
      </div>
    </div>
  );
}