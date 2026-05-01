# User Authentication Setup

## Installation Steps

1. Install new dependencies:
```bash
pip install -r requirements.txt
```

2. Run migration script (ONLY ONCE):
```bash
python migrate_auth.py
```

3. Start the application:
```bash
python app.py
```

4. Open browser and go to: http://127.0.0.1:5000

## Default Login (if you have existing data)
- Email: admin@example.com
- Password: admin123

## Features Added

✅ User signup and login
✅ Secure password hashing
✅ Session management
✅ Each user sees only their own plans
✅ Protected routes - must login to access
✅ Logout functionality

## Security Notes

- Change SECRET_KEY in app.py before production
- Remove hardcoded GEMINI_API_KEY (line 32 in app.py)
- Use environment variables for sensitive data

## Usage

1. New users: Click "Sign up" to create account
2. Existing users: Login with email/password
3. All plans are private to each user
4. Logout button in top-right corner
