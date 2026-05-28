<div align="center">

# 📄 DocRAG 
### 100% Private, Zero-Cost AI for Business Documents

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js 16](https://img.shields.io/badge/Next.js-16-black.svg?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791.svg?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)

**DocRAG** is a powerful tool that reads complex PDFs (like GST invoices, vendor contracts, and legal notices) and lets you chat with them. 

Unlike most AI apps that send your private files to OpenAI or Google, **DocRAG runs entirely on your own machine.** It costs nothing to run, and your data never leaves your computer.

</div>

---

## 🌟 What Does It Look Like?

The user interface is built with Next.js and looks exactly like a premium, professional software product. You upload a document on the left, and chat with the AI on the right. 

<div align="center">
<img width="1494" height="879" alt="image" src="https://github.com/user-attachments/assets/447d9f96-cd8f-4f2d-85a3-f8ee762a70d4" />
</div>

---

## 💡 Why I Built This (The Business Problem)

Most small and medium-sized businesses (SMEs) want to use AI to read their documents, but they face two massive problems:
1. **Privacy:** You cannot legally send confidential employee contracts or tax invoices to public AI servers like ChatGPT.
2. **Cost:** Paying for APIs every time you process a 50-page document gets incredibly expensive.

**The Solution:** I built DocRAG to run locally. By using local AI models (Llama 3.3) and open-source tools, this software turns a massive monthly API bill into **₹0 per month**, while keeping data completely safe.

---

## ⚙️ How It Actually Works 

<div align="center">
<img width="895" height="447" alt="image" src="https://github.com/user-attachments/assets/525befb0-c132-4c27-abac-f365b70c42d9" />
</div>

When you upload a PDF and ask a question, here is what happens behind the scenes:

### 1. Reading the Document
Normal AI tools struggle to read tables inside PDFs. DocRAG uses **IBM Docling** to carefully extract text and tables so the AI understands rows and columns perfectly.

<div align="center">
<img width="888" height="436" alt="image" src="https://github.com/user-attachments/assets/5f2653a3-cdfb-4072-ba48-9ccc3e7bc0fc" />
</div>

### 2. Searching for the Answer
When you ask a question (e.g., *"What is the total tax?"*), the system searches through the document to find the exact paragraph or table that contains the answer. It uses **ChromaDB** to do this in milliseconds.

### 3. Preventing "Hallucinations" (AI Making Things Up)
AI sometimes lies or makes up answers. To stop this, I added a "Self-Correction" loop using **LangGraph**. Before the AI shows you an answer, the system double-checks: *"Did this answer actually come from the document?"* If it didn't, the system forces the AI to try again.

<div align="center">
<img width="704" height="496" alt="image" src="https://github.com/user-attachments/assets/379934b1-ea14-4179-b549-9935f80d0485" />
</div>

---

## 🔒 Keeping Data Safe (Multi-Tenant Security)

If two different companies use this app, Company A must never be able to see Company B's documents. I built a strict security wall at the database level using **PostgreSQL Row-Level Security (RLS)**. Even if a bug happens, the database physically blocks users from seeing data that doesn't belong to them.

<div align="center">
<img width="849" height="407" alt="image" src="https://github.com/user-attachments/assets/5bdbe06f-b37e-4fc0-a1e0-b9830a2090ac" />
</div>

---

## 📊 Performance & Analytics Dashboard

To make sure the system is running fast and smoothly, DocRAG includes a real-time analytics dashboard. It tracks how fast documents are being read and how accurate the AI is.

<div align="center">
<img width="894" height="445" alt="image" src="https://github.com/user-attachments/assets/604b1886-754e-4df9-aa34-05ef57542100" />
</div>

---

## 💻 Technologies Used

* **Frontend:** Next.js 16, React, Tailwind CSS (for a fast, beautiful website).
* **Backend:** FastAPI, Python (for fast, asynchronous processing).
* **AI Brain:** Llama 3.3 via Ollama (local AI model).
* **PDF Reader:** IBM Docling (for advanced table reading).
* **Database:** PostgreSQL (for users) and ChromaDB (for searching documents).

---

## 🚀 How to Run It on Your Computer

You can start the entire system with just a few commands. It requires no paid API keys.

```bash
# 1. Clone the code to your computer
git clone [https://github.com/sat1828/DocRAG.git](https://github.com/sat1828/DocRAG.git)
cd DocRAG

# 2. Start the database and website
docker-compose up -d --build

# 3. Download the free AI model
ollama pull llama3.3
