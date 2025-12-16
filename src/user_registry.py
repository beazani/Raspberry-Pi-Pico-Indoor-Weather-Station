import json

USER_FILE = "users_reg.json"


def load_users():
    try:
        with open(USER_FILE, "r") as f:
            return json.load(f)
    except OSError:
        # File does not exist yet
        return {}


def save_users(users):
    with open(USER_FILE, "w") as f:
        json.dump(users, f)


def get_user(username):
    users = load_users()
    return users.get(username)


def register_user(username, age, sex):
    users = load_users()
    users[username] = {
        "age": age,
        "sex": sex
    }
    save_users(users)
