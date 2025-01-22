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

    # Initialize CORS
    CORS(app, supports_credentials=True)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    babel.init_app(app)

    # Register blueprints
    from app.auth import auth_bp
    from app.api import api_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(api_bp, url_prefix='/api')

    # Ensure the migrations directory exists and initialize if needed
    with app.app_context():
        if not os.path.exists('migrations'):
            from flask_migrate import init as init_migrations
            init_migrations('migrations')
            from flask_migrate import migrate as run_migrations
            run_migrations()
            from flask_migrate import upgrade as upgrade_migrations
            upgrade_migrations()

    return app