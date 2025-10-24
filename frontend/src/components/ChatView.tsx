import React, { useState, useEffect, useRef } from "react";
import { Send, Bot, User, AlertCircle } from "lucide-react";
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

type Props = { sessionId: string };

const ChatView: React.FC<Props> = ({ sessionId }) => {
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
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
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

  return (
    <div className="chat-container h-[90vh]">
      <div className="chat-header">
        <div className="chat-header-content">
          <Bot className="chat-header-icon" />
          <div>
            <h2 className="chat-header-title">Chat with Tejas</h2>
            <p className="chat-header-subtitle">
              {apiError
                ? "⚠️ Limited responses - Add API key for full chat"
                : "Ask me anything"}
            </p>
          </div>
        </div>
      </div>
      {/* 
      {apiError && (
        <div className="api-error-banner">
          <AlertCircle size={16} />
          <span>AI backend not configured. Please add an API key.</span>
        </div>
      )} */}

      <div className="chat-messages h-80">
        {messages.map((message) => (
          <div key={message.id} className={`message-wrapper ${message.sender}`}>
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
          </div>
        ))}

        {isTyping && (
          <div className="message-wrapper bot">
            <div className="message-avatar">
              <img
                src={image}
                alt="owner"
                className="rounded-full scale-150 w-7 h-7 object-cover"
              />
            </div>
            <div className="message-bubble typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
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
          <button
            onClick={handleSend}
            className="chat-send-button"
            disabled={!input.trim()}
          >
            <Send size={20} />
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatView;
