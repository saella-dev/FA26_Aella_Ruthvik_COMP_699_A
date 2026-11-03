import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-development-key")
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "tif", "tiff", "webp"}
