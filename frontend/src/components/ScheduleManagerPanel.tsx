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
type FriendlyScheduleType = "lighting" | "feeding" | "flow" | "pump" | "custom";

type FormState = {
  id?: number;
  device_key: string;
  schedule_type: FriendlyScheduleType;
  name: string;
  enabled: boolean;

  start_hour: string;
  start_minute: string;
  end_hour: string;
  end_minute: string;

  feed_hour: string;
  feed_minute: string;
  duration_seconds: string;

  day_start_hour: string;
  day_start_minute: string;
  day_end_hour: string;
  day_end_minute: string;
  day_intensity: string;
  night_intensity: string;

  advancedMode: boolean;
  configText: string;
};

const defaultCreateState: FormState = {
  device_key: "lights_main",
  schedule_type: "lighting",
  name: "Primary Lighting Window",
  enabled: true,

  start_hour: "14",
  start_minute: "00",
  end_hour: "23",
  end_minute: "00",

  feed_hour: "14",
  feed_minute: "00",
  duration_seconds: "5",

  day_start_hour: "12",
  day_start_minute: "00",
  day_end_hour: "23",
  day_end_minute: "00",
  day_intensity: "high",
  night_intensity: "low",

  advancedMode: false,
  configText: `{
  "start_hour_utc": 14,
  "end_hour_utc": 23,
  "power_on": true
}`,
};

function toInt(value: string, fallback: number): number {
  const parsed = Number.parseInt(value, 10);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function clampHour(value: string, fallback: number): number {
  const parsed = toInt(value, fallback);
  return Math.min(23, Math.max(0, parsed));
}

function clampMinute(value: string, fallback: number): number {
  const parsed = toInt(value, fallback);
  return Math.min(59, Math.max(0, parsed));
}

function timeStringFromHourMinute(hour: string, minute: string): string {
  const hh = String(clampHour(hour, 0)).padStart(2, "0");
  const mm = String(clampMinute(minute, 0)).padStart(2, "0");
  return `${hh}:${mm}`;
}

function hourMinuteToDecimalHour(hour: string, minute: string): number {
  const hh = clampHour(hour, 0);
  const mm = clampMinute(minute, 0);
  return hh + mm / 60;
}

function formatLocalFriendlyTime(hour: string, minute: string): string {
  const date = new Date();
  date.setHours(clampHour(hour, 0), clampMinute(minute, 0), 0, 0);
  return date.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
}

function buildConfigPayloadFromForm(form: FormState): Record<string, unknown> {
  switch (form.schedule_type) {
    case "lighting":
      return {
        start_hour_utc: hourMinuteToDecimalHour(form.start_hour, form.start_minute),
        end_hour_utc: hourMinuteToDecimalHour(form.end_hour, form.end_minute),
        power_on: true,
      };

    case "feeding":
      return {
        hour_utc: hourMinuteToDecimalHour(form.feed_hour, form.feed_minute),
        duration_seconds: toInt(form.duration_seconds, 5),
      };

    case "flow":
      return {
        day_start_hour_utc: hourMinuteToDecimalHour(form.day_start_hour, form.day_start_minute),
        day_end_hour_utc: hourMinuteToDecimalHour(form.day_end_hour, form.day_end_minute),
        day_intensity: form.day_intensity,
        night_intensity: form.night_intensity,
      };

    case "pump":
      return {
        start_hour_utc: hourMinuteToDecimalHour(form.start_hour, form.start_minute),
        end_hour_utc: hourMinuteToDecimalHour(form.end_hour, form.end_minute),
        power_on: true,
      };

    case "custom":
    default: {
      const parsed = JSON.parse(form.configText);
      if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
        throw new Error("Config payload must be a JSON object.");
      }
      return parsed as Record<string, unknown>;
    }
  }
}

function buildSummaryText(form: FormState): string {
  switch (form.schedule_type) {
    case "lighting":
      return `This schedule will turn ${form.device_key} on daily at ${formatLocalFriendlyTime(form.start_hour, form.start_minute)} and off at ${formatLocalFriendlyTime(form.end_hour, form.end_minute)}.`;

    case "feeding":
      return `This schedule will run ${form.device_key} daily at ${formatLocalFriendlyTime(form.feed_hour, form.feed_minute)} for ${toInt(form.duration_seconds, 5)} seconds.`;

    case "flow":
      return `This schedule will run ${form.device_key} in ${form.day_intensity} mode from ${formatLocalFriendlyTime(form.day_start_hour, form.day_start_minute)} to ${formatLocalFriendlyTime(form.day_end_hour, form.day_end_minute)}, then switch to ${form.night_intensity}.`;

    case "pump":
      return `This schedule will run ${form.device_key} between ${formatLocalFriendlyTime(form.start_hour, form.start_minute)} and ${formatLocalFriendlyTime(form.end_hour, form.end_minute)}.`;

    case "custom":
    default:
      return `This custom schedule will use the advanced JSON payload for ${form.device_key}.`;
  }
}

