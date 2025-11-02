# Company Enrichment Feature Guide

## Overview

The Company Enrichment feature uses AI to analyze your company profile and enrich each target company with personalized insights, pain points, and value propositions. This helps you create highly targeted outreach campaigns.

## How It Works

### 1. Setup Your Company Profile

First, you need to create your company profile so the AI knows what you offer:

1. Go to the **Companies** page
2. Click the **"My Profile"** button (purple button in the top right)
3. Enter your company's website URL
4. Click **"Analyze Website with AI"**
5. The AI will automatically extract:
   - Company name and tagline
   - What you do (description)
   - Products/services you offer
   - Target customers
   - Value propositions
   - Differentiators
   - Common use cases

The profile is automatically saved after analysis.

### 2. Enrich Individual Companies

To enrich a single company:

1. Go to the **Companies** page
2. Find the company you want to enrich
3. Click the **magic wand icon** (🪄) in the Actions column
4. The AI will analyze the company and generate:
   - **Industry Analysis**: Their position, challenges, and opportunities
   - **Pain Points**: Specific problems they likely face
   - **Value Proposition**: Personalized pitch for how your product solves their problems
   - **Enrichment Notes**: Additional insights, objections, and recommended approach
   - **Outreach Angle**: Best angle to use (cost savings, efficiency, growth, etc.)
   - **Talking Points**: Specific points for sales conversations

### 3. Enrich All Companies (Batch)

To enrich all companies at once:

1. Go to the **Companies** page
2. Click the **"Enrich All"** button (green button in the top right)
3. Confirm the action
4. The AI will enrich all companies in your database

**Note**: This may take a while and use API credits, so use it wisely!

### 4. View Enrichment Data

To view the enrichment data for a company:

1. Click the **eye icon** (👁️) in the Actions column
2. A modal will open showing:
   - Basic company information
   - Industry analysis
   - Pain points (as a list)
   - Personalized value proposition
   - Enrichment notes with outreach strategy

## Enrichment Status

Companies show their enrichment status in the **Enrichment** column:
- **✅ Enriched** (green badge): Company has been enriched
- **⚪ Not enriched** (gray badge): Company needs enrichment

## API Endpoints

The feature adds these new endpoints:

### Company Profile
- `POST /api/profile/create` - Create/update company profile from website
- `GET /api/profile` - Get current company profile

### Company Enrichment
- `POST /api/companies/{id}/enrich` - Enrich a single company
- `POST /api/companies/enrich-all` - Enrich all companies (optional `limit` parameter)

## Database Schema

### New Fields in `companies` Table
- `industry_analysis` (TEXT): AI-generated industry analysis
- `pain_points` (JSON): List of identified pain points
- `value_proposition` (TEXT): Personalized value proposition
- `enrichment_notes` (TEXT): Additional insights and strategy
- `last_enriched_at` (DATETIME): When the company was last enriched

### New `company_profile` Table
- `website_url`: Your company's website
- `company_name`: Your company name
- `tagline`: Your tagline/slogan
- `description`: What you do
- `products_services` (JSON): List of products/services
- `target_customers`: Who you serve
- `value_propositions` (JSON): Key value props
- `differentiators`: What makes you unique
- `use_cases` (JSON): Common use cases
- `ai_summary`: AI-generated summary

## Example Workflow

1. **Setup** (one-time):
   ```
   Click "My Profile" → Enter website → Click "Analyze Website with AI"
   ```

2. **Enrich Companies**:
   ```
   Option A: Click magic wand on individual companies
   Option B: Click "Enrich All" to batch enrich
   ```

3. **Use Enrichment Data**:
   ```
   Click eye icon → View personalized insights → Use in outreach
   ```

## Tips

- **Setup your profile first**: The enrichment quality depends on having a good company profile
- **Review AI analysis**: The AI-generated profile can be edited if needed
- **Enrich strategically**: Start with high-priority companies before batch enriching
- **Use enrichment data**: Reference the pain points and value props in your outreach
- **Re-enrich periodically**: Companies change, so re-enrich important targets every few months

## Technical Details

### Services
- **CompanyProfileService** (`services/company_profile_service.py`):
  - Scrapes website content using BeautifulSoup
  - Analyzes with Claude AI
  - Saves profile to database

- **CompanyEnrichmentService** (`services/company_enrichment_service.py`):
  - Takes company data + your profile
  - Uses Claude AI to generate personalized insights
  - Saves enrichment to database

### AI Model
- Uses **Claude 3.5 Sonnet** for both profile analysis and company enrichment
- Requires `ANTHROPIC_API_KEY` environment variable

### Rate Limiting
- Each enrichment makes 1 API call to Claude
- Batch enrichment processes companies sequentially
- Consider API costs when enriching many companies

## Troubleshooting

**"Company profile service not available"**
- Make sure `ANTHROPIC_API_KEY` is set in your `.env` file
- Restart the server after adding the API key

**"Please create your company profile first"**
- You need to setup your profile before enriching companies
- Click "My Profile" and analyze your website

**"Failed to scrape website"**
- Check that the website URL is correct and accessible
- Some websites block scrapers - try a different URL format

**Enrichment takes too long**
- Each company takes ~5-10 seconds to enrich
- Use the single-company enrichment for urgent needs
- Run batch enrichment during off-hours

## Future Enhancements

Potential improvements:
- [ ] Edit company profile manually
- [ ] Re-enrich specific companies
- [ ] Export enrichment data to CSV
- [ ] Enrichment templates for different industries
- [ ] Bulk import companies for enrichment
- [ ] Enrichment quality scoring
- [ ] A/B testing different value propositions

