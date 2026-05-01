from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models_mongo import User, StudyPlan, Activity, plans_collection
from parser_mongo import parse_plan_text
from datetime import datetime, date, timedelta
from bson import ObjectId
from google import genai
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.find_by_id(user_id)

# ── Gemini AI Setup ──────────────────────────────────────────
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', 'AIzaSyDdQ4usMeVV04WGDCWzuxLGFTavY1a03Ic')
_gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

def _build_prompt(subject: str, days: int, hours: float) -> str:
    if hours < 1.5:
        depth_rule = 'Add "(overview)" after every topic.'
    elif hours >= 3:
        depth_rule = 'Add "(deep dive)" after every topic.'
    else:
        depth_rule = 'Do not add any label.'

    return f"""You are an expert study plan generator.
Create a {days}-day study plan for learning: {subject}.
Student studies {hours} hours per day.

Rules:
- Organise into weeks of 7 days.
- Follow this EXACT format with no deviations:

Week 1 — Days 1–7
Day 1 – Topic
Day 2 – Topic

Week 2 — Days 8–14
Day 8 – Topic

- {depth_rule}
- Do NOT add any explanations, introductions, conclusions, or blank lines between days.
- Output ONLY the plan text, nothing else.
- Topics must progress logically from beginner to advanced.
- Every day must have exactly one topic."""

def _clean_plan(text: str) -> str:
    lines = text.splitlines()
    cleaned = [l.strip() for l in lines
               if l.strip().startswith('Week') or l.strip().startswith('Day')]
    return '\n'.join(cleaned)

def _generate_plan(subject: str, days: int, hours: float) -> str:
    if not _gemini_client:
        raise Exception("Gemini API key not configured")
    
    prompt = _build_prompt(subject, days, hours)
    models_to_try = ['gemini-2.0-flash-lite', 'gemini-2.0-flash', 'gemini-flash-latest']
    
    for model in models_to_try:
        try:
            response = _gemini_client.models.generate_content(model=model, contents=prompt)
            return _clean_plan(response.text.strip())
        except Exception as e:
            last_error = e
            continue
    raise last_error

def _time_ago(dt):
    diff = datetime.utcnow() - dt
    s = int(diff.total_seconds())
    if s < 60: return 'Just now'
    if s < 3600: return f'{s // 60} min ago'
    if s < 86400: return f'{s // 3600} hr ago'
    return f'{s // 86400}d ago'

# ── Authentication Routes ────────────────────────────────────

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.find_by_email(email)
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
        return render_template('login.html', error='Invalid email or password')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.find_by_email(email):
            return render_template('signup.html', error='Email already registered')
        if User.find_by_username(username):
            return render_template('signup.html', error='Username already taken')
        
        user = User(username=username, email=email)
        user.set_password(password)
        user.save()
        
        login_user(user)
        return redirect(url_for('index'))
    
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# ── Page Routes ──────────────────────────────────────────────

@app.route('/')
@login_required
def index():
    plans = StudyPlan.find_by_user(current_user.id)
    # Add id field for template compatibility
    for p in plans:
        p['id'] = str(p['_id'])
    by_subject = {}
    for p in plans:
        by_subject.setdefault(p['subject'], []).append(p)
    return render_template('index.html', by_subject=by_subject, username=current_user.username)

@app.route('/create')
@login_required
def create_page():
    return render_template('create_plan.html')

@app.route('/all-plans')
@login_required
def all_plans_page():
    return render_template('all_plans.html')

@app.route('/all-calendar')
@login_required
def all_calendar_page():
    return render_template('all_calendar.html', username=current_user.username)

@app.route('/all-progress')
@login_required
def all_progress_page():
    return render_template('all_progress.html')

@app.route('/plan/<plan_id>/weeks')
@login_required
def weeks_page(plan_id):
    plan = StudyPlan.find_by_id(plan_id, current_user.id)
    if not plan:
        return redirect(url_for('index'))
    # Add id field for template compatibility
    plan['id'] = str(plan['_id'])
    weeks = plan.get('weeks', [])
    # Add id to each week for template
    for w in weeks:
        w['id'] = w['week_number']
    return render_template('weeks.html', plan=plan, weeks=weeks)

