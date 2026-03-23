class UserAuth:
    def __init__(self):
        self.users = {}
    
    def register(self, username, password):
        if username in self.users:
            return False
        self.users[username] = password
        return True
    
    def login(self, username, password):
        if username not in self.users:
            return None
        if self.users[username] == password:
            return {"username": username, "logged_in": True}
        return None
    
    def change_password(self, username, old_password, new_password):
        if self.users.get(username) != old_password:
            return False
        self.users[username] = new_password
        return True
    
    def delete_user(self, username):
        if username in self.users:
            del self.users[username]
            return True
        return False
