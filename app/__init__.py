from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_cors import CORS
from datetime import timedelta
import os
import logging
from logging.handlers import RotatingFileHandler

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

def create_app():
    app = Flask(__name__)

    # Configure logging
    if not app.debug:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/telemed.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Telemedicine startup')

    # Configure the Flask application
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-please-change')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
    app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=7)
    app.config['REMEMBER_COOKIE_SAMESITE'] = 'Lax'

    # Configure CORS to allow credentials
    CORS(app, supports_credentials=True, resources={
        "/api/*": {"origins": ["http://localhost:5000", "https://localhost:5000"]}
    })

    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    migrate.init_app(app, db)

    # Import and register blueprints
    from .auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')

    from .chat import bp as chat_bp
    app.register_blueprint(chat_bp, url_prefix='/api/chat')

    # Ensure all database tables exist
    with app.app_context():
        try:
            db.create_all()
            # Create initial admin user if not exists
            from .models import User
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                admin = User(
                    username='admin',
                    email='admin@example.com',
                    name='Admin User',
                    role='admin'
                )
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
                app.logger.info('Created admin user')

            app.logger.info('Database tables created successfully')
        except Exception as e:
            app.logger.error(f'Error creating database tables: {str(e)}')
            raise

    return app