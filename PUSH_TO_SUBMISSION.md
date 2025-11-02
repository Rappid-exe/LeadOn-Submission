# Push to Submission Repository

## Problem
GitHub blocked the push because it detected API keys in the git history (from old test files).

## Solution
Create a fresh git repository without the old history.

## Quick Start

### Windows
```bash
cd hackathon
clean_push.bat
```

### Manual Steps
```bash
cd hackathon

# Remove old git history
rm -rf .git

# Initialize fresh repository
git init
git remote add origin https://github.com/Rappid-exe/LeadOn-Submission.git

# Add files (gitignore will exclude sensitive files)
git add .

# Commit and push
git commit -m "Initial commit - LeadOn CRM hackathon submission"
git branch -M main
git push -u origin main --force
```

## What's Excluded

The `.gitignore` now excludes:
- `.env` files (API keys)
- `linkedin_cookies.json` (session data)
- `*.session` files (Telegram sessions)
- `test_*.py` (test scripts)
- `debug_*.py` and `debug_*.png` (debug files)
- `clear_contacts.py` (utility script)
- `MAGIC_WAND_FIX.md` (internal docs)
- `cleanup_for_submission.py` (cleanup script)
- `__pycache__/` and `*.pyc` (Python cache)
- `database/leadon.db` (your data)

## What's Included

✅ All source code
✅ README.md with setup instructions
✅ SUBMISSION_GUIDE.md
✅ requirements.txt
✅ .env.example (template)
✅ Database migrations
✅ Frontend files
✅ Documentation

## Verification

After pushing, check:
1. Visit: https://github.com/Rappid-exe/LeadOn-Submission
2. Verify `.env` is NOT visible
3. Verify test files are NOT visible
4. Check README displays correctly
5. Verify no API keys in any files

## If You Need to Update

After the initial push, you can make changes normally:

```bash
cd hackathon
git add .
git commit -m "Your commit message"
git push
```

The `.gitignore` will continue to protect sensitive files.

## Troubleshooting

### "remote: Repository not found"
- Make sure the repository exists on GitHub
- Check you have push access
- Verify the URL is correct

### "failed to push some refs"
- Use `--force` flag for initial push
- This overwrites any existing content

### Still seeing secrets warning
- Double-check `.gitignore` includes the file
- Make sure you removed `.git` folder
- Verify the file isn't already committed

## Support

If you encounter issues:
1. Check CLEAN_PUSH_INSTRUCTIONS.md
2. Review .gitignore
3. Verify no hardcoded secrets in code
