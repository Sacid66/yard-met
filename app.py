from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO, join_room, leave_room, send
import uuid

app = Flask(__name__)
app.config["SECRET_KEY"] = "your_secret_key"
socketio = SocketIO(app, cors_allowed_origins="*")

rooms = {}

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        username = request.form.get("username")
        if not username:
            return render_template("index.html", error="Kullanıcı adı boş olamaz!")
        
        room_code = str(uuid.uuid4())[:6]  # 6 karakterli oda kodu
        rooms[room_code] = {"members": 0}
        
        # Yönlendirme direkt URL olarak yapılıyor
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
    join_room(room)
    rooms[room]["members"] += 1
    
    send({"username": "Sistem", "message": f"{username} odaya katıldı!"}, to=room)

@socketio.on("message")
def handle_message(data):
    room = data["room"]
    send({"username": data["username"], "message": data["message"]}, to=room)

@socketio.on("leave")
def handle_leave(data):
    room = data["room"]
    username = data["username"]
    leave_room(room)
    rooms[room]["members"] -= 1
    
    send({"username": "Sistem", "message": f"{username} odadan ayrıldı."}, to=room)

if __name__ == "__main__":
    socketio.run(app, debug=True)
