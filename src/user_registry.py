import json

USER_FILE = "users_reg.json"


def load_users():
    """Load user registry from JSON file. Returns empty dict if file doesn't exist."""
    try:
        with open(USER_FILE, "r") as f:
            return json.load(f)
    except OSError:
        # File does not exist yet
        return {}


def save_users(users):
    """Save user registry to JSON file."""
    with open(USER_FILE, "w") as f:
        json.dump(users, f)


def get_user(username):
    """Retrieve user data by username. Returns dict with age and sex, or None if not found."""
    users = load_users()
    return users.get(username)


def register_user(username, age, sex):
    """Register a new user with age and sex, storing in JSON registry."""
    users = load_users()
    users[username] = {
        "age": age,
        "sex": sex
    }
    save_users(users)
