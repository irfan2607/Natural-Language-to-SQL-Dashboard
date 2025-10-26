import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    DATABASE_PATH = os.environ.get('DATABASE_PATH') or 'database/business.db'
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    
class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}