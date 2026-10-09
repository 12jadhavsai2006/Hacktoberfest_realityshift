# 👁️‍🗨️ RealityShift

> **Multimodal Counterfactual Reasoning Engine** powered by Google’s **Gemma 4** (`gemma-4-26b-a4b-it`) and FastAPI.

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Google GenAI SDK](https://img.shields.io/badge/Google%20GenAI-SDK-4285F4.svg?logo=google&logoColor=white)](https://github.com/google/genai-sdk)
[![Hacktoberfest](https://img.shields.io/badge/Hacktoberfest-2026-orange.svg)](https://hacktoberfest.com/)

---

## 🚀 Overview

**RealityShift** moves beyond standard image captioning by performing rigorous **counterfactual visual reasoning**. Given two states of reality—**Image A** (the baseline "before" state) and **Image B** (the "after" / counterfactual state)—the engine automatically maps the delta between them, detects broken or formed physical/logical relationships, and models multi-step downstream consequences with confidence scoring.

---

## ✨ Key Features

* **🧠 Powered by Gemma 4**: Utilizes `gemma-4-26b-a4b-it` via the official `google-genai` SDK for state-of-the-art multimodal reasoning.
* **🔒 Strict Pydantic v2 Schema Enforcement**: Guarantees structured, type-safe JSON outputs complete with automated fallback repair for truncated tokens.
* **🔗 Dynamic Causal Mapping**: Automatically transforms visual delta into entity changes, relationship breakdowns, and ranked risk assessments.
* **📊 Interactive Visualizations**: Features a glassmorphic web dashboard with real-time analysis and integrated Mermaid.js causal diagramming.

---

## 🛠️ Tech Stack

* **AI/ML**: Google GenAI SDK (`google-genai`), Gemma 4
* **Backend**: FastAPI, Python 3.10+, Pydantic v2, Uvicorn
* **Frontend**: HTML5, CSS3 Glassmorphism, Mermaid.js

---

## 🏁 Quickstart

### 1. Clone & Set Up Environment
```powershell
git clone [https://github.com/YOUR_USERNAME/realityshift.git](https://github.com/YOUR_USERNAME/realityshift.git)
cd realityshift

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt



2. Configure API Key
Create a .env file in the root directory:

GOOGLE_API_KEY=your_google_gemini_api_key_here



3. Run the Server
PowerShell
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
Navigate to http://127.0.0.1:8000/graph-viewer to use the interactive dashboard!



🤝 Contributing for Hacktoberfest
We love contributions from the open-source community! Whether you want to fix UI bugs, optimize JSON parsing, or improve Mermaid graph generation:

Fork the repository.

Create your feature branch (git checkout -b feature/amazing-feature).

Commit your changes (git commit -m 'Add some amazing feature').

Push to the branch (git push origin feature/amazing-feature).

Open a Pull Request.

Please make sure your code follows the existing style guidelines and check out our open Issues tab to find tasks to tackle!



📄 License
Distributed under the MIT License. See LICENSE for more information.


---

### What to do next:
1. Save this file as `README.md` in your project folder.
2. Commit and push it to GitHub:
   ```powershell
   git add README.md
   git commit -m "Add professional Hacktoberfest README"
   git push origin main