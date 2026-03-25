import { useEffect, useState } from "react";

import {
  applyThresholdPreset,
  clearActiveThresholdPreset,
  fetchThresholdPresets,
  fetchThresholds,
  resetThreshold,
  updateThreshold,
} from "../api/queries";
import type {
  ThresholdConfigItem,
  ThresholdListResponse,
  ThresholdPresetItem,
  ThresholdPresetListResponse,
} from "../types/thresholds";

type EditableThresholdState = {
  min: string;
  max: string;
  severity: "warning" | "critical";
  enabled: boolean;
};

function toEditableState(item: ThresholdConfigItem): EditableThresholdState {
  return {
    min: item.min === null ? "" : String(item.min),
    max: item.max === null ? "" : String(item.max),
    severity: item.severity,
    enabled: item.enabled,
  };
}

function pageCard(children: React.ReactNode): JSX.Element {
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

function PresetCard({
  item,
  onApply,
  busy,
}: {
  item: ThresholdPresetItem;
  onApply: (presetKey: string) => Promise<void>;
  busy: boolean;
}) {
  return (
    <article
      style={{
        border: item.active ? "1px solid #0969da" : "1px solid #e5e7eb",
        background: item.active ? "#eff6ff" : "#ffffff",
        borderRadius: 14,
        padding: 18,
      }}
    >
      <div style={{ display: "grid", gap: 12 }}>
        <div>
          <div style={{ fontSize: 18, fontWeight: 800, color: "#111827" }}>{item.label}</div>
          <div style={{ color: "#6b7280", marginTop: 6, lineHeight: 1.5 }}>{item.description}</div>
        </div>

        <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
          <span
            style={{
              border: "1px solid #d1d5db",
              borderRadius: 999,
              padding: "4px 10px",
              fontSize: 12,
              fontWeight: 700,
              background: "#f9fafb",
              color: "#374151",
            }}
          >
            {item.threshold_count} thresholds
          </span>

          {item.active ? (
            <span
              style={{
                border: "1px solid #93c5fd",
                borderRadius: 999,
                padding: "4px 10px",
                fontSize: 12,
                fontWeight: 700,
                background: "#dbeafe",
                color: "#1d4ed8",
              }}
            >
              Active
            </span>
          ) : null}
        </div>

        <div>
          <button
            onClick={() => void onApply(item.key)}
            disabled={busy}
            style={{
              border: "1px solid #0969da",
              borderRadius: 10,
              padding: "10px 14px",
              background: item.active ? "#ffffff" : "#0969da",
              color: item.active ? "#0969da" : "#ffffff",
              fontWeight: 700,
              cursor: busy ? "not-allowed" : "pointer",
              opacity: busy ? 0.7 : 1,
            }}
          >
            {item.active ? "Reapply Preset" : "Apply Preset"}
          </button>
        </div>
      </div>
    </article>
  );
}

function ThresholdCard({
  item,
  onSave,
  onReset,
}: {
  item: ThresholdConfigItem;
  onSave: (sensorKey: string, next: EditableThresholdState) => Promise<void>;
  onReset: (sensorKey: string) => Promise<void>;
}) {
  const [form, setForm] = useState<EditableThresholdState>(toEditableState(item));
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    setForm(toEditableState(item));
  }, [item]);

  async function handleSave() {
    setBusy(true);
    setMessage(null);

    try {
      await onSave(item.sensor_key, form);
      setMessage("Threshold saved.");
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Failed to save threshold");
    } finally {
      setBusy(false);
    }
  }

  async function handleReset() {
    setBusy(true);
    setMessage(null);

    try {
      await onReset(item.sensor_key);
      setMessage("Threshold reset to default.");
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Failed to reset threshold");
    } finally {
      setBusy(false);
    }
  }

  return (
    <article
      style={{
        border: "1px solid #e5e7eb",
        borderRadius: 14,
        padding: 18,
        background: "#ffffff",
      }}
    >
      <div style={{ display: "grid", gap: 14 }}>
        <div>
          <div style={{ fontSize: 18, fontWeight: 800, color: "#111827" }}>{item.label}</div>
          <div style={{ color: "#6b7280", marginTop: 4 }}>
            Sensor key: {item.sensor_key} {item.unit ? `· Unit: ${item.unit}` : ""}
          </div>
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(4, minmax(0, 1fr))",
            gap: 12,
          }}
        >
          <label style={{ display: "grid", gap: 6 }}>
            <span style={{ fontSize: 13, fontWeight: 700, color: "#374151" }}>Minimum</span>
            <input
              value={form.min}
              onChange={(event) => setForm((current) => ({ ...current, min: event.target.value }))}
              style={{
                border: "1px solid #d1d5db",
                borderRadius: 10,
                padding: "10px 12px",
                font: "inherit",
              }}
              placeholder="Disabled"
            />
          </label>

          <label style={{ display: "grid", gap: 6 }}>
            <span style={{ fontSize: 13, fontWeight: 700, color: "#374151" }}>Maximum</span>
            <input
              value={form.max}
              onChange={(event) => setForm((current) => ({ ...current, max: event.target.value }))}
              style={{
                border: "1px solid #d1d5db",
                borderRadius: 10,
                padding: "10px 12px",
                font: "inherit",
              }}
              placeholder="Disabled"
            />
          </label>

          <label style={{ display: "grid", gap: 6 }}>
            <span style={{ fontSize: 13, fontWeight: 700, color: "#374151" }}>Severity</span>
            <select
              value={form.severity}
              onChange={(event) =>
                setForm((current) => ({
                  ...current,
                  severity: event.target.value as "warning" | "critical",
                }))
              }
              style={{
                border: "1px solid #d1d5db",
                borderRadius: 10,
                padding: "10px 12px",
                font: "inherit",
                background: "#ffffff",
              }}
            >
              <option value="warning">warning</option>
              <option value="critical">critical</option>
            </select>
          </label>

          <label style={{ display: "grid", gap: 6 }}>
            <span style={{ fontSize: 13, fontWeight: 700, color: "#374151" }}>Enabled</span>
            <div
              style={{
                border: "1px solid #d1d5db",
                borderRadius: 10,
                padding: "10px 12px",
                display: "flex",
                alignItems: "center",
                gap: 10,
                minHeight: 42,
              }}
            >
              <input
                type="checkbox"
                checked={form.enabled}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    enabled: event.target.checked,
                  }))
                }
              />
              <span>{form.enabled ? "Enabled" : "Disabled"}</span>
            </div>
          </label>
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
            gap: 12,
            fontSize: 13,
            color: "#6b7280",
          }}
        >
          <div>
            Default min: {String((item.default["min"] as number | null | undefined) ?? "disabled")}
          </div>
          <div>
            Default max: {String((item.default["max"] as number | null | undefined) ?? "disabled")}
          </div>
          <div>Default severity: {String(item.default["severity"] ?? "warning")}</div>
          <div>Override active: {item.has_override ? "Yes" : "No"}</div>
        </div>

        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          <button
            onClick={() => void handleSave()}
            disabled={busy}
            style={{
              border: "1px solid #0969da",
              borderRadius: 10,
              padding: "10px 14px",
              background: "#0969da",
              color: "#ffffff",
              fontWeight: 700,
              cursor: busy ? "not-allowed" : "pointer",
              opacity: busy ? 0.7 : 1,
            }}
          >
            Save
          </button>

          <button
            onClick={() => void handleReset()}
            disabled={busy}
            style={{
              border: "1px solid #d1d5db",
              borderRadius: 10,
              padding: "10px 14px",
              background: "#ffffff",
              color: "#111827",
              fontWeight: 700,
              cursor: busy ? "not-allowed" : "pointer",
              opacity: busy ? 0.7 : 1,
            }}
          >
            Reset to Default
          </button>
        </div>

        {message ? (
          <div
            style={{
              border: "1px solid #e5e7eb",
              borderRadius: 10,
              padding: "10px 12px",
              background: "#f9fafb",
              color: "#374151",
              fontWeight: 600,
            }}
          >
            {message}
          </div>
        ) : null}
      </div>
    </article>
  );
}

