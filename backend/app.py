import os
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from config import config
from models import db
from routes import api
from auth_routes import auth_api

# Load environment variables
load_dotenv()

def create_app(config_name=None):
    """Application factory"""
    
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config.get(config_name, config['default']))
    
    # Initialize extensions
    db.init_app(app)
    CORS(app)
    
    # Register blueprints
    app.register_blueprint(auth_api)
    app.register_blueprint(api)
    
    # Create database tables
    with app.app_context():
        db.create_all()
        # Create default admin user if none exists
        from models import User
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@pos.local',
                full_name='Administrator',
                role='ADMIN'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("Default admin user created: admin/admin123")
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Resource not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({'error': 'Bad request'}), 400
    
    return app

if __name__ == '__main__':
    app = create_app()
    debug = os.environ.get('FLASK_DEBUG', True)
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=debug, host='0.0.0.0', port=port)
