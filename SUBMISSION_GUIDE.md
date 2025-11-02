# Hackathon Submission Guide

## 📦 Submission Repository

This repository is ready for hackathon submission. It's a clean, standalone project with all necessary files.

---

## ✅ Pre-Submission Checklist

### 1. Code Quality
- [x] All features working and tested
- [x] No sensitive data in code (API keys, tokens)
- [x] Clean code with comments
- [x] No debug/test files in main codebase
- [x] Error handling implemented

### 2. Documentation
- [x] README.md with clear setup instructions
- [x] Architecture diagram included
- [x] API documentation available
- [x] Feature descriptions complete
- [x] Troubleshooting guide included

### 3. Configuration
- [x] `.env.example` file provided
- [x] `.gitignore` properly configured
- [x] `requirements.txt` up to date
- [x] Database migrations included

### 4. Demo Preparation
- [ ] Test with fresh `.env` file
- [ ] Verify all dependencies install correctly
- [ ] Prepare demo script/walkthrough
- [ ] Record demo video (if required)
- [ ] Prepare presentation slides (if required)

### 5. Repository Cleanup
- [ ] Remove unnecessary files
- [ ] Clear database (or provide clean sample data)
- [ ] Remove debug screenshots
- [ ] Remove test scripts (or move to `/tests`)
- [ ] Clear `__pycache__` directories

---

## 🧹 Cleanup Commands

Run these before submission:

```bash
# Remove Python cache files
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# Remove test/debug files (optional - review first!)
rm -f test_*.py
rm -f debug_*.py
rm -f debug_*.png

# Clear database (optional - if you want fresh start)
rm -f database/leadon.db
python database/migrations/add_contact_tags.py
python database/migrations/add_workflow_columns.py
python database/migrations/add_telegram_campaign.py

# Remove cookies/session files
rm -f linkedin_cookies.json
rm -f *.session
```

**Windows PowerShell:**
```powershell
# Remove Python cache
Get-ChildItem -Path . -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
Get-ChildItem -Path . -Recurse -File -Filter "*.pyc" | Remove-Item -Force

# Remove test files (review first!)
Remove-Item test_*.py -Force
Remove-Item debug_*.py -Force
Remove-Item debug_*.png -Force

# Clear database
Remove-Item database\leadon.db -Force
python database\migrations\add_contact_tags.py
python database\migrations\add_workflow_columns.py
python database\migrations\add_telegram_campaign.py
```

---

## 📝 Files to Keep

### Essential Files
- `README.md` - Main documentation
- `requirements.txt` - Dependencies
- `.env.example` - Configuration template
- `.gitignore` - Git ignore rules
- `start_crm.bat` - Quick start script

### Source Code
- `ai_agent/` - AI intent parsing
- `crm_integration/` - Backend and frontend
- `database/` - Database models and migrations
- `scrapers/` - Data scrapers
- `services/` - Business logic

### Documentation
- `docs/` - Additional guides
- `MAGIC_WAND_FIX.md` - Technical documentation

---

## 🗑️ Files to Remove (Optional)

### Test Files
- `test_*.py` - Test scripts
- `debug_*.py` - Debug scripts
- `debug_*.png` - Debug screenshots

### Session Files
- `linkedin_cookies.json` - LinkedIn session
- `*.session` - Telegram session files

### Database
- `database/leadon.db` - Contains your data (clear for fresh demo)

### Cache
- `__pycache__/` - Python cache directories
- `*.pyc` - Compiled Python files

---

## 🎬 Demo Preparation

### 1. Fresh Installation Test

Test that someone can clone and run your project:

```bash
# Clone the repo
git clone [your-repo-url]
cd hackathon

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with API keys

# Run migrations
python database/migrations/add_contact_tags.py
python database/migrations/add_workflow_columns.py
python database/migrations/add_telegram_campaign.py

# Start server
python crm_integration/chat_api.py

# Open browser
# http://localhost:8000/crm
```

### 2. Demo Script

**5-Minute Demo Flow:**

1. **Introduction (30 seconds)**
   - "LeadOn CRM - AI-powered lead generation system"
   - Show architecture diagram

2. **AI Search (1 minute)**
   - Open CRM interface
   - Use chat: "Find CTOs at AI companies in San Francisco"
   - Show results populating in real-time

