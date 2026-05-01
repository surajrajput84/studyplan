from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, StudyPlan, Week, Day, Activity
from parser import parse_plan_text
from datetime import datetime, date, timedelta
from google import genai
from google.genai import types
import os
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()

# ── Gemini AI Setup ──────────────────────────────────────────
GEMINI_API_KEY = 'AIzaSyDdQ4usMeVV04WGDCWzuxLGFTavY1a03Ic'
_gemini_client = genai.Client(api_key=GEMINI_API_KEY)


# ── Gemini Plan Generator ────────────────────────────────────

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
    """Keep only lines starting with Week or Day — strips any LLM preamble/suffix."""
    lines = text.splitlines()
    cleaned = [l.strip() for l in lines
               if l.strip().startswith('Week') or l.strip().startswith('Day')]
    return '\n'.join(cleaned)


def _generate_plan(subject: str, days: int, hours: float) -> str:
    prompt = _build_prompt(subject, days, hours)
    # Try models in order — fall back if one is quota-exhausted or unavailable
    models_to_try = [
        'gemini-2.0-flash-lite',
        'gemini-2.0-flash',
        'gemini-2.5-flash',
        'gemini-flash-latest',
    ]
    last_error = None
    for model in models_to_try:
        try:
            response = _gemini_client.models.generate_content(
                model=model,
                contents=prompt
            )
            return _clean_plan(response.text.strip())
        except Exception as e:
            last_error = e
            continue
    raise last_error


# ── Helpers ──────────────────────────────────────────────────

def _plan_progress(plan_id):
    weeks = Week.query.filter_by(plan_id=plan_id).order_by(Week.week_number).all()
    total = done = 0
    weeks_data = []
    for week in weeks:
        days = Day.query.filter_by(week_id=week.id).order_by(Day.day_number).all()
        w_total = len(days)
        w_done  = sum(1 for d in days if d.status == 'completed')
        weeks_data.append({
            'week_id': week.id, 'title': week.title,
            'total': w_total, 'completed': w_done,
            'percent': round(w_done / w_total * 100) if w_total else 0,
            'days': [{
                'day_id': d.id, 'day_number': d.day_number,
                'title': d.title, 'status': d.status,
                'date': d.date.isoformat() if d.date else None,
                'completed_at': d.completed_at.isoformat() if d.completed_at else None
            } for d in days]
        })
        total += w_total
        done  += w_done
    return weeks_data, total, done


def _time_ago(dt):
    diff = datetime.utcnow() - dt
    s = int(diff.total_seconds())
    if s < 60:    return 'Just now'
    if s < 3600:  return f'{s // 60} min ago'
    if s < 86400: return f'{s // 3600} hr ago'
    return f'{s // 86400}d ago'


# ── Authentication Routes ──────────────────────────────────

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
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
        
        if User.query.filter_by(email=email).first():
            return render_template('signup.html', error='Email already registered')
        if User.query.filter_by(username=username).first():
            return render_template('signup.html', error='Username already taken')
        
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
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
    plans = StudyPlan.query.filter_by(user_id=current_user.id).order_by(StudyPlan.created_at.desc()).all()
    by_subject = {}
    for p in plans:
        by_subject.setdefault(p.subject, []).append(p)
    return render_template('index.html', by_subject=by_subject, username=current_user.username)


@app.route('/create')
@login_required
def create_page():
    return render_template('create_plan.html')


@app.route('/plan/<int:plan_id>/weeks')
@login_required
def weeks_page(plan_id):
    plan = StudyPlan.query.filter_by(id=plan_id, user_id=current_user.id).first_or_404()
    weeks = Week.query.filter_by(plan_id=plan_id).order_by(Week.week_number).all()
    return render_template('weeks.html', plan=plan, weeks=weeks)


@app.route('/week/<int:week_id>/days')
@login_required
def days_page(week_id):
    week = Week.query.get_or_404(week_id)
    if week.plan.user_id != current_user.id:
        return redirect(url_for('index'))
    days = Day.query.filter_by(week_id=week_id).order_by(Day.day_number).all()
    return render_template('days.html', week=week, days=days)


@app.route('/plan/<int:plan_id>/dashboard')
@login_required
def dashboard_page(plan_id):
    plan = StudyPlan.query.filter_by(id=plan_id, user_id=current_user.id).first_or_404()
    return render_template('dashboard.html', plan=plan)


