import re
from datetime import timedelta

def parse_plan_text(text, plan_id, db, Week, Day, start_date=None):
    from datetime import date as date_type
    current_week = None
    week_count   = 0
    day_count    = 0          # global day counter for date offset

    for raw_line in text.strip().splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if re.match(r'^week\s+\d+', line, re.IGNORECASE):
            week_count += 1
            current_week = Week(week_number=week_count, title=line, plan_id=plan_id)
            db.session.add(current_week)
            db.session.flush()

        else:
            if not current_week:
                week_count   += 1
                current_week  = Week(week_number=week_count, title='Week 1', plan_id=plan_id)
                db.session.add(current_week)
                db.session.flush()

            # local day number within week
            local_count = Day.query.filter_by(week_id=current_week.id).count()
            assigned_date = (start_date + timedelta(days=day_count)) if start_date else None
            day = Day(
                day_number=local_count + 1,
                title=line,
                week_id=current_week.id,
                date=assigned_date
            )
            db.session.add(day)
            day_count += 1

    db.session.commit()
