import { useEffect, useState } from "react";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";

function App() {
  const [dashboard, setDashboard] = useState({
    total_blocks: 0,
    active_anomalies: [],
    resolved_anomalies: [],
    recent_events: [],
  });

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchDashboard = async () => {
    try {
      const response = await fetch(
        `${API_URL}/api/dashboard`
      );

      if (!response.ok) {
        throw new Error("Failed to fetch dashboard data");
      }

      const data = await response.json();

      setDashboard(data);
      setError("");
    } catch (err) {
      console.error(err);
      setError("Unable to connect to monitoring API");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();

    const interval = setInterval(
      fetchDashboard,
      3000
    );

    return () => clearInterval(interval);
  }, []);

  const handleResolve = async (blockId) => {
    try {
      const response = await fetch(
        `${API_URL}/api/blocks/${encodeURIComponent(blockId)}/resolve`,
        {
          method: "POST",
        }
      );

      if (!response.ok) {
        throw new Error("Failed to resolve anomaly");
      }

      await fetchDashboard();
    } catch (err) {
      console.error(err);
      setError("Unable to resolve anomaly");
    }
  };

  const activeAnomalies =
    dashboard.active_anomalies || [];

  const resolvedAnomalies =
    dashboard.resolved_anomalies || [];

  return (
    <div className="dashboard">

      {/* Header */}

      <header className="header">
        <div>
          <h1>HDFS Log Analytics</h1>
          <p>
            Real-time anomaly monitoring
          </p>
        </div>

        <div className="live-status">
          <span className="live-dot"></span>
          LIVE
        </div>
      </header>

      {/* Connection status */}

      {error && (
        <div className="error-banner">
          {error}
        </div>
      )}

      {/* Statistics */}

      <section className="stats-grid">

        <div className="stat-card">
          <span className="stat-label">
            Total Blocks
          </span>

          <span className="stat-value">
            {dashboard.total_blocks}
          </span>
        </div>

        <div className="stat-card danger">
          <span className="stat-label">
            Active Anomalies
          </span>

          <span className="stat-value">
            {activeAnomalies.length}
          </span>
        </div>

        <div className="stat-card">
          <span className="stat-label">
            Resolved
          </span>

          <span className="stat-value">
            {resolvedAnomalies.length}
          </span>
        </div>

        <div className="stat-card">
          <span className="stat-label">
            Monitoring Window
          </span>

          <span className="stat-value">
            5 min
          </span>
        </div>

      </section>

      {/* Active anomalies */}

      <section className="panel">

        <div className="panel-header">

          <div>
            <h2>
              Active Anomalies
            </h2>

            <p>
              Detected by the LSTM model
            </p>
          </div>

          <span className="count-badge">
            {activeAnomalies.length}
          </span>

        </div>

        {loading ? (

          <div className="empty-state">
            Loading monitoring data...
          </div>

        ) : activeAnomalies.length === 0 ? (

          <div className="empty-state">

            <div className="empty-icon">
              ✓
            </div>

            <h3>
              No active anomalies
            </h3>

            <p>
              The system is monitoring HDFS logs normally.
            </p>

          </div>

        ) : (

          <div className="anomaly-list">

            {activeAnomalies.map(
              (anomaly) => (

                <div
                  className="anomaly-card"
                  key={anomaly.block_id}
                >

                  <div className="anomaly-top">

                    <div>

                      <span className="severity-badge">
                        ANOMALY
                      </span>

                      <h3>
                        {anomaly.block_id}
                      </h3>

                    </div>

                    <div className="probability">

                      <span>
                        Probability
                      </span>

                      <strong>
                        {Number(
                          anomaly.probability
                        ).toFixed(2)}
                        %
                      </strong>

                    </div>

                  </div>

                  <div className="anomaly-details">

                    <div>
                      <span>
                        Component
                      </span>

                      <strong>
                        {anomaly.component}
                      </strong>
                    </div>

                    <div>
                      <span>
                        Sequence
                      </span>

                      <strong>
                        {anomaly.sequence_length}
                        {" "}
                        events
                      </strong>
                    </div>

                    <div>
                      <span>
                        Time
                      </span>

                      <strong>
                        {anomaly.time}
                      </strong>
                    </div>

                  </div>

                  <div className="message">

                    <span>
                      Log Message
                    </span>

                    <p>
                      {anomaly.message}
                    </p>

                  </div>

                  <div className="anomaly-actions">

                    <button
                      className="resolve-button"
                      onClick={() =>
                        handleResolve(
                          anomaly.block_id
                        )
                      }
                    >
                      Resolve
                    </button>

                  </div>

                </div>

              )
            )}

          </div>

        )}

      </section>

      {/* Recent events */}

      <section className="panel">

        <div className="panel-header">

          <div>
            <h2>
              Recent Events
            </h2>

            <p>
              Latest events received from the replay
            </p>
          </div>

          <span className="count-badge neutral">
            {dashboard.recent_events?.length || 0}
          </span>

        </div>

        <div className="history-list">

          {(dashboard.recent_events || [])
            .slice()
            .reverse()
            .slice(0, 10)
            .map((event, index) => (

              <div
                className="history-row"
                key={`${event.time}-${event.block_id}-${index}`}
              >

                <div>

                  <strong>
                    {event.block_id || "Unknown"}
                  </strong>

                  <span>
                    {event.component}
                  </span>

                </div>

                <div>

                  <span>
                    {event.time}
                  </span>

                  <small>
                    {event.message}
                  </small>

                </div>

              </div>

            ))}

        </div>

      </section>

      {/* Resolved anomalies */}

      <section className="panel">

        <div className="panel-header">

          <div>
            <h2>
              Resolved Anomalies
            </h2>

            <p>
              Previously acknowledged anomalies
            </p>
          </div>

          <span className="count-badge neutral">
            {resolvedAnomalies.length}
          </span>

        </div>

        {resolvedAnomalies.length === 0 ? (

          <div className="empty-history">
            No resolved anomalies yet.
          </div>

        ) : (

          <div className="history-list">

            {resolvedAnomalies
              .slice()
              .reverse()
              .map((item, index) => (

                <div
                  className="history-row"
                  key={`${item.block_id}-${index}`}
                >

                  <div>

                    <strong>
                      {item.block_id}
                    </strong>

                    <span>
                      {item.component}
                    </span>

                  </div>

                  <div>

                    <span>
                      {Number(
                        item.probability
                      ).toFixed(2)}
                      %
                    </span>

                    <small>
                      Resolved{" "}
                      {item.resolved_at}
                    </small>

                  </div>

                </div>

              ))}

          </div>

        )}

      </section>

    </div>
  );
}

export default App;