3. **Contact Management (1 minute)**
   - Show contacts table with enriched data
   - Demonstrate filtering and search
   - Show workflow stages

4. **AI Pitch Generator (1 minute)**
   - Click magic wand button
   - Show personalized pitch generation
   - Explain how it uses contact context

5. **Company Enrichment (1 minute)**
   - Navigate to Companies page
   - Show enriched company data
   - Demonstrate Apollo integration

6. **Telegram Campaigns (1 minute)**
   - Show Integrations page
   - Explain Telegram DM automation
   - Show rate limiting and tracking

7. **Wrap-up (30 seconds)**
   - Highlight key features
   - Mention tech stack
   - Q&A

### 3. Key Talking Points

**Problem:**
- Manual lead generation is time-consuming
- Finding the right contacts is difficult
- Personalized outreach doesn't scale

**Solution:**
- AI-powered natural language search
- Automatic data enrichment from Apollo.io
- Personalized message generation with Claude
- Multi-channel outreach (LinkedIn, Telegram)

**Tech Stack:**
- FastAPI backend
- Claude AI for intent parsing
- Apollo.io for contact data
- SQLite database
- Vanilla JS frontend

**Unique Features:**
- Agentic search (AI refines queries iteratively)
- Job posting enrichment (find companies hiring)
- Telegram User API (not bot - real DMs)
- AI pitch generator with context awareness

---

## 📹 Video Demo Tips

If recording a video:

1. **Preparation**
   - Clear browser cache
   - Close unnecessary tabs
   - Use incognito mode
   - Prepare sample data

2. **Recording**
   - Use screen recording software (OBS, Loom, etc.)
   - Record in 1080p
   - Enable microphone for narration
   - Keep it under 5 minutes

3. **Content**
   - Start with quick intro
   - Show actual usage, not just code
   - Highlight unique features
   - End with impact/results

4. **Editing**
   - Add captions for key points
   - Speed up slow parts (2x)
   - Add background music (optional)
   - Export in MP4 format

---

## 🚀 Deployment (Optional)

If you want to deploy for the demo:

### Option 1: Railway.app
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

### Option 2: Render.com
1. Connect GitHub repo
2. Select "Web Service"
3. Build command: `pip install -r requirements.txt`
4. Start command: `python crm_integration/chat_api.py`
5. Add environment variables

### Option 3: Heroku
```bash
# Install Heroku CLI
heroku login
heroku create leadon-crm
git push heroku main
heroku config:set APOLLO_API_KEY=xxx
heroku config:set ANTHROPIC_API_KEY=xxx
```

---

## 📊 Metrics to Highlight

If asked about impact/results:

- **Time Saved**: "Reduces lead research time from 30 min to 30 seconds"
- **Scale**: "Access to 275M+ contacts via Apollo.io"
- **Automation**: "Sends 10 personalized Telegram DMs per day automatically"
- **AI-Powered**: "Uses Claude for intent parsing and message generation"
- **Enrichment**: "Automatically enriches contacts with company data and job postings"

---

## 🎯 Submission Platforms

### GitHub
- Make repository public
- Add topics/tags: `hackathon`, `crm`, `ai`, `lead-generation`
- Add description and website URL
- Create releases/tags if required

### Devpost
- Create project page
- Upload demo video
- Add screenshots
- Link to GitHub repo
- Fill out all required fields

### Other Platforms
- Follow specific submission guidelines
- Include all required information
- Submit before deadline
- Keep confirmation email

---

## 🔗 Useful Links

- **Live Demo**: http://localhost:8000/crm (or deployed URL)
- **API Docs**: http://localhost:8000/docs
- **GitHub Repo**: [your-repo-url]
- **Demo Video**: [youtube/loom-url]
- **Presentation**: [slides-url]

---

## 📧 Support

For questions during judging:
- Email: [your-email]
- GitHub Issues: [repo-url]/issues
- Discord/Slack: [your-handle]

---

## 🏆 Good Luck!

Remember:
- Test everything before submitting
- Have a backup plan for demo
- Be ready to explain technical decisions
- Show passion for the problem you're solving
- Have fun!

**You've built something awesome! 🚀**
