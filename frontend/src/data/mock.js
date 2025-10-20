export const portfolioData = {
  personal: {
    name: "Tejas M",
    title: "Full Stack Developer & AI Enthusiast",
    tagline: "Building intelligent systems with modern web technologies",
    email: "tejasmt884@gmail.com",
    phone: "+91 7411545570",
    location: "Bengaluru, India",
    linkedin: "https://linkedin.com/in/tejas-m",
    github: "https://github.com/tejas-m",
    bio: "Graduate Software Engineer at FYND with expertise in full-stack development, AI agents, and modern web technologies. Passionate about building intelligent systems using LangChain, LangGraph, and cutting-edge AI frameworks.",
  },

  experience: [
    {
      id: 1,
      company: "FYND",
      role: "Graduate SDE (Frontend Developer)",
      duration: "Oct 2024 - Present",
      location: "Bengaluru, KA",
      description: [
        "Developed full-stack features using Next.js, Node.js, and TypeScript",
        "Architected and built RESTful APIs and microservices with Express.js and Prisma on MongoDB backends",
        "Collaborated cross-functionally through Git workflows, coordinating merges for zero-downtime deployments",
      ],
      technologies: [
        "Next.js",
        "Node.js",
        "TypeScript",
        "Express.js",
        "Prisma",
        "MongoDB",
      ],
    },
    {
      id: 2,
      company: "FYND",
      role: "Full Stack Intern",
      duration: "Jul 2024 - Sep 2024",
      location: "Bengaluru, KA",
      description: [
        "Implemented responsive front-end components using Next.js, Shadcn UI and Tailwind CSS",
        "Spearheaded UI/UX overhaul by translating Figma designs with pixel-perfect accuracy",
        "Collaborated with QA and DevOps teams to integrate AI test-generation modules",
      ],
      technologies: ["Next.js", "Shadcn UI", "Tailwind CSS", "Figma"],
    },
  ],

  projects: [
    {
      id: 1,
      name: "Pull Request Analyser",
      description:
        "Built a GPT-4-powered LangChain agent to fetch, parse, and analyze PR diffs from Azure DevOps. Conducted deep-dive reviews spotting code smells, bugs, and security vulnerabilities, posting threaded Slack updates for instant team feedback.",
      impact: "Cut manual review effort by 60% in pilot phase",
      technologies: [
        "Python",
        "LangGraph",
        "LangChain",
        "OpenAI",
        "Azure DevOps",
        "Slack",
      ],
      date: "June 2025",
      status: "Completed",
    },
    {
      id: 2,
      name: "AI Portfolio Manager",
      description:
        "Building autonomous agents using LangChain for stock portfolio analysis. Features real-time stock data ingestion, autonomous workflows for portfolio rebalancing, risk analysis, and GPT-based conversational interface.",
      impact:
        "Learning advanced agentic workflows and decision-making patterns",
      technologies: [
        "Next.js",
        "TypeScript",
        "Node.js",
        "MongoDB",
        "Prisma",
        "LangChain",
        "OpenAI",
      ],
      date: "March 2025",
      status: "In Progress",
    },
  ],

  skills: {
    languages: ["JavaScript", "TypeScript", "Python", "Java"],
    frontend: ["Next.js", "React", "Tailwind CSS", "Shadcn UI", "Bootstrap"],
    backend: ["Node.js", "Express.js", "FastAPI", "RESTful APIs"],
    ai: ["LangChain", "LangGraph", "OpenAI", "RAG", "Agentic Workflows"],
    databases: ["MongoDB", "PostgreSQL", "MySQL", "Prisma"],
    tools: [
      "Git/GitHub",
      "AWS (EC2, S3, Amplify)",
      "Vercel",
      "Azure DevOps",
      "NPM",
    ],
  },

  education: {
    degree: "Bachelor of Engineering - Computer Science",
    institution: "Don Bosco Institute of Technology (VTU)",
    duration: "December 2020 - Present",
    cgpa: "9.0",
    location: "Bengaluru, KA",
  },

  certifications: ["Responsive Web Design - freeCodeCamp"],
};

export const mockChatResponses = [
  {
    trigger: ["hello", "hi", "hey"],
    response:
      "Hey! 👋 What's up? Feel free to ask me about my work, projects, or anything tech-related!",
  },
  {
    trigger: ["experience", "work", "job"],
    response:
      "I'm a Graduate SDE at FYND, working with Next.js, Node, and TypeScript. Building full-stack features and REST APIs with Express and Prisma. Pretty fun stuff!",
  },
  {
    trigger: ["projects", "built", "created"],
    response:
      "My favorite is the PR Analyser - uses GPT-4 to auto-review code and catch bugs. Cut review time by 60%! Also working on an AI Portfolio Manager with LangChain.",
  },
  {
    trigger: ["skills", "technologies", "tech stack"],
    response:
      "I'm into JavaScript/TypeScript, Python, React, Next.js, and Node. On the AI side - LangChain, LangGraph, and GPT-4. Also work with MongoDB and AWS.",
  },
  {
    trigger: ["ai", "langchain", "langgraph", "agent"],
    response:
      "Yeah, I'm super into AI agents! Built production systems with LangChain and LangGraph - automated PR reviews, portfolio managers, that kind of thing. It's honestly my favorite area right now.",
  },
  {
    trigger: ["education", "college", "university"],
    response:
      "Doing my BE in CS from Don Bosco (VTU) with a 9.0 CGPA. Good times!",
  },
  {
    trigger: ["contact", "reach", "email"],
    response:
      "Sure! Reach me at tejasmt884@gmail.com or +91 7411545570. I'm in Bengaluru and always down to chat about cool projects!",
  },
  {
    trigger: ["default"],
    response:
      "Not sure I got that - wanna know about my experience, projects, skills, or something else?",
  },
];
