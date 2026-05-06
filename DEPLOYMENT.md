# 🚀 Deployment Guide - Get Your Live Link

## Important: Why This Runs Locally

This project is **designed for local deployment** because:
- ✅ **Zero Cost**: No monthly hosting fees (₹0 forever)
- ✅ **Complete Privacy**: Your GST invoices/contracts never leave your machine
- ✅ **Data Sovereignty**: Critical for Indian tax/legal compliance
- ✅ **No API Costs**: Uses local Ollama instead of OpenAI (saves $200+/month)

However, if you need a **shareable demo link**, here are your options:

---

## Option 1: Local Development (FASTEST - 10 minutes)

**You'll get**: `http://localhost:3000`

### Quick Start on Windows:
```powershell
# Run the automated setup script
cd d:\Multi\indian-sme-doc-intelligence-rag
.\setup.bat

# Then start Docker Desktop and run:
docker-compose up --build
```

**Access**: 
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/api/docs
- Login: admin@demo.com / Admin@123

---

## Option 2: FREE Cloud Deployment (30 minutes)

### A. Backend on Render.com (FREE)

1. **Create GitHub Repository**
```bash
cd d:\Multi\indian-sme-doc-intelligence-rag
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/indian-sme-rag.git
git push -u origin main
```

2. **Deploy Backend to Render**
   - Go to https://render.com
   - Sign up (free)
   - New Web Service → Connect your GitHub repo
   - Root Directory: `backend`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Add PostgreSQL database (Render provides free tier)
   - Set environment variables from `backend/.env.example`

3. **Get your backend URL**: `https://your-app-name.onrender.com`

### B. Frontend on Vercel (FREE)

1. **Deploy to Vercel**
   - Go to https://vercel.com
   - Sign up with GitHub
   - Import your repository
   - Root Directory: `frontend`
   - Framework Preset: Next.js
   - Environment Variable: `NEXT_PUBLIC_API_URL=https://your-backend.onrender.com`
   - Deploy

2. **Get your frontend URL**: `https://your-app.vercel.app`

### C. AI Model on Groq API (FREE tier)

Since Ollama requires GPU servers (expensive), use Groq's free API:
1. Sign up at https://groq.com
2. Get free API key
3. Update backend to use Groq instead of Ollama
4. Free tier: 30 requests/minute

---

## Option 3: Railway.app (EASIEST - One Click)

Railway has better free tier for full-stack apps:

1. **Deploy to Railway**
   - Go to https://railway.app
   - Click "Deploy from GitHub"
   - Select your repository
   - Railway auto-detects `docker-compose.yml`
   - Add services:
     - PostgreSQL (provided free)
     - Backend (from `backend/` directory)
     - Frontend (from `frontend/` directory)
   - Set environment variables

2. **Get your URLs**:
   - Frontend: `https://your-project.up.railway.app`
   - Backend: `https://backend-service.up.railway.app`

---

## Option 4: Record a Demo Video (BEST for Job Applications)

Instead of live hosting, **record a 2-minute demo**:

### Using OBS Studio (FREE):
1. Install OBS: https://obsproject.com
2. Set up screen recording
3. Record this flow:
   - Login page
   - Upload a sample GST PDF
   - Show processing
   - Ask questions in chat
   - Show grounded answers with citations
   - Show admin dashboard metrics
4. Upload to YouTube (unlisted)
5. Share link in resume/portfolio

**This is MORE impressive than a slow free-tier deployment!**

---

## Option 5: Google Colab Demo (FREE GPU)

For AI evaluation notebook:
1. Open `notebooks/eval.ipynb` in Colab
2. Run cells with free GPU
3. Share notebook link

---

## 🎯 Recommendation for 50 LPA Job Applications

**Do this combination**:

1. **Local Development** (for your own testing)
   - Run on your machine with Docker
   - URL: `http://localhost:3000`

2. **2-Minute Demo Video** (for recruiters)
   - Record with OBS/Loom
   - Upload to YouTube (unlisted)
   - Add link to resume

3. **GitHub Repository** (for technical interviewers)
   - Push code to GitHub
   - Comprehensive README (already done!)
   - Architecture diagram, metrics, setup instructions

4. **Live Blog Post** (bonus points)
   - Write on Medium/Dev.to: "How I Built a Production RAG SaaS for Indian SMEs"
   - Include architecture, challenges, metrics
   - Link to GitHub + demo video

**This approach is 10x better than a slow free-tier deployment** because:
- Shows you understand production trade-offs
- Demonstrates privacy-first design (important for Indian businesses)
- Avoids free-tier limitations (slow, sleeps after inactivity)
- Proves you can architect complete systems

---

## Quick Commands Reference

### Local Setup
```bash
# Windows
.\setup.bat

# Docker
docker-compose up --build

# Access
http://localhost:3000
```

### Push to GitHub
```bash
git init
git add .
git commit -m "Production RAG SaaS for Indian SMEs"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/indian-sme-rag.git
git push -u origin main
```

### Create Demo Video
```bash
# Install OBS Studio
# Record 2-minute walkthrough
# Upload to YouTube as "Unlisted"
# Add link to resume
```

---

## Need Help?

1. **Setup Issues**: See `SETUP.md`
2. **API Docs**: http://localhost:8000/api/docs (when running)
3. **Project Summary**: See `PROJECT_SUMMARY.md`

---

**Bottom Line**: The best "link" you can give recruiters is:
- GitHub repo link (code quality)
- YouTube demo link (working product)
- Blog post link (communication skills)

Not a flaky free-tier deployment that times out during interviews! 🚀
