import React, { useEffect, useState } from "react";
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

const PortfolioView: React.FC = () => {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    setIsVisible(true);
  }, []);

  return (
    <div className="portfolio-container">
      {/* Hero Section */}
      <section className="hero-section">
        <div className={`hero-content ${isVisible ? "fade-in" : ""}`}>
          <div className="hero-label">Full Stack Developer • AI Engineer</div>
          <h1 className="hero-title">{portfolioData.personal.name}</h1>
          <p className="hero-tagline">{portfolioData.personal.tagline}</p>
          <p className="hero-bio">{portfolioData.personal.bio}</p>
          <div className="hero-cta">
            <a href="#contact" className="cta-primary">
              Get In Touch
            </a>
            <a href="#projects" className="cta-secondary">
              View Projects
            </a>
          </div>
        </div>
        <div className="hero-decoration">
          <div className="floating-shape shape-1"></div>
          <div className="floating-shape shape-2"></div>
          <div className="floating-shape shape-3"></div>
        </div>
      </section>

      {/* Experience Section */}
      <section className="section-container" id="experience">
        <div className="section-header">
          <Briefcase className="section-icon" />
          <h2 className="section-title">Experience</h2>
        </div>
        <div className="timeline">
          {portfolioData.experience.map((exp, index) => (
            <div
              key={exp.id}
              className={`timeline-item ${isVisible ? "slide-up" : ""}`}
              style={{ animationDelay: `${index * 0.2}s` }}
            >
              <div className="timeline-marker"></div>
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
            </div>
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
            <div
              key={project.id}
              className={`project-card ${isVisible ? "fade-in" : ""}`}
              style={{ animationDelay: `${index * 0.2}s` }}
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
            </div>
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
          <div className="skill-category">
            <h3 className="skill-category-title">Languages</h3>
            <div className="skill-tags">
              {portfolioData.skills.languages.map((skill, i) => (
                <span key={i} className="skill-tag">
                  {skill}
                </span>
              ))}
            </div>
          </div>
          <div className="skill-category">
            <h3 className="skill-category-title">Frontend</h3>
            <div className="skill-tags">
              {portfolioData.skills.frontend.map((skill, i) => (
                <span key={i} className="skill-tag">
                  {skill}
                </span>
              ))}
            </div>
          </div>
          <div className="skill-category">
            <h3 className="skill-category-title">Backend</h3>
            <div className="skill-tags">
              {portfolioData.skills.backend.map((skill, i) => (
                <span key={i} className="skill-tag">
                  {skill}
                </span>
              ))}
            </div>
          </div>
          <div className="skill-category">
            <h3 className="skill-category-title">AI & Agentic Systems</h3>
            <div className="skill-tags">
              {portfolioData.skills.ai.map((skill, i) => (
                <span key={i} className="skill-tag skill-tag-highlight">
                  {skill}
                </span>
              ))}
            </div>
          </div>
          <div className="skill-category">
            <h3 className="skill-category-title">Databases</h3>
            <div className="skill-tags">
              {portfolioData.skills.databases.map((skill, i) => (
                <span key={i} className="skill-tag">
                  {skill}
                </span>
              ))}
            </div>
          </div>
          <div className="skill-category">
            <h3 className="skill-category-title">Tools & Platforms</h3>
            <div className="skill-tags">
              {portfolioData.skills.tools.map((skill, i) => (
                <span key={i} className="skill-tag">
                  {skill}
                </span>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Education Section */}
      <section className="section-container" id="education">
        <div className="section-header">
          <Book className="section-icon" />
          <h2 className="section-title">Education</h2>
        </div>
        <div className="education-card">
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
        </div>
      </section>

      {/* Contact Section */}
      <section className="section-container" id="contact">
        <div className="section-header">
          <Mail className="section-icon" />
          <h2 className="section-title">Let's Connect</h2>
        </div>
        <div className="contact-grid">
          <a
            href={`mailto:${portfolioData.personal.email}`}
            className="contact-item"
          >
            <Mail size={24} />
            <span>{portfolioData.personal.email}</span>
          </a>
          <a
            href={`${import.meta.env.VITE_BACKEND_URL}/api/resume`}
            className="contact-item"
          >
            <Download size={24} />
            <span>Download Resume</span>
          </a>
          <div className="contact-item">
            <MapPin size={24} />
            <span>{portfolioData.personal.location}</span>
          </div>
          <a
            href={portfolioData.personal.github}
            className="contact-item"
            target="_blank"
            rel="noopener noreferrer"
          >
            <Github size={24} />
            <span>GitHub</span>
          </a>
          <a
            href={portfolioData.personal.linkedin}
            className="contact-item"
            target="_blank"
            rel="noopener noreferrer"
          >
            <Linkedin size={24} />
            <span>LinkedIn</span>
          </a>
        </div>
      </section>
    </div>
  );
};

export default PortfolioView;
