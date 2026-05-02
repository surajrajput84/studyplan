from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId
import bcrypt
import os
import certifi

# MongoDB connection
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')

_client = None
_db = None
_collections_cache = {}

# Lazy connection - only connect when needed
def get_db():
    global _client, _db
    if _db is None:
        # Check if using MongoDB Atlas (cloud) or local
        is_atlas = 'mongodb+srv://' in MONGO_URI or 'mongodb.net' in MONGO_URI
        
        if is_atlas:
            # Atlas requires SSL/TLS
            _client = MongoClient(
                MONGO_URI,
                serverSelectionTimeoutMS=5000,
                tlsCAFile=certifi.where(),
                tls=True,
                tlsAllowInvalidCertificates=False
            )
        else:
            # Local MongoDB - no SSL
            _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        
        _db = _client['study_planner']
    return _db

# Get collection with lazy initialization
def get_collection(name):
    if name not in _collections_cache:
        db = get_db()
        _collections_cache[name] = db[name]
        
        # Create indexes on first access
        if name == 'users':
            try:
                _collections_cache[name].create_index('email', unique=True, background=True)
                _collections_cache[name].create_index('username', unique=True, background=True)
            except:
                pass
        elif name == 'plans':
            try:
                _collections_cache[name].create_index('user_id', background=True)
            except:
                pass
    
    return _collections_cache[name]

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
        users_coll = get_collection('users')
        if self.id:
            users_coll.update_one({'_id': ObjectId(self.id)}, {'$set': user_data})
        else:
            result = users_coll.insert_one(user_data)
            self.id = str(result.inserted_id)
        return self
    
    @staticmethod
    def find_by_email(email):
        users_coll = get_collection('users')
        user_data = users_coll.find_one({'email': email})
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
        users_coll = get_collection('users')
        user_data = users_coll.find_one({'username': username})
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
            users_coll = get_collection('users')
            user_data = users_coll.find_one({'_id': ObjectId(user_id)})
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
        plans_coll = get_collection('plans')
        plan_data = {
            'title': title,
            'subject': subject,
            'description': description,
            'user_id': user_id,
            'created_at': datetime.utcnow(),
            'weeks': []
        }
        result = plans_coll.insert_one(plan_data)
        return str(result.inserted_id)
    
    @staticmethod
    def find_by_id(plan_id, user_id=None):
        try:
            plans_coll = get_collection('plans')
            query = {'_id': ObjectId(plan_id)}
            if user_id:
                query['user_id'] = user_id
            return plans_coll.find_one(query)
        except:
            return None
    
    @staticmethod
    def find_by_user(user_id):
        plans_coll = get_collection('plans')
        return list(plans_coll.find({'user_id': user_id}).sort('created_at', -1))
    
    @staticmethod
    def delete(plan_id, user_id):
        plans_coll = get_collection('plans')
        plans_coll.delete_one({'_id': ObjectId(plan_id), 'user_id': user_id})
    
    @staticmethod
    def count_by_user(user_id):
        plans_coll = get_collection('plans')
        return plans_coll.count_documents({'user_id': user_id})

class Week:
    @staticmethod
    def add_to_plan(plan_id, week_number, title):
        plans_coll = get_collection('plans')
        week_data = {
            'week_number': week_number,
            'title': title,
            'days': []
        }
        plans_coll.update_one(
            {'_id': ObjectId(plan_id)},
            {'$push': {'weeks': week_data}}
        )
        return week_number

class Day:
    @staticmethod
    def add_to_week(plan_id, week_number, day_data):
        plans_coll = get_collection('plans')
        plans_coll.update_one(
            {'_id': ObjectId(plan_id), 'weeks.week_number': week_number},
            {'$push': {'weeks.$.days': day_data}}
        )
    
    @staticmethod
    def update_status(plan_id, week_number, day_number, status):
        plans_coll = get_collection('plans')
        update_data = {'weeks.$[week].days.$[day].status': status}
        if status == 'completed':
            update_data['weeks.$[week].days.$[day].completed_at'] = datetime.utcnow()
        else:
            update_data['weeks.$[week].days.$[day].completed_at'] = None
        
        plans_coll.update_one(
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
        activities_coll = get_collection('activities')
        activity_data = {
            'message': message,
            'plan_title': plan_title,
            'user_id': user_id,
            'created_at': datetime.utcnow()
        }
        activities_coll.insert_one(activity_data)
    
    @staticmethod
    def get_recent(user_id, limit=5):
        activities_coll = get_collection('activities')
        return list(activities_coll.find({'user_id': user_id}).sort('created_at', -1).limit(limit))
