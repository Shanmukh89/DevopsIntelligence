# Auditr — Product Requirements Document
### Automated DevOps Intelligence Platform
**Version:** 1.0  
**Status:** In Development  
**Author:** Antigravity  
**Last Updated:** March 2026

---

## Table of Contents

1. [Project Identity](#1-project-identity)
2. [Problem Statement](#2-problem-statement)
3. [Solution Overview](#3-solution-overview)
4. [Who Is This For](#4-who-is-this-for)
5. [How The Product Works — Big Picture](#5-how-the-product-works--big-picture)
6. [Feature Specifications](#6-feature-specifications)
   - 6.1 Codebase Q&A Chat
   - 6.2 AI Code Reviewer
   - 6.3 Code Clone Detector
   - 6.4 Auto Documentation Generator
   - 6.5 CI Failure Explainer
   - 6.6 Stack Overflow Error Matcher
   - 6.7 Log Anomaly Detector
   - 6.8 Dependency Vulnerability Scanner
   - 6.9 SQL Query Optimizer
   - 6.10 Cloud Cost Optimizer
   - 6.11 Performance Tracer
7. [Tech Stack](#7-tech-stack)
8. [System Architecture](#8-system-architecture)
9. [Database Design](#9-database-design)
10. [API Design](#10-api-design)
11. [Build Order & Timeline](#11-build-order--timeline)
12. [Resume Positioning](#12-resume-positioning)

---

## 1. Project Identity

| Field | Value |
|---|---|
| **Product Name** | Auditr |
| **Resume Title** | Automated DevOps Intelligence Platform |
| **Type** | Web-based SaaS (Software as a Service) |
| **Category** | Developer Tooling |
| **Target Users** | Software development teams of 3–50 engineers |
| **Core Value Prop** | One AI-powered platform that watches your codebase, builds, security, database, and cloud — so your team spends less time on detective work and more time shipping |

---

## 2. Problem Statement

Software development teams today are drowning in tool sprawl and invisible problems.

### 2.1 The Tool Sprawl Problem

A typical development team uses at minimum 8–10 separate tools daily:

- **GitHub** — code and pull requests
- **Jenkins / GitHub Actions** — CI/CD pipelines
- **Slack** — team communication
- **AWS / GCP Console** — cloud infrastructure
- **Datadog / Sentry** — error monitoring
- **Snyk** — security scanning
- **pgAdmin** — database management
- **Confluence / Notion** — documentation

Every one of these tools lives in a different tab, sends different notifications, and requires a different mental context switch. There is no unified view of the health of an engineering team's operation.

### 2.2 The Hidden Problems Problem

Beyond tool sprawl, teams suffer from problems that are hard to see until they've already caused damage:

- A build fails at 11pm. The developer stares at 500 lines of red logs for an hour before finding the actual error on line 412.
- A new developer joins a 3-year-old codebase with 200,000 lines of code. They spend the first two weeks just trying to understand where things live.
- Two developers on different teams independently build an "email sending" function. Six months later there are bugs in both versions and nobody knows they're duplicates.
- A security vulnerability is disclosed for a library your project uses. Nobody on the team sees the advisory for three weeks.
- Your AWS bill climbs from ₹50,000 to ₹1.8 lakh over four months. Nobody notices until finance flags it.
- A slow SQL query is introduced in a Monday deploy. By Thursday, the checkout page takes 8 seconds to load. The team spends two days bisecting which query is the culprit.

### 2.3 The Real Cost

These aren't minor inconveniences. Industry research consistently shows:

- Developers spend **42% of their time** on maintenance, debugging, and understanding existing code rather than writing new features
- The average cost of a **data breach from an unpatched vulnerability** is $4.45 million
- **Unplanned cloud waste** accounts for 32% of cloud spend at most companies
- A **bad code review** that misses a security issue costs 30x more to fix in production than at the PR stage

Auditr exists to eliminate these problems before they start.

---

## 3. Solution Overview

Auditr is a web application that connects to a team's GitHub repositories, CI/CD pipeline, cloud provider, and database — and uses a combination of AI (LLMs, RAG, ML models) to automatically surface problems, answer questions, and give teams actionable intelligence in one place.

The key principle is **zero workflow change for developers**. Developers continue using VS Code, GitHub, and Slack exactly as they do today. Auditr quietly connects in the background and pushes insights to them — through GitHub PR comments, Slack messages, and a central dashboard — without requiring any new habits.

### 3.1 What It Does In One Paragraph

When a developer opens a pull request, Auditr reads the changed code and posts an AI review comment within 60 seconds. When a build fails, Auditr reads the error logs and sends a Slack message explaining what went wrong and how to fix it — alongside the top 3 Stack Overflow solutions for that exact error. At all times, any developer can open the Auditr dashboard and ask "where is the payment logic?" in plain English and get the exact file and line number. Every day, Auditr checks your project's dependencies against known vulnerability databases and alerts you if any library you're using has a security hole. It also watches your cloud bill, clusters spending patterns, and tells you which servers are wasting money.

---

## 4. Who Is This For

### Primary User: The Developer

A software engineer working on a team. They push code, open pull requests, read build logs, and write SQL queries. They want fast feedback on their code without waiting for a senior developer to be free.

**Pain points Auditr solves for them:**
- Instant feedback on their PR before waiting hours for human review
- Plain English explanation when their build breaks
- Ability to navigate an unfamiliar codebase by asking questions

### Secondary User: The Tech Lead / Engineering Manager

Oversees the team. Reviews PRs, monitors build health, manages cloud budget. They want a single view of what's happening across all services.

**Pain points Auditr solves for them:**
- Dashboard showing all PR review statuses at a glance
- Build health across all services in one view
- Cloud cost breakdown with specific savings recommendations
- Security vulnerability alerts before they become incidents

---

## 5. How The Product Works — Big Picture

Auditr operates through two main mechanisms:

### 5.1 Event-Driven (Triggered by GitHub)

This covers everything related to code and builds. When something happens on GitHub — a PR is opened, a build completes, code is pushed — GitHub sends an instant notification to Auditr via a **webhook** (an automatic HTTP POST request). Auditr receives this, processes it using AI, and responds within 60 seconds.

```
Developer pushes code
        ↓
GitHub fires webhook to Auditr server
        ↓
Auditr reads the relevant data (PR diff / build logs)
        ↓
Auditr runs AI analysis
        ↓
Auditr posts result (GitHub comment / Slack message / dashboard update)
```

### 5.2 Scheduled (Background Jobs)

This covers everything that doesn't need to react to an event — vulnerability scanning, cloud cost analysis, dependency monitoring. These run on a schedule (daily, hourly) using a job queue. The results appear on the dashboard and trigger alerts when something is found.

```
Scheduler fires at midnight
        ↓
Job fetches your package.json / requirements.txt
        ↓
Checks each dependency against GitHub Advisory Database API
        ↓
If vulnerability found → creates alert on dashboard + Slack notification
        ↓
Repeats daily
```

### 5.3 On-Demand (User Initiated)

This covers the codebase chat and SQL optimizer — features a user actively triggers from the dashboard.

---

## 6. Feature Specifications

---

### 6.1 Codebase Q&A Chat

**What it does:**  
A chat interface on the dashboard where any developer can ask plain English questions about the codebase — "where is authentication handled?", "which service calls the payments API?", "what does the UserFactory class do?" — and receive precise, cited answers pointing to specific files and line numbers.

**The problem it solves:**  
New developers waste weeks learning a large codebase. Even experienced developers lose time searching for where a specific piece of logic lives. This replaces that search with a conversation.

**How it works technically:**

This feature uses a technique called **RAG (Retrieval Augmented Generation)**. The idea is that instead of feeding the entire codebase to an LLM (which is too expensive and slow), you pre-process the codebase into a searchable index and only feed the relevant parts to the LLM when a question is asked.

**Step 1 — Indexing (runs once on setup, then on every push):**
1. Clone the GitHub repository to the Auditr server
2. Walk every file in the repo (`.py`, `.js`, `.ts`, `.java`, `.go`, etc.)
3. Split each file into chunks of ~300-500 tokens. Chunking is done by function/class boundaries using Tree-sitter (a code parsing library), not arbitrary character counts — this ensures each chunk is semantically meaningful
4. Run each chunk through an embedding model (OpenAI `text-embedding-3-small` or a locally hosted `all-MiniLM-L6-v2` via sentence-transformers) to convert it into a vector — a list of numbers that represents the meaning of that code
5. Store the vector + the original code chunk + metadata (file path, line number, language) in a vector database (pgvector inside PostgreSQL)

**Step 2 — Answering a question (runs on every user query):**
1. User types a question in the dashboard chat
2. The question is also converted into a vector using the same embedding model
3. A similarity search is run against the vector database — finds the top 5 chunks whose vectors are closest to the question vector (cosine similarity)
4. Those 5 chunks (the actual code) are retrieved and assembled into a prompt
5. The prompt is sent to an LLM (Claude claude-sonnet-4-20250514 via Anthropic API or GPT-4o via OpenAI API) with the instruction: "Answer this question about the codebase using only the provided code snippets. Cite the file path and line number."
6. The LLM's response is streamed back to the user in the chat interface

**Already being done by:**
- **GitHub Copilot Chat** — same RAG-over-codebase pattern, Microsoft's implementation
- **Cursor AI** — entire product built around this concept
- **Codeium** — free alternative, same approach
- **LangChain** — has a step-by-step tutorial called "Chat with your code" that is the canonical reference for this implementation
- **LlamaIndex** — another library with built-in code indexing support

**Reference implementation:** LangChain's `RetrievalQA` chain with a `FAISS` or `Chroma` vector store is the starting point. The main customisation is using Tree-sitter for smarter chunking instead of character-based splitting.

**Domain:** RAG  
**Difficulty:** Easy  
**Estimated build time:** 1 week

---

### 6.2 AI Code Reviewer

**What it does:**  
Every time a developer opens a pull request on GitHub, Auditr automatically reads the changed lines of code and posts a review comment on the PR within 60 seconds — flagging security vulnerabilities, potential bugs, bad practices, performance issues, and suggestions for improvement. Looks identical to a comment from a human teammate.

**The problem it solves:**  
Human code review is slow — reviewers are often busy, in meetings, or in a different timezone. Small issues (null pointer risks, missing error handling, SQL injection vulnerabilities) slip through because reviewers are tired. AI review catches these instantly and consistently.

**How it works technically:**

1. A GitHub webhook is configured on the repository pointing to Auditr's `/webhooks/github` endpoint
2. When a PR is opened or updated, GitHub sends a POST request to this endpoint with the PR details
3. Auditr calls the **GitHub REST API** to fetch the **diff** — the exact lines added and removed in the PR. This is just a text format showing `+` for added lines and `-` for removed lines
4. The diff is inserted into a carefully crafted prompt and sent to an LLM
5. The LLM response is parsed to extract structured issues (severity, line number, description, suggestion)
6. Auditr calls the **GitHub REST API** again — this time to post a review comment on the PR using `POST /repos/{owner}/{repo}/pulls/{pull_number}/reviews`

**The prompt structure:**
```
You are an expert code reviewer with 10 years of experience. 
Review the following code changes and identify:
- Security vulnerabilities (label: SECURITY)
- Potential bugs or edge cases (label: BUG)  
- Performance issues (label: PERFORMANCE)
- Style or maintainability issues (label: STYLE)

For each issue, specify the exact line number, severity (critical/warning/info), 
a one-sentence description, and a concrete fix suggestion.

Code diff:
{diff}
```

**Already being done by:**
- **CodeRabbit** — production tool, $12/month per user, does exactly this
- **PR-Agent by CodiumAI** — open source, can self-host, excellent reference
- **Reviewpad** — GitHub Action that does LLM review
- **GitHub Copilot for PRs** — Microsoft's enterprise version

**Reference implementation:** CodiumAI's PR-Agent is fully open source on GitHub and is the best reference. The core logic in `pr_agent/git_providers/github_provider.py` shows exactly how to fetch diffs and post comments.

**Domain:** Gen AI  
**Difficulty:** Easy  
**Estimated build time:** 3–4 days

---

### 6.3 Code Clone Detector

**What it does:**  
Periodically scans the entire codebase to find functions or blocks of code that do the same thing but are written in multiple different places by different developers. Surfaces these as "clone pairs" on the dashboard so the team can consolidate them into shared utilities.

**The problem it solves:**  
In large codebases, especially ones with multiple teams, the same logic gets written independently by different developers. A bug fixed in one copy never gets fixed in the others. Technical debt accumulates silently.

**How it works technically:**

This is the most technically interesting ML feature in Auditr. It uses **code embeddings** to find semantic similarity — meaning it finds code that does the same thing even if variable names, structure, and language keywords are different.

1. Use **Tree-sitter** to parse every source file into an Abstract Syntax Tree (AST) and extract individual functions/methods as discrete units
2. Run each function through **CodeBERT** — a pre-trained transformer model from Microsoft specifically trained on code, available for free on HuggingFace (`microsoft/codebert-base`). This converts each function into a 768-dimensional embedding vector
3. Store all function embeddings in a matrix
4. Compute **cosine similarity** between every pair of function embeddings using `numpy` or `faiss`
5. Flag pairs with similarity above a configurable threshold (default: 0.85) as potential clones
6. Group clones by cluster and surface them on the dashboard with side-by-side diffs

**The key insight:** CodeBERT was trained on millions of code-comment pairs across 6 programming languages. Its embeddings capture semantic meaning — so `calculateTotal(items)` and `computeSum(products)` that do the same thing will have very similar vectors even though they share no keywords.

**Already being done by:**
- **SonarQube** — enterprise code quality tool, has a "duplications" feature
- **PMD CPD** (Copy-Paste Detector) — open source, token-based (less sophisticated than embedding approach)
- **Academic tool CCFinderX** — research-grade clone detection
- **Sourcegraph** — code intelligence platform with clone detection

**Reference implementation:** The HuggingFace `transformers` library makes loading CodeBERT trivial: `AutoModel.from_pretrained("microsoft/codebert-base")`. The `faiss` library from Facebook AI handles fast similarity search at scale. Search GitHub for "codebert clone detection" for multiple open source reference implementations.

**Domain:** ML / Deep Learning  
**Difficulty:** Hard  
**Estimated build time:** 2 weeks

---

### 6.4 Auto Documentation Generator

**What it does:**  
Reads your codebase and automatically generates readable documentation — function descriptions, parameter explanations, usage examples, and module overviews. Re-generates whenever code changes so docs are never stale.

**The problem it solves:**  
Documentation is always outdated, always incomplete, and always the last thing developers do. Teams waste hours reading source code to understand what a function does when a clear docstring would take 5 seconds.

**How it works technically:**

1. On each push to the repository, identify which files changed
2. For each changed file, extract functions/classes that lack documentation or whose documentation is older than the last code change
3. Send each undocumented function to an LLM with its source code
4. Prompt:
```
Generate a documentation comment for this function in the appropriate 
format for its language (JSDoc for JavaScript, Google-style docstring 
for Python, JavaDoc for Java). Include: purpose, parameters with types, 
return value, and one usage example. Be concise.

Function:
{source_code}
```
5. Store generated docs in a separate docs database (not modifying source files unless the team opts in)
6. Display in a browseable docs section on the dashboard

**Already being done by:**
- **Mintlify Doc Writer** — VS Code extension, same LLM prompt approach
- **GitHub Copilot** — inline doc generation in the editor
- **Swimm** — AI-powered documentation platform for teams
- **Stenography** — automatic docstring generation service

**Reference implementation:** This is a pure LLM prompt. No special libraries needed beyond the LLM API client. The complexity is in the incremental update logic — tracking which functions have changed since last documentation using git blame/diff.

**Domain:** Gen AI  
**Difficulty:** Easy  
**Estimated build time:** 3–4 days

---

### 6.5 CI Failure Explainer

**What it does:**  
When a CI/CD build fails, Auditr reads the error logs and sends a Slack message within 60 seconds explaining what went wrong in plain English and giving a specific, actionable fix — tagging the developer who made the failing push.

**The problem it solves:**  
Build logs are dense, technical, and often hundreds of lines long. The actual error is usually buried. Developers waste 30–60 minutes reading logs to understand something that could be explained in 2 sentences.

**How it works technically:**

1. GitHub webhook fires when a workflow run completes with a `failure` status
2. Auditr calls `GET /repos/{owner}/{repo}/actions/runs/{run_id}/logs` to download the full log archive (a `.zip` file)
3. Extract the log text, take the **last 150 lines** (where errors always appear) to avoid token limits
4. Send to LLM with prompt:
```
The following is the end of a failed CI/CD build log. 

In 2-3 plain English sentences, explain what caused the failure — 
do not repeat the error text verbatim, translate it to human language.

Then provide one specific, actionable step to fix it. Be direct.

Log:
{last_150_lines}
```
5. Send the response to Slack using the **Slack Web API** (`chat.postMessage`) to the team's `#builds` channel, tagging the commit author

**Already being done by:**
- **Trunk.io** — CI management platform with AI failure analysis
- **BuildPulse** — flaky test detection and CI intelligence
- Dozens of open source GitHub Action scripts on GitHub Marketplace
- **LinearB** — engineering metrics platform with CI insights

**Reference implementation:** This is the simplest feature in Auditr. The entire core is: receive webhook → download logs → call LLM API → call Slack API. Search GitHub for "github actions webhook slack notification" for the boilerplate, then add the LLM call in the middle. The Slack Python SDK (`slack_sdk`) and GitHub's official `PyGithub` library handle the API calls.

**Domain:** Gen AI  
**Difficulty:** Easy  
**Estimated build time:** 2–3 days

---

### 6.6 Stack Overflow Error Matcher

**What it does:**  
When a build fails, alongside the AI explanation, Auditr also automatically searches Stack Overflow for the exact error message and surfaces the top 3 most upvoted real-world solutions — giving the developer proven fixes from the developer community.

**The problem it solves:**  
The first thing any developer does when they hit an error is Google it and open Stack Overflow. Auditr does this automatically so the developer doesn't have to context-switch. The AI explanation tells you what went wrong; the Stack Overflow results tell you what others did to fix the exact same thing.

**How it works technically:**

1. After extracting the error message from the build log (a regex to isolate the main exception line), pass it to the **Stack Exchange API**
2. Call `GET https://api.stackexchange.com/2.3/search/advanced` with parameters: `q={error_message}`, `tagged=python` (or relevant language), `sort=votes`, `site=stackoverflow`
3. This returns JSON with the top questions matching the error, including vote counts, answer counts, and links
4. Filter for questions with accepted answers and at least 10 votes
5. For each result, call `GET /questions/{id}/answers` to get the top answer text
6. Summarise each answer with a one-sentence description and attach the link
7. Include these alongside the AI explanation in the Slack message and dashboard

**Note:** This uses the Stack Exchange **official public API** — no scraping required. The API is free for up to 300 requests per day without a key, 10,000 with a registered key. This is simply a JSON API integration, not web scraping.

**Already being done by:**
- Stack Overflow's own **Overflow AI** — they built this into their platform
- **Pieces for Developers** — developer context tool that does SO matching
- **Raycast** — developer productivity tool with SO integration
- Every major IDE has Stack Overflow search integration

**Reference implementation:** The Stack Exchange API documentation at `api.stackexchange.com` is excellent. The `requests` library in Python is all you need. The main engineering challenge is extracting a clean, searchable error string from a messy log — this is a regex problem, not an ML problem.

**Domain:** Scraping / API Integration  
**Difficulty:** Easy  
**Estimated build time:** 2 days

---

### 6.7 Log Anomaly Detector

**What it does:**  
Watches your application's server logs in real time. Learns what "normal" looks like over 1–2 weeks of data. Then continuously monitors for deviations — unusual error rates, response time spikes, sudden drops in throughput — and alerts the team before users start complaining.

**The problem it solves:**  
Production issues usually have early warning signs in the logs — small spikes, subtle error rate increases, latency creep — that go unnoticed because nobody has time to manually watch logs. By the time someone notices, it's already a major incident.

**How it works technically:**

This uses **unsupervised machine learning** — specifically an **LSTM Autoencoder** — to learn normal patterns and flag anomalies.

**Phase 1 — Training (runs once with historical data):**
1. Collect 2–4 weeks of historical logs from the application
2. Parse logs into structured features: error rate per minute, average response time per minute, request count per minute, 5xx rate per minute
3. Create rolling windows of 60 time steps (representing 60 minutes of data)
4. Train an **LSTM Autoencoder** on this data. The autoencoder learns to compress and reconstruct normal log patterns. Its reconstruction error on normal data is low
5. Calculate the 99th percentile reconstruction error on training data — this becomes the anomaly threshold

**Phase 2 — Live monitoring (runs continuously):**
1. Ingest real-time logs via a log shipper (Filebeat → Logstash, or directly via the application logging to a Kafka topic)
2. Every minute, compute the same features from the latest 60 minutes of data
3. Run through the trained LSTM Autoencoder
4. If reconstruction error exceeds the threshold, an anomaly is detected
5. Alert sent to Slack: "Anomaly detected on payments-service — error rate is 12x above baseline for the last 8 minutes"

**LSTM Autoencoder architecture:**
```
Input (60 timesteps × 4 features)
  → LSTM Encoder (64 units) → Bottleneck (32 units)
  → LSTM Decoder (64 units)
  → Output (reconstructed sequence)
Loss: Mean Squared Error between input and reconstruction
```

**Already being done by:**
- **Datadog** — enterprise observability platform, uses similar ML under the hood
- **Elastic SIEM** — anomaly detection built into Elasticsearch
- **Splunk ITSI** — IT service intelligence with ML-based alerting
- Multiple academic papers on LSTM autoencoders for log anomaly detection

**Reference implementation:** Search GitHub for "LSTM autoencoder anomaly detection time series" — multiple well-documented Python implementations exist. The PyTorch implementation is simpler than TensorFlow for this use case. The `PyTorch Forecasting` library also has built-in anomaly detection support. The key reference paper is "Robust Log-Based Anomaly Detection on Unstable Log Data" (2019).

**Domain:** ML / Deep Learning  
**Difficulty:** Hard  
**Estimated build time:** 2–3 weeks

---

### 6.8 Dependency Vulnerability Scanner

**What it does:**  
Every day, Auditr reads your project's dependency file (`requirements.txt`, `package.json`, `pom.xml`, etc.), checks each dependency against public vulnerability databases, and immediately alerts the team if any library your project uses has a known security hole — with the CVE ID, severity score, and recommended version to upgrade to.

**The problem it solves:**  
Security vulnerabilities in open source libraries are disclosed every single day. The Log4Shell vulnerability (2021) affected millions of applications for months because teams didn't know they were using the vulnerable version of Log4j. Keeping track of dependency security manually is impossible at scale.

**How it works technically:**

1. A daily scheduled job reads the dependency file from the connected GitHub repository
2. Parse the file to extract each dependency name and pinned version
3. For each dependency, call the **GitHub Advisory Database API** (free, no key required): `GET https://api.github.com/advisories?ecosystem=pip&package={name}`
4. This returns all known security advisories for that package in JSON format, including: CVE ID, GHSA ID, severity (critical/high/medium/low), affected version ranges, patched version
5. Check if the pinned version falls within any affected version range
6. If a vulnerability is found, create an alert in the Auditr database and send a Slack notification
7. The dashboard shows a live "Security" panel listing all current vulnerabilities with severity badges

**Vulnerability severity scoring uses CVSS (Common Vulnerability Scoring System):**
- Critical (9.0–10.0): Immediate action required
- High (7.0–8.9): Fix within 48 hours
- Medium (4.0–6.9): Fix in next sprint
- Low (0.1–3.9): Fix when convenient

**Already being done by:**
- **Snyk** — market leader, $52–$590/month per team
- **GitHub Dependabot** — free, built into GitHub, does exactly this
- **OWASP Dependency-Check** — open source, widely used in enterprise
- **npm audit** — built into npm itself for JavaScript projects
- **pip-audit** — Python's equivalent

**Reference implementation:** GitHub's Advisory Database API is the simplest starting point — it's REST, returns JSON, and requires no authentication for public data. For more comprehensive data, the **OSV (Open Source Vulnerabilities)** database at `osv.dev` provides a unified API across all ecosystems. The Python `packaging` library handles version range comparison (checking if version 2.3.1 is in the affected range `>=2.0.0, <2.4.0`).

**Domain:** Scraping / API Integration  
**Difficulty:** Medium  
**Estimated build time:** 1 week

---

### 6.9 SQL Query Optimizer

**What it does:**  
A developer pastes a slow SQL query into the Auditr dashboard. Auditr runs it through PostgreSQL's `EXPLAIN ANALYZE` command to generate a performance report, then sends both the original query and the performance report to an LLM which rewrites the query for better performance and explains every change it made in plain English.

**The problem it solves:**  
Most developers can write SQL but don't have deep expertise in query optimization — understanding query plans, choosing the right indexes, avoiding sequential scans. A slow query in production can take down an entire service. This makes query optimization accessible to every developer on the team.

**How it works technically:**

1. Developer pastes a query into the SQL Optimizer page on the dashboard
2. Auditr connects to a **read replica** of the team's database (important — never run EXPLAIN ANALYZE on the primary production database as it actually executes the query)
3. Runs `EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}` — this executes the query and returns a full JSON performance report including: sequential scans vs index scans, rows examined vs rows returned, execution time per node, buffer hits vs disk reads
4. The JSON report is summarised into human-readable key metrics: total execution time, number of seq scans, missing index indicators
5. Both the original query and the summarised EXPLAIN output are sent to an LLM:
```
You are a PostgreSQL performance expert. The following SQL query is running slowly.

Original query:
{query}

EXPLAIN ANALYZE output (summarised):
{explain_output}

Provide:
1. A rewritten version of the query that would perform better
2. A numbered list of every change you made and why
3. Any indexes that should be created (write the CREATE INDEX statement)
```
6. The response is displayed side-by-side with the original query on the dashboard

**Already being done by:**
- **EverSQL** — dedicated SQL optimization service, $49/month
- **pganalyze** — PostgreSQL performance monitoring with query analysis
- **Metis** — AI-powered database observability
- **Postgres.ai** — database lab with query analysis

**Reference implementation:** PostgreSQL's `EXPLAIN ANALYZE` is documented exhaustively in the official Postgres docs. The `psycopg2` Python library connects to PostgreSQL. The hard part is parsing the EXPLAIN JSON output into a readable summary — there are open source Python parsers for this (search "pev2" — Postgres Explain Visualizer, which parses the JSON format).

**Domain:** Gen AI  
**Difficulty:** Medium  
**Estimated build time:** 1 week

---

### 6.10 Cloud Cost Optimizer

**What it does:**  
Ingests your AWS or GCP billing export (a CSV file you download from the cloud console), runs ML clustering on spending patterns, and produces a dashboard showing exactly where money is being wasted — which EC2 instances are oversized, which RDS replicas are idle, which S3 buckets contain old backups — with a specific dollar/rupee saving for each recommendation.

**The problem it solves:**  
Cloud bills are complex, itemised across hundreds of line items, and grow silently. Most teams have no systematic way to identify waste. The average company wastes 32% of its cloud spend on idle or oversized resources.

**How it works technically:**

1. User uploads their AWS Cost and Usage Report (CUR) CSV from the AWS Billing Console, or connects via the **AWS Cost Explorer API** (`boto3` library)
2. Load the CSV into a Pandas DataFrame. Key columns: service name, resource ID, usage type, usage amount, cost, usage start date
3. Feature engineer: compute **utilization rate** (average CPU/memory usage as a percentage of provisioned capacity — pulled from CloudWatch metrics via `boto3`), cost per day, days since last meaningful usage
4. Run **K-Means clustering** on these features to group resources into natural clusters. Typical clusters that emerge: "high cost, low utilization" (waste candidates), "high cost, high utilization" (appropriately sized), "low cost, any utilization" (not worth optimising)
5. For resources in the "high cost, low utilization" cluster, generate specific recommendations based on rule-based logic:
   - EC2 instance with <10% average CPU over 14 days → "Downsize from m5.xlarge to m5.large, save $180/month"
   - RDS instance with 0 connections in 7 days → "This read replica appears unused, terminating it saves $240/month"
   - S3 objects last accessed >180 days → "Move to S3 Glacier, saves $45/month"
6. Display total potential savings on the dashboard with an itemised breakdown

**Already being done by:**
- **CloudHealth by VMware** — enterprise cloud cost management
- **Spot.io** — cloud optimization platform
- **AWS Trusted Advisor** — AWS's own built-in cost recommendations
- **Infracost** — open source cloud cost estimation

**Reference implementation:** AWS's `boto3` library is comprehensive and well-documented for fetching Cost Explorer data and CloudWatch metrics. Scikit-learn's `KMeans` is 5 lines of code. The main complexity is in the feature engineering and the rule-based recommendation generation after clustering. AWS has public documentation on all CUR column definitions.

**Domain:** ML  
**Difficulty:** Medium  
**Estimated build time:** 1.5 weeks

---

### 6.11 Performance Tracer

**What it does:**  
Collects timing data from every step a user request travels through your microservices — from the API gateway through each service to the database and back. Renders this as a **flame graph** on the dashboard showing exactly how long each step takes, making it immediately obvious which service or database call is causing slowness.

**The problem it solves:**  
In a microservices architecture, a slow user-facing request could be caused by any one of 10 different services. Without distributed tracing, finding the slow part requires manually adding timing logs to each service and correlating them. This is a 2-day debugging exercise that should take 2 minutes.

**How it works technically:**

This feature uses the **OpenTelemetry** standard — the industry-standard open source framework for distributed tracing.

**Instrumentation (in each microservice):**
1. Add the OpenTelemetry SDK to each service (available for Python, Node.js, Java, Go, etc.)
2. Auto-instrumentation patches common libraries (FastAPI, Django, Express, SQLAlchemy) automatically — no manual code changes required in most cases
3. Each incoming request automatically gets a unique `trace_id`. Each step within the request creates a `span` — a record of: service name, operation name, start time, end time, status, any errors

**Collection:**
1. All spans are sent to an **OpenTelemetry Collector** running as a sidecar container
2. The Collector exports spans to **Jaeger** (open source distributed tracing backend) or directly to **ClickHouse** for storage at scale

**Visualisation:**
1. Auditr queries the trace storage to retrieve all spans for a given trace ID
2. Assembles them into a parent-child tree (each span knows its parent span ID)
3. Renders a flame graph in the React dashboard using a library like `react-flame-graph` or D3.js
4. The flame graph shows the full request timeline with each span as a coloured bar — width represents duration, colour represents service

**Already being done by:**
- **Jaeger** — open source distributed tracing, originally built by Uber
- **Zipkin** — open source, originally built by Twitter
- **Datadog APM** — enterprise version, $31/host/month
- **New Relic** — enterprise observability platform
- **Honeycomb** — observability platform focused on tracing

**Reference implementation:** OpenTelemetry's official docs at `opentelemetry.io` are the canonical reference. The auto-instrumentation packages for Python (`opentelemetry-auto-instrumentation`) and Node.js (`@opentelemetry/auto-instrumentations-node`) require almost no code changes to existing services. Jaeger has an official Docker image that can be running in 2 commands.

**Domain:** Systems / Observability  
**Difficulty:** Hard  
**Estimated build time:** 2 weeks

---

## 7. Tech Stack

### 7.1 Frontend

| Technology | Purpose | Why |
|---|---|---|
| **Next.js 14** | Web framework | React-based, handles both frontend and lightweight API routes. Industry standard for SaaS dashboards. |
| **TypeScript** | Language | Type safety reduces bugs significantly. Expected in any professional codebase. |
| **Tailwind CSS** | Styling | Utility-first CSS. Fast to build with, looks clean. |
| **shadcn/ui** | Component library | Pre-built accessible components (tables, cards, charts) that look professional. |
| **Recharts** | Data visualisation | React-native charting library for cost graphs, build success rates, etc. |
| **D3.js** | Flame graph | Custom flame graph rendering for the performance tracer. |
| **Socket.io (client)** | Real-time updates | Live dashboard updates when builds fail or new alerts arrive. |

### 7.2 Backend

| Technology | Purpose | Why |
|---|---|---|
| **FastAPI (Python)** | Main API server | Python is the right choice because all the ML/AI libraries are Python-first. FastAPI is the modern, fast, async Python web framework. |
| **Celery** | Background job queue | Handles scheduled jobs (daily vulnerability scans, cloud cost analysis) and async tasks (log processing, embedding generation). |
| **Redis** | Message broker + cache | Celery uses Redis as its message broker. Also caches frequently accessed data. |
| **Socket.io (server)** | WebSocket server | Pushes real-time alerts and build status updates to the frontend. |

### 7.3 Databases

| Technology | Purpose | Why |
|---|---|---|
| **PostgreSQL** | Primary database | Stores users, repositories, alerts, PR reviews, feature data. Mature, reliable, ACID compliant. |
| **pgvector** | Vector storage | PostgreSQL extension that adds vector similarity search. Stores code embeddings for the codebase Q&A feature. Avoids needing a separate vector database. |
| **ClickHouse** | Time-series / logs | Columnar database optimised for analytics queries on large volumes of log data and trace spans. Can query billions of log lines in milliseconds. |
| **Redis** | Cache + queue | Already listed above. Also used to cache embedding results and rate limit API calls. |

### 7.4 AI / ML

| Technology | Purpose | Why |
|---|---|---|
| **OpenAI API (GPT-4o)** | LLM for all Gen AI features | Code review, CI explanation, SQL optimization, doc generation. GPT-4o has strong code understanding. |
| **Anthropic API (Claude)** | Alternative LLM | Claude claude-sonnet-4-20250514 is strong at code review. Can switch between providers. |
| **OpenAI Embeddings API** | Code embedding for Q&A | `text-embedding-3-small` for converting code chunks to vectors. |
| **sentence-transformers** | Local embedding alternative | `all-MiniLM-L6-v2` for generating embeddings without API cost. |
| **CodeBERT (HuggingFace)** | Code clone detection | `microsoft/codebert-base` — pre-trained on code, free, no API cost. |
| **PyTorch** | LSTM autoencoder training | For the log anomaly detector. Most flexible deep learning framework. |
| **scikit-learn** | K-Means clustering | For the cloud cost optimizer. Standard ML library. |
| **LangChain** | RAG orchestration | Handles the chunking, embedding, retrieval chain for codebase Q&A. |

### 7.5 Infrastructure

| Technology | Purpose | Why |
|---|---|---|
| **Docker** | Containerisation | Every service runs in a Docker container. Consistent across environments. |
| **Docker Compose** | Local orchestration | Runs all services locally in one command. |
| **GitHub Actions** | CI/CD for Auditr itself | Auditr uses CI/CD for its own deployments — dogfooding. |
| **Nginx** | Reverse proxy | Routes traffic from the outside world to the appropriate service. |
| **Jaeger** | Trace storage | Stores and visualises distributed traces for the performance tracer. |
| **Tree-sitter** | Code parsing | Parses source code into ASTs for smart chunking and function extraction. |

### 7.6 External APIs & Services

| Service | Feature | Cost |
|---|---|---|
| **GitHub REST API** | Webhooks, PR comments, fetching diffs, build logs | Free for public repos, included in GitHub plans for private |
| **Slack Web API** | Sending alerts and build explanations | Free tier is sufficient |
| **Stack Exchange API** | Searching Stack Overflow for error solutions | Free, 10,000 requests/day with key |
| **GitHub Advisory Database API** | Vulnerability data for dependencies | Free, no auth required |
| **AWS Cost Explorer API** | Cloud billing data | $0.01 per API request |
| **OpenTelemetry Collector** | Trace collection from microservices | Open source, free |

---

## 8. System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                             │
│              Next.js Dashboard (Browser)                        │
│     Real-time updates via WebSocket (Socket.io)                 │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTPS / WSS
┌──────────────────────────▼──────────────────────────────────────┐
│                      API GATEWAY (Nginx)                        │
│              Rate limiting · Auth · SSL termination             │
└──────┬───────────────────┬───────────────────┬──────────────────┘
       │                   │                   │
┌──────▼──────┐   ┌────────▼───────┐   ┌──────▼──────────┐
│  FastAPI    │   │  Socket.io     │   │  Webhook        │
│  REST API   │   │  Server        │   │  Handler        │
│  (main)     │   │  (real-time)   │   │  (GitHub events)│
└──────┬──────┘   └────────────────┘   └──────┬──────────┘
       │                                       │
       │         ┌─────────────────────────────▼──────┐
       │         │           Celery Workers            │
       │         │  Task Queue (Redis broker)          │
       │         │  - PR review jobs                   │
       │         │  - Embedding generation             │
       │         │  - Vulnerability scans (daily)      │
       │         │  - Cloud cost analysis (daily)      │
       │         │  - Log anomaly detection (1min)     │
       │         └─────────────────────────────────────┘
       │
┌──────▼────────────────────────────────────────────────────────┐
│                        DATA LAYER                              │
│  PostgreSQL + pgvector │  ClickHouse  │  Redis Cache          │
│  (main data + vectors) │  (logs+traces│  (cache + queue)      │
└───────────────────────────────────────────────────────────────┘
       │
┌──────▼────────────────────────────────────────────────────────┐
│                    EXTERNAL SERVICES                           │
│  OpenAI / Anthropic API  │  GitHub API  │  Slack API          │
│  Stack Exchange API      │  AWS API     │  GitHub Advisory API │
└───────────────────────────────────────────────────────────────┘
```

---

## 9. Database Design

### Core Tables (PostgreSQL)

```sql
-- Teams using Auditr
CREATE TABLE teams (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Connected GitHub repositories
CREATE TABLE repositories (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  team_id UUID REFERENCES teams(id),
  github_repo_id BIGINT UNIQUE NOT NULL,
  full_name VARCHAR(255) NOT NULL,  -- e.g. "antigravity/auditr"
  default_branch VARCHAR(100) DEFAULT 'main',
  webhook_secret VARCHAR(255),
  last_indexed_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Code chunks and their embeddings (pgvector)
CREATE TABLE code_embeddings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  repo_id UUID REFERENCES repositories(id),
  file_path VARCHAR(500) NOT NULL,
  start_line INTEGER NOT NULL,
  end_line INTEGER NOT NULL,
  chunk_text TEXT NOT NULL,
  embedding vector(1536),  -- OpenAI embedding dimensions
  language VARCHAR(50),
  last_updated TIMESTAMP DEFAULT NOW()
);
CREATE INDEX ON code_embeddings USING ivfflat (embedding vector_cosine_ops);

-- PR review records
CREATE TABLE pr_reviews (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  repo_id UUID REFERENCES repositories(id),
  pr_number INTEGER NOT NULL,
  pr_title VARCHAR(500),
  author_github_login VARCHAR(100),
  status VARCHAR(50),  -- 'clean', 'issues_found', 'critical'
  issues_count INTEGER DEFAULT 0,
  review_body TEXT,
  reviewed_at TIMESTAMP DEFAULT NOW()
);

-- Individual issues found in PR reviews
CREATE TABLE pr_issues (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  pr_review_id UUID REFERENCES pr_reviews(id),
  severity VARCHAR(20),  -- 'critical', 'warning', 'info'
  category VARCHAR(50),  -- 'security', 'bug', 'performance', 'style'
  file_path VARCHAR(500),
  line_number INTEGER,
  description TEXT,
  suggestion TEXT
);

-- CI build records
CREATE TABLE builds (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  repo_id UUID REFERENCES repositories(id),
  github_run_id BIGINT UNIQUE,
  branch VARCHAR(100),
  commit_sha VARCHAR(40),
  author_github_login VARCHAR(100),
  status VARCHAR(50),  -- 'success', 'failure', 'cancelled'
  ai_explanation TEXT,
  stackoverflow_results JSONB,
  started_at TIMESTAMP,
  completed_at TIMESTAMP
);

-- Security vulnerability alerts
CREATE TABLE vulnerability_alerts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  repo_id UUID REFERENCES repositories(id),
  package_name VARCHAR(255) NOT NULL,
  installed_version VARCHAR(100),
  patched_version VARCHAR(100),
  cve_id VARCHAR(50),
  ghsa_id VARCHAR(50),
  severity VARCHAR(20),
  description TEXT,
  status VARCHAR(50) DEFAULT 'open',  -- 'open', 'dismissed', 'resolved'
  detected_at TIMESTAMP DEFAULT NOW()
);

-- Code clone pairs
CREATE TABLE code_clones (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  repo_id UUID REFERENCES repositories(id),
  file_path_a VARCHAR(500),
  start_line_a INTEGER,
  file_path_b VARCHAR(500),
  start_line_b INTEGER,
  similarity_score FLOAT,
  detected_at TIMESTAMP DEFAULT NOW()
);

-- Cloud cost recommendations
CREATE TABLE cost_recommendations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  team_id UUID REFERENCES teams(id),
  provider VARCHAR(50),  -- 'aws', 'gcp'
  resource_id VARCHAR(255),
  resource_type VARCHAR(100),
  current_cost_monthly DECIMAL(10,2),
  potential_saving DECIMAL(10,2),
  recommendation TEXT,
  status VARCHAR(50) DEFAULT 'open',
  detected_at TIMESTAMP DEFAULT NOW()
);
```

---

## 10. API Design

### Webhook Endpoints (received from GitHub)

```
POST /webhooks/github
  → Handles: pull_request, workflow_run, push events
  → Verified using HMAC-SHA256 signature (X-Hub-Signature-256 header)
```

### REST API Endpoints (consumed by frontend)

```
# Repositories
GET  /api/repos                          → List connected repos
POST /api/repos                          → Connect a new repo
GET  /api/repos/{repo_id}/status         → Health overview for a repo

# Codebase Q&A
POST /api/repos/{repo_id}/chat           → Ask a question, returns streamed answer
GET  /api/repos/{repo_id}/chat/history   → Past questions and answers

# PR Reviews
GET  /api/repos/{repo_id}/prs            → List all reviewed PRs
GET  /api/repos/{repo_id}/prs/{pr_id}    → Single PR review details

# Builds
GET  /api/repos/{repo_id}/builds         → Build history with AI explanations
GET  /api/repos/{repo_id}/builds/{id}    → Single build with SO results

# Security
GET  /api/repos/{repo_id}/vulnerabilities         → All open vulnerability alerts
POST /api/repos/{repo_id}/vulnerabilities/{id}/dismiss → Dismiss an alert

# SQL Optimizer
POST /api/sql/optimize                   → Submit query, returns optimized version

# Cloud Costs
GET  /api/costs                          → Cost recommendations
POST /api/costs/import                   → Upload billing CSV
GET  /api/costs/summary                  → Total spend + potential savings

# Performance Traces
GET  /api/traces                         → Recent traces
GET  /api/traces/{trace_id}              → Full trace with flame graph data
```

---

## 11. Build Order & Timeline

Build one feature at a time. Each week ends with something working and deployable.

### Phase 1 — Core (Weeks 1–4)
*Goal: Have something impressive to show after one month*

| Week | Feature | Why First |
|---|---|---|
| Week 1 | Project setup + GitHub webhook infrastructure + dashboard skeleton | Everything else depends on this plumbing |
| Week 2 | CI Failure Explainer + Stack Overflow Matcher | Easiest features, immediately useful, validates the whole webhook → LLM → Slack pipeline |
| Week 3 | AI Code Reviewer | Builds directly on the webhook infrastructure already built |
| Week 4 | Codebase Q&A Chat | The flagship feature. Needs most polish. |

**End of Phase 1:** You have a working product. A team can connect their repo and get AI PR reviews, build failure explanations with SO results, and ask questions about their codebase.

### Phase 2 — Intelligence (Weeks 5–8)
*Goal: Add the ML and security features*

| Week | Feature | Notes |
|---|---|---|
| Week 5 | Dependency Vulnerability Scanner | Medium difficulty, high value, uses clean APIs |
| Week 6 | Auto Documentation Generator | Quick win, pure LLM |
| Week 7 | SQL Query Optimizer | Standalone feature, good demo |
| Week 8 | Cloud Cost Optimizer | ML + data viz, visually impressive |

### Phase 3 — Advanced (Weeks 9–12)
*Goal: Add the hard features that show real depth*

| Week | Feature | Notes |
|---|---|---|
| Week 9–10 | Log Anomaly Detector | Hardest ML feature, needs historical data |
| Week 11 | Code Clone Detector | CodeBERT + FAISS, hard but impressive |
| Week 12 | Performance Tracer + Polish | OpenTelemetry setup, flame graph UI |

**End of Phase 3:** Complete product. All 11 features working.

---

## 12. Resume Positioning

### The Line

```
Auditr — Automated DevOps Intelligence Platform
```

### Bullet Points for Resume

```
• Built Auditr, a full-stack AI platform that automates code review, 
  build failure diagnosis, and security scanning for software development teams

• Implemented RAG pipeline using LangChain, CodeBERT embeddings, and pgvector 
  to enable natural language Q&A over entire codebases with sub-2s response times

• Developed GitHub webhook integration that triggers LLM-based PR reviews 
  (GPT-4o / Claude) and posts structured feedback as native GitHub review comments

• Trained LSTM autoencoder on production log data for real-time anomaly 
  detection, reducing mean time to detection from hours to under 5 minutes

• Integrated GitHub Advisory Database API for daily dependency vulnerability 
  scanning across Python and JavaScript projects with Slack alerting

• Built K-Means clustering pipeline on AWS Cost Explorer data to identify 
  cloud waste, generating itemised savings recommendations per resource

• Implemented distributed tracing using OpenTelemetry and Jaeger, visualised 
  as interactive flame graphs in a React/Next.js dashboard

• Stack: Python, FastAPI, Next.js, TypeScript, PostgreSQL, pgvector, 
  ClickHouse, Redis, Celery, Docker, LangChain, PyTorch, scikit-learn
```

### Domains Covered (for skills section)

- **Generative AI** — LLM integration (OpenAI, Anthropic), prompt engineering
- **RAG** — LangChain, vector databases, semantic search, embeddings
- **Machine Learning** — LSTM, autoencoders, K-Means, anomaly detection
- **Web Development** — Next.js, FastAPI, REST APIs, WebSockets
- **Scraping / API Integration** — GitHub API, Stack Exchange API, OSV API
- **Systems / DevOps** — OpenTelemetry, distributed tracing, Docker, CI/CD

---

*Document maintained by Antigravity. Last updated March 2026.*