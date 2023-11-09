from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, send
# from flask_cors import CORS
from flask_socketio import join_room, leave_room
from nanoid import generate

app = Flask(__name__)
# CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Maintain a list of connected players
players = {}
ongoing_game = {}
def get_winner(roomId):
    if roomId in players and len(players[roomId]) == 2:
        player1_choices = players[roomId][0]["options"]
        player2_choices = players[roomId][1]["options"]

        player1_wins = 0
        player2_wins = 0

        for round_number in player1_choices:
            player1_choice = player1_choices[round_number]
            player2_choice = player2_choices.get(round_number)

            if player2_choice is not None:
                result = determine_winner(player1_choice, player2_choice)

                if result == "Win":
                    player1_wins += 1
                elif result == "Lose":
                    player2_wins += 1

        if player1_wins > player2_wins:
            return players[roomId][0]["name"]
        elif player2_wins > player1_wins:
            return players[roomId][1]["name"]
        else:
            return "It's a tie!"

    else:
        return "Game not finished yet"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/room/<roomid>')
def room(roomid):
    return render_template('index.html')

@socketio.on('join')
def on_join(data):
    username = data['username']
    room = data['room']
    if ongoing_game.get(room) is None:
        ongoing_game[room] = [0, 0]

    if players.get(room) is None:
        players[room] = [{"name": username, "options": []}]
    else:
        players[room].append({"name": username, "options": []})
    join_room(room)
    print(f"{username} joined")
    emit('message', {'message': f'{username} joined the room, waiting...', 'type': "message"}, to=room)
    if username == "guest 2":
        emit('message', {'config': {"times": 2, "ttl": 10000}, 'type': "gameplay"}, to=room)
    print(ongoing_game)

@socketio.on('leave')
def on_leave(data):
    username = data['username']
    room = data['room']
    leave_room(room)
    send(username + ' has left the room.', to=room)

@socketio.on('connect')
def handle_connect():
     emit('message', {'message': f'Join or create a room to start', 'type': "message"})

@socketio.on('join_req')
def handle_join_request():
    new_roomid = generate(size=5)
    emit('join_acc', new_roomid)


@socketio.on('send_options')
def handle_set_options(data):
    print(data)
    ongoing_game[data["roomId"]][data["playerIndex"]] += 1
    room = players.get(data["roomId"])
    if room is not None:
        players[data["roomId"]][data["playerIndex"]]["options"] = data["options"]

        if ongoing_game[data["roomId"]][0] == 1 and ongoing_game[data["roomId"]][1] == 1:
            winner = get_winner(data["roomId"])
            emit('message', {'message': f'{winner} won the game', 'type': "message"}, to=data["roomId"])


@socketio.on('choose')
def handle_choice(data):
    if len(players) == 2:
        players_choice = {
            players[0]: data['choice1'],
            players[1]: data['choice2']
        }

        player1_choice = players_choice[players[0]]
        player2_choice = players_choice[players[1]]

        result = determine_winner(player1_choice, player2_choice)
        emit('result', {'message': f'Player 1 chose {player1_choice}, Player 2 chose {player2_choice}. {result}'}, broadcast=True)
    else:
        emit('message', {'message': 'Waiting for another player...'})

def determine_winner(player1_choice, player2_choice):

    # Implement your Rock, Paper, Scissors game logic here
    # Compare the choices and return the result (win, lose, or tie)

    if player1_choice ==  player2_choice:
        return "Tie"
    elif (player1_choice == 'rock' and  player2_choice == 'scissors') or (player1_choice == 'scissors' and  player2_choice == 'paper') or (player1_choice == 'paper' and  player2_choice == 'rock'):
        return "Win"
    else:
         return "Lose"


