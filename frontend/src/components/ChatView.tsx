import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, User } from "lucide-react";
import axios from "axios";
import image from "../assets/pic.jpg";

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL as string;
const API = `${BACKEND_URL}/api`;

type Message = {
  id: number;
  sender: "bot" | "user";
  text: string;
  timestamp: Date;
};

type Props = { sessionId: string; visitorId?: string };

const ChatView: React.FC<Props> = ({ sessionId, visitorId }) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 1,
      sender: "bot",
      text: `Hey! 👋 I'm Tejas. Ask me anything about my work, projects, or tech - happy to chat!`,
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [useRealAPI, setUseRealAPI] = useState(true);
  const [apiError, setApiError] = useState(false);
  const messagesContainerRef = useRef<HTMLDivElement | null>(null);

  const scrollToBottom = () => {
    const node = messagesContainerRef.current;
    if (node) {
      node.scrollTo({ top: node.scrollHeight, behavior: "smooth" });
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      id: messages.length + 1,
      sender: "user",
      text: input,
      timestamp: new Date(),
    };

    setMessages([...messages, userMessage]);
    const userInput = input;
    setInput("");
    setIsTyping(true);
    setApiError(false);

    // Try real API first if enabled
    if (useRealAPI) {
      try {
        const response = await axios.post(
          `${API}/chat`,
          {
            message: userInput,
            session_id: sessionId,
            meta: {
              visitor_id: visitorId,
              page_url: window.location.href,
              referrer: document.referrer || undefined,
              timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
              locale: navigator.language,
              user_agent: navigator.userAgent,
              dnt: navigator.doNotTrack === "1",
            },
          },
          {
            timeout: 30000, // 30 second timeout
          }
        );

        const botMessage: Message = {
          id: messages.length + 2,
          sender: "bot",
          text: response.data.response,
          timestamp: new Date(response.data.timestamp),
        };

        setMessages((prev) => [...prev, botMessage]);
        setIsTyping(false);
      } catch (error: any) {
        console.error("API Error:", error);

        // If API key not configured (503) or timeout, fall back to mock
        if (error.response?.status === 503 || error.code === "ECONNABORTED") {
          setApiError(true);
          setUseRealAPI(false);
        } else {
          // Show error message
          const errorMessage: Message = {
            id: messages.length + 2,
            sender: "bot",
            text: "Sorry, I encountered an error. Please try again.",
            timestamp: new Date(),
          };
          setMessages((prev) => [...prev, errorMessage]);
          setIsTyping(false);
        }
      }
    }
  };

  const handleKeyPress: React.KeyboardEventHandler<HTMLInputElement> = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const messageVariants = {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
  };

  return (
    <motion.div
      className="chat-container"
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
    >
      <div className="chat-messages h-full" ref={messagesContainerRef}>
        <AnimatePresence initial={false}>
          {messages.map((message) => (
            <motion.div
              key={message.id}
              className={`message-wrapper ${message.sender}`}
              layout
              variants={messageVariants}
              initial="initial"
              animate="animate"
              transition={{ duration: 0.3 }}
            >
              <div className="message-avatar">
                {message.sender === "bot" ? (
                  <img
                    src={image}
                    alt="owner"
                    className="rounded-full scale-150 w-7 h-7 object-cover"
                  />
                ) : (
                  <User size={20} />
                )}
              </div>
              <div className="message-bubble">
                <p className="message-text">{message.text}</p>
                <span className="message-time">
                  {message.timestamp.toLocaleTimeString([], {
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </span>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {isTyping && (
          <motion.div
            className="message-wrapper bot"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            <div className="message-avatar">
              <img
                src={image}
                alt="owner"
                className="rounded-full scale-150 w-7 h-7 object-cover"
              />
            </div>
            <div className="bg-transparent mt-2 typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </motion.div>
        )}
      </div>

      <div className="chat-input-container">
        <div className="chat-input-wrapper">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask about experience, projects, skills..."
            className="chat-input"
          />
          <motion.button
            onClick={handleSend}
            className="chat-send-button"
            disabled={!input.trim()}
            whileHover={{ scale: input.trim() ? 1.05 : 1 }}
            whileTap={{ scale: input.trim() ? 0.96 : 1 }}
          >
            <Send size={20} />
          </motion.button>
        </div>
      </div>
    </motion.div>
  );
};

export default ChatView;
