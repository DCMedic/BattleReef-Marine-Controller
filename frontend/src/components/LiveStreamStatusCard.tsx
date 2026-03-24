type Props = {
  connected: boolean;
  lastUpdated: string | null;
  error: string | null;
};

export default function LiveStreamStatusCard({
  connected,
  lastUpdated,
  error,
}: Props) {
  const tone = !connected
    ? { bg: "#fff1f2", border: "#fecdd3", fg: "#9f1239" }
    : error
    ? { bg: "#fffbeb", border: "#fde68a", fg: "#92400e" }
    : { bg: "#ecfdf5", border: "#a7f3d0", fg: "#065f46" };

  return (
    <section
      style={{
        background: tone.bg,
        border: `1px solid ${tone.border}`,
        borderRadius: 16,
        padding: 20,
        color: tone.fg,
      }}
    >
      <div style={{ fontWeight: 800, marginBottom: 8 }}>Live Stream Status</div>
      <div style={{ display: "grid", gap: 6, fontSize: 14 }}>
        <div>Connection: {connected ? "Connected" : "Disconnected"}</div>
        <div>Last Update: {lastUpdated ?? "No live update received yet"}</div>
        <div>Error: {error ?? "None"}</div>
      </div>
    </section>
  );
}