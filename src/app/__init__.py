import os
from flask import Flask
from config import Config
from .database import init_app, init_db
from .fragments import fragments_bp

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    os.makedirs(app.instance_path, exist_ok=True)
    upload_folder = app.config.get(
        "UPLOAD_FOLDER", os.path.join(app.instance_path, "uploads")
    )
    os.makedirs(upload_folder, exist_ok=True)
    app.config["UPLOAD_FOLDER"] = upload_folder

    init_app(app)
    app.register_blueprint(fragments_bp)

    with app.app_context():
        init_db()

    @app.errorhandler(413)
    def file_too_large(_error):
        from flask import flash, redirect, url_for
        flash("The uploaded file is too large. Maximum size is 10 MB.", "error")
        return redirect(url_for("fragments.new_fragment"))

    return app