@app.route('/plan/<int:plan_id>/calendar')
@login_required
def calendar_page(plan_id):
    plan = StudyPlan.query.filter_by(id=plan_id, user_id=current_user.id).first_or_404()
    return render_template('calendar.html', plan=plan)


# ── Dashboard Data ───────────────────────────────────────────

@app.route('/dashboard-data', methods=['GET'])
@login_required
def dashboard_data():
    plans = StudyPlan.query.filter_by(user_id=current_user.id).order_by(StudyPlan.created_at.desc()).all()
    all_days = Day.query.join(Week).join(StudyPlan).filter(StudyPlan.user_id == current_user.id).all()
    total    = len(all_days)
    done     = sum(1 for d in all_days if d.status == 'completed')
    today    = date.today()

    plans_data = []
    today_day  = None

    for p in plans:
        weeks_data, p_total, p_done = _plan_progress(p.id)
        pct = round(p_done / p_total * 100, 1) if p_total else 0

        for w in weeks_data:
            for d in w['days']:
                if d['date'] == today.isoformat() and not today_day:
                    today_day = {**d, 'plan_title': p.title, 'plan_id': p.id}

        plans_data.append({
            'id': p.id, 'title': p.title, 'subject': p.subject,
            'description': p.description,
            'created_at': p.created_at.strftime('%b %d, %Y'),
            'total': p_total, 'completed': p_done, 'percent': pct,
            'weeks': weeks_data
        })

    completed_dates = list({
        d.date.isoformat() for d in all_days
        if d.status == 'completed' and d.date
    })

    activities = Activity.query.order_by(Activity.created_at.desc()).limit(5).all()
    activity_data = [{
        'message': a.message,
        'plan': a.plan_title,
        'time': _time_ago(a.created_at)
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
    plan = StudyPlan(
        title=data['title'], subject=data['subject'],
        description=data.get('description', ''),
        user_id=current_user.id
    )
    db.session.add(plan)
    db.session.commit()
    return jsonify({'id': plan.id, 'title': plan.title}), 201


@app.route('/parse-plan', methods=['POST'])
@login_required
def parse_plan():
    data = request.json
    plan = StudyPlan(
        title=data['title'], subject=data['subject'],
        description=data.get('description', ''),
        user_id=current_user.id
    )
    db.session.add(plan)
    db.session.flush()
    start = date.today()
    parse_plan_text(data['text'], plan.id, db, Week, Day, start)
    return jsonify({'id': plan.id, 'title': plan.title}), 201


@app.route('/plan/<int:plan_id>', methods=['DELETE'])
@login_required
def delete_plan(plan_id):
    plan = StudyPlan.query.filter_by(id=plan_id, user_id=current_user.id).first_or_404()
    db.session.delete(plan)
    db.session.commit()
    return jsonify({'message': 'Plan deleted'})


@app.route('/plans', methods=['GET'])
@login_required
def list_plans():
    plans = StudyPlan.query.filter_by(user_id=current_user.id).all()
    return jsonify([{'id': p.id, 'title': p.title, 'subject': p.subject} for p in plans])


@app.route('/stats', methods=['GET'])
@login_required
def global_stats():
    all_days = Day.query.join(Week).join(StudyPlan).filter(StudyPlan.user_id == current_user.id).all()
    total = len(all_days)
    done  = sum(1 for d in all_days if d.status == 'completed')
    return jsonify({
        'plans': StudyPlan.query.filter_by(user_id=current_user.id).count(),
        'total_days': total, 'completed': done,
        'percent': round(done / total * 100, 1) if total else 0
    })


@app.route('/weeks/<int:plan_id>', methods=['GET'])
@login_required
def list_weeks(plan_id):
    plan = StudyPlan.query.filter_by(id=plan_id, user_id=current_user.id).first_or_404()
    weeks = Week.query.filter_by(plan_id=plan_id).order_by(Week.week_number).all()
    return jsonify([{'id': w.id, 'week_number': w.week_number, 'title': w.title} for w in weeks])


@app.route('/days/<int:week_id>', methods=['GET'])
@login_required
def list_days(week_id):
    week = Week.query.get_or_404(week_id)
    if week.plan.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    days = Day.query.filter_by(week_id=week_id).order_by(Day.day_number).all()
    return jsonify([{
        'id': d.id, 'day_number': d.day_number, 'title': d.title,
        'status': d.status, 'date': d.date.isoformat() if d.date else None
    } for d in days])


@app.route('/day/<int:day_id>', methods=['PUT'])
@login_required
def update_day(day_id):
    day  = Day.query.get_or_404(day_id)
    if day.week.plan.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    data = request.json
    new_status = data.get('status', day.status)

    if new_status == 'completed' and day.status != 'completed':
        day.completed_at = datetime.utcnow()
        plan = day.week.plan
        act  = Activity(
            message=f'Completed Day {day.day_number} \u2013 {day.title}',
            plan_title=plan.title
        )
        db.session.add(act)
    elif new_status == 'pending':
        day.completed_at = None

    day.status = new_status
    db.session.commit()
    return jsonify({'id': day.id, 'status': day.status})


@app.route('/progress/<int:plan_id>', methods=['GET'])
@login_required
def get_progress(plan_id):
    plan = StudyPlan.query.filter_by(id=plan_id, user_id=current_user.id).first_or_404()
    weeks_data, total, done = _plan_progress(plan_id)
    return jsonify({
        'plan_id': plan_id, 'weeks': weeks_data,
        'total': total, 'completed': done,
        'percent': round(done / total * 100) if total else 0
    })


@app.route('/analytics/<int:plan_id>', methods=['GET'])
@login_required
def get_analytics(plan_id):
    """Full plan health analytics — all metrics computed server-side."""
    plan = StudyPlan.query.filter_by(id=plan_id, user_id=current_user.id).first_or_404()
    today = date.today()

    # Collect all days flat across all weeks
    weeks = Week.query.filter_by(plan_id=plan_id).order_by(Week.week_number).all()
    all_days = []
    for week in weeks:
        days = Day.query.filter_by(week_id=week.id).order_by(Day.day_number).all()
        for d in days:
            all_days.append({
                'day_id':       d.id,
                'day_number':   d.day_number,
                'title':        d.title,
                'status':       d.status,
                'date':         d.date,
                'completed_at': d.completed_at,
                'week_title':   week.title,
                'week_number':  week.week_number,
            })

    total = len(all_days)
    if total == 0:
        return jsonify({'error': 'No days found'}), 404

    completed   = [d for d in all_days if d['status'] == 'completed']
    pending     = [d for d in all_days if d['status'] == 'pending']
    overdue     = [d for d in pending if d['date'] and d['date'] < today]
    future_days = [d for d in pending if d['date'] and d['date'] >= today]

    # ── On-time vs Late ──────────────────────────────────────
    on_time_list, late_list = [], []
    delays = []
    for d in completed:
        if d['date'] and d['completed_at']:
            comp_date = d['completed_at'].date()
            delay     = (comp_date - d['date']).days
            delays.append(delay)
            if delay <= 0:
                on_time_list.append(d)
            else:
                late_list.append(d)
        else:
            on_time_list.append(d)   # no date info → assume on time

    avg_delay    = round(sum(delays) / len(delays), 1) if delays else 0
    on_time_pct  = round(len(on_time_list) / len(completed) * 100) if completed else 0

    # ── Streaks ──────────────────────────────────────────────
    # Sort completed days by completed_at date
    comp_dates = sorted(set(
        d['completed_at'].date() for d in completed if d['completed_at']
    ))
    current_streak = longest_streak = temp = 0
    for i, cd in enumerate(comp_dates):
        if i == 0 or (cd - comp_dates[i-1]).days == 1:
            temp += 1
        else:
            temp = 1
        longest_streak = max(longest_streak, temp)
    # Current streak: count backwards from today
    current_streak = 0
    check = today
    while check in comp_dates or (check - timedelta(days=1)) in comp_dates:
        if check in comp_dates:
            current_streak += 1
            check -= timedelta(days=1)
        else:
            break

    missed = len(overdue)

    # ── Plan Health Score ────────────────────────────────────
    comp_rate    = len(completed) / total                                    # 0-1
    consist_rate = len(on_time_list) / len(completed) if completed else 0   # 0-1
    delay_score  = max(0, 1 - avg_delay / 7)                                # 0-1
    streak_score = min(current_streak / 7, 1)                               # 0-1

    health = round(
        consist_rate * 40 +
        delay_score  * 20 +
        comp_rate    * 30 +
        streak_score * 10
    )

    if health >= 85:   health_label, health_emoji = 'Excellent',       '🚀'
    elif health >= 60: health_label, health_emoji = 'On Track',        '✅'
    elif health >= 40: health_label, health_emoji = 'Falling Behind',  '⚠️'
    else:              health_label, health_emoji = 'Needs Attention', '❌'

    # ── Weekly Performance ───────────────────────────────────
    weekly_perf = []
    for week in weeks:
        wdays = [d for d in all_days if d['week_number'] == week.week_number]
        w_total    = len(wdays)
        w_done     = [d for d in wdays if d['status'] == 'completed']
        w_on_time  = sum(1 for d in w_done
                         if d['date'] and d['completed_at']
                         and (d['completed_at'].date() - d['date']).days <= 0)
        w_late     = len(w_done) - w_on_time
        w_overdue  = sum(1 for d in wdays
                         if d['status'] == 'pending' and d['date'] and d['date'] < today)
        weekly_perf.append({
            'week':     week.title,
            'total':    w_total,
            'done':     len(w_done),
            'on_time':  w_on_time,
            'late':     w_late,
            'overdue':  w_overdue,
            'pct':      round(len(w_done) / w_total * 100) if w_total else 0,
        })

    # ── Cumulative trend ─────────────────────────────────────
    trend = []
    comp_so_far = 0
    for d in all_days:
        if d['status'] == 'completed':
            comp_so_far += 1
        trend.append({
            'day':   d['day_number'],
            'pct':   round(comp_so_far / total * 100, 1),
            'title': d['title'][:30],
        })

    # ── Calendar heatmap ─────────────────────────────────────
    heatmap = {}
    for d in all_days:
        if not d['date']:
            continue
        ds = d['date'].isoformat()
        if d['status'] == 'completed' and d['completed_at']:
            delay = (d['completed_at'].date() - d['date']).days
            heatmap[ds] = 'on-time' if delay <= 0 else 'late'
        elif d['status'] == 'pending' and d['date'] < today:
            heatmap[ds] = 'missed'
        elif d['status'] == 'pending':
            heatmap[ds] = 'future'

    # ── Smart Insights ───────────────────────────────────────
    insights = []
    if avg_delay > 1:
        insights.append(f'You complete tasks on average {avg_delay} days late. Try starting earlier each day.')
    elif avg_delay > 0:
        insights.append(f'You complete tasks about {avg_delay} day late on average. Small improvement needed.')
    else:
        insights.append('You are completing tasks on time. Excellent discipline!')

    if current_streak >= 3:
        insights.append(f'You are on a {current_streak}-day streak. Keep the momentum going!')
    elif current_streak == 0 and len(completed) > 0:
        insights.append('Your streak has been broken. Try to complete at least one task today to restart it.')

    if missed > 0:
        insights.append(f'You have {missed} overdue day(s). Consider a catch-up session this weekend.')

    if on_time_pct >= 80:
        insights.append('You complete most tasks on time. Your consistency is a strong habit.')
    elif on_time_pct < 50 and len(completed) > 2:
        insights.append('More than half your completions are late. Try studying at a fixed time each day.')

    if longest_streak >= 7:
        insights.append(f'Your longest streak is {longest_streak} days — you have proven you can be consistent!')

    comp_rate_pct = round(comp_rate * 100)
    if comp_rate_pct < 30 and total > 7:
        insights.append('Overall completion is low. Break your plan into smaller daily goals to build momentum.')

    # ── Detailed day table ───────────────────────────────────
    day_table = []
    for d in all_days:
        delay_days = None
        if d['status'] == 'completed' and d['date'] and d['completed_at']:
            delay_days = (d['completed_at'].date() - d['date']).days
        day_table.append({
            'day_number':   d['day_number'],
            'title':        d['title'],
            'planned_date': d['date'].strftime('%b %d') if d['date'] else '—',
            'completed_at': d['completed_at'].strftime('%b %d') if d['completed_at'] else '—',
            'status':       d['status'],
            'delay':        delay_days,
        })

    return jsonify({
        'health':       {'score': health, 'label': health_label, 'emoji': health_emoji},
        'streaks':      {'current': current_streak, 'longest': longest_streak, 'missed': missed},
        'completion':   {'total': total, 'completed': len(completed), 'on_time': len(on_time_list),
                         'late': len(late_list), 'overdue': missed, 'pct': round(comp_rate * 100)},
        'avg_delay':    avg_delay,
        'on_time_pct':  on_time_pct,
        'weekly_perf':  weekly_perf,
        'trend':        trend,
        'heatmap':      heatmap,
        'insights':     insights,
        'day_table':    day_table,
    })


# ── Manual Entry APIs ────────────────────────────────────────

@app.route('/week', methods=['POST'])
@login_required
def add_week():
    data  = request.json
    plan = StudyPlan.query.filter_by(id=data['plan_id'], user_id=current_user.id).first_or_404()
    count = Week.query.filter_by(plan_id=data['plan_id']).count()
    week  = Week(week_number=count + 1, title=data['title'], plan_id=data['plan_id'])
    db.session.add(week)
    db.session.commit()
    return jsonify({'id': week.id}), 201


@app.route('/day', methods=['POST'])
@login_required
def add_day():
    data  = request.json
    week = Week.query.get_or_404(data['week_id'])
    if week.plan.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    count = Day.query.filter_by(week_id=data['week_id']).count()
    d     = date.fromisoformat(data['date']) if data.get('date') else None
    day   = Day(day_number=count + 1, title=data['title'], week_id=data['week_id'], date=d)
    db.session.add(day)
    db.session.commit()
    return jsonify({'id': day.id}), 201


# ── AI Chatbot (Gemini) ──────────────────────────────────────

@app.route('/chatbot', methods=['POST'])
@login_required
def chatbot():
    """
    Stateless 4-step chatbot powered by Gemini AI.
    Steps: 0=greet  1=subject  2=days  3=hours+generate  4=done
    """
    data    = request.json or {}
    step    = int(data.get('step', 0))
    message = data.get('message', '').strip()
    ctx     = data.get('context', {})

    reply     = ''
    next_step = step
    plan_text = None

    if step == 0:
        reply = (
            'Hi! I am your AI Study Plan Assistant \U0001f916\n\n'
            'I use Gemini AI to generate a personalised day-by-day study plan for you.\n\n'
            'What subject do you want to study?\n'
            '\U0001f449 e.g. Backend, Cybersecurity, Kotlin Android, System Design, Blockchain'
        )
        next_step = 1

    elif step == 1:
        if not message:
            reply     = 'Please tell me the subject you want to study.'
            next_step = 1
        else:
            ctx['subject'] = message.title()
            reply = (
                f'Great choice \u2014 **{ctx["subject"]}**! \U0001f3af\n\n'
                'How many days do you want the plan to be?\n'
                '\U0001f449 e.g. 7, 14, 21, 30, 60, 90'
            )
            next_step = 2

    elif step == 2:
        try:
            days = int(''.join(filter(str.isdigit, message)))
            if days < 1 or days > 365:
                raise ValueError
            ctx['days'] = days
            reply = (
                f'Perfect \u2014 a **{days}-day** plan! \U0001f4c5\n\n'
                'How many hours per day can you study?\n'
                '\U0001f449 e.g. 1, 1.5, 2, 3'
            )
            next_step = 3
        except (ValueError, TypeError):
            reply     = 'Please enter a valid number of days (1\u2013365). e.g. 30'
            next_step = 2

    elif step == 3:
        try:
            hours = float(''.join(c for c in message if c.isdigit() or c == '.'))
            if hours <= 0 or hours > 24:
                raise ValueError
            ctx['hours'] = hours
            subject = ctx.get('subject', 'Backend')
            days    = ctx.get('days', 30)

            # Gemini generates the plan
            plan_text = _generate_plan(subject, days, hours)

            reply = (
                f'Here is your **{days}-day {subject}** plan at **{hours}h/day** \U0001f680\n\n'
                'Gemini AI has generated it below.\n'
                'Review it and click **"Use This Plan"** to save it!'
            )
            next_step = 4

        except (ValueError, TypeError):
            reply     = 'Please enter valid hours. e.g. 2 or 1.5'
            next_step = 3
        except Exception as e:
            reply = (
                f'Gemini API error: {str(e)}\n\n'
                'Make sure your API key is set correctly in app.py (GEMINI_API_KEY).'
            )
            next_step = 3

    elif step == 4:
        reply     = 'Plan already generated! Click "Use This Plan" to save it, or click Reset to start over.'
        next_step = 4

    return jsonify({
        'reply':     reply,
        'next_step': next_step,
        'context':   ctx,
        'plan_text': plan_text,
    })


if __name__ == '__main__':
    app.run(debug=True)
