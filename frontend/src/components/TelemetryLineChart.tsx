import type { TelemetryWindowPoint } from "../types/telemetryTrends";

type ThresholdInfo = {
  min?: number | null;
  max?: number | null;
  severity?: "warning" | "critical";
};

type Props = {
  points: TelemetryWindowPoint[];
  threshold?: ThresholdInfo;
  height?: number;
};

function lineColor(points: TelemetryWindowPoint[]): string {
  if (points.length === 0) {
    return "#9ca3af";
  }
  return "#2563eb";
}

export default function TelemetryLineChart({
  points,
  threshold,
  height = 180,
}: Props) {
  const width = 1000;
  const padding = 48;

  if (points.length === 0) {
    return (
      <div
        style={{
          height,
          display: "grid",
          placeItems: "center",
          color: "#6b7280",
          border: "1px dashed #d1d5db",
          borderRadius: 12,
          background: "#f9fafb",
        }}
      >
        No data available
      </div>
    );
  }

  const values = points.map((point) => point.value);
  const thresholdValues = [threshold?.min, threshold?.max].filter(
    (value): value is number => typeof value === "number"
  );

  let minValue = Math.min(...values, ...(thresholdValues.length ? thresholdValues : [Number.POSITIVE_INFINITY]));
  let maxValue = Math.max(...values, ...(thresholdValues.length ? thresholdValues : [Number.NEGATIVE_INFINITY]));

  if (!Number.isFinite(minValue)) {
    minValue = Math.min(...values);
  }
  if (!Number.isFinite(maxValue)) {
    maxValue = Math.max(...values);
  }

  if (minValue === maxValue) {
    minValue -= 1;
    maxValue += 1;
  }

  const xForIndex = (index: number) => {
    if (points.length === 1) {
      return width / 2;
    }
    return padding + (index / (points.length - 1)) * (width - padding * 2);
  };

  const yForValue = (value: number) => {
    const ratio = (value - minValue) / (maxValue - minValue);
    return height - padding - ratio * (height - padding * 2);
  };

  const polylinePoints = points
    .map((point, index) => `${xForIndex(index)},${yForValue(point.value)}`)
    .join(" ");

  const bandColor =
    threshold?.severity === "critical"
      ? "rgba(239, 68, 68, 0.16)"
      : "rgba(245, 158, 11, 0.16)";

  const normalBandColor = "rgba(34, 197, 94, 0.12)";

  const minBandY = typeof threshold?.min === "number" ? yForValue(threshold.min) : null;
  const maxBandY = typeof threshold?.max === "number" ? yForValue(threshold.max) : null;

  const gridLines = 4;

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      width="100%"
      height={height}
      style={{
        display: "block",
        borderRadius: 12,
        background: "#ffffff",
        border: "1px solid #e5e7eb",
      }}
    >
      {typeof threshold?.min === "number" && typeof threshold?.max === "number" ? (
        <>
          <rect x={0} y={0} width={width} height={maxBandY ?? 0} fill={bandColor} />
          <rect
            x={0}
            y={maxBandY ?? 0}
            width={width}
            height={(minBandY ?? height) - (maxBandY ?? 0)}
            fill={normalBandColor}
          />
          <rect
            x={0}
            y={minBandY ?? height}
            width={width}
            height={height - (minBandY ?? height)}
            fill={bandColor}
          />
        </>
      ) : typeof threshold?.min === "number" ? (
        <>
          <rect x={0} y={0} width={width} height={minBandY ?? 0} fill={normalBandColor} />
          <rect
            x={0}
            y={minBandY ?? 0}
            width={width}
            height={height - (minBandY ?? 0)}
            fill={bandColor}
          />
        </>
      ) : typeof threshold?.max === "number" ? (
        <>
          <rect x={0} y={0} width={width} height={maxBandY ?? 0} fill={bandColor} />
          <rect
            x={0}
            y={maxBandY ?? 0}
            width={width}
            height={height - (maxBandY ?? 0)}
            fill={normalBandColor}
          />
        </>
      ) : null}

      {Array.from({ length: gridLines + 1 }).map((_, index) => {
        const y = padding + (index / gridLines) * (height - padding * 2);
        return (
          <line
            key={index}
            x1={padding}
            y1={y}
            x2={width - padding}
            y2={y}
            stroke="#e5e7eb"
            strokeWidth="1"
          />
        );
      })}

      <line
        x1={padding}
        y1={padding}
        x2={padding}
        y2={height - padding}
        stroke="#9ca3af"
        strokeWidth="1.5"
      />
      <line
        x1={padding}
        y1={height - padding}
        x2={width - padding}
        y2={height - padding}
        stroke="#9ca3af"
        strokeWidth="1.5"
      />

      {typeof threshold?.min === "number" ? (
        <line
          x1={padding}
          y1={yForValue(threshold.min)}
          x2={width - padding}
          y2={yForValue(threshold.min)}
          stroke="#f59e0b"
          strokeDasharray="6 6"
          strokeWidth="2"
        />
      ) : null}

      {typeof threshold?.max === "number" ? (
        <line
          x1={padding}
          y1={yForValue(threshold.max)}
          x2={width - padding}
          y2={yForValue(threshold.max)}
          stroke="#ef4444"
          strokeDasharray="6 6"
          strokeWidth="2"
        />
      ) : null}

      <polyline
        fill="none"
        stroke={lineColor(points)}
        strokeWidth="3"
        points={polylinePoints}
        strokeLinejoin="round"
        strokeLinecap="round"
      />
    </svg>
  );
}