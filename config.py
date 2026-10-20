import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-key"
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or "mysql+pymysql://root:santi654@localhost/renta_sprinter"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class DevelopmentConfig(Config):
    DEBUG = True
