import React from "react";
import { motion } from "framer-motion";
import { portfolioData } from "../data/mock.js";
import {
  Briefcase,
  Code,
  Lightbulb,
  Mail,
  MapPin,
  Download,
  Github,
  Linkedin,
  Award,
  Book,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

const sectionVariants = {
  hidden: { opacity: 0, y: 40 },
  visible: { opacity: 1, y: 0 },
};

const cardVariants = {
  hidden: { opacity: 0, y: 30 },
  visible: { opacity: 1, y: 0 },
};

const PortfolioView: React.FC = () => {
  async function downloadResume() {
    const response = await fetch(
      `${import.meta.env.VITE_BACKEND_URL}/api/resume`
    );
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "resume.pdf";
    a.click();
  }

  const skillSections = [
    { title: "Languages", items: portfolioData.skills.languages },
    { title: "Frontend", items: portfolioData.skills.frontend },
    { title: "Backend", items: portfolioData.skills.backend },
    {
      title: "AI & Agentic Systems",
      items: portfolioData.skills.ai,
      highlight: true,
    },
    { title: "Databases", items: portfolioData.skills.databases },
    { title: "Tools & Platforms", items: portfolioData.skills.tools },
  ];

  const contactItems: Array<{
    label: string;
    icon: LucideIcon;
    href?: string;
    external?: boolean;
    action?: () => void;
  }> = [
    {
      label: portfolioData.personal.email,
      icon: Mail,
      href: `mailto:${portfolioData.personal.email}`,
    },
    {
      label: "Download Resume",
      icon: Download,
      action: downloadResume,
    },
    {
      label: portfolioData.personal.location,
      icon: MapPin,
    },
    {
      label: "GitHub",
      icon: Github,
      href: portfolioData.personal.github,
      external: true,
    },
    {
      label: "LinkedIn",
      icon: Linkedin,
      href: portfolioData.personal.linkedin,
      external: true,
    },
  ];

  return (
    <div className="portfolio-container">
      {/* Hero Section */}
      <motion.section
        className="hero-section"
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease: "easeOut" }}
      >
        <motion.div className="hero-content">
          <motion.div
            className="hero-label glass-pill"
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.2, type: "spring", stiffness: 120 }}
          >
            Full Stack Developer • AI Engineer
          </motion.div>

          <motion.h1
            className="hero-title"
            variants={sectionVariants}
            initial="hidden"
            animate="visible"
            transition={{ delay: 0.25, duration: 0.7 }}
          >
            {portfolioData.personal.name}
          </motion.h1>

          <motion.p
            className="hero-tagline"
            variants={sectionVariants}
            initial="hidden"
            animate="visible"
            transition={{ delay: 0.35, duration: 0.6 }}
          >
            {portfolioData.personal.tagline}
          </motion.p>

          <motion.p
            className="hero-bio"
            variants={sectionVariants}
            initial="hidden"
            animate="visible"
            transition={{ delay: 0.45, duration: 0.6 }}
          >
            {portfolioData.personal.bio}
          </motion.p>

          <motion.div
            className="hero-cta"
            variants={sectionVariants}
            initial="hidden"
            animate="visible"
            transition={{ delay: 0.55, duration: 0.6 }}
          >
            <motion.a
              href="#contact"
              className="cta-primary"
              whileHover={{ scale: 1.04, y: -2 }}
              whileTap={{ scale: 0.98 }}
            >
              Get In Touch
            </motion.a>
            <motion.a
              href="#projects"
              className="cta-secondary"
              whileHover={{ scale: 1.04, y: -2 }}
              whileTap={{ scale: 0.98 }}
            >
              View Projects
            </motion.a>
          </motion.div>
        </motion.div>

        <div className="hero-decoration">
          <div className="floating-shape shape-1" />
          <div className="floating-shape shape-2" />
          <div className="floating-shape shape-3" />
        </div>
      </motion.section>

      {/* Experience Section */}
      <section className="section-container" id="experience">
        <div className="section-header">
          <Briefcase className="section-icon" />
          <h2 className="section-title">Experience</h2>
        </div>
        <div className="timeline">
          {portfolioData.experience.map((exp, index) => (
            <motion.article
              key={exp.id}
              className="timeline-item"
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, amount: 0.2 }}
              transition={{ duration: 0.6, delay: index * 0.1 }}
              variants={sectionVariants}
              whileHover={{ x: 6 }}
            >
              <div className="timeline-marker max-md:-left-[30px]" />
              <div className="timeline-content">
                <div className="timeline-header">
                  <h3 className="timeline-role">{exp.role}</h3>
                  <span className="timeline-duration">{exp.duration}</span>
                </div>
                <div className="timeline-company">
                  {exp.company} • {exp.location}
                </div>
                <ul className="timeline-description">
                  {exp.description.map((item, i) => (
                    <li key={i}>{item}</li>
                  ))}
                </ul>
                <div className="timeline-tech">
                  {exp.technologies.map((tech, i) => (
                    <span key={i} className="tech-badge">
                      {tech}
                    </span>
                  ))}
                </div>
              </div>
            </motion.article>
          ))}
        </div>
      </section>

      {/* Projects Section */}
      <section className="section-container" id="projects">
        <div className="section-header">
          <Code className="section-icon" />
          <h2 className="section-title">Featured Projects</h2>
        </div>
        <div className="projects-grid">
          {portfolioData.projects.map((project, index) => (
            <motion.article
              key={project.id}
              className="project-card"
              variants={cardVariants}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, amount: 0.2 }}
              transition={{ duration: 0.6, delay: index * 0.1 }}
              whileHover={{ y: -12, scale: 1.01 }}
            >
              <div className="project-header">
                <h3 className="project-name">{project.name}</h3>
                <span
                  className={`project-status ${
                    project.status === "Completed"
                      ? "status-completed"
                      : "status-progress"
                  }`}
                >
                  {project.status}
                </span>
              </div>
              <p className="project-description">{project.description}</p>
              <div className="project-impact">
                <Lightbulb size={16} />
                <span>{project.impact}</span>
              </div>
              <div className="project-tech">
                {project.technologies.map((tech, i) => (
                  <span key={i} className="tech-badge">
                    {tech}
                  </span>
                ))}
              </div>
              <div className="project-date">{project.date}</div>
            </motion.article>
          ))}
        </div>
      </section>

      {/* Skills Section */}
      <section className="section-container" id="skills">
        <div className="section-header">
          <Award className="section-icon" />
          <h2 className="section-title">Technical Skills</h2>
        </div>
        <div className="skills-grid">
          {skillSections.map((section, index) => (
            <motion.div
              key={section.title}
              className="skill-category"
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, amount: 0.2 }}
              transition={{ duration: 0.5, delay: index * 0.05 }}
              variants={cardVariants}
            >
              <h3 className="skill-category-title">{section.title}</h3>
              <div className="skill-tags">
                {section.items.map((skill) => (
                  <span
                    key={skill}
                    className={`skill-tag ${
                      section.highlight ? "skill-tag-highlight" : ""
                    }`}
                  >
                    {skill}
                  </span>
                ))}
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Education Section */}
      <section className="section-container" id="education">
        <div className="section-header">
          <Book className="section-icon" />
          <h2 className="section-title">Education</h2>
        </div>
        <motion.div
          className="education-card"
          variants={sectionVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, amount: 0.3 }}
          transition={{ duration: 0.6 }}
        >
          <h3 className="education-degree">{portfolioData.education.degree}</h3>
          <div className="education-institution">
            {portfolioData.education.institution}
          </div>
          <div className="education-details">
            <span>{portfolioData.education.duration}</span>
            <span className="education-cgpa">
              CGPA: {portfolioData.education.cgpa}
            </span>
          </div>
        </motion.div>
      </section>

      {/* Contact Section */}
      <section className="section-container" id="contact">
        <div className="section-header">
          <Mail className="section-icon" />
          <h2 className="section-title">Let's Connect</h2>
        </div>
        <div className="contact-grid">
          {contactItems.map((item) => {
            const Content = (
              <>
                <item.icon size={24} />
                <span>{item.label}</span>
              </>
            );

            if (item.href) {
              return (
                <motion.a
                  key={item.label}
                  href={item.href}
                  className="contact-item"
                  target={item.external ? "_blank" : undefined}
                  rel={item.external ? "noopener noreferrer" : undefined}
                  whileHover={{ y: -6, scale: 1.01 }}
                  whileTap={{ scale: 0.98 }}
                >
                  {Content}
                </motion.a>
              );
            }

            if (item.action) {
              return (
                <motion.button
                  key={item.label}
                  className="contact-item"
                  onClick={item.action}
                  type="button"
                  whileHover={{ y: -6, scale: 1.01 }}
                  whileTap={{ scale: 0.98 }}
                >
                  {Content}
                </motion.button>
              );
            }

            return (
              <motion.div
                key={item.label}
                className="contact-item"
                whileHover={{ y: -6, scale: 1.01 }}
              >
                {Content}
              </motion.div>
            );
          })}
        </div>
      </section>
    </div>
  );
};

export default PortfolioView;
