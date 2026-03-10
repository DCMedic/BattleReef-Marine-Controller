type MetricCardProps = {
  title: string;
  value: string;
  subtitle?: string;
};

export function MetricCard({ title, value, subtitle }: MetricCardProps) {
  return (
    <div
      style={{
        border: "1px solid #d0d7de",
        borderRadius: "12px",
        padding: "16px",
        background: "#ffffff",
        boxShadow: "0 1px 3px rgba(0,0,0,0.06)",
      }}
    >
      <div
        style={{
          fontSize: "0.9rem",
          fontWeight: 600,
          color: "#57606a",
          marginBottom: "8px",
        }}
      >
        {title}
      </div>
      <div
        style={{
          fontSize: "1.8rem",
          fontWeight: 700,
          color: "#1f2328",
          marginBottom: subtitle ? "6px" : "0",
        }}
      >
        {value}
      </div>
      {subtitle ? (
        <div
          style={{
            fontSize: "0.85rem",
            color: "#656d76",
          }}
        >
          {subtitle}
        </div>
      ) : null}
    </div>
  );
}