from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_cors import CORS
from datetime import timedelta
import os
import logging
from logging.handlers import RotatingFileHandler
from sqlalchemy import event, DDL

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
    app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=7)
    app.config['REMEMBER_COOKIE_SAMESITE'] = 'Lax'

    # Configure CORS to allow credentials
    CORS(app, resources={
        "/api/*": {"origins": ["http://localhost:5000"], "supports_credentials": True}
    })

    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    migrate.init_app(app, db, compare_type=True)

    # Import and register blueprints
    from .auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')

    # Initialize database
    with app.app_context():
        try:
            # Drop schema and recreate it to ensure a clean slate
            db.session.execute('DROP SCHEMA public CASCADE')
            db.session.execute('CREATE SCHEMA public')
            db.session.commit()

            # Create all tables fresh
            db.create_all()
            app.logger.info('Database tables created successfully')
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Error managing database tables: {str(e)}')
            raise

    return app