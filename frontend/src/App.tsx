import React, { useState } from "react";
import "./App.css";
import PortfolioView from "./pages/PortfolioView";
import ChatView from "./pages/ChatView";
import { User, MessageSquare } from "lucide-react";

const App: React.FC = () => {
  const [activeView, setActiveView] = useState<"portfolio" | "chat">(
    "portfolio"
  );

  return (
    <div className="App">
      {/* Navigation Tab Switcher */}
      <nav className="nav-tabs">
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

      {/* View Container */}
      <main className="view-container">
        {activeView === "portfolio" ? <PortfolioView /> : <ChatView />}
      </main>
    </div>
  );
};

export default App;
