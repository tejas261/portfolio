import React, { useMemo, useState } from "react";
import "./App.css";
import PortfolioView from "./components/PortfolioView";
import ChatView from "./components/ChatView";
import { User, MessageSquare } from "lucide-react";
import { v4 as uuidv4 } from "uuid";

const App: React.FC = () => {
  const [activeView, setActiveView] = useState<"portfolio" | "chat">(
    "portfolio"
  );
  const sessionId = useMemo(() => uuidv4(), []);

  return (
    <div className="App">
      {/* Navigation Tab Switcher */}
      <nav className="nav-tabs floating-nav bg-transparent w-full top-0">
        <button
          className={`nav-tab ${activeView === "portfolio" ? "active" : ""}`}
          onClick={() => setActiveView("portfolio")}
        >
          <User size={20} />
          <span>Portfolio</span>
        </button>
        <button
          className={`nav-tab ${activeView === "chat" ? "active" : ""}`}
          onClick={() => setActiveView("chat")}
        >
          <MessageSquare size={20} />
          <span>AI Chat</span>
        </button>
        <div className={`tab-indicator ${activeView}`}></div>
      </nav>

      {/* View Container: keep both mounted to preserve state; toggle visibility */}
      <main className="view-container">
        <div style={{ display: activeView === "portfolio" ? "block" : "none" }}>
          <PortfolioView />
        </div>
        <div style={{ display: activeView === "chat" ? "block" : "none" }}>
          <ChatView sessionId={sessionId} />
        </div>
      </main>
    </div>
  );
};

export default App;
