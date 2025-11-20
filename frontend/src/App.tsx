import React, { useMemo, useState } from "react";
import { motion } from "framer-motion";
import "./App.css";
import PortfolioView from "./components/PortfolioView";
import ChatView from "./components/ChatView";
import { User, MessageSquare } from "lucide-react";
import { v4 as uuidv4 } from "uuid";

const getOrCreateVisitorId = (): string => {
  const key = "visitor_id";
  try {
    const existing = localStorage.getItem(key);
    if (existing) return existing;
    const id = uuidv4();
    localStorage.setItem(key, id);
    return id;
  } catch {
    return uuidv4();
  }
};

const App: React.FC = () => {
  const [activeView, setActiveView] = useState<"portfolio" | "chat">(
    "portfolio"
  );
  const sessionId = useMemo(() => uuidv4(), []);
  const visitorId = useMemo(() => getOrCreateVisitorId(), []);

  const tabs = [
    { id: "portfolio" as const, label: "Portfolio", Icon: User },
    { id: "chat" as const, label: "AI Chat", Icon: MessageSquare },
  ];

  const viewVariants = {
    active: { opacity: 1, x: 0, filter: "blur(0px)" },
    inactive: { opacity: 0, x: -40, filter: "blur(12px)" },
  };

  return (
    <div className="App">
      <div className="stellar-bg" aria-hidden="true">
        <div className="stellar-gradient" />
        <div className="stellar-grid" />
        <div className="stellar-orb orb-left" />
        <div className="stellar-orb orb-right" />
      </div>
      {/* Navigation Tab Switcher */}
      <motion.nav
        className="nav-tabs floating-nav"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
      >
        {tabs.map(({ id, label, Icon }) => (
          <motion.button
            key={id}
            className={`nav-tab ${activeView === id ? "active" : ""}`}
            onClick={() => setActiveView(id)}
            whileHover={{ y: -2 }}
            whileTap={{ scale: 0.98 }}
          >
            {activeView === id && (
              <motion.span
                layoutId="tab-indicator"
                className="tab-indicator"
                transition={{ type: "spring", stiffness: 350, damping: 30 }}
              />
            )}
            <Icon size={18} />
            <span>{label}</span>
          </motion.button>
        ))}
      </motion.nav>

      {/* View Container: keep both mounted to preserve state; toggle visibility */}
      <main className="view-container">
        <motion.div
          className="view-panel"
          animate={activeView === "portfolio" ? "active" : "inactive"}
          variants={viewVariants}
          transition={{ duration: 0.7, ease: "easeOut" }}
          aria-hidden={activeView !== "portfolio"}
          style={{
            pointerEvents: activeView === "portfolio" ? "auto" : "none",
            position: activeView === "portfolio" ? "relative" : "absolute",
            inset: activeView === "portfolio" ? "auto" : 0,
          }}
        >
          <PortfolioView />
        </motion.div>
        <motion.div
          className="view-panel"
          animate={activeView === "chat" ? "active" : "inactive"}
          variants={viewVariants}
          transition={{ duration: 0.7, ease: "easeOut" }}
          aria-hidden={activeView !== "chat"}
          style={{
            pointerEvents: activeView === "chat" ? "auto" : "none",
            position: activeView === "chat" ? "relative" : "absolute",
            inset: activeView === "chat" ? "auto" : 0,
          }}
        >
          <ChatView sessionId={sessionId} visitorId={visitorId} />
        </motion.div>
      </main>
    </div>
  );
};

export default App;
