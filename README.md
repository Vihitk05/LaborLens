# Job Market AI Analyst

**Job Market AI Analyst** is a platform powered by [CrewAI](https://docs.crewai.com/) that analyzes job markets using collaborative autonomous AI agents. Designed as a learning project, it demonstrates agentic workflows and real-world application of multi-agent systems.

---

## 🚀 Key Features

- 🤖 **Multi-Agent Analysis** — 5 specialized AI agents, each with a distinct role  
- 🧩 **Customizable Reports** — Choose the metrics: skills, salaries, companies, or hiring trends  
- 📡 **Real-Time Streaming** — See agents collaborate and solve tasks live  
- 📄 **PDF Export** — Download rich, formatted reports with visual insights  

---

## 🛠 Tech Stack

### Frontend
- [Next.js 14](https://nextjs.org/)
- [ShadCN UI](https://ui.shadcn.com/)
- [React Markdown](https://github.com/remarkjs/react-markdown)

### Backend
- [FastAPI](https://fastapi.tiangolo.com/)
- [CrewAI](https://docs.crewai.com/)
- [Mistral-Nemo (via Ollama)](https://ollama.com/)

### Infrastructure
- Docker
- Redis
- Celery

---

## ⚙️ Getting Started

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- Node.js 18+
- Python 3.10+

### Installation

Clone the repository:
```bash
git clone https://github.com/yourusername/job-market-ai.git
````

Start the backend services:

```bash
cd job-market-ai/backend
docker-compose up -d
```

Start the frontend:

```bash
cd ../frontend
npm install
npm run dev
```

---

## 🧠 How Agents Work

| Agent          | Responsibility                               |
| -------------- | -------------------------------------------- |
| **Researcher** | Gathers job market data from various sources |
| **Analyst**    | Analyzes and detects trends or anomalies     |
| **Comparer**   | Compares findings across regions or roles    |
| **Reporter**   | Structures and compiles the report           |
| **Editor**     | Refines language, accuracy, and formatting   |

---

## ⚙️ Configuration

Create a `.env` file with the following:

```ini
TAVILY_API_KEY=your_key_here
OPENAI_API_KEY=optional_for_alternate_llm
```

> ℹ️ **Note:** The local LLM (Mistral-Nemo) uses Ollama and may require a machine with substantial RAM.

---

## ⚠️ Known Limitations

* PDF export may need adjustment for lengthy or complex reports
* The system works best in English-language environments
* Performance may degrade on low-spec machines due to LLM memory usage


## 📬 Contact

Feel free to reach out:

* GitHub: [@Vihitk05](https://github.com/Vihitk05)
* Email: [vihitk05@gmail.com](mailto:vihitk05@gmail.com)