function inferScheduleType(value: string): FriendlyScheduleType {
  if (value === "lighting" || value === "feeding" || value === "flow" || value === "pump") {
    return value;
  }
  return "custom";
}

function populateFormFromSchedule(item: ScheduleResponse): FormState {
  const type = inferScheduleType(item.schedule_type);
  const config = item.config_payload ?? {};

  const startHour = Number(config.start_hour_utc ?? 14);
  const endHour = Number(config.end_hour_utc ?? 23);
  const feedHour = Number(config.hour_utc ?? 14);
  const dayStart = Number(config.day_start_hour_utc ?? 12);
  const dayEnd = Number(config.day_end_hour_utc ?? 23);

  function splitHour(value: number): { hour: string; minute: string } {
    const whole = Math.floor(value);
    const mins = Math.round((value - whole) * 60);
    return {
      hour: String(whole),
      minute: String(mins),
    };
  }

  const start = splitHour(startHour);
  const end = splitHour(endHour);
  const feed = splitHour(feedHour);
  const dayStartSplit = splitHour(dayStart);
  const dayEndSplit = splitHour(dayEnd);

  return {
    id: item.id,
    device_key: item.device_key,
    schedule_type: type,
    name: item.name,
    enabled: item.enabled,

    start_hour: start.hour,
    start_minute: start.minute,
    end_hour: end.hour,
    end_minute: end.minute,

    feed_hour: feed.hour,
    feed_minute: feed.minute,
    duration_seconds: String(config.duration_seconds ?? 5),

    day_start_hour: dayStartSplit.hour,
    day_start_minute: dayStartSplit.minute,
    day_end_hour: dayEndSplit.hour,
    day_end_minute: dayEndSplit.minute,
    day_intensity: String(config.day_intensity ?? "high"),
    night_intensity: String(config.night_intensity ?? "low"),

    advancedMode: false,
    configText: JSON.stringify(item.config_payload, null, 2),
  };
}

function ScheduleTypeBadge({ type }: { type: string }) {
  return (
    <span
      style={{
        display: "inline-block",
        border: "1px solid #d0d7de",
        borderRadius: "999px",
        padding: "4px 10px",
        fontSize: "0.75rem",
        fontWeight: 700,
        color: "#57606a",
        background: "#f6f8fa",
      }}
    >
      {type}
    </span>
  );
}

function ScheduleSummary({
  item,
  onEdit,
  onToggleEnabled,
  busy,
}: {
  item: ScheduleResponse;
  onEdit: (item: ScheduleResponse) => void;
  onToggleEnabled: (item: ScheduleResponse) => Promise<void>;
  busy: boolean;
}) {
  const config = item.config_payload ?? {};
  let summary = "Custom schedule configuration.";

  if (item.schedule_type === "lighting") {
    summary = `Turns on at ${config.start_hour_utc ?? "?"} and off at ${config.end_hour_utc ?? "?"}.`;
  } else if (item.schedule_type === "feeding") {
    summary = `Feeds at ${config.hour_utc ?? "?"} for ${config.duration_seconds ?? "?"} seconds.`;
  } else if (item.schedule_type === "flow") {
    summary = `Uses ${config.day_intensity ?? "?"} during the day and ${config.night_intensity ?? "?"} at night.`;
  } else if (item.schedule_type === "pump") {
    summary = `Runs between ${config.start_hour_utc ?? "?"} and ${config.end_hour_utc ?? "?"}.`;
  }

  return (
    <div
      style={{
        border: "1px solid #d8dee4",
        borderRadius: "10px",
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
              fontSize: "0.95rem",
              fontWeight: 700,
              color: "#1f2328",
              marginBottom: "6px",
            }}
          >
            #{item.id} · {item.name}
          </div>

          <div
            style={{
              display: "flex",
              gap: "8px",
              alignItems: "center",
              flexWrap: "wrap",
              marginBottom: "8px",
            }}
          >
            <ScheduleTypeBadge type={item.schedule_type} />
            <span
              style={{
                fontSize: "0.8rem",
                fontWeight: 700,
                color: item.enabled ? "#1a7f37" : "#cf222e",
              }}
            >
              {item.enabled ? "Enabled" : "Disabled"}
            </span>
          </div>

          <div
            style={{
              fontSize: "0.84rem",
              color: "#57606a",
              marginBottom: "6px",
            }}
          >
            {summary}
          </div>

          <div
            style={{
              fontSize: "0.8rem",
              color: "#57606a",
            }}
          >
            Updated: {new Date(item.updated_at).toLocaleString()}
          </div>
        </div>

        <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
          <button
            type="button"
            disabled={busy}
            onClick={() => onEdit(item)}
            style={smallButtonStyle}
          >
            Edit
          </button>

          <button
            type="button"
            disabled={busy}
            onClick={() => void onToggleEnabled(item)}
            style={smallButtonStyle}
          >
            {item.enabled ? "Disable" : "Enable"}
          </button>
        </div>
      </div>
    </div>
  );
}

