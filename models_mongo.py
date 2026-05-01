from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId
import bcrypt
import os
import certifi

# MongoDB connection
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')

# Lazy connection - only connect when needed
def get_db():
    client = MongoClient(
        MONGO_URI,
        serverSelectionTimeoutMS=5000,
        tlsCAFile=certifi.where(),
        tls=True,
        tlsAllowInvalidCertificates=False
    )
    return client['study_planner']

# Initialize collections lazily
def get_collections():
    db = get_db()
    users_collection = db['users']
    plans_collection = db['plans']
    activities_collection = db['activities']
    
    # Create indexes only if not exists
    try:
        users_collection.create_index('email', unique=True, background=True)
        users_collection.create_index('username', unique=True, background=True)
        plans_collection.create_index('user_id', background=True)
    except:
        pass  # Indexes might already exist
    
    return users_collection, plans_collection, activities_collection

# Get collections
users_collection, plans_collection, activities_collection = get_collections()

class User:
    def __init__(self, username, email, password=None, _id=None, created_at=None):
        self.id = str(_id) if _id else None
        self.username = username
        self.email = email
        self.password = password
        self.created_at = created_at or datetime.utcnow()
    
    def set_password(self, password):
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))
    
    def save(self):
        user_data = {
            'username': self.username,
            'email': self.email,
            'password': self.password,
            'created_at': self.created_at
        }
        if self.id:
            users_collection.update_one({'_id': ObjectId(self.id)}, {'$set': user_data})
        else:
            result = users_collection.insert_one(user_data)
            self.id = str(result.inserted_id)
        return self
    
    @staticmethod
    def find_by_email(email):
        user_data = users_collection.find_one({'email': email})
        if user_data:
            return User(
                username=user_data['username'],
                email=user_data['email'],
                password=user_data['password'],
                _id=user_data['_id'],
                created_at=user_data.get('created_at')
            )
        return None
    
    @staticmethod
    def find_by_username(username):
        user_data = users_collection.find_one({'username': username})
        if user_data:
            return User(
                username=user_data['username'],
                email=user_data['email'],
                password=user_data['password'],
                _id=user_data['_id'],
                created_at=user_data.get('created_at')
            )
        return None
    
    @staticmethod
    def find_by_id(user_id):
        try:
            user_data = users_collection.find_one({'_id': ObjectId(user_id)})
            if user_data:
                return User(
                    username=user_data['username'],
                    email=user_data['email'],
                    password=user_data['password'],
                    _id=user_data['_id'],
                    created_at=user_data.get('created_at')
                )
        except:
            pass
        return None
    
    def get_id(self):
        return self.id
    
    @property
    def is_authenticated(self):
        return True
    
    @property
    def is_active(self):
        return True
    
    @property
    def is_anonymous(self):
        return False

class StudyPlan:
    @staticmethod
    def create(title, subject, description, user_id):
        plan_data = {
            'title': title,
            'subject': subject,
            'description': description,
            'user_id': user_id,
            'created_at': datetime.utcnow(),
            'weeks': []
        }
        result = plans_collection.insert_one(plan_data)
        return str(result.inserted_id)
    
    @staticmethod
    def find_by_id(plan_id, user_id=None):
        try:
            query = {'_id': ObjectId(plan_id)}
            if user_id:
                query['user_id'] = user_id
            return plans_collection.find_one(query)
        except:
            return None
    
    @staticmethod
    def find_by_user(user_id):
        return list(plans_collection.find({'user_id': user_id}).sort('created_at', -1))
    
    @staticmethod
    def delete(plan_id, user_id):
        plans_collection.delete_one({'_id': ObjectId(plan_id), 'user_id': user_id})
    
    @staticmethod
    def count_by_user(user_id):
        return plans_collection.count_documents({'user_id': user_id})

class Week:
    @staticmethod
    def add_to_plan(plan_id, week_number, title):
        week_data = {
            'week_number': week_number,
            'title': title,
            'days': []
        }
        plans_collection.update_one(
            {'_id': ObjectId(plan_id)},
            {'$push': {'weeks': week_data}}
        )
        return week_number

class Day:
    @staticmethod
    def add_to_week(plan_id, week_number, day_data):
        plans_collection.update_one(
            {'_id': ObjectId(plan_id), 'weeks.week_number': week_number},
            {'$push': {'weeks.$.days': day_data}}
        )
    
    @staticmethod
    def update_status(plan_id, week_number, day_number, status):
        update_data = {'weeks.$[week].days.$[day].status': status}
        if status == 'completed':
            update_data['weeks.$[week].days.$[day].completed_at'] = datetime.utcnow()
        else:
            update_data['weeks.$[week].days.$[day].completed_at'] = None
        
        plans_collection.update_one(
            {'_id': ObjectId(plan_id)},
            {'$set': update_data},
            array_filters=[
                {'week.week_number': week_number},
                {'day.day_number': day_number}
            ]
        )

class Activity:
    @staticmethod
    def create(message, plan_title, user_id):
        activity_data = {
            'message': message,
            'plan_title': plan_title,
            'user_id': user_id,
            'created_at': datetime.utcnow()
        }
        activities_collection.insert_one(activity_data)
    
    @staticmethod
    def get_recent(user_id, limit=5):
        return list(activities_collection.find({'user_id': user_id}).sort('created_at', -1).limit(limit))
