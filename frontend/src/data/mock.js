export const portfolioData = {
  personal: {
    name: "Tejas M",
    title: "Full Stack Developer & AI Enthusiast",
    tagline: "Building intelligent systems with modern web technologies",
    email: "tejasmt884@gmail.com",
    phone: "+91 7411545570",
    location: "Bengaluru, India",
    linkedin: "https://linkedin.com/in/tejas26",
    github: "https://github.com/tejas261",
    bio: "Graduate Software Engineer at FYND with expertise in full-stack development, AI agents, and modern web technologies. Passionate about building intelligent systems using LangChain, LangGraph, and cutting-edge AI frameworks.",
  },

  experience: [
    {
      id: 1,
      company: "FYND",
      role: "Graduate SDE",
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
    cgpa: "8.3",
    location: "Bengaluru, KA",
  },

  certifications: ["Responsive Web Design - freeCodeCamp"],
};
