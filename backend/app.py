import os
import sys

# Ensure project root is in sys.path for direct script execution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
from backend.config import config_by_name
from backend.database.db import close_db, init_db_schema

def create_app(config_name=None):
    """Application factory for PBRMS backend."""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')

    app = Flask(
        __name__,
        static_folder=os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend')),
        static_url_path=''
    )
    app.config.from_object(config_by_name.get(config_name, config_by_name['default']))

    # Enable Cross-Origin Resource Sharing
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Teardown database connection
    app.teardown_appcontext(close_db)

    # Register Blueprints
    from backend.routes.auth_routes import auth_bp
    from backend.routes.station_routes import station_bp
    from backend.routes.bicycle_routes import bicycle_bp
    from backend.routes.rental_routes import rental_bp
    from backend.routes.payment_routes import payment_bp
    from backend.routes.admin_routes import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(station_bp)
    app.register_blueprint(bicycle_bp)
    app.register_blueprint(rental_bp)
    app.register_blueprint(payment_bp)
    app.register_blueprint(admin_bp)

    # Frontend Static Serving Routes
    @app.route('/')
    def index():
        return send_from_directory(app.static_folder, 'index.html')

    @app.route('/<path:filename>')
    def serve_frontend_files(filename):
        target_path = os.path.join(app.static_folder, filename)
        if os.path.exists(target_path) and not os.path.isdir(target_path):
            return send_from_directory(app.static_folder, filename)
        # Check if html exists
        if os.path.exists(target_path + '.html'):
            return send_from_directory(app.static_folder, filename + '.html')
        # Fallback to 404
        return jsonify({'error': f"File '{filename}' not found."}), 404

    # API Error Handlers
    @app.errorhandler(400)
    def bad_request(e):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Bad Request', 'message': str(e)}), 400
        return str(e), 400

    @app.errorhandler(401)
    def unauthorized(e):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Unauthorized', 'message': str(e)}), 401
        return str(e), 401

    @app.errorhandler(403)
    def forbidden(e):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Forbidden', 'message': str(e)}), 403
        return str(e), 403

    @app.errorhandler(404)
    def not_found(e):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Endpoint not found.'}), 404
        return str(e), 404

    @app.errorhandler(500)
    def internal_error(e):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Internal server error', 'message': str(e)}), 500
        return str(e), 500

    return app

if __name__ == '__main__':
    app = create_app()

    if '--init-db' in sys.argv:
        with app.app_context():
            print("Initializing database schema...")
            init_db_schema()
            print("Database schema initialized successfully.")
        sys.exit(0)

    port = int(os.getenv('PORT', 5000))
    print(f"Starting PBRMS server on http://127.0.0.1:{port}")
    app.run(host='0.0.0.0', port=port, debug=True)
