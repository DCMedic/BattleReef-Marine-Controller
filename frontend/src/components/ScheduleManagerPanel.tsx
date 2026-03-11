import { useEffect, useMemo, useState } from "react";

import {
  createSchedule,
  fetchSchedules,
  seedDefaultSchedules,
  updateSchedule,
} from "../api/queries";
import type {
  ScheduleCreateRequest,
  ScheduleResponse,
  ScheduleUpdateRequest,
} from "../types";

type ScheduleManagerPanelProps = {
  refreshToken?: number;
};

type EditorMode = "create" | "edit";

type FormState = {
  id?: number;
  device_key: string;
  schedule_type: string;
  name: string;
  enabled: boolean;
  configText: string;
};

const defaultCreateState: FormState = {
  device_key: "",
  schedule_type: "lighting",
  name: "",
  enabled: true,
  configText: `{
  "start_hour_utc": 14,
  "end_hour_utc": 23,
  "power_on": true
}`,
};

export function ScheduleManagerPanel({
  refreshToken = 0,
}: ScheduleManagerPanelProps) {
  const [items, setItems] = useState<ScheduleResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [mode, setMode] = useState<EditorMode>("create");
  const [form, setForm] = useState<FormState>(defaultCreateState);

  async function loadSchedules() {
    try {
      setLoading(true);
      const data = await fetchSchedules();
      setItems(data.items);
      setMessage("");
    } catch (error) {
      const text = error instanceof Error ? error.message : "Failed to load schedules";
      setMessage(text);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadSchedules();
  }, [refreshToken]);

  const grouped = useMemo(() => {
    const map = new Map<string, ScheduleResponse[]>();

    for (const item of items) {
      const key = item.device_key;
      const current = map.get(key) ?? [];
      current.push(item);
      map.set(key, current);
    }

    return Array.from(map.entries()).sort((a, b) => a[0].localeCompare(b[0]));
  }, [items]);

  function resetForm() {
    setMode("create");
    setForm(defaultCreateState);
  }

  function populateEditForm(item: ScheduleResponse) {
    setMode("edit");
    setForm({
      id: item.id,
      device_key: item.device_key,
      schedule_type: item.schedule_type,
      name: item.name,
      enabled: item.enabled,
      configText: JSON.stringify(item.config_payload, null, 2),
    });
  }

  function updateForm<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  function parseConfigText(): Record<string, unknown> {
    const parsed = JSON.parse(form.configText);
    if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
      throw new Error("Config payload must be a JSON object.");
    }
    return parsed as Record<string, unknown>;
  }

  async function handleSeedDefaults() {
    try {
      setBusy(true);
      const result = await seedDefaultSchedules();
      setItems(result.items);
      setMessage("Default schedules loaded successfully.");
    } catch (error) {
      const text = error instanceof Error ? error.message : "Failed to seed schedules.";
      setMessage(text);
    } finally {
      setBusy(false);
    }
  }

  async function handleSubmit() {
    try {
      setBusy(true);
      setMessage("");

      const parsedConfig = parseConfigText();

      if (mode === "create") {
        const payload: ScheduleCreateRequest = {
          device_key: form.device_key.trim(),
          schedule_type: form.schedule_type.trim(),
          name: form.name.trim(),
          enabled: form.enabled,
          config_payload: parsedConfig,
        };

        const created = await createSchedule(payload);
        setItems((prev) => [...prev, created].sort((a, b) => a.id - b.id));
        setMessage(`Schedule created for ${created.device_key}.`);
        resetForm();
      } else {
        if (!form.id) {
          throw new Error("Missing schedule ID for edit.");
        }

        const payload: ScheduleUpdateRequest = {
          name: form.name.trim(),
          enabled: form.enabled,
          config_payload: parsedConfig,
        };

        const updated = await updateSchedule(form.id, payload);
        setItems((prev) =>
          prev.map((item) => (item.id === updated.id ? updated : item))
        );
        setMessage(`Schedule ${updated.id} updated successfully.`);
      }
    } catch (error) {
      const text = error instanceof Error ? error.message : "Failed to save schedule.";
      setMessage(text);
    } finally {
      setBusy(false);
    }
  }

  async function handleToggleEnabled(item: ScheduleResponse) {
    try {
      setBusy(true);
      setMessage("");

      const updated = await updateSchedule(item.id, {
        enabled: !item.enabled,
      });

      setItems((prev) =>
        prev.map((schedule) => (schedule.id === updated.id ? updated : schedule))
      );

      setMessage(
        `Schedule ${updated.id} ${updated.enabled ? "enabled" : "disabled"} successfully.`
      );
    } catch (error) {
      const text =
        error instanceof Error ? error.message : "Failed to toggle schedule.";
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
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: "12px",
          marginBottom: "12px",
          flexWrap: "wrap",
        }}
      >
        <div>
          <div
            style={{
              fontSize: "1rem",
              fontWeight: 700,
              color: "#1f2328",
            }}
          >
            Schedule Manager
          </div>
          <div
            style={{
              fontSize: "0.85rem",
              color: "#57606a",
              marginTop: "4px",
            }}
          >
            Create, review, enable, and edit persistent automation schedules.
          </div>
        </div>

        <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
          <button
            type="button"
            disabled={busy}
            onClick={handleSeedDefaults}
            style={buttonStyle}
          >
            Seed Defaults
          </button>

          <button
            type="button"
            disabled={busy}
            onClick={resetForm}
            style={buttonStyle}
          >
            New Schedule
          </button>
        </div>
      </div>

      <div
        style={{
          minHeight: "20px",
          marginBottom: "12px",
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

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "minmax(320px, 420px) 1fr",
          gap: "16px",
          alignItems: "start",
        }}
      >
        <div
          style={{
            border: "1px solid #d8dee4",
            borderRadius: "10px",
            padding: "16px",
            background: "#f6f8fa",
          }}
        >
          <div style={sectionTitleStyle}>
            {mode === "create" ? "Create Schedule" : `Edit Schedule #${form.id}`}
          </div>

          <label style={labelStyle}>
            Device Key
            <input
              type="text"
              value={form.device_key}
              onChange={(e) => updateForm("device_key", e.target.value)}
              disabled={mode === "edit" || busy}
              style={inputStyle}
              placeholder="lights_main"
            />
          </label>

          <label style={labelStyle}>
            Schedule Type
            <select
              value={form.schedule_type}
              onChange={(e) => updateForm("schedule_type", e.target.value)}
              disabled={mode === "edit" || busy}
              style={inputStyle}
            >
              <option value="lighting">lighting</option>
              <option value="feeding">feeding</option>
              <option value="flow">flow</option>
              <option value="pump">pump</option>
              <option value="custom">custom</option>
            </select>
          </label>

          <label style={labelStyle}>
            Schedule Name
            <input
              type="text"
              value={form.name}
              onChange={(e) => updateForm("name", e.target.value)}
              disabled={busy}
              style={inputStyle}
              placeholder="Primary Lighting Window"
            />
          </label>

          <label style={checkboxRowStyle}>
            <input
              type="checkbox"
              checked={form.enabled}
              onChange={(e) => updateForm("enabled", e.target.checked)}
              disabled={busy}
            />
            <span>Enabled</span>
          </label>

          <label style={labelStyle}>
            Config Payload (JSON)
            <textarea
              value={form.configText}
              onChange={(e) => updateForm("configText", e.target.value)}
              disabled={busy}
              style={textAreaStyle}
              spellCheck={false}
            />
          </label>

          <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
            <button
              type="button"
              disabled={busy}
              onClick={handleSubmit}
              style={buttonStyle}
            >
              {mode === "create" ? "Create Schedule" : "Save Changes"}
            </button>

            <button
              type="button"
              disabled={busy}
              onClick={resetForm}
              style={buttonStyle}
            >
              Reset
            </button>
          </div>
        </div>

        <div
          style={{
            border: "1px solid #d8dee4",
            borderRadius: "10px",
            padding: "16px",
            background: "#ffffff",
          }}
        >
          <div style={sectionTitleStyle}>Configured Schedules</div>

          {loading ? (
            <div style={{ color: "#57606a" }}>Loading schedules...</div>
          ) : grouped.length === 0 ? (
            <div style={{ color: "#57606a" }}>No schedules configured.</div>
          ) : (
            <div style={{ display: "grid", gap: "14px" }}>
              {grouped.map(([deviceKey, schedules]) => (
                <div
                  key={deviceKey}
                  style={{
                    border: "1px solid #d8dee4",
                    borderRadius: "10px",
                    padding: "12px",
                    background: "#f6f8fa",
                  }}
                >
                  <div
                    style={{
                      fontSize: "0.95rem",
                      fontWeight: 700,
                      color: "#1f2328",
                      marginBottom: "10px",
                    }}
                  >
                    {deviceKey}
                  </div>

                  <div style={{ display: "grid", gap: "10px" }}>
                    {schedules.map((item) => (
                      <div
                        key={item.id}
                        style={{
                          border: "1px solid #d8dee4",
                          borderRadius: "8px",
                          padding: "12px",
                          background: "#ffffff",
                        }}
                      >
                        <div
                          style={{
                            display: "flex",
                            justifyContent: "space-between",
                            alignItems: "start",
                            gap: "12px",
                            flexWrap: "wrap",
                          }}
                        >
                          <div>
                            <div
                              style={{
                                fontSize: "0.92rem",
                                fontWeight: 700,
                                color: "#1f2328",
                              }}
                            >
                              #{item.id} · {item.name}
                            </div>
                            <div
                              style={{
                                fontSize: "0.82rem",
                                color: "#57606a",
                                marginTop: "4px",
                              }}
                            >
                              Type: {item.schedule_type} · Enabled:{" "}
                              {item.enabled ? "True" : "False"}
                            </div>
                            <div
                              style={{
                                fontSize: "0.8rem",
                                color: "#57606a",
                                marginTop: "4px",
                              }}
                            >
                              Updated: {new Date(item.updated_at).toLocaleString()}
                            </div>
                          </div>

                          <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
                            <button
                              type="button"
                              disabled={busy}
                              onClick={() => populateEditForm(item)}
                              style={smallButtonStyle}
                            >
                              Edit
                            </button>

                            <button
                              type="button"
                              disabled={busy}
                              onClick={() => handleToggleEnabled(item)}
                              style={smallButtonStyle}
                            >
                              {item.enabled ? "Disable" : "Enable"}
                            </button>
                          </div>
                        </div>

                        <pre
                          style={{
                            marginTop: "10px",
                            marginBottom: 0,
                            padding: "10px",
                            borderRadius: "8px",
                            background: "#f6f8fa",
                            border: "1px solid #d8dee4",
                            fontSize: "0.78rem",
                            whiteSpace: "pre-wrap",
                            wordBreak: "break-word",
                            color: "#1f2328",
                          }}
                        >
                          {JSON.stringify(item.config_payload, null, 2)}
                        </pre>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

const sectionTitleStyle: React.CSSProperties = {
  fontSize: "1rem",
  fontWeight: 700,
  color: "#1f2328",
  marginBottom: "12px",
};

const labelStyle: React.CSSProperties = {
  display: "grid",
  gap: "6px",
  fontSize: "0.86rem",
  fontWeight: 600,
  color: "#1f2328",
  marginBottom: "12px",
};

const checkboxRowStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: "8px",
  fontSize: "0.86rem",
  fontWeight: 600,
  color: "#1f2328",
  marginBottom: "12px",
};

const inputStyle: React.CSSProperties = {
  width: "100%",
  border: "1px solid #d0d7de",
  borderRadius: "8px",
  padding: "8px 10px",
  fontSize: "0.9rem",
  background: "#ffffff",
  color: "#1f2328",
  boxSizing: "border-box",
};

const textAreaStyle: React.CSSProperties = {
  width: "100%",
  minHeight: "180px",
  border: "1px solid #d0d7de",
  borderRadius: "8px",
  padding: "10px",
  fontSize: "0.85rem",
  fontFamily: "Consolas, Monaco, monospace",
  background: "#ffffff",
  color: "#1f2328",
  boxSizing: "border-box",
  resize: "vertical",
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

const smallButtonStyle: React.CSSProperties = {
  border: "1px solid #d0d7de",
  borderRadius: "8px",
  background: "#f6f8fa",
  color: "#1f2328",
  padding: "6px 10px",
  fontSize: "0.82rem",
  fontWeight: 600,
  cursor: "pointer",
};