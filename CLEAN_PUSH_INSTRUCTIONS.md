# Clean Push Instructions

GitHub detected API keys in the git history. Here's how to create a clean submission:

## Option 1: Fresh Repository (Recommended)

```bash
# 1. Navigate to hackathon folder
cd hackathon

# 2. Remove old git history
rm -rf .git

# 3. Initialize fresh repository
git init

# 4. Add remote
git remote add origin https://github.com/Rappid-exe/LeadOn-Submission.git

# 5. Add all files (gitignore will exclude sensitive files)
git add .

# 6. Commit
git commit -m "Initial commit - LeadOn CRM submission"

# 7. Push to main branch
git branch -M main
git push -u origin main --force
```

## Option 2: Remove Secrets from History (Advanced)

If you want to keep the git history:

```bash
# Install BFG Repo Cleaner
# Download from: https://rtyley.github.io/bfg-repo-cleaner/

# Remove files with secrets
java -jar bfg.jar --delete-files test_claude_api.py hackathon

# Clean up
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Force push
git push origin main --force
```

## What Was Detected

GitHub found Anthropic API keys in:
- `test_claude_api.py` (blob: 1af3d1af...)
- Other test files in history

These files are now in `.gitignore` but were in previous commits.

## Verification

After pushing, verify no secrets are exposed:
1. Go to: https://github.com/Rappid-exe/LeadOn-Submission
2. Check that `.env` is not in the repo
3. Check that test files are not visible
4. Verify API keys are not in any files

## Important

- Never commit `.env` files
- Never hardcode API keys in code
- Always use environment variables
- Review `.gitignore` before committing
