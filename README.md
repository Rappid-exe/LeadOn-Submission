# LeadOn CRM - AI-Powered Lead Generation System

**LeadOn CRM** is an intelligent lead generation and customer relationship management system that uses AI to automate contact discovery, enrichment, and outreach campaigns via LinkedIn and Telegram.

---

## 🎯 Overview

LeadOn CRM combines:
- **🤖 Agentic AI Systems**: Autonomous agents that iteratively search, analyze, and optimize lead generation
- **AI-Powered Search**: Natural language queries to find contacts (e.g., "Find CTOs at AI companies in San Francisco")
- **Apollo.io Integration**: Real contact data with 275M+ contacts and 73M+ companies
- **Intelligent Enrichment**: AI analyzes job postings, company profiles, and generates personalized pitches
- **LinkedIn Automation**: Automated likes, connections, and endorsements with session management
- **Telegram Campaigns**: Send personalized DMs with rate limiting (10/day, 1/hour)
- **Custom CRM**: Modern interface with contacts, companies, and campaigns management

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (HTML/JS)                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Contacts │  │Companies │  │Campaigns │  │Integration│   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              FastAPI Backend (chat_api.py)                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ AI Agent (Claude) - Intent Parsing & Orchestration   │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Services Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │Apollo Scraper│  │Job Enrichment│  │Telegram DMs  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │Company Enrich│  │Phone Enrich  │  │Agentic Search│     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              SQLite Database (leadon.db)                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Contacts │  │Companies │  │Campaigns │  │Integrations│  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                 │
│  │Job Posts │  │ Profiles │  │Telegram  │                 │
│  └──────────┘  └──────────┘  │Messages  │                 │
│                               └──────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+**
- **Apollo.io API Key** (get from https://app.apollo.io/#/settings/integrations/api)
- **Anthropic API Key** (get from https://console.anthropic.com/)
- **Telegram API Credentials** (optional, for DM campaigns - get from https://my.telegram.org/apps)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/OnchainAlpha/hackathon.git
cd hackathon
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment variables**

Create a `.env` file in the root directory:

```env
# Apollo.io API Configuration
APOLLO_API_KEY=your_apollo_api_key_here

# Claude API Key (Anthropic)
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Telegram User API (Optional - for DM campaigns)
TELEGRAM_API_ID=your_api_id_here
TELEGRAM_API_HASH=your_api_hash_here
TELEGRAM_PHONE=+1234567890

# Database Configuration
DATABASE_URL=sqlite:///database/leadon.db

# Rate Limiting
MAX_DAILY_LINKEDIN_ACTIONS=50
TELEGRAM_DAILY_MESSAGE_LIMIT=10
TELEGRAM_MESSAGE_INTERVAL_SECONDS=3600
```

4. **Run database migrations**
```bash
python database/migrations/add_contact_tags.py
python database/migrations/add_workflow_columns.py
python database/migrations/add_telegram_campaign.py
```

5. **Start the server**
```bash
python crm_integration/chat_api.py
```

Or use the batch file:
```bash
start_crm.bat
```

6. **Access the CRM**

Open your browser and navigate to:
- **CRM Interface**: http://localhost:8000/crm
- **API Documentation**: http://localhost:8000/docs

---

## 📁 Project Structure

```
LeadOn/
├── ai_agent/                    # AI intent parsing and orchestration
│   ├── intent_parser.py         # Claude-powered intent parser
│   └── __init__.py
├── cli/                         # Command-line interface
│   ├── search_mock.py           # Mock data for testing
│   └── __init__.py
├── crm_integration/             # CRM backend and frontend
│   ├── chat_api.py              # FastAPI backend (main server)
│   ├── frontend/                # HTML/JS frontend files
│   │   ├── leadon_crm.html      # Contacts page
│   │   ├── companies.html       # Companies page
│   │   ├── campaigns.html       # Campaigns page
│   │   ├── integrations.html    # Integrations page
│   │   └── *.js                 # JavaScript files
│   └── __init__.py
├── database/                    # Database models and migrations
│   ├── models.py                # SQLAlchemy ORM models
│   ├── db_manager.py            # Database connection manager
│   ├── migrations/              # Database migration scripts
│   │   ├── add_contact_tags.py
│   │   ├── add_workflow_columns.py
│   │   └── add_telegram_campaign.py
│   ├── leadon.db                # SQLite database file
│   └── __init__.py
├── docs/                        # Documentation
│   ├── COMPANY_ENRICHMENT_GUIDE.md
│   ├── TELEGRAM_CAMPAIGNS_GUIDE.md
│   └── WORKFLOW_STAGES.md
├── scrapers/                    # Data scrapers
│   ├── apollo_scraper.py        # Apollo.io API client
│   ├── linkedin_scraper.py      # LinkedIn scraper (future)
│   ├── schemas.py               # Pydantic data models
│   └── __init__.py
├── services/                    # Business logic services
│   ├── agentic_search_service.py        # AI-powered search
│   ├── apollo_company_enrichment.py     # Company data enrichment
│   ├── apollo_phone_enrichment.py       # Phone number enrichment
│   ├── company_enrichment_service.py    # Company AI analysis
│   ├── company_profile_service.py       # Company profile management
│   ├── job_enrichment_service.py        # Job posting enrichment
│   ├── telegram_campaign_service.py     # Telegram DM campaigns
│   └── __init__.py
├── .env                         # Environment variables (not in git)
├── .env.example                 # Environment template
├── .gitignore                   # Git ignore rules
├── requirements.txt             # Python dependencies
├── README.md                    # This file
└── start_crm.bat                # Windows startup script
```

---

## 🔑 Key Features

### 1. 🤖 Agentic AI Systems

LeadOn uses **autonomous AI agents** that iteratively refine and optimize searches:

**Agentic Search Service:**
- AI agent runs multiple search iterations to find the best contacts
- Automatically refines queries based on results
- Learns from each iteration to improve targeting
- Combines multiple data sources intelligently
- Example: "Find CTOs at AI companies" → Agent searches, analyzes results, refines criteria, searches again

**Job Enrichment Agent:**
- Scrapes company job postings automatically
- AI analyzes job descriptions to match your product
- Scores companies based on relevance (0-100)
- Finds decision-makers at companies actively hiring
- Generates match reasoning for each company

**AI Pitch Generator:**
- Analyzes contact's role, company, and industry
- Generates personalized outreach messages using Claude
- Considers search context (why they were found)
- Creates multiple variations for A/B testing
- Keeps messages under LinkedIn's 280-character limit

### 2. AI-Powered Contact Discovery

Use natural language to find contacts:

```
"Find CTOs at AI companies in San Francisco"
"Get investors in the FinTech space"
"Partnership outreach to SaaS CEOs"
```

The AI agent:
1. Parses your intent using Claude
2. Calls Apollo API with appropriate filters
3. Enriches contacts with company data
4. Saves to CRM database
5. Returns results

### 2. Apollo.io Integration

- **275M+ contacts** and **73M+ companies**
- Real-time data enrichment
- Phone number lookup (uses credits)
- Company information (size, funding, tech stack)
- Job titles and seniority levels

### 3. LinkedIn Automation

Automate LinkedIn outreach with intelligent bot:

**Features:**
- **Session Management**: Persistent login with cookie-based authentication
- **Like Posts**: Automatically like recent posts on target profiles
- **Send Connections**: Send personalized connection requests
- **Endorse Skills**: Endorse skills to build rapport
- **Rate Limiting**: Respects LinkedIn limits to avoid detection
- **Workflow Tracking**: Updates CRM with automation status

**Actions:**
```python
# Like 3 recent posts
bot.like_posts(profile_url, count=3)

# Send connection request
bot.send_connection_request(profile_url, note="Hi {name}...")

# Endorse skills
bot.endorse_skills(profile_url, skills=["Python", "AI"])
```

**Integration:**
- Connects directly to CRM database
- Updates contact workflow stages automatically
- Tracks last action and next action dates
- Stores automation notes for each contact

### 4. Telegram DM Campaigns

Send personalized messages via Telegram:

**Features:**
- Connect your Telegram account (User API, not bot)
- Discover contacts by phone number
- Send personalized DMs with template variables
- Automatic rate limiting (10/day, 1/hour)
- Track message status and history

**Phone Enrichment:**
- Use Apollo credits to get phone numbers
- Batch enrichment for multiple contacts
- Automatic database updates

**Example:**
```
Hi {first_name},

I noticed you're working as a {title} at {company}.

I'd love to connect and discuss how we can help with [your value proposition].

Best regards
```

### 5. Company Enrichment

Automatic company data enrichment:
- Founded year, funding stage, total funding
- Technologies used (tech stack)
- Employee count and location
- LinkedIn URL and Apollo ID
- AI-generated industry analysis
- Pain points and value propositions

### 6. Workflow Management

Track contacts through 9 stages:
1. **new** - Just added
2. **researching** - Gathering information
3. **qualified** - Meets criteria
4. **reaching_out** - Initial contact
5. **connected** - Accepted connection
6. **engaged** - Active conversation
7. **meeting_scheduled** - Call/meeting booked
8. **opportunity** - Potential deal
9. **disqualified** - Not a fit

### 7. Tagging System

Automatic tags based on:
- **Role**: founder, c_level, vp, director, manager, individual_contributor
- **Seniority**: executive, senior, mid_level, entry_level
- **Industry**: technology, finance, healthcare, etc.
- **Custom tags**: Add your own

---

## 📊 Database Schema

### Core Tables

**contacts** - Contact information
- id, first_name, last_name, email, phone
- company, title, location, linkedin_url
- tags (JSON), workflow_stage, workflow_notes
- source, created_at, updated_at

**companies** - Company/organization data
- id, name, website, industry, description
- employee_count, location, apollo_id
- founded_year, funding_stage, total_funding
- technologies (JSON), tags (JSON)
- relationship_stage, enrichment data

**campaigns** - Marketing campaigns
- id, name, type, status, integration_id
- target_audience, message_template
- start_date, end_date, metrics (JSON)

**integrations** - Connected accounts
- id, platform, status, account_name
- phone_number (for Telegram)
- access_token, refresh_token
- messages_sent, connections_made

**telegram_messages** - Telegram DM tracking
- id, campaign_id, contact_id, integration_id
- phone_number, telegram_user_id, telegram_username
- message_text, message_id, status, error_message
- sent_at, created_at

**job_postings** - Job posting data
- id, company_id, job_title, description
- location, salary_range, posted_date
- is_relevant, relevance_score

**company_profiles** - AI-generated profiles
- id, company_name, industry, pain_points (JSON)
- value_proposition, enrichment_notes

**search_history** - Search query history
- id, query, filters (JSON), results_count
- created_at

---

## 🔌 API Endpoints

### Contacts

- `GET /api/contacts` - List all contacts
- `POST /api/contacts` - Create contact
- `PUT /api/contacts/{id}` - Update contact
- `DELETE /api/contacts/{id}` - Delete contact
- `POST /api/contacts/enrich-phones` - Enrich with phone numbers from Apollo

### Companies

- `GET /api/companies` - List all companies
- `POST /api/companies` - Create company
- `PUT /api/companies/{id}` - Update company
- `POST /api/companies/{id}/enrich` - Enrich company data

### Campaigns

- `GET /api/campaigns` - List all campaigns
- `POST /api/campaigns` - Create campaign
- `PUT /api/campaigns/{id}` - Update campaign
- `DELETE /api/campaigns/{id}` - Delete campaign

### Integrations

- `GET /api/integrations` - List integrations
- `POST /api/integrations/telegram/connect` - Connect Telegram User API
- `POST /api/integrations/{platform}/disconnect` - Disconnect integration

### Telegram Campaigns

- `POST /api/telegram/campaign/start` - Start Telegram DM campaign
- `GET /api/telegram/campaign/status` - Get campaign status and rate limits
- `GET /api/telegram/messages` - Get message history

### Chat/Search

- `POST /api/chat` - Natural language search
- `POST /api/agentic-search` - AI-powered agentic search

---

## 🛠️ Development

### Running the Server

**Development mode:**
```bash
python crm_integration/chat_api.py
```

**Production mode:**
```bash
uvicorn crm_integration.chat_api:app --host 0.0.0.0 --port 8000
```

### Database Migrations

When adding new fields or tables:

1. Update `database/models.py`
2. Create migration script in `database/migrations/`
3. Run migration: `python database/migrations/your_migration.py`

### Adding New Services

1. Create service file in `services/`
2. Import in `crm_integration/chat_api.py`
3. Add API endpoints
4. Update frontend to use new endpoints

---

## 📝 Configuration

### Environment Variables

See `.env.example` for all available configuration options.

**Required:**
- `APOLLO_API_KEY` - Apollo.io API key
- `ANTHROPIC_API_KEY` - Claude API key

**Optional:**
- `TELEGRAM_API_ID` - Telegram API ID (for DM campaigns)
- `TELEGRAM_API_HASH` - Telegram API Hash
- `TELEGRAM_PHONE` - Your phone number with country code

### Rate Limits

Configure in `.env`:
```env
MAX_DAILY_LINKEDIN_ACTIONS=50
TELEGRAM_DAILY_MESSAGE_LIMIT=10
TELEGRAM_MESSAGE_INTERVAL_SECONDS=3600
APOLLO_REQUESTS_PER_MINUTE=60
```

---

## 🔒 Security Notes

1. **Never commit `.env` file** - Contains API keys
2. **Use `.env.example`** - Template for team members
3. **Encrypt tokens** - In production, encrypt access tokens
4. **Rate limiting** - Enforced to prevent abuse
5. **Input validation** - All API inputs are validated

---

## 🐛 Troubleshooting

### Server won't start

- Check Python version: `python --version` (need 3.11+)
- Install dependencies: `pip install -r requirements.txt`
- Check port 8000 is available

### Apollo API errors

- Verify API key in `.env`
- Check credit balance at https://app.apollo.io
- Review rate limits (60 requests/minute)

### Telegram connection fails

- Get credentials from https://my.telegram.org/apps
- Ensure phone number has country code (+1234567890)
- Check internet connection
- First connection requires verification code

### Database errors

- Run migrations: `python database/migrations/*.py`
- Check `database/leadon.db` exists
- Verify SQLite is installed

---

## 📚 Additional Documentation

- **Telegram Campaigns**: `docs/TELEGRAM_CAMPAIGNS_GUIDE.md`
- **Company Enrichment**: `docs/COMPANY_ENRICHMENT_GUIDE.md`
- **Workflow Stages**: `docs/WORKFLOW_STAGES.md`

---

## 🤝 Contributing

This is a hackathon project. For production use:

1. Add authentication and authorization
2. Implement proper token encryption
3. Add comprehensive error handling
4. Write unit and integration tests
5. Set up CI/CD pipeline
6. Add monitoring and logging
7. Implement backup strategy

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🎉 Credits

Built with:
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - SQL toolkit and ORM
- **Anthropic Claude** - AI agent for intent parsing
- **Apollo.io** - Contact and company data
- **Telethon** - Telegram User API client
- **Tailwind CSS** - UI styling

---

**Happy Lead Generating! 🚀**

