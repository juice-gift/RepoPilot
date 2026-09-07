import { useEffect, useState } from "react";

import { getHealth } from "./api/health";
import "./App.css";

type BackendStatus = "checking" | "connected" | "unavailable";

const statusMessages: Record<BackendStatus, string> = {
  checking: "Checking backend…",
  connected: "Backend connected",
  unavailable: "Backend unavailable",
};

function App() {
  const [backendStatus, setBackendStatus] = useState<BackendStatus>("checking");

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

    void checkBackend();
    return () => controller.abort();
  }, []);

  return (
    <main>
      <h1>RepoPilot</h1>
      <p className={`status status--${backendStatus}`} role="status">
        {statusMessages[backendStatus]}
      </p>
    </main>
  );
}

export default App;
