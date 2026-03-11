import { useEffect, useMemo, useState } from "react";

import { fetchSchedules } from "../api/queries";
import type { ScheduleResponse } from "../types";

type WeeklyScheduleTimelineProps = {
  refreshToken?: number;
};

type TimelineBlock = {
  id: string;
  deviceKey: string;
  scheduleName: string;
  scheduleType: string;
  enabled: boolean;
  startHour: number;
  endHour: number;
  label: string;
  isPointEvent?: boolean;
};

const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const HOURS = Array.from({ length: 24 }, (_, i) => i);

function normalizeHour(value: unknown, fallback: number): number {
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) return fallback;
  return Math.min(24, Math.max(0, parsed));
}

function inferBlocks(schedule: ScheduleResponse): TimelineBlock[] {
  const config = schedule.config_payload ?? {};
  const blocks: TimelineBlock[] = [];

  if (schedule.schedule_type === "lighting" || schedule.schedule_type === "pump") {
    const start = normalizeHour(config.start_hour_utc, 14);
    const end = normalizeHour(config.end_hour_utc, 23);

    for (const day of DAYS) {
      blocks.push({
        id: `${schedule.id}-${day}`,
        deviceKey: schedule.device_key,
        scheduleName: schedule.name,
        scheduleType: schedule.schedule_type,
        enabled: schedule.enabled,
        startHour: start,
        endHour: end,
        label: `${schedule.name} (${start.toFixed(2)}-${end.toFixed(2)})`,
      });
    }
  } else if (schedule.schedule_type === "flow") {
    const start = normalizeHour(config.day_start_hour_utc, 12);
    const end = normalizeHour(config.day_end_hour_utc, 23);
    const dayIntensity = String(config.day_intensity ?? "high");
    const nightIntensity = String(config.night_intensity ?? "low");

    for (const day of DAYS) {
      blocks.push({
        id: `${schedule.id}-${day}-day`,
        deviceKey: schedule.device_key,
        scheduleName: schedule.name,
        scheduleType: schedule.schedule_type,
        enabled: schedule.enabled,
        startHour: start,
        endHour: end,
        label: `${schedule.name} (${dayIntensity}/${nightIntensity})`,
      });
    }
  } else if (schedule.schedule_type === "feeding") {
    const hour = normalizeHour(config.hour_utc, 14);
    const durationSeconds = Number(config.duration_seconds ?? 5);

    for (const day of DAYS) {
      blocks.push({
        id: `${schedule.id}-${day}-feed`,
        deviceKey: schedule.device_key,
        scheduleName: schedule.name,
        scheduleType: schedule.schedule_type,
        enabled: schedule.enabled,
        startHour: hour,
        endHour: Math.min(24, hour + 0.15),
        label: `${schedule.name} (${durationSeconds}s)`,
        isPointEvent: true,
      });
    }
  }

  return blocks;
}

function scheduleColor(scheduleType: string): string {
  switch (scheduleType) {
    case "lighting":
      return "#f59e0b";
    case "feeding":
      return "#10b981";
    case "flow":
      return "#3b82f6";
    case "pump":
      return "#8b5cf6";
    default:
      return "#6b7280";
  }
}

function leftPercent(startHour: number): number {
  return (startHour / 24) * 100;
}

function widthPercent(startHour: number, endHour: number): number {
  const width = Math.max(0.75, endHour - startHour);
  return (width / 24) * 100;
}

