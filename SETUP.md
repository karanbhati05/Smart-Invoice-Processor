# Setup Guide - Smart Invoice Processor

Complete setup instructions to get the Smart Invoice Processor running locally and deployed to production.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Configuration](#configuration)
4. [Google OAuth Setup](#google-oauth-setup)
5. [SMTP Email Setup](#smtp-email-setup)
6. [Vercel Deployment](#vercel-deployment)
7. [Testing](#testing)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

Before you begin, ensure you have:

- **Python 3.9+** installed ([Download](https://www.python.org/downloads/))
- **Git** installed ([Download](https://git-scm.com/downloads))
- **Node.js** (for Vercel CLI) ([Download](https://nodejs.org/))
- **OCR.space API Key** ([Get free key](https://ocr.space/ocrapi))
- **Google Cloud Project** (for OAuth) ([Console](https://console.cloud.google.com))
- **Email Account** with SMTP access (Gmail recommended)

## Local Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/smart-invoice-processor.git
cd smart-invoice-processor
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` and add your credentials (see [Configuration](#configuration) section).

### 4. Run the Application

```bash
python api/index.py
```

The application will start on `http://localhost:5000`

- Single Invoice Processor: `http://localhost:5000/single.html`
- Batch Processor Dashboard: `http://localhost:5000/batch.html`
- Login Page: `http://localhost:5000/login.html`

## Configuration

### Environment Variables

Edit your `.env` file with the following:

```env
# OCR API Configuration
OCR_API_KEY=K87654321
# Get your free key at: https://ocr.space/ocrapi

# Google OAuth Configuration
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
# See "Google OAuth Setup" section below

# JWT Secret (generate a random string)
JWT_SECRET=your-super-secret-random-string-here
# You can generate one with: python -c "import secrets; print(secrets.token_hex(32))"

# SMTP Configuration (for email features)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-specific-password
# See "SMTP Email Setup" section below

# Base URL (update for production)
VERCEL_URL=http://localhost:5000
# For production, this will be your Vercel domain
```

## Google OAuth Setup

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Click **"Create Project"** or select an existing project
3. Name it "Smart Invoice Processor" (or your preferred name)

### Step 2: Enable Google+ API

1. In the sidebar, go to **"APIs & Services"** > **"Library"**
2. Search for **"Google+ API"**
3. Click on it and press **"Enable"**

### Step 3: Configure OAuth Consent Screen

1. Go to **"APIs & Services"** > **"OAuth consent screen"**
2. Select **"External"** user type
3. Fill in the required fields:
   - **App name:** Smart Invoice Processor
   - **User support email:** Your email
   - **Developer contact:** Your email
4. Click **"Save and Continue"**
5. On the "Scopes" page, click **"Add or Remove Scopes"**
   - Add: `userinfo.email`
   - Add: `userinfo.profile`
6. Click **"Save and Continue"**
7. Add test users (your email address)
8. Click **"Save and Continue"**

### Step 4: Create OAuth Credentials

1. Go to **"APIs & Services"** > **"Credentials"**
2. Click **"+ Create Credentials"** > **"OAuth client ID"**
3. Select application type: **"Web application"**
4. Name: "Invoice Processor Web Client"
5. Add **Authorized JavaScript origins:**
   - `http://localhost:5000` (for local testing)
   - `https://your-vercel-domain.vercel.app` (for production)
6. Add **Authorized redirect URIs:**
   - `http://localhost:5000/api/v2/auth/google/callback` (local)
   - `https://your-vercel-domain.vercel.app/api/v2/auth/google/callback` (production)
7. Click **"Create"**
8. Copy your **Client ID** and **Client Secret**
9. Add them to your `.env` file

## SMTP Email Setup

### For Gmail Users (Recommended)

1. **Enable 2-Factor Authentication:**
   - Go to [Google Account Security](https://myaccount.google.com/security)
   - Enable "2-Step Verification"

2. **Generate App Password:**
   - Go to [App Passwords](https://myaccount.google.com/apppasswords)
   - Select "Mail" and "Other (Custom name)"
   - Name it "Invoice Processor"
   - Click "Generate"
   - Copy the 16-character password

3. **Update .env:**
   ```env
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your-email@gmail.com
   SMTP_PASSWORD=your-16-char-app-password
   ```

### For Other Email Providers

#### Outlook/Hotmail
```env
SMTP_HOST=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_USER=your-email@outlook.com
SMTP_PASSWORD=your-password
```

#### Yahoo Mail
```env
SMTP_HOST=smtp.mail.yahoo.com
SMTP_PORT=587
SMTP_USER=your-email@yahoo.com
SMTP_PASSWORD=your-app-password
```

## Vercel Deployment

### Step 1: Install Vercel CLI

```bash
npm install -g vercel
```

### Step 2: Login to Vercel

```bash
vercel login
```

### Step 3: Deploy

From the project directory:

```bash
vercel --prod
```

Follow the prompts:
- **Set up and deploy?** Yes
- **Which scope?** Your account
- **Link to existing project?** No
- **Project name?** smart-invoice-processor
- **Directory?** ./
- **Override settings?** No

### Step 4: Add Environment Variables in Vercel

1. Go to your Vercel dashboard
2. Select your project
3. Go to **"Settings"** > **"Environment Variables"**
4. Add each variable from your `.env` file:
   - `OCR_API_KEY`
   - `GOOGLE_CLIENT_ID`
   - `GOOGLE_CLIENT_SECRET`
   - `JWT_SECRET`
   - `SMTP_HOST`
   - `SMTP_PORT`
   - `SMTP_USER`
   - `SMTP_PASSWORD`
   - `VERCEL_URL` (set to your production URL)

5. Redeploy:
   ```bash
   vercel --prod
   ```

### Step 5: Update OAuth Redirect URLs

Go back to Google Cloud Console and add your production URL to the authorized redirect URIs:
- `https://your-app.vercel.app/api/v2/auth/google/callback`

## Testing

### Test OCR Processing

1. Go to `http://localhost:5000/single.html`
2. Upload a sample invoice (PDF, JPG, or PNG)
3. Verify data extraction works

### Test Google OAuth

1. Go to `http://localhost:5000/login.html`
2. Click "Sign in with Google"
3. Complete OAuth flow
4. Verify you're redirected back with user info

### Test Email Features

1. Process an invoice
2. Click "Email Report"
3. Check your inbox for the email

### Test Batch Processing

1. Login with Google account
2. Go to `http://localhost:5000/batch.html`
3. Upload multiple invoices
4. Verify all invoices are processed and stored
5. Test export and email features

## Troubleshooting

### Issue: "OCR API Key Invalid"

**Solution:** Verify your OCR.space API key:
- Check it's correctly copied to `.env`
- Ensure there are no extra spaces
- Get a new key if needed: https://ocr.space/ocrapi

### Issue: "OAuth Redirect URI Mismatch"

**Solution:** 
- Verify redirect URIs in Google Cloud Console match exactly
- Include both `http://localhost:5000` and production URL
- Clear browser cache and try again

### Issue: "Email Not Sending"

**Solution:**
- For Gmail: Use App Password, not regular password
- Verify SMTP settings are correct
- Check firewall isn't blocking port 587
- Test with a simple SMTP client first

### Issue: "Database Not Persisting on Vercel"

**Note:** This is expected behavior. Vercel's serverless functions are stateless. The SQLite database is temporary and resets on each deployment. For production:
- Consider using Vercel Postgres
- Or use an external database service
- Current implementation is designed for demo purposes

### Issue: "Module Not Found"

**Solution:**
```bash
pip install -r requirements.txt --force-reinstall
```

### Issue: "Port Already in Use"

**Solution:**
```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# macOS/Linux
lsof -ti:5000 | xargs kill
```

## Next Steps

- Read the [README.md](README.md) for feature documentation
- Check [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines
- Review the [LICENSE](LICENSE) for usage terms

## Support

If you encounter issues not covered here:
1. Check existing [GitHub Issues](https://github.com/yourusername/smart-invoice-processor/issues)
2. Create a new issue with detailed description
3. Include error logs and environment details

---

Happy invoice processing! 💼