export default function ThresholdsPage() {
  const [data, setData] = useState<ThresholdListResponse | null>(null);
  const [presets, setPresets] = useState<ThresholdPresetListResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [presetBusy, setPresetBusy] = useState(false);
  const [presetMessage, setPresetMessage] = useState<string | null>(null);

  async function load() {
    try {
      const [thresholdResponse, presetResponse] = await Promise.all([
        fetchThresholds(),
        fetchThresholdPresets(),
      ]);

      setData(thresholdResponse);
      setPresets(presetResponse);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load threshold configuration");
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function handleSave(sensorKey: string, next: EditableThresholdState) {
    const parseValue = (value: string): number | null => {
      const cleaned = value.trim();
      if (!cleaned) {
        return null;
      }

      const parsed = Number(cleaned);
      if (Number.isNaN(parsed)) {
        throw new Error("Threshold values must be numeric or blank.");
      }

      return parsed;
    };

    await updateThreshold(sensorKey, {
      min: parseValue(next.min),
      max: parseValue(next.max),
      severity: next.severity,
      enabled: next.enabled,
    });

    await load();
  }

  async function handleReset(sensorKey: string) {
    await resetThreshold(sensorKey);
    await load();
  }

  async function handleApplyPreset(presetKey: string) {
    setPresetBusy(true);
    setPresetMessage(null);

    try {
      const result = await applyThresholdPreset(presetKey);
      setPresetMessage(`Applied preset: ${result.label}.`);
      await load();
    } catch (err) {
      setPresetMessage(err instanceof Error ? err.message : "Failed to apply preset");
    } finally {
      setPresetBusy(false);
    }
  }

  async function handleClearPreset() {
    setPresetBusy(true);
    setPresetMessage(null);

    try {
      await clearActiveThresholdPreset();
      setPresetMessage("Cleared active preset marker. Existing overrides remain in place.");
      await load();
    } catch (err) {
      setPresetMessage(err instanceof Error ? err.message : "Failed to clear active preset");
    } finally {
      setPresetBusy(false);
    }
  }

  return (
    <div style={{ display: "grid", gap: 16, padding: 24, maxWidth: 1400, margin: "0 auto" }}>
      {pageCard(
        <div>
          <h1 style={{ margin: 0, fontSize: 28 }}>Threshold Configuration</h1>
          <p style={{ margin: "8px 0 0 0", color: "#4b5563", lineHeight: 1.6 }}>
            Tune sensor-specific alert thresholds without editing environment variables or code.
            Apply presets for common system types, then fine-tune individual boundaries as needed.
          </p>
        </div>
      )}

      {error ? (
        <section
          style={{
            background: "#fff1f2",
            border: "1px solid #fecdd3",
            borderRadius: 16,
            padding: 16,
            color: "#9f1239",
          }}
        >
          {error}
        </section>
      ) : null}

      {pageCard(
        <div style={{ display: "grid", gap: 16 }}>
          <div>
            <h2 style={{ margin: 0, fontSize: 22 }}>Threshold Presets</h2>
            <p style={{ margin: "8px 0 0 0", color: "#6b7280", lineHeight: 1.6 }}>
              Switch operational baselines in one click for different aquarium system types.
            </p>
          </div>

          <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
            <span
              style={{
                border: "1px solid #d1d5db",
                borderRadius: 999,
                padding: "4px 10px",
                fontSize: 12,
                fontWeight: 700,
                background: "#f9fafb",
                color: "#374151",
              }}
            >
              Active profile: {presets?.active_profile ?? "none"}
            </span>

            <button
              onClick={() => void handleClearPreset()}
              disabled={presetBusy}
              style={{
                border: "1px solid #d1d5db",
                borderRadius: 10,
                padding: "10px 14px",
                background: "#ffffff",
                color: "#111827",
                fontWeight: 700,
                cursor: presetBusy ? "not-allowed" : "pointer",
                opacity: presetBusy ? 0.7 : 1,
              }}
            >
              Clear Active Profile Marker
            </button>
          </div>

          {presetMessage ? (
            <div
              style={{
                border: "1px solid #e5e7eb",
                borderRadius: 10,
                padding: "10px 12px",
                background: "#f9fafb",
                color: "#374151",
                fontWeight: 600,
              }}
            >
              {presetMessage}
            </div>
          ) : null}

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
              gap: 16,
            }}
          >
            {(presets?.items ?? []).map((item) => (
              <PresetCard
                key={item.key}
                item={item}
                onApply={handleApplyPreset}
                busy={presetBusy}
              />
            ))}
          </div>
        </div>
      )}

      <div style={{ display: "grid", gap: 16 }}>
        {(data?.items ?? []).map((item) => (
          <ThresholdCard
            key={item.sensor_key}
            item={item}
            onSave={handleSave}
            onReset={handleReset}
          />
        ))}
      </div>
    </div>
  );
}