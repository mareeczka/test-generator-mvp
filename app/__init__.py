from flask import Flask

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'dev-secret-key'  # Замени в продакшене!

    # Простой health-check эндпоинт
    @app.route('/health')
    def health():
        return {'status': 'OK', 'message': 'Server is running'}

    return app
