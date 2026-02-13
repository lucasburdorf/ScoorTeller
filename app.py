from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import re
from difflib import get_close_matches

app = Flask(__name__)
DATABASE = 'wedstrijden.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    conn = get_db_connection()
    rows = conn.execute('SELECT * FROM weddies').fetchall()
    conn.close()
    return render_template('home.html', weddies=rows)

@app.route('/add_game', methods=['GET', 'POST'])
def add_game():
    if request.method == 'POST':
        winners = request.form['winners']
        score = request.form['score']
        team_1 = request.form['team_1']
        team_2 = request.form['team_2']
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO weddies (winners, score, team_1, team_2) VALUES (?, ?, ?, ?)',
            (winners, score, team_1, team_2)
        )
        conn.commit()
        conn.close()
        return redirect(url_for('add_game'))
    conn = get_db_connection()
    rows = conn.execute('SELECT * FROM weddies').fetchall()
    conn.close()
    return render_template('add_game.html', weddies=rows)

@app.route('/calculate_game', methods=['GET', 'POST'])
def calculate_game():
    message = None
    suggestion1 = None
    suggestion2 = None
    team1_input = ''
    team2_input = ''
    
    if request.method == 'POST':
        team1_input = request.form.get('team1', '').strip()
        team2_input = request.form.get('team2', '').strip()
        
        sugg1 = request.form.get('suggestion1')
        sugg2 = request.form.get('suggestion2')
        
        if request.form.get('use_suggestion1') and sugg1:
            team1_input = sugg1.strip()
        if request.form.get('use_suggestion2') and sugg2:
            team2_input = sugg2.strip()
        
        t1 = team1_input.casefold()
        t2 = team2_input.casefold()
        
        if not t1 or not t2:
            message = "Fill in both team names!"
        elif t1 == t2:
            message = "Team 1 and Team 2 cannot be the same!"
        else:
            conn = get_db_connection()
            
            all_teams = [row['team_1'].lower() for row in conn.execute('SELECT DISTINCT team_1 FROM weddies').fetchall()]
            all_teams += [row['team_2'].lower() for row in conn.execute('SELECT DISTINCT team_2 FROM weddies').fetchall()]
            all_teams = list(set(all_teams))
            
            rows1 = conn.execute(
                "SELECT score, team_1, team_2, winners FROM wed