export function WeeklyScheduleTimeline({
  refreshToken = 0,
}: WeeklyScheduleTimelineProps) {
  const [items, setItems] = useState<ScheduleResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");

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
    const enabledSchedules = items.filter((item) => item.enabled);
    const deviceMap = new Map<string, TimelineBlock[]>();

    for (const item of enabledSchedules) {
      const blocks = inferBlocks(item);
      const existing = deviceMap.get(item.device_key) ?? [];
      existing.push(...blocks);
      deviceMap.set(item.device_key, existing);
    }

    return Array.from(deviceMap.entries()).sort((a, b) => a[0].localeCompare(b[0]));
  }, [items]);

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
        Weekly Schedule Timeline
      </div>

      <div
        style={{
          fontSize: "0.85rem",
          color: "#57606a",
          marginBottom: "14px",
        }}
      >
        Visual schedule view for lighting, feeding, flow, and pump automation across the week.
      </div>

      <div
        style={{
          display: "flex",
          gap: "14px",
          flexWrap: "wrap",
          marginBottom: "14px",
          fontSize: "0.82rem",
          color: "#57606a",
        }}
      >
        <LegendItem color="#f59e0b" label="Lighting" />
        <LegendItem color="#10b981" label="Feeding" />
        <LegendItem color="#3b82f6" label="Flow" />
        <LegendItem color="#8b5cf6" label="Pump" />
      </div>

      {message ? (
        <div
          style={{
            marginBottom: "12px",
            color: "#cf222e",
            fontSize: "0.85rem",
          }}
        >
          {message}
        </div>
      ) : null}

      {loading ? (
        <div style={{ color: "#57606a" }}>Loading timeline...</div>
      ) : grouped.length === 0 ? (
        <div style={{ color: "#57606a" }}>No enabled schedules available.</div>
      ) : (
        <div style={{ overflowX: "auto" }}>
          <div style={{ minWidth: "1100px" }}>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "180px 1fr",
                alignItems: "center",
                marginBottom: "8px",
              }}
            >
              <div />
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(24, 1fr)",
                  gap: "0",
                }}
              >
                {HOURS.map((hour) => (
                  <div
                    key={hour}
                    style={{
                      fontSize: "0.74rem",
                      color: "#57606a",
                      textAlign: "center",
                      paddingBottom: "4px",
                    }}
                  >
                    {String(hour).padStart(2, "0")}
                  </div>
                ))}
              </div>
            </div>

            <div style={{ display: "grid", gap: "16px" }}>
              {grouped.map(([deviceKey, blocks]) => (
                <div key={deviceKey}>
                  <div
                    style={{
                      fontSize: "0.92rem",
                      fontWeight: 700,
                      color: "#1f2328",
                      marginBottom: "8px",
                    }}
                  >
                    {deviceKey}
                  </div>

                  <div style={{ display: "grid", gap: "8px" }}>
                    {DAYS.map((day) => {
                      const dayBlocks = blocks.filter((block) => block.id.includes(`-${day}`));

                      return (
                        <div
                          key={`${deviceKey}-${day}`}
                          style={{
                            display: "grid",
                            gridTemplateColumns: "180px 1fr",
                            alignItems: "center",
                            gap: "10px",
                          }}
                        >
                          <div
                            style={{
                              fontSize: "0.82rem",
                              color: "#57606a",
                              fontWeight: 600,
                            }}
                          >
                            {day}
                          </div>

                          <div
                            style={{
                              position: "relative",
                              height: "34px",
                              border: "1px solid #d8dee4",
                              borderRadius: "8px",
                              background:
                                "repeating-linear-gradient(to right, #ffffff 0%, #ffffff 4.166%, #f6f8fa 4.166%, #f6f8fa 4.25%)",
                              overflow: "hidden",
                            }}
                          >
                            {dayBlocks.map((block) => {
                              const color = scheduleColor(block.scheduleType);

                              if (block.isPointEvent) {
                                return (
                                  <div
                                    key={block.id}
                                    title={block.label}
                                    style={{
                                      position: "absolute",
                                      top: "50%",
                                      left: `${leftPercent(block.startHour)}%`,
                                      transform: "translate(-50%, -50%)",
                                      width: "12px",
                                      height: "12px",
                                      borderRadius: "999px",
                                      background: color,
                                      border: "2px solid #ffffff",
                                      boxShadow: "0 0 0 1px rgba(0,0,0,0.15)",
                                    }}
                                  />
                                );
                              }

                              return (
                                <div
                                  key={block.id}
                                  title={block.label}
                                  style={{
                                    position: "absolute",
                                    top: "5px",
                                    left: `${leftPercent(block.startHour)}%`,
                                    width: `${widthPercent(block.startHour, block.endHour)}%`,
                                    height: "24px",
                                    borderRadius: "6px",
                                    background: color,
                                    opacity: block.enabled ? 0.9 : 0.35,
                                    color: "#ffffff",
                                    fontSize: "0.72rem",
                                    fontWeight: 700,
                                    display: "flex",
                                    alignItems: "center",
                                    paddingLeft: "8px",
                                    whiteSpace: "nowrap",
                                    overflow: "hidden",
                                    textOverflow: "ellipsis",
                                  }}
                                >
                                  {block.scheduleName}
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function LegendItem({ color, label }: { color: string; label: string }) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: "8px",
      }}
    >
      <span
        style={{
          width: "12px",
          height: "12px",
          borderRadius: "999px",
          background: color,
          display: "inline-block",
        }}
      />
      <span>{label}</span>
    </div>
  );
}