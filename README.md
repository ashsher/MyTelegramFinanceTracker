# 💰 Finance Tracker - Telegram Mini-App

A comprehensive personal finance tracker built as a Telegram Mini-App. Track expenses, manage multiple money sources, and visualize your spending habits with beautiful charts.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0.0-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ Features

### 💳 Money Source Management
- Track multiple payment sources (Credit Cards, Cash, PayPal, Bank Accounts)
- Real-time balance monitoring
- Low balance warnings
- Automatic balance updates when expenses are added

### 📊 Expense Tracking
- Quick expense entry with category selection
- 7 predefined categories: Food, Transport, Shopping, Bills, Entertainment, Health, Other
- Optional notes for each expense
- Delete expenses with automatic balance restoration

### 📈 Statistics & Visualization
- **Monthly Statistics:** Pie chart showing spending by category
- **Weekly Trend:** Bar chart showing daily spending for the past 7 days
- Real-time balance summary dashboard

### 🎨 User Interface
- Beautiful gradient design
- Responsive mobile-first layout
- Smooth animations and transitions
- Intuitive category selection with icons
- Native Telegram Mini-App integration

## 🏗️ Architecture

### Tech Stack
- **Backend:** Python 3.9+ with Flask
- **Database:** SQLite3
- **Frontend:** HTML5, CSS3, Vanilla JavaScript
- **Charts:** Chart.js
- **Hosting:** Render.com (Free Tier)
- **Platform:** Telegram Mini Apps

### Database Schema

```sql
users
├── id (INTEGER, PRIMARY KEY)
├── telegram_id (INTEGER, UNIQUE)
├── username (TEXT)
└── created_at (TIMESTAMP)

money_sources
├── id (INTEGER, PRIMARY KEY)
├── user_id (INTEGER, FOREIGN KEY)
├── name (TEXT)
├── balance (REAL)
├── type (TEXT)
└── created_at (TIMESTAMP)

expenses
├── id (INTEGER, PRIMARY KEY)
├── user_id (INTEGER, FOREIGN KEY)
├── source_id (INTEGER, FOREIGN KEY)
├── amount (REAL)
├── category (TEXT)
├── note (TEXT)
└── created_at (TIMESTAMP)
```

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/init` | Initialize/get user |
| GET | `/api/sources` | Get all money sources |
| POST | `/api/sources` | Add new money source |
| PUT | `/api/sources/:id` | Update source balance |
| DELETE | `/api/sources/:id` | Delete money source |
| GET | `/api/expenses` | Get all expenses |
| POST | `/api/expenses` | Add new expense |
| DELETE | `/api/expenses/:id` | Delete expense |
| GET | `/api/statistics/monthly` | Get monthly statistics |
| GET | `/api/statistics/weekly` | Get weekly statistics |
| GET | `/api/statistics/sources` | Get source statistics |

## 🚀 Quick Start

### Prerequisites
- Python 3.9 or higher
- Git
- Telegram account
- GitHub account (for deployment)
- Render.com account (free)

### Local Development

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/finance-tracker-bot.git
cd finance-tracker-bot
```

2. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Run the application:**
```bash
python app.py
```

5. **Open in browser:**
```
http://localhost:5000
```

### Database Management

Use the included database management script:

```bash
python database_setup.py
```

Options:
1. Create/Initialize Database
2. Add Sample Data (for testing)
3. View Database Contents
4. Reset Database (delete all data)

## 📦 Deployment

### Deploy to Render.com

1. **Create Telegram Bot:**
   - Message @BotFather on Telegram
   - Send `/newbot` and follow instructions
   - Save your bot token

2. **Push to GitHub:**
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/yourusername/finance-tracker-bot.git
git push -u origin main
```

3. **Deploy on Render:**
   - Go to [render.com](https://render.com)
   - Create new Web Service
   - Connect your GitHub repository
   - Configure:
     - Build Command: `pip install -r requirements.txt`
     - Start Command: `gunicorn app:app`
   - Add environment variable:
     - `TELEGRAM_BOT_TOKEN`: Your bot token

4. **Register Mini-App:**
   - Go back to @BotFather
   - Send `/newapp`
   - Select your bot
   - Enter details and your Render URL
   - Get your mini-app link

**Detailed deployment guide:** See [DEPLOYMENT.md](DEPLOYMENT.md)

## 💰 Cost

**Total: $0/month** ✨

- ✅ Render.com Free Tier (750 hours/month)
- ✅ GitHub (Free)
- ✅ Telegram Bot (Free)

**Note:** App may sleep after 15 minutes of inactivity on free tier. It wakes up automatically when accessed.

## 📱 Usage

1. Open your bot in Telegram
2. Click "Open App" or use the direct link
3. Add your money sources (e.g., Credit Card, Cash)
4. Start tracking expenses!
5. View beautiful statistics on your spending

## 🎓 Educational Value

This project demonstrates:
- ✅ Full-stack web development
- ✅ RESTful API design
- ✅ Database design and management
- ✅ Frontend UI/UX implementation
- ✅ Third-party API integration (Telegram)
- ✅ Cloud deployment and DevOps
- ✅ Git version control
- ✅ Data visualization

Perfect for:
- Final year projects
- Portfolio demonstrations
- Learning modern web development
- Understanding Telegram Mini Apps

## 🔧 Configuration

### Environment Variables

```bash
TELEGRAM_BOT_TOKEN=your_bot_token_here
FLASK_ENV=production
DATABASE_URL=sqlite:///finance.db
PORT=5000
```

### Categories

Default categories (can be customized in `index.html`):
- 🍔 Food
- 🚗 Transport
- 🛍️ Shopping
- 💡 Bills
- 🎬 Entertainment
- 💊 Health
- 📦 Other

### Money Source Types
- 💵 Cash
- 💳 Credit/Debit Card
- 🅿️ PayPal
- 🏦 Bank Account
- 📦 Other

## 🐛 Troubleshooting

### Common Issues

**Issue:** App shows blank screen
- **Solution:** Check if backend is running, verify Render URL is correct

**Issue:** "Insufficient balance" error
- **Solution:** Ensure money source has enough balance

**Issue:** App sleeps on Render
- **Solution:** This is normal on free tier. App wakes automatically (30-60s)

**Issue:** Database errors
- **Solution:** Run `database_setup.py` to reset database

## 🚀 Future Enhancements

Possible additions:
- [ ] Export data to CSV/Excel
- [ ] Budget limits and notifications
- [ ] Recurring expenses
- [ ] Multi-currency support
- [ ] Receipt photo upload
- [ ] Custom categories
- [ ] Shared expenses
- [ ] Income tracking
- [ ] Monthly email reports
- [ ] Dark mode

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**Your Name**
- Telegram: @ashsher

## 🙏 Acknowledgments

- Telegram for their excellent Mini Apps platform
- Flask community for the amazing web framework
- Chart.js for beautiful data visualizations
- Render.com for free hosting

## 📞 Support

If you have any questions or issues:
1. Check the [Deployment Guide](DEPLOYMENT.md)
2. Review [Troubleshooting](#troubleshooting) section
3. Open an issue on GitHub
4. Contact via Telegram: @ashsher

---

**⭐ If you find this project helpful, please give it a star!**

Made with ❤️ for learning and productivity
