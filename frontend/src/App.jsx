import { useEffect, useState } from "react";
import { Activity, CheckCircle, XCircle, RefreshCw } from "lucide-react";
import "./App.css";

const API = "http://127.0.0.1:8000";

function App() {
  const [monitors, setMonitors] = useState([]);
  const [summary, setSummary] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  
  // State variables for adding monitors
  const [name, setName] = useState("");
  const [url, setUrl] = useState("");
  const [adding, setAdding] = useState(false);
  const [formMessage, setFormMessage] = useState("");

  async function loadDashboard() {
    setLoading(true);
    setError("");

    try {
      const [monitorResponse, summaryResponse, historyResponse] =
        await Promise.all([
          fetch(`${API}/monitors`),
          fetch(`${API}/summary`),
          fetch(`${API}/history`),
        ]);

      if (
        !monitorResponse.ok ||
        !summaryResponse.ok ||
        !historyResponse.ok
      ) {
        throw new Error("Could not load dashboard data");
      }

      const monitorData = await monitorResponse.json();
      const summaryData = await summaryResponse.json();
      const historyData = await historyResponse.json();

      const monitorsWithHealth = await Promise.all(
        monitorData.map(async (monitor) => {
          const response = await fetch(
            `${API}/monitors/${monitor.id}/latest`
          );

          if (!response.ok) {
            throw new Error("Could not load monitor health");
          }

          const latest = await response.json();
          return { ...monitor, latest };
        })
      );

      setMonitors(monitorsWithHealth);
      setSummary(summaryData);
      setHistory(historyData);
    } catch {
      setError("Could not connect to PulseCheck. Check your backend.");
    } finally {
      setLoading(false);
    }
  }

  // Submit function for adding a monitor
  async function addMonitor(e) {
    e.preventDefault();
    setAdding(true);
    setFormMessage("");

    try {
      const response = await fetch(`${API}/monitors`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, url }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Could not add monitor");
      }

      setName("");
      setUrl("");
      setFormMessage("Monitor added successfully!");
      await loadDashboard();
    } catch (err) {
      setFormMessage(err.message);
    } finally {
      setAdding(false);
    }
  }

  useEffect(() => {
    loadDashboard();

    const intervalId = setInterval(() => {
      loadDashboard();
    }, 30000);

    return () => clearInterval(intervalId);
  }, []);

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <Activity size={28} />
          <span>PulseCheck</span>
        </div>
        <button onClick={loadDashboard} className="refresh-btn">
          <RefreshCw size={16} /> Refresh
        </button>
      </header>

      <main>
        <section className="welcome">
          <p className="eyebrow">MONITORING OVERVIEW</p>
          <h1>Your APIs, at a glance.</h1>
          <p>Monitor endpoint health and response performance.</p>
        </section>

        {error && <p className="error">{error}</p>}

        {loading ? (
          <p>Loading dashboard...</p>
        ) : (
          <>
            <section className="stats">
              <Stat label="Total Checks" value={summary?.total_checks ?? 0} />
              <Stat label="Successful" value={summary?.successful_checks ?? 0} />
              <Stat label="Failed" value={summary?.failed_checks ?? 0} />
              <Stat
                label="Check Success Rate"
                value={`${summary?.uptime_percentage ?? 0}%`}
              />
            </section>

            <section className="panel add-panel">
              <h2>Add a Monitor</h2>

              <form onSubmit={addMonitor} className="monitor-form">
                <input
                  placeholder="Monitor name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                />

                <input
                  type="url"
                  placeholder="https://example.com"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  required
                />

                <button type="submit" disabled={adding}>
                  {adding ? "Adding..." : "Add Monitor"}
                </button>
              </form>

              {formMessage && <p>{formMessage}</p>}
            </section>

            <section className="panel">
              <h2>Registered Monitors</h2>

              {monitors.length === 0 ? (
                <p>No monitors registered yet.</p>
              ) : (
                <div className="monitor-list">
                  {monitors.map((monitor) => (
                    <div className="monitor" key={monitor.id}>
                      <div>
                        <strong>{monitor.name}</strong>
                        <p>{monitor.url}</p>
                      </div>
                      <div>
                        <span className={
                          monitor.latest.status === "Healthy"
                            ? "active"
                            : monitor.latest.status === "Unhealthy"
                              ? "inactive"
                              : ""
                        }>
                          {monitor.latest.status}
                        </span>

                        <p>
                          {monitor.latest.response_time_ms != null
                            ? `${monitor.latest.response_time_ms} ms`
                            : "No response time"}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>

            <section className="panel">
              <h2>Monitoring History</h2>

              {history.length === 0 ? (
                <p>No monitoring history available yet.</p>
              ) : (
                <div className="history-table-wrapper">
                  <table className="history-table">
                    <thead>
                      <tr>
                        <th>URL</th>
                        <th>Status Code</th>
                        <th>Response Time</th>
                        <th>Health</th>
                        <th>Checked At</th>
                      </tr>
                    </thead>

                    <tbody>
                      {history.map((item) => (
                        <tr key={item.id}>
                          <td className="history-url">{item.url}</td>
                          <td>{item.status_code ?? "N/A"}</td>
                          <td>
                            {item.response_time_ms == null
                              ? "N/A"
                              : `${item.response_time_ms.toFixed(2)} ms`}
                          </td>
                          <td>
                            <span
                              className={
                                item.is_healthy ? "active" : "inactive"
                              }
                            >
                              {item.is_healthy ? "Healthy" : "Unhealthy"}
                            </span>
                          </td>
                          <td>
                            {item.checked_at
                              ? new Date(item.checked_at).toLocaleString()
                              : "N/A"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </section>
          </>
        )}
      </main>
    </div>
  );
}

function Stat({ label, value }) {
  return (
    <div className="stat-card">
      <p>{label}</p>
      <h2>{value}</h2>
    </div>
  );
}

export default App;