@app.route('/week/<int:week_id>/days')
@login_required
def days_page(week_id):
    # MongoDB doesn't use week_id, need to find by plan and week number
    # For now, redirect to index
    return redirect(url_for('index'))

@app.route('/plan/<plan_id>/calendar')
@login_required
def calendar_page(plan_id):
    plan = StudyPlan.find_by_id(plan_id, current_user.id)
    if not plan:
        return redirect(url_for('index'))
    plan['id'] = str(plan['_id'])
    print(f"Calendar page - Plan ID: {plan['id']}, Title: {plan['title']}")
    return render_template('calendar.html', plan=plan)

@app.route('/plan/<plan_id>/dashboard')
@login_required
def dashboard_page(plan_id):
    plan = StudyPlan.find_by_id(plan_id, current_user.id)
    if not plan:
        return redirect(url_for('index'))
    plan['id'] = str(plan['_id'])
    return render_template('dashboard.html', plan=plan)

# ── Dashboard Data ───────────────────────────────────────────

@app.route('/dashboard-data', methods=['GET'])
@login_required
def dashboard_data():
    plans = StudyPlan.find_by_user(current_user.id)
    
    all_days = []
    for p in plans:
        for w in p.get('weeks', []):
            all_days.extend(w.get('days', []))
    
    total = len(all_days)
    done = sum(1 for d in all_days if d.get('status') == 'completed')
    today = date.today().isoformat()
    
    plans_data = []
    today_day = None
    
    for p in plans:
        p_total = p_done = 0
        weeks_data = []
        
        for w in p.get('weeks', []):
            w_days = w.get('days', [])
            w_total = len(w_days)
            w_done = sum(1 for d in w_days if d.get('status') == 'completed')
            
            weeks_data.append({
                'week_number': w['week_number'],
                'title': w['title'],
                'total': w_total,
                'completed': w_done,
                'percent': round(w_done / w_total * 100) if w_total else 0,
                'days': w_days
            })
            
            p_total += w_total
            p_done += w_done
            
            for d in w_days:
                if d.get('date') == today and not today_day:
                    today_day = {**d, 'plan_title': p['title'], 'plan_id': str(p['_id'])}
        
        plans_data.append({
            'id': str(p['_id']),
            'title': p['title'],
            'subject': p['subject'],
            'description': p.get('description', ''),
            'created_at': p['created_at'].strftime('%b %d, %Y'),
            'total': p_total,
            'completed': p_done,
            'percent': round(p_done / p_total * 100, 1) if p_total else 0,
            'weeks': weeks_data
        })
    
    completed_dates = list({d.get('date') for d in all_days if d.get('status') == 'completed' and d.get('date')})
    
    activities = Activity.get_recent(current_user.id)
    activity_data = [{
        'message': a['message'],
        'plan': a['plan_title'],
        'time': _time_ago(a['created_at'])
    } for a in activities]
    
    return jsonify({
        'stats': {
            'plans': len(plans),
            'total_days': total,
            'completed': done,
            'percent': round(done / total * 100, 1) if total else 0
        },
        'plans': plans_data,
        'today_day': today_day,
        'completed_dates': completed_dates,
        'activities': activity_data
    })

# ── REST APIs ────────────────────────────────────────────────

@app.route('/plan', methods=['POST'])
@login_required
def create_plan():
    data = request.json
    plan_id = StudyPlan.create(
        title=data['title'],
        subject=data['subject'],
        description=data.get('description', ''),
        user_id=current_user.id
    )
    return jsonify({'id': plan_id, 'title': data['title']}), 201

@app.route('/parse-plan', methods=['POST'])
@login_required
def parse_plan():
    data = request.json
    plan_id = StudyPlan.create(
        title=data['title'],
        subject=data['subject'],
        description=data.get('description', ''),
        user_id=current_user.id
    )
    parse_plan_text(data['text'], plan_id, None, None, date.today())
    return jsonify({'id': plan_id, 'title': data['title']}), 201

@app.route('/plan/<plan_id>', methods=['DELETE'])
@login_required
def delete_plan(plan_id):
    StudyPlan.delete(plan_id, current_user.id)
    return jsonify({'message': 'Plan deleted'})

@app.route('/plans', methods=['GET'])
@login_required
def list_plans():
    plans = StudyPlan.find_by_user(current_user.id)
    return jsonify([{'id': str(p['_id']), 'title': p['title'], 'subject': p['subject']} for p in plans])

@app.route('/stats', methods=['GET'])
@login_required
def global_stats():
    plans = StudyPlan.find_by_user(current_user.id)
    all_days = []
    for p in plans:
        for w in p.get('weeks', []):
            all_days.extend(w.get('days', []))
    
    total = len(all_days)
    done = sum(1 for d in all_days if d.get('status') == 'completed')
    return jsonify({
        'plans': len(plans),
        'total_days': total,
        'completed': done,
        'percent': round(done / total * 100, 1) if total else 0
    })

@app.route('/weeks/<plan_id>', methods=['GET'])
@login_required
def list_weeks(plan_id):
    plan = StudyPlan.find_by_id(plan_id, current_user.id)
    if not plan:
        return jsonify({'error': 'Not found'}), 404
    weeks = plan.get('weeks', [])
    return jsonify([{'id': w['week_number'], 'week_number': w['week_number'], 'title': w['title']} for w in weeks])

@app.route('/days/<int:week_id>', methods=['GET'])
@login_required
def list_days(week_id):
    # MongoDB structure is different, return empty for now
    return jsonify([])

