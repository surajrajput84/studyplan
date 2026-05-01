# 📚 Study Plan Manager

A full-stack web application for creating, managing, and tracking personalized study plans with AI-powered plan generation.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)
![MongoDB](https://img.shields.io/badge/MongoDB-4.4+-brightgreen.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ Features

- 🤖 **AI-Powered Plan Generation** - Generate customized study plans using Google Gemini AI
- 📅 **Calendar View** - Visualize your study schedule with an interactive calendar
- 📊 **Progress Tracking** - Monitor your learning progress with detailed analytics
- 🎯 **Multiple Study Plans** - Create and manage multiple plans for different subjects
- 👤 **User Authentication** - Secure login and signup system
- 📱 **Responsive Design** - Works seamlessly on desktop and mobile devices
- 🌙 **Dark Mode** - Eye-friendly dark theme support

## 🚀 Demo

[Live Demo](https://your-vercel-app.vercel.app) _(Add your Vercel deployment URL)_

## 📸 Screenshots

_(Add screenshots of your application here)_

## 🛠️ Tech Stack

### Backend
- **Flask** - Python web framework
- **MongoDB** - NoSQL database
- **Flask-Login** - User session management
- **Google Gemini AI** - AI-powered plan generation
- **Bcrypt** - Password hashing

### Frontend
- **HTML5/CSS3** - Structure and styling
- **JavaScript (Vanilla)** - Interactive functionality
- **Responsive Design** - Mobile-first approach

## 📋 Prerequisites

- Python 3.8 or higher
- MongoDB (local or MongoDB Atlas)
- Google Gemini API key
- Git

## 🔧 Installation

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/study-plan-manager.git
cd study-plan-manager
```

### 2. Create virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up environment variables
Create a `.env` file in the root directory:
```env
SECRET_KEY=your-secret-key-here
MONGO_URI=mongodb://localhost:27017/study_planner
GEMINI_API_KEY=your-gemini-api-key-here
```

**Generate a secure SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 5. Set up MongoDB

**Option A: Local MongoDB**
```bash
# Install MongoDB and start the service
mongod
```

**Option B: MongoDB Atlas (Cloud)**
1. Create account at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Create a cluster
3. Get connection string and update `MONGO_URI` in `.env`

### 6. Run the application
```bash
python app.py
```

Visit `http://localhost:5000` in your browser.

## 🌐 Deployment

### Deploy to Vercel

1. **Install Vercel CLI**
```bash
npm i -g vercel
```

2. **Login to Vercel**
```bash
vercel login
```

3. **Deploy**
```bash
vercel
```

4. **Set Environment Variables** in Vercel Dashboard:
   - `SECRET_KEY`
   - `MONGO_URI`
   - `GEMINI_API_KEY`

### Deploy to Heroku

1. **Create Heroku app**
```bash
heroku create your-app-name
```

2. **Set environment variables**
```bash
heroku config:set SECRET_KEY=your-secret-key
heroku config:set MONGO_URI=your-mongodb-uri
heroku config:set GEMINI_API_KEY=your-gemini-key
```

3. **Deploy**
```bash
git push heroku main
```

## 📁 Project Structure

```
study-plan-manager/
├── api/
│   └── index.py          # Vercel serverless entry point
├── static/
│   ├── style.css         # Main stylesheet
│   ├── theme.js          # Theme switcher
│   ├── cubes.css         # 3D cube animations
│   └── cubes.js          # Cube logic
├── templates/
│   ├── index.html        # Dashboard
│   ├── login.html        # Login page
│   ├── signup.html       # Signup page
│   ├── create_plan.html  # Create plan with AI
│   ├── weeks.html        # Week view
│   ├── calendar.html     # Calendar view
│   ├── dashboard.html    # Analytics dashboard
│   └── ...
├── app.py                # Main Flask application
├── models_mongo.py       # MongoDB models
├── parser_mongo.py       # Plan text parser
├── requirements.txt      # Python dependencies
├── vercel.json          # Vercel configuration
├── .vercelignore        # Vercel ignore file
└── README.md            # This file
```

## 🎯 Usage

### Creating a Study Plan

**Method 1: AI Chatbot**
1. Click "Create New Plan"
2. Select "AI Chatbot" tab
3. Answer questions about subject, duration, and daily hours
4. AI generates a customized plan
5. Review and save

**Method 2: Paste Plan**
1. Click "Create New Plan"
2. Select "Paste Plan" tab
3. Paste your pre-formatted plan text
4. System parses and creates the plan

**Method 3: Manual**
1. Click "Create New Plan"
2. Select "Manual" tab
3. Enter plan details
4. Add weeks and days manually

### Tracking Progress
- Mark days as completed by clicking on them
- View progress in the dashboard
- Check calendar for visual overview
- Monitor analytics and streaks

## 🔑 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Dashboard |
| GET | `/login` | Login page |
| POST | `/login` | Authenticate user |
| GET | `/signup` | Signup page |
| POST | `/signup` | Register new user |
| GET | `/create` | Create plan page |
| POST | `/plan` | Create new plan |
| POST | `/parse-plan` | Parse and create plan |
| DELETE | `/plan/<id>` | Delete plan |
| GET | `/plan/<id>/weeks` | View plan weeks |
| GET | `/plan/<id>/calendar` | Calendar view |
| GET | `/progress/<id>` | Get plan progress |
| PUT | `/day/<plan_id>/<week>/<day>` | Update day status |
| POST | `/chatbot` | AI chatbot interaction |

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 🐛 Known Issues

- Week-based day navigation needs improvement
- Analytics calculations for streaks need refinement
- Mobile calendar view can be optimized

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**Your Name**
- GitHub: [@yourusername](https://github.com/yourusername)
- LinkedIn: [Your LinkedIn](https://linkedin.com/in/yourprofile)

## 🙏 Acknowledgmentsgit add .

- [Flask](https://flask.palletsprojects.com/) - Web framework
- [MongoDB](https://www.mongodb.com/) - Database
- [Google Gemini AI](https://ai.google.dev/) - AI plan generation
- [Vercel](https://vercel.com/) - Deployment platform

## 📧 Support

For support, email your-email@example.com or open an issue in the repository.

---

⭐ **Star this repo if you find it helpful!**
