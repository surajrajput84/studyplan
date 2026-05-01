from datetime import date, timedelta
import re

def parse_plan_text(text, plan_id, Week, Day, start_date):
    """Parse plan text and add weeks/days to MongoDB plan"""
    from models_mongo import plans_collection
    from bson import ObjectId
    
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    current_week = None
    current_date = start_date
    
    for line in lines:
        if line.startswith('Week'):
            match = re.search(r'Week\s+(\d+)', line)
            if match:
                week_num = int(match.group(1))
                week_title = line
                
                week_data = {
                    'week_number': week_num,
                    'title': week_title,
                    'days': []
                }
                
                plans_collection.update_one(
                    {'_id': ObjectId(plan_id)},
                    {'$push': {'weeks': week_data}}
                )
                current_week = week_num
        
        elif line.startswith('Day') and current_week:
            match = re.search(r'Day\s+(\d+)', line)
            if match:
                day_num = int(match.group(1))
                day_title = line
                
                day_data = {
                    'day_number': day_num,
                    'title': day_title,
                    'status': 'pending',
                    'date': current_date.isoformat(),
                    'completed_at': None
                }
                
                plans_collection.update_one(
                    {'_id': ObjectId(plan_id), 'weeks.week_number': current_week},
                    {'$push': {'weeks.$.days': day_data}}
                )
                
                current_date += timedelta(days=1)
