from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO, join_room, leave_room
import uuid

app = Flask(__name__)
app.config["SECRET_KEY"] = "your_secret_key"

# Gevent tabanlı WebSocket desteği sağlamak için async_mode="gevent" ekliyoruz
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="gevent",
                    logger=True, engineio_logger=True,
                    max_http_buffer_size=50_000_000)

rooms = {}  # Aktif odaları saklamak için sözlük

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        username = request.form.get("username")
        if not username:
            return render_template("index.html", error="Kullanıcı adı boş olamaz!")

        room_code = str(uuid.uuid4())[:6]
        rooms[room_code] = {"members": 0}
        return redirect(f"/chat/{room_code}/{username}")
    return render_template("index.html")

@app.route("/join_room", methods=["POST"])
def join_room_view():
    username = request.form.get("username")
    room_code = request.form.get("room_code")

    if room_code not in rooms:
        return render_template("index.html", error="Böyle bir oda bulunamadı!")

    return redirect(f"/chat/{room_code}/{username}")

@app.route("/chat/<room_code>/<username>")
def chat(room_code, username):
    if room_code not in rooms:
        return redirect(url_for("home"))
    return render_template("chat.html", room_code=room_code, username=username)

@socketio.on("join")
def handle_join(data):
    room = data["room"]
    username = data["username"]

    if room not in rooms:
        rooms[room] = {"members": 0}

    join_room(room)
    rooms[room]["members"] += 1
    # Sadece sistem mesajı gönderiyoruz
    socketio.emit("message", {
        "username": "Sistem",
        "message": f"{username} odaya katıldı!"
    }, room=room)

@socketio.on("message")
def handle_message(data):
    room = data["room"]
    socketio.emit("message", {
        "username": data["username"],
        "message": data["message"]
    }, room=room)

@socketio.on("file")
def handle_file(data):
    room = data["room"]
    socketio.emit("file", data, room=room)

@socketio.on("typing")
def handle_typing(data):
    room = data["room"]
    username = data["username"]
    socketio.emit("typing", {"username": username}, room=room)

@socketio.on("stop_typing")
def handle_stop_typing(data):
    room = data["room"]
    username = data["username"]
    socketio.emit("stop_typing", {"username": username}, room=room)

@socketio.on("leave")
def handle_leave(data):
    room = data["room"]
    username = data["username"]

    leave_room(room)
    rooms[room]["members"] -= 1
    if rooms[room]["members"] <= 0:
        del rooms[room]

    # Sadece sistem mesajı gönderiyoruz
    socketio.emit("message", {
        "username": "Sistem",
        "message": f"{username} odadan ayrıldı."
    }, room=room)

if __name__ == "__main__":
    socketio.run(app, debug=True)
