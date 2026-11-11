# S MUKUL PRETHAM

[mukulpretham@gmail.com](mailto:mukulpretham@gmail.com) | +91-9059015626 | [github.com/MukulPretham](https://github.com/MukulPretham) | [linkedin.com/in/mukulpretham](https://linkedin.com/in/mukulpretham)

---

## SUMMARY

Full-stack engineer building production features at Lupira and distributed backend systems on the side — from real-time monitoring pipelines to LLM-driven automation. Comfortable across the stack, with a growing focus on backend architecture: concurrency, message queues, and systems built to hold up under load.

---

## TECHNICAL SKILLS

- **Languages:** C, Java, JavaScript, TypeScript, Python, Go
- **Core CS:** Data Structures and Algorithms (DSA), Object-Oriented Programming (OOP), Operating Systems, Computer Networks, DBMS
- **Frontend:** HTML, CSS, Tailwind CSS, React.js, Next.js
- **Backend / APIs:** Node.js, Express.js, Spring Boot, Gin, REST API design, Microservices Architecture
- **Databases:** MongoDB, MySQL, PostgreSQL, SQL, Redis
- **DevOps / Cloud:** Linux, Git, Docker, Kubernetes, CI/CD (GitHub Actions), AWS (EC2, S3)
- **AI:** LangChain, LangGraph, RAG, Chroma DB, LLM APIs, Claude Code, n8n, ML (TensorFlow, Pandas, Jupyter Notebook)

---

## EXPERIENCE

### Full-Stack Intern — Lupira | Next.js, Node.js, AWS (SES, S3)
*June 2026 – August 2026*

- Engineered the POS billing page in Next.js with live product and customer search against a Node.js REST API, cutting average lookup time to under 1 second on a multi-thousand-record catalog.
- Integrated AWS SES for transactional emails on sign-up and purchase events, wiring triggers through both direct API calls and webhooks, keeping delivery reliable across concurrent order volume.
- Secured the platform with session-based authentication and role-based access control (RBAC), scoping billing and admin actions to authorized roles only.
- Built a product and customer photo upload feature backed by AWS S3, handling multipart uploads and serving images directly from cloud storage.

Proof of work — [drive.google.com/file/d/1gurAWKw-19k5W3IEmhUL4m3KO8AKregI](https://drive.google.com/file/d/1gurAWKw-19k5W3IEmhUL4m3KO8AKregI)

---

## PROJECTS

### DocForge — AI-Powered Documentation Automation Tool | React, TypeScript, Express, Prisma, PostgreSQL, LangGraph
[github.com/MukulPretham/doc_forge_fe](https://github.com/MukulPretham/doc_forge_fe) | [github.com/MukulPretham/doc_forge_be](https://github.com/MukulPretham/doc_forge_be)

- Built an 8-node LangGraph agent in TypeScript that explores a GitHub repo, drafts README/docs, and opens a PR on approval.
- Added human-in-the-loop review using LangGraph `interrupt()`, with state checkpointed in PostgreSQL so runs resume across requests.
- Opened PRs through the GitHub Git Data API (blob, tree, commit, ref), authenticated via OAuth with AES-256-GCM encrypted tokens.

### DesignBench — LLD Practice and AI Feedback Platform | Next.js, TypeScript, Prisma, PostgreSQL, LangGraph
[designbench-red.vercel.app](https://designbench-red.vercel.app) | [github.com/MukulPretham/DesignBench](https://github.com/MukulPretham/DesignBench)

- Built an LLD practice platform where users upload code with an explanation and iterate across versioned submissions.
- Designed a 3-pass LangGraph reviewer (approach, code audit, verdict) with typed state and JSON-validation retries.
- Decoupled evaluation from upload: the API returns 201 PENDING, the graph runs in the background, and the client polls until DONE.

### CodeDrop — React Deployment Platform | Node.js, Express.js, Redis, AWS S3, Docker
[github.com/MukulPretham/CodeDrop](https://github.com/MukulPretham/CodeDrop)

- Designed an asynchronous GitHub-to-URL deployment pipeline using Redis-backed worker queues, processing build jobs concurrently so incoming requests never block on a running build.
- Integrated AWS S3 for build artifact storage with unique ID-based retrieval, automating repo fetch, build, and deploy end-to-end via the GitHub API.

---

## CERTIFICATIONS

- Back End Development and APIs — freeCodeCamp, Feb 2025 | Verify
- Supervised Machine Learning — DeepLearning.AI & Stanford University (Coursera), Jun 2025 | Verify

---

## EDUCATION

**Guru Nanak Institute of Technology** — B.Tech, Computer Science and Engineering (AI & ML)
2023 – 2027 | CGPA: 8.0 / 10

**Sri Chaitanya Junior College** — TSBIE (Class XII), 91%

**Sri Chaitanya Techno School** — CBSE (Class X), CGPA: 9.4
