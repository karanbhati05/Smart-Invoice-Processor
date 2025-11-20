# Smart Invoice Processor 💼

> AI-powered invoice processing web application with Google OAuth authentication, batch processing, and professional email reports

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/karanbhati05/Smart-Invoice-Processor)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![Flask](https://img.shields.io/badge/flask-2.3+-green.svg)

## 🌟 Features

### Processing Modes
- **Single Invoice Processing** - Quick, in-memory processing for individual invoices
- **Batch Processing** - Upload and process multiple invoices at once with database storage

### Core Functionality
- 🤖 **AI-Powered OCR** - Automatic extraction of invoice data using OCR.space API
- 🔐 **Google OAuth** - Secure authentication with Google accounts
- 📊 **Dashboard** - Real-time statistics and invoice management
- 📥 **Multiple Export Formats** - JSON, CSV, and PDF exports
- 📧 **Email Reports** - Beautiful HTML email reports with detailed statistics
- 🎨 **Dark/Light Mode** - Theme toggle with localStorage persistence
- 📱 **Mobile Responsive** - Optimized UI with hamburger menu and bottom navigation
- 🔒 **User Isolation** - Each user's data is completely isolated

### Dashboard Features
- Real-time invoice statistics
- Invoice listing with search and filter
- Detailed invoice view
- Batch operations
- Top vendors analysis
- Recent invoices tracking

## 🚀 Live Demo

Visit the live application: [Smart Invoice Processor](https://ai-invoice-automation-one.vercel.app)

## 📁 Project Structure

```
smart-invoice-processor/
├── api/
│   ├── index.py              # Main Flask application
│   ├── processor.py          # Invoice processing logic
│   └── __init__.py
├── public/
│   ├── login.html            # Login page
│   ├── single.html           # Single invoice processor
│   ├── batch.html            # Batch processing dashboard
│   ├── index.html            # Landing page
│   └── assets/
│       └── logo.png          # Application logo
├── requirements.txt          # Python dependencies
├── vercel.json              # Vercel configuration
├── .gitignore               # Git ignore rules
├── .env.example             # Environment variables template
├── LICENSE                  # MIT License
├── CONTRIBUTING.md          # Contribution guidelines
└── README.md                # This file
└── ENHANCEMENT_SUMMARY.md    # What's new in v2.0
```

## 📋 Prerequisites

- Python 3.9 or higher
- OCR.space API key (free tier available at [ocr.space](https://ocr.space/ocrapi))
- Google OAuth credentials ([Google Cloud Console](https://console.cloud.google.com))
- SMTP server credentials (for email features)

## 🛠️ Installation

### 1. Clone the repository

```bash
git clone https://github.com/karanbhati05/Smart-Invoice-Processor.git
cd Smart-Invoice-Processor
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up environment variables

Copy `.env.example` to `.env` and configure:

```env
# OCR API
OCR_API_KEY=your_ocr_space_api_key

# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# JWT Secret
JWT_SECRET=your_random_secret_key

# SMTP Configuration (for email features)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# Base URL (for OAuth redirects)
VERCEL_URL=http://localhost:5000
```

### 4. Run locally

```bash
python api/index.py
```

The application will be available at `http://localhost:5000`

## 🌐 Deployment to Vercel

### 1. Install Vercel CLI

```bash
npm i -g vercel
```

### 2. Deploy

```bash
vercel --prod
```

### 3. Configure Environment Variables

Add the following environment variables in your Vercel project settings:
- `OCR_API_KEY`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `JWT_SECRET`
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USER`
- `SMTP_PASSWORD`

## 📡 API Endpoints

### Authentication
- `POST /api/v2/auth/google` - Initiate Google OAuth
- `GET /api/v2/auth/google/callback` - OAuth callback
- `POST /api/v2/auth/guest` - Guest login

### Invoice Processing
- `POST /api/v2/process` - Process single invoice
- `POST /api/v2/batch` - Process multiple invoices
- `GET /api/v2/invoices` - List invoices
- `GET /api/v2/invoices/{id}` - Get invoice details

### Export & Reports
- `GET /api/v2/export` - Export invoices (JSON/CSV/PDF)
- `POST /api/v2/send-single-invoice` - Email single invoice
- `POST /api/v2/send-report` - Email batch report

### Database
- `POST /api/v2/reset-database` - Clear user's invoices
- `GET /api/v2/stats` - Get user statistics

## 🎯 Usage

### Single Invoice Processing

1. **Login** - Sign in with Google or continue as guest
2. **Upload** - Drag & drop or click to upload an invoice (PDF, JPG, PNG)
3. **Preview** - View extracted data in real-time
4. **Export** - Download as JSON/CSV or email the report

### Batch Processing

1. **Login** - Sign in with Google (required for batch mode)
2. **Upload Multiple** - Select multiple invoice files
3. **Process** - Batch processes all invoices
4. **Manage** - View, filter, and manage all invoices
5. **Export/Email** - Export all data or receive email reports with vendor breakdown

## 🎨 Customization

### Theme Colors

Edit the CSS variables in `single.html` and `batch.html`:

```css
:root {
    --primary: #6366f1;
    --primary-dark: #4f46e5;
    --secondary: #8b5cf6;
    --success: #10b981;
    --danger: #ef4444;
    --warning: #f59e0b;
}
```

### Logo

Replace `/public/assets/logo.png` with your own logo.

## 🔒 Security Features

- JWT-based authentication
- OAuth 2.0 integration
- User data isolation
- Secure cookie handling
- Environment variable protection
- Bearer token authentication on all API calls

## 📊 Technologies Used

### Backend
- **Flask** - Python web framework
- **SQLite** - Database
- **OCR.space API** - Invoice text extraction
- **PyJWT** - Token authentication
- **Requests** - HTTP client

### Frontend
- **Vanilla JavaScript** - No framework dependencies
- **HTML5/CSS3** - Modern web standards
- **Responsive Design** - Mobile-first approach

### Deployment
- **Vercel** - Serverless deployment
- **Python Runtime** - Serverless functions

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

Built with ❤️ for efficient invoice processing

## 🙏 Acknowledgments

- [OCR.space](https://ocr.space/) for the OCR API
- [Vercel](https://vercel.com/) for hosting
- [Google](https://developers.google.com/identity) for OAuth services

## 📧 Support

For support, open an issue in the repository or contact the maintainers.

## 🗺️ Roadmap

- [ ] Add support for more invoice formats
- [ ] Implement invoice templates
- [ ] Add multi-language support
- [ ] Integration with accounting software (QuickBooks, Xero)
- [ ] Advanced analytics dashboard
- [ ] Mobile app (React Native)
- [ ] Webhook support for integrations
- [ ] Multi-currency support improvements

---

**Live Demo:** [https://ai-invoice-automation-one.vercel.app](https://ai-invoice-automation-one.vercel.app)

## ⭐ Support

If this project helped you, please give it a star! ⭐

---

**Invoice Processor Pro v2.0** - Enterprise-grade invoice processing powered by AI 🚀
