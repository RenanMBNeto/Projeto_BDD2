import urllib
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from app.config import Config

db = SQLAlchemy()
ma = Marshmallow()
bcrypt = Bcrypt()
jwt = JWTManager()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app)
    db.init_app(app)
    ma.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)

    # Importação das rotas
    from app.routes import (
        auth_routes,
        client_routes,
        product_routes,
        portfolio_routes,
        order_routes,
        suitability_routes,
        client_portal_routes,
        grupo_routes
    )

    # Registo das Blueprints
    app.register_blueprint(auth_routes.bp)
    app.register_blueprint(client_routes.bp)
    app.register_blueprint(product_routes.bp)
    app.register_blueprint(portfolio_routes.bp)
    app.register_blueprint(order_routes.bp)
    app.register_blueprint(suitability_routes.bp)
    app.register_blueprint(client_portal_routes.bp)
    app.register_blueprint(grupo_routes.bp, url_prefix='/api/grupos')

    return app