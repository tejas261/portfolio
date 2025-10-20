---
globs: frontend/components.json
description: Ensure shadcn components are installed as TypeScript React
  components in Vite projects and paths match the alias configuration.
alwaysApply: false
---

When (re)installing shadcn/ui components, set components.json to tsx: true and place components under src/components/ui with .tsx extensions. Use the Vite alias @ for imports.