# 📱 Telegram DM Campaigns Guide

Complete guide to setting up and running Telegram DM campaigns in LeadOn CRM.

---

## 🎯 Overview

The Telegram Campaign feature allows you to:
- **Connect your Telegram account** using the User API (not bot)
- **Discover contacts** by phone number
- **Send personalized DMs** using enriched contact data
- **Automatic rate limiting**: 10 messages per 24 hours, 1 per hour
- **Track campaign progress** and message history

---

## 🚀 Quick Start

### Step 1: Get Telegram API Credentials

1. Go to https://my.telegram.org/apps
2. Log in with your phone number
3. Click "API development tools"
4. Create a new application:
   - **App title**: LeadOn CRM
   - **Short name**: leadon
   - **Platform**: Desktop
5. Copy your **API ID** and **API Hash**

### Step 2: Add Credentials to .env

```env
# Telegram User API (for DM campaigns)
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=abcdef1234567890abcdef1234567890
TELEGRAM_PHONE=+1234567890
```

### Step 3: Install Dependencies

```bash
pip install telethon==1.34.0
```

Or install all requirements:
```bash
pip install -r requirements.txt
```

### Step 4: Run Database Migration

```bash
python database/migrations/add_telegram_campaign.py
```

This creates:
- `phone_number` field in `integrations` table
- `telegram_messages` table for tracking sent messages

### Step 5: Connect Your Telegram Account

1. Start the server: `python crm_integration/chat_api.py`
2. Go to http://localhost:8000/crm/integrations
3. Click "Connect Telegram User API"
4. Enter your API ID, API Hash, and phone number
5. You'll receive a verification code via Telegram
6. Enter the code to complete authentication

---

## 📊 How It Works

### 1. Contact Discovery

The system tries to find Telegram accounts by phone number:

```python
# For each contact with a phone number
contact = {
    'phone': '+1234567890',
    'first_name': 'John',
    'last_name': 'Doe'
}

# System adds contact to Telegram and checks if they have an account
telegram_user = await find_contact_by_phone(contact['phone'])

if telegram_user:
    # Contact has Telegram! Can send DM
    send_message(telegram_user['id'], message)
else:
    # Contact doesn't have Telegram
    # Marked as 'no_telegram' in database
```

### 2. Personalized Messages

Use template variables in your messages:

```
Hi {first_name},

I noticed you're working as a {title} at {company}. 

I'd love to connect and discuss how we can help with [your value proposition].

Best regards
```

Available variables:
- `{first_name}` - Contact's first name
- `{last_name}` - Contact's last name
- `{company}` - Company name
- `{title}` - Job title
- `{email}` - Email address
- Any other field from the contact record

### 3. Rate Limiting

**Automatic rate limiting** to comply with Telegram's policies:

- **Daily Limit**: 10 messages per 24 hours
- **Hourly Limit**: 1 message per hour
- **Flood Protection**: Handles Telegram's FloodWaitError

If you hit a limit, the system will:
- Queue remaining messages
- Show time until next message can be sent
- Resume automatically when limit resets

---

## 🔌 API Endpoints

### Connect Telegram User API

```http
POST /api/integrations/telegram/connect-user
Content-Type: application/json

{
  "api_id": "12345678",
  "api_hash": "abcdef1234567890abcdef1234567890",
  "phone": "+1234567890"
}
```

**Response:**
```json
{
  "message": "Telegram User API connected successfully",
  "platform": "telegram_user",
  "phone": "+1234567890"
}
```

### Start Campaign

```http
POST /api/telegram/campaign/start
Content-Type: application/json

{
  "contact_ids": [1, 2, 3, 4, 5],
  "message_template": "Hi {first_name}, I noticed you're working at {company}...",
  "campaign_id": 123
}
```

**Response:**
```json
{
  "message": "Telegram campaign started",
  "total_contacts": 5,
  "status": "processing"
}
```

### Get Campaign Status

```http
GET /api/telegram/campaign/status
```

**Response:**
```json
{
  "connected": true,
  "phone": "+1234567890",
  "messages_sent_today": 3,
  "daily_limit": 10,
  "messages_remaining_today": 7,
  "total_sent": 45,
  "total_failed": 2,
  "total_no_telegram": 8,
  "last_used": "2024-01-15T10:30:00"
}
```

### Get Message History

```http
GET /api/telegram/messages?limit=50
```

**Response:**
```json
{
  "messages": [
    {
      "id": 1,
      "contact_id": 123,
      "phone_number": "+1234567890",
      "telegram_username": "johndoe",
      "status": "sent",
      "error_message": null,
      "sent_at": "2024-01-15T10:30:00",
      "created_at": "2024-01-15T10:29:55"
    }
  ]
}
```

---

## 📋 Database Schema

### `integrations` Table (Updated)

```sql
ALTER TABLE integrations ADD COLUMN phone_number VARCHAR(50);
```

For Telegram User API integrations:
- `platform` = 'telegram_user'
- `phone_number` = User's phone number
- `refresh_token` = API ID
- `access_token` = API Hash

### `telegram_messages` Table (New)

```sql
CREATE TABLE telegram_messages (
    id INTEGER PRIMARY KEY,
    campaign_id INTEGER,
    contact_id INTEGER NOT NULL,
    integration_id INTEGER NOT NULL,
    phone_number VARCHAR(50) NOT NULL,
    telegram_user_id VARCHAR(100),
    telegram_username VARCHAR(100),
    message_text TEXT NOT NULL,
    message_id VARCHAR(100),
    status VARCHAR(20) DEFAULT 'pending',
    error_message TEXT,
    sent_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Status values:**
- `pending` - Queued for sending
- `sent` - Successfully sent
- `failed` - Failed to send (error in error_message)
- `no_telegram` - Contact doesn't have Telegram

---

## 🎨 Frontend Integration

### Campaign Modal (Coming Soon)

Add a "Start Telegram Campaign" button to the Contacts page:

```javascript
async function startTelegramCampaign() {
    const selectedContacts = getSelectedContactIds();
    const messageTemplate = document.getElementById('message-template').value;
    
    const response = await fetch('/api/telegram/campaign/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            contact_ids: selectedContacts,
            message_template: messageTemplate
        })
    });
    
    const result = await response.json();
    alert(`Campaign started! Sending to ${result.total_contacts} contacts`);
}
```

---

## ⚠️ Important Notes

### Rate Limits

- **10 messages per 24 hours** - Hard limit enforced by the system
- **1 message per hour** - Prevents spam detection
- **Telegram FloodWait** - If Telegram rate limits you, the system will wait automatically

### Privacy & Compliance

- **User Consent**: Only message contacts who have opted in
- **Unsubscribe**: Provide a way for users to opt out
- **GDPR**: Ensure compliance with data protection regulations
- **Telegram ToS**: Follow Telegram's Terms of Service

### Best Practices

1. **Personalize messages** - Use contact data to make messages relevant
2. **Test first** - Send to yourself before launching campaign
3. **Monitor responses** - Track which messages get replies
4. **Respect limits** - Don't try to bypass rate limits
5. **Quality over quantity** - 10 well-targeted messages > 100 spam messages

---

## 🐛 Troubleshooting

### "Failed to connect to Telegram"

- Check your API ID and API Hash are correct
- Ensure phone number includes country code (+1234567890)
- Verify you have internet connection
- Try logging out and back in to Telegram

### "Contact does not have Telegram"

- Contact's phone number may be incorrect
- Contact may not have a Telegram account
- Phone number format may be wrong (needs country code)

### "Daily limit reached"

- Wait 24 hours for limit to reset
- Check `/api/telegram/campaign/status` for reset time
- Consider spreading campaigns across multiple days

### "FloodWaitError"

- Telegram has rate limited your account
- System will automatically wait the required time
- Reduce sending frequency if this happens often

---

## 🚀 Next Steps

1. **Install Telethon**: `pip install telethon==1.34.0`
2. **Run migration**: `python database/migrations/add_telegram_campaign.py`
3. **Get API credentials**: https://my.telegram.org/apps
4. **Connect account**: http://localhost:8000/crm/integrations
5. **Start your first campaign**!

---

## 📚 Resources

- **Telethon Documentation**: https://docs.telethon.dev/
- **Telegram API**: https://core.telegram.org/api
- **Get API Credentials**: https://my.telegram.org/apps
- **Telegram ToS**: https://telegram.org/tos

---

**Happy Campaigning! 🎉**

