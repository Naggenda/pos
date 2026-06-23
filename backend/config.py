import os
from datetime import timedelta

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_SORT_KEYS = False
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///pos_system.db')

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///pos_system.db')

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

# EFRIS Configuration
EFRIS_CONFIG = {
    'base_url': os.environ.get('EFRIS_BASE_URL', 'https://restapi.efris.go.ug/api'),
    'username': os.environ.get('EFRIS_USERNAME', ''),
    'password': os.environ.get('EFRIS_PASSWORD', ''),
    'tin': os.environ.get('EFRIS_TIN', ''),  # Tax Identification Number
    'device_serial': os.environ.get('EFRIS_DEVICE_SERIAL', ''),
}

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
