from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user,
)
from werkzeug.security import generate_password_hash, check_password_hash
from flask_socketio import SocketIO, emit, join_room

app = Flask(__name__)

app.config["SECRET_KEY"] = "my-secret-key"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"

db = SQLAlchemy(app)
socketio = SocketIO(app, async_mode="threading", cors_allowed_origins="*")

login_manager = LoginManager()
login_manager.init_app(app)

login_manager.login_view = "login"


# =====================
# DATABASE MODELS
# =====================


class User(db.Model, UserMixin):

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(50), unique=True, nullable=False)

    email = db.Column(db.String(100), unique=True, nullable=False)

    password = db.Column(db.String(200), nullable=False)


class Message(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    sender_id = db.Column(db.Integer)

    receiver_id = db.Column(db.Integer)

    text = db.Column(db.String(500))


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# =====================
# ROUTES
# =====================


@app.route("/")
def home():

    return redirect(url_for("users"))


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]

        password = generate_password_hash(request.form["password"])

        user = User(username=username, email=email, password=password)

        db.session.add(user)
        db.session.commit()

        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):

            login_user(user)

            return redirect(url_for("users"))

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():

    logout_user()

    return redirect(url_for("login"))


@app.route("/users")
@login_required
def users():

    users = User.query.filter(User.id != current_user.id).all()

    return render_template("users.html", users=users)


@app.route("/chat/<int:user_id>", methods=["GET", "POST"])
@login_required
def chat(user_id):

    other_user = User.query.get_or_404(user_id)

    if request.method == "POST":

        message = Message(
            sender_id=current_user.id,
            receiver_id=other_user.id,
            text=request.form["message"],
        )

        db.session.add(message)
        db.session.commit()

    messages = Message.query.filter(
        (
            (Message.sender_id == current_user.id)
            & (Message.receiver_id == other_user.id)
        )
        | (
            (Message.sender_id == other_user.id)
            & (Message.receiver_id == current_user.id)
        )
    ).all()

    return render_template("chat.html", user=other_user, messages=messages)


# =====================
# START
# =====================

with app.app_context():

    db.create_all()


@socketio.on("connect")
def connected():
    print("Client connected")


@socketio.on("join")
def on_join(data):

    room = data["room"]

    join_room(room)

    print(f"Joined {room}")


@socketio.on("send_message")
def handle_send_message(data):

    print("RECEIVED:", data)

    message = Message(
        sender_id=data["sender_id"], receiver_id=data["receiver_id"], text=data["text"]
    )

    db.session.add(message)
    db.session.commit()

    emit(
        "receive_message",
        {"sender_id": data["sender_id"], "text": data["text"]},
        room=data["room"],
    )

    return {"status": "ok"}


if __name__ == "__main__":
    socketio.run(app, debug=True, use_reloader=False)
