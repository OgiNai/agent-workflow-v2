def process_user(user):
    name = user.get("name", "").strip().lower()
    email = user.get("email", "").strip().lower()
    return {"name": name, "email": email}


def process_admin(admin):
    name = admin.get("name", "").strip().lower()
    email = admin.get("email", "").strip().lower()
    return {"name": name, "email": email}
