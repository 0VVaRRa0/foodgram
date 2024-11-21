import os
from uuid import uuid4


def avatar_upload_path(instance, filename):
    ext = os.path.splitext(filename)[1]
    new_filename = f"{instance.username}_avatar_{uuid4().hex}{ext}"
    return os.path.join('avatars/', new_filename)