@app.route('/progress/<plan_id>', methods=['GET'])
@login_required
def get_progress(plan_id):
    try:
        print(f"Progress request for plan_id: {plan_id}")
        plan = StudyPlan.find_by_id(plan_id, current_user.id)
        if not plan:
            print(f"Plan not found: {plan_id}")
            return jsonify({'error': 'Not found'}), 404
        
        print(f"Plan found: {plan['title']}, weeks: {len(plan.get('weeks', []))}")
        
        total = done = 0
        weeks_data = []
        
        for w in plan.get('weeks', []):
            w_days = w.get('days', [])
            w_total = len(w_days)
            w_done = sum(1 for d in w_days if d.get('status') == 'completed')
            
            weeks_data.append({
                'week_id': w['week_number'],
                'week_number': w['week_number'],
                'title': w['title'],
                'total': w_total,
                'completed': w_done,
                'percent': round(w_done / w_total * 100) if w_total else 0,
                'days': w_days
            })
            
            total += w_total
            done += w_done
        
        result = {
            'plan_id': plan_id,
            'weeks': weeks_data,
            'total': total,
            'completed': done,
            'percent': round(done / total * 100) if total else 0
        }
        print(f"Returning progress: {total} total days, {done} completed")
        return jsonify(result)
    except Exception as e:
        print(f"Progress error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/analytics/<plan_id>', methods=['GET'])
@login_required
def get_analytics(plan_id):
    try:
        plan = StudyPlan.find_by_id(plan_id, current_user.id)
        if not plan:
            return jsonify({'error': 'Plan not found'}), 404
        
        # Simple analytics for MongoDB
        all_days = []
        for w in plan.get('weeks', []):
            all_days.extend(w.get('days', []))
        
        completed = [d for d in all_days if d.get('status') == 'completed']
        
        # Return basic structure even if no data
        return jsonify({
            'streaks': {
                'current': 0,
                'longest': 0,
                'missed': 0
            },
            'completion': {
                'total': len(all_days),
                'completed': len(completed),
                'pct': round(len(completed) / len(all_days) * 100) if all_days else 0
            },
            'health': {
                'score': 0,
                'label': 'No Data',
                'emoji': '📊'
            },
            'weekly_perf': [],
            'trend': [],
            'heatmap': {},
            'insights': ['Add weeks and days to your plan to see analytics.'] if not all_days else [],
            'day_table': []
        })
    except Exception as e:
        print(f"Analytics error: {e}")
        return jsonify({
            'error': str(e),
            'streaks': {'current': 0, 'longest': 0, 'missed': 0},
            'completion': {'total': 0, 'completed': 0, 'pct': 0}
        }), 500

@app.route('/week', methods=['POST'])
@login_required
def add_week():
    data = request.json
    plan_id = data.get('plan_id')
    title = data.get('title')
    
    plan = StudyPlan.find_by_id(plan_id, current_user.id)
    if not plan:
        return jsonify({'error': 'Unauthorized'}), 403
    
    week_number = len(plan.get('weeks', [])) + 1
    
    from models_mongo import Week
    Week.add_to_plan(plan_id, week_number, title)
    
    return jsonify({'id': week_number}), 201

@app.route('/day', methods=['POST'])
@login_required
def add_day():
    data = request.json
    # MongoDB implementation for adding days
    return jsonify({'id': 1}), 201

@app.route('/day/<plan_id>/<int:week_num>/<int:day_num>', methods=['PUT'])
@login_required
def update_day(plan_id, week_num, day_num):
    plan = StudyPlan.find_by_id(plan_id, current_user.id)
    if not plan:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.json
    new_status = data.get('status', 'pending')
    
    from models_mongo import Day
    Day.update_status(plan_id, week_num, day_num, new_status)
    
    if new_status == 'completed':
        Activity.create(
            message=f'Completed Day {day_num}',
            plan_title=plan['title'],
            user_id=current_user.id
        )
    
    return jsonify({'status': new_status})

# Legacy route for compatibility
@app.route('/day/<int:day_id>', methods=['PUT'])
@login_required
def update_day_legacy(day_id):
    # This is for backward compatibility with old frontend code
    # Extract plan_id, week_num, day_num from the request or session
    data = request.json
    return jsonify({'id': day_id, 'status': data.get('status', 'pending')})

# ── AI Chatbot ───────────────────────────────────────────────

@app.route('/chatbot', methods=['POST'])
@login_required
def chatbot():
    data = request.json or {}
    step = int(data.get('step', 0))
    message = data.get('message', '').strip()
    ctx = data.get('context', {})
    
    reply = ''
    next_step = step
    plan_text = None
    
    if step == 0:
        reply = 'Hi! I am your AI Study Plan Assistant 🤖\n\nWhat subject do you want to study?\n👉 e.g. Backend, Python, React'
        next_step = 1
    
    elif step == 1:
        if not message:
            reply = 'Please tell me the subject you want to study.'
            next_step = 1
        else:
            ctx['subject'] = message.title()
            reply = f'Great choice — **{ctx["subject"]}**! 🎯\n\nHow many days?\n👉 e.g. 7, 14, 30'
            next_step = 2
    
    elif step == 2:
        try:
            days = int(''.join(filter(str.isdigit, message)))
            if days < 1 or days > 365:
                raise ValueError
            ctx['days'] = days
            reply = f'Perfect — a **{days}-day** plan! 📅\n\nHow many hours per day?\n👉 e.g. 1, 2, 3'
            next_step = 3
        except:
            reply = 'Please enter a valid number of days (1–365)'
            next_step = 2
    
    elif step == 3:
        try:
            hours = float(''.join(c for c in message if c.isdigit() or c == '.'))
            if hours <= 0 or hours > 24:
                raise ValueError
            ctx['hours'] = hours
            
            plan_text = _generate_plan(ctx.get('subject', 'Backend'), ctx.get('days', 30), hours)
            reply = f'Here is your plan! 🚀\n\nReview it and click **"Use This Plan"** to save it!'
            next_step = 4
        except:
            reply = 'Please enter valid hours. e.g. 2 or 1.5'
            next_step = 3
    
    elif step == 4:
        reply = 'Plan already generated! Click "Use This Plan" to save it.'
        next_step = 4
    
    return jsonify({
        'reply': reply,
        'next_step': next_step,
        'context': ctx,
        'plan_text': plan_text
    })

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False, port=5000)
