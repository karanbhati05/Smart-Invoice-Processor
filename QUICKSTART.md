# Quick Start

Get the Smart Invoice Processor running in 5 minutes!

## ⚡ Express Setup

### 1. Clone & Install
```bash
git clone https://github.com/yourusername/smart-invoice-processor.git
cd smart-invoice-processor
pip install -r requirements.txt
```

### 2. Configure
```bash
cp .env.example .env
# Edit .env with your credentials
```

### 3. Run
```bash
python api/index.py
```

Visit: `http://localhost:5000`

## 🔑 Required API Keys

### OCR.space (Free)
1. Visit https://ocr.space/ocrapi
2. Sign up with email
3. Copy your API key
4. Add to `.env` as `OCR_API_KEY`

### Google OAuth
1. Go to https://console.cloud.google.com
2. Create new project
3. Enable Google+ API
4. Create OAuth 2.0 credentials
5. Add redirect URI: `http://localhost:5000/api/v2/auth/google/callback`
6. Copy Client ID and Secret to `.env`

### Gmail SMTP (for emails)
1. Enable 2FA on your Google account
2. Generate App Password at https://myaccount.google.com/apppasswords
3. Add to `.env` as `SMTP_PASSWORD`

## 📦 Deploy to Vercel

```bash
npm i -g vercel
vercel --prod
```

Add environment variables in Vercel dashboard → Settings → Environment Variables

## 📚 Documentation

- **Full Setup Guide**: [SETUP.md](SETUP.md)
- **Feature Documentation**: [README.md](README.md)
- **Contributing**: [CONTRIBUTING.md](CONTRIBUTING.md)

## 🆘 Need Help?

Check the [troubleshooting section](SETUP.md#troubleshooting) in SETUP.md

---

**Live Demo**: https://ai-invoice-automation-one.vercel.app