function TimeFieldRow({
  label,
  hour,
  minute,
  onHourChange,
  onMinuteChange,
}: {
  label: string;
  hour: string;
  minute: string;
  onHourChange: (value: string) => void;
  onMinuteChange: (value: string) => void;
}) {
  return (
    <div style={{ marginBottom: "12px" }}>
      <div style={labelCaptionStyle}>{label}</div>
      <div style={{ display: "flex", gap: "8px" }}>
        <input
          type="number"
          min="0"
          max="23"
          value={hour}
          onChange={(e) => onHourChange(e.target.value)}
          style={inputStyle}
          placeholder="HH"
        />
        <input
          type="number"
          min="0"
          max="59"
          value={minute}
          onChange={(e) => onMinuteChange(e.target.value)}
          style={inputStyle}
          placeholder="MM"
        />
      </div>
      <div style={helperTextStyle}>
        Local time preview: {formatLocalFriendlyTime(hour, minute)}
      </div>
    </div>
  );
}

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

  function resetForm(nextType?: FriendlyScheduleType, nextDevice?: string) {
    setMode("create");
    setForm({
      ...defaultCreateState,
      schedule_type: nextType ?? defaultCreateState.schedule_type,
      device_key: nextDevice ?? defaultCreateState.device_key,
      name:
        nextType === "feeding"
          ? "Daily Feed"
          : nextType === "flow"
          ? "Flow Profile"
          : nextType === "pump"
          ? "Pump Window"
          : "Primary Lighting Window",
    });
  }

  function updateForm<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  function populateEditForm(item: ScheduleResponse) {
    setMode("edit");
    setForm(populateFormFromSchedule(item));
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

      const configPayload = form.advancedMode
        ? (() => {
            const parsed = JSON.parse(form.configText);
            if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
              throw new Error("Config payload must be a JSON object.");
            }
            return parsed as Record<string, unknown>;
          })()
        : buildConfigPayloadFromForm(form);

      if (mode === "create") {
        const payload: ScheduleCreateRequest = {
          device_key: form.device_key.trim(),
          schedule_type: form.schedule_type.trim(),
          name: form.name.trim(),
          enabled: form.enabled,
          config_payload: configPayload,
        };

        const created = await createSchedule(payload);
        setItems((prev) => [...prev, created].sort((a, b) => a.id - b.id));
        setMessage(`Schedule created for ${created.device_key}.`);
        resetForm(form.schedule_type, form.device_key);
      } else {
        if (!form.id) {
          throw new Error("Missing schedule ID for edit.");
        }

        const payload: ScheduleUpdateRequest = {
          name: form.name.trim(),
          enabled: form.enabled,
          config_payload: configPayload,
        };

        const updated = await updateSchedule(form.id, payload);
        setItems((prev) =>
          prev.map((item) => (item.id === updated.id ? updated : item))
        );
        setMessage(`Schedule ${updated.id} updated successfully.`);
        setForm(populateFormFromSchedule(updated));
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

  function renderEditorFields() {
    switch (form.schedule_type) {
      case "lighting":
        return (
          <>
            <TimeFieldRow
              label="Turn lights on at"
              hour={form.start_hour}
              minute={form.start_minute}
              onHourChange={(value) => updateForm("start_hour", value)}
              onMinuteChange={(value) => updateForm("start_minute", value)}
            />

            <TimeFieldRow
              label="Turn lights off at"
              hour={form.end_hour}
              minute={form.end_minute}
              onHourChange={(value) => updateForm("end_hour", value)}
              onMinuteChange={(value) => updateForm("end_minute", value)}
            />
          </>
        );

      case "feeding":
        return (
          <>
            <TimeFieldRow
              label="Feed at"
              hour={form.feed_hour}
              minute={form.feed_minute}
              onHourChange={(value) => updateForm("feed_hour", value)}
              onMinuteChange={(value) => updateForm("feed_minute", value)}
            />

            <label style={labelStyle}>
              Feed Duration (seconds)
              <input
                type="number"
                min="1"
                max="120"
                value={form.duration_seconds}
                onChange={(e) => updateForm("duration_seconds", e.target.value)}
                disabled={busy}
                style={inputStyle}
              />
            </label>
          </>
        );

      case "flow":
        return (
          <>
            <TimeFieldRow
              label="Day profile starts at"
              hour={form.day_start_hour}
              minute={form.day_start_minute}
              onHourChange={(value) => updateForm("day_start_hour", value)}
              onMinuteChange={(value) => updateForm("day_start_minute", value)}
            />

            <TimeFieldRow
              label="Day profile ends at"
              hour={form.day_end_hour}
              minute={form.day_end_minute}
              onHourChange={(value) => updateForm("day_end_hour", value)}
              onMinuteChange={(value) => updateForm("day_end_minute", value)}
            />

            <label style={labelStyle}>
              Day Intensity
              <select
                value={form.day_intensity}
                onChange={(e) => updateForm("day_intensity", e.target.value)}
                disabled={busy}
                style={inputStyle}
              >
                <option value="low">low</option>
                <option value="medium">medium</option>
                <option value="high">high</option>
              </select>
            </label>

            <label style={labelStyle}>
              Night Intensity
              <select
                value={form.night_intensity}
                onChange={(e) => updateForm("night_intensity", e.target.value)}
                disabled={busy}
                style={inputStyle}
              >
                <option value="low">low</option>
                <option value="medium">medium</option>
                <option value="high">high</option>
              </select>
            </label>
          </>
        );

      case "pump":
        return (
          <>
            <TimeFieldRow
              label="Pump starts at"
              hour={form.start_hour}
              minute={form.start_minute}
              onHourChange={(value) => updateForm("start_hour", value)}
              onMinuteChange={(value) => updateForm("start_minute", value)}
            />

            <TimeFieldRow
              label="Pump stops at"
              hour={form.end_hour}
              minute={form.end_minute}
              onHourChange={(value) => updateForm("end_hour", value)}
              onMinuteChange={(value) => updateForm("end_minute", value)}
            />
          </>
        );

      case "custom":
      default:
        return null;
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
            Create and manage lighting, feeding, flow, and pump schedules using simple operator forms.
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
            onClick={() => resetForm()}
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
          gridTemplateColumns: "minmax(340px, 460px) 1fr",
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
            Device
            <select
              value={form.device_key}
              onChange={(e) => updateForm("device_key", e.target.value)}
              disabled={mode === "edit" || busy}
              style={inputStyle}
            >
              <option value="lights_main">lights_main</option>
              <option value="feeder_main">feeder_main</option>
              <option value="wavemaker_left">wavemaker_left</option>
              <option value="wavemaker_right">wavemaker_right</option>
              <option value="return_pump_main">return_pump_main</option>
              <option value="heater_main">heater_main</option>
            </select>
          </label>

          <label style={labelStyle}>
            Schedule Type
            <select
              value={form.schedule_type}
              onChange={(e) =>
                updateForm("schedule_type", e.target.value as FriendlyScheduleType)
              }
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

          <div
            style={{
              border: "1px solid #d8dee4",
              borderRadius: "8px",
              padding: "12px",
              background: "#ffffff",
              marginBottom: "12px",
            }}
          >
            <div style={labelCaptionStyle}>Schedule Preview</div>
            <div style={{ fontSize: "0.85rem", color: "#57606a", lineHeight: 1.5 }}>
              {buildSummaryText(form)}
            </div>
          </div>

          {renderEditorFields()}

          <label style={checkboxRowStyle}>
            <input
              type="checkbox"
              checked={form.advancedMode}
              onChange={(e) => updateForm("advancedMode", e.target.checked)}
              disabled={busy}
            />
            <span>Advanced JSON mode</span>
          </label>

          {form.advancedMode ? (
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
          ) : null}

          <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
            <button
              type="button"
              disabled={busy}
              onClick={() => void handleSubmit()}
              style={buttonStyle}
            >
              {mode === "create" ? "Create Schedule" : "Save Changes"}
            </button>

            <button
              type="button"
              disabled={busy}
              onClick={() => resetForm(form.schedule_type, form.device_key)}
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
                      <ScheduleSummary
                        key={item.id}
                        item={item}
                        onEdit={populateEditForm}
                        onToggleEnabled={handleToggleEnabled}
                        busy={busy}
                      />
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

const labelCaptionStyle: React.CSSProperties = {
  fontSize: "0.84rem",
  fontWeight: 700,
  color: "#1f2328",
  marginBottom: "6px",
};

const helperTextStyle: React.CSSProperties = {
  fontSize: "0.78rem",
  color: "#57606a",
  marginTop: "6px",
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