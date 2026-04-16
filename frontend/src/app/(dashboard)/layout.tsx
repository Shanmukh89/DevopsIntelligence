import Sidebar from "@/components/sidebar";
import Topbar from "@/components/topbar";

export default function DashboardLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <>
      {/* Mobile gate */}
      <div className="mobile-gate">
        <div
          className="flex items-center justify-center rounded font-mono font-bold"
          style={{
            width: 48,
            height: 48,
            backgroundColor: "var(--accent-500)",
            color: "#fff",
            fontSize: 20,
          }}
        >
          A
        </div>
        <h1
          style={{
            fontSize: "var(--text-xl)",
            color: "var(--text-primary)",
            fontWeight: 500,
          }}
        >
          Auditr works best on a larger screen
        </h1>
        <p
          style={{
            fontSize: "var(--text-base)",
            color: "var(--text-secondary)",
          }}
        >
          Open Auditr on a desktop or laptop for the full experience.
        </p>
      </div>

      {/* Desktop layout */}
      <div className="desktop-only flex h-screen overflow-hidden">
        <Sidebar />
        <div className="flex-1 flex flex-col overflow-hidden">
          <Topbar />
          <main
            className="flex-1 overflow-y-auto"
            style={{ padding: 32, maxWidth: 1440, margin: "0 auto", width: "100%" }}
          >
            {children}
          </main>
        </div>
      </div>
    </>
  );
}
