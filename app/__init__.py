from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_cors import CORS
from flask_babel import Babel
import os

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
babel = Babel()

def create_app():
    app = Flask(__name__)

    # Configure the Flask application
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Configure CORS to allow credentials
    CORS(app, supports_credentials=True, resources={
        "/api/*": {"origins": ["http://localhost:5000", "https://localhost:5000"]}
    })

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    babel.init_app(app)

    # Import and register blueprints
    from app.auth import bp as auth_bp
    from app.api import bp as api_bp
    from app.chat import bp as chat_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(chat_bp, url_prefix='/api/chat')

    # Ensure the instance and migrations directories exist
    with app.app_context():
        if not os.path.exists('migrations'):
            from flask_migrate import init as init_migrations
            init_migrations('migrations')
            from flask_migrate import migrate as run_migrations
            run_migrations()
            from flask_migrate import upgrade as upgrade_migrations
            upgrade_migrations()

    return app