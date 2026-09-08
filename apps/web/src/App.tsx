import { useEffect, useState } from "react";

import { getDatabaseHealth, getHealth } from "./api/health";
import "./App.css";

type ConnectionStatus = "checking" | "connected" | "unavailable";

const statusMessages: Record<ConnectionStatus, string> = {
  checking: "Checking…",
  connected: "Connected",
  unavailable: "Unavailable",
};

function App() {
  const [backendStatus, setBackendStatus] =
    useState<ConnectionStatus>("checking");
  const [databaseStatus, setDatabaseStatus] =
    useState<ConnectionStatus>("checking");

  useEffect(() => {
    const controller = new AbortController();

    async function checkBackend(): Promise<void> {
      try {
        await getHealth(controller.signal);
        setBackendStatus("connected");
      } catch (error: unknown) {
        if (error instanceof DOMException && error.name === "AbortError") {
          return;
        }
        setBackendStatus("unavailable");
      }
    }

    async function checkDatabase(): Promise<void> {
      try {
        await getDatabaseHealth(controller.signal);
        setDatabaseStatus("connected");
      } catch (error: unknown) {
        if (error instanceof DOMException && error.name === "AbortError") {
          return;
        }
        setDatabaseStatus("unavailable");
      }
    }

    void checkBackend();
    void checkDatabase();
    return () => controller.abort();
  }, []);

  return (
    <main>
      <h1>RepoPilot</h1>
      <div className="connections" role="status">
        <p className={`status status--${backendStatus}`}>
          Backend: {statusMessages[backendStatus]}
        </p>
        <p className={`status status--${databaseStatus}`}>
          Database: {statusMessages[databaseStatus]}
        </p>
      </div>
    </main>
  );
}

export default App;
