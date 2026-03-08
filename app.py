from flask import Flask, render_template, request, redirect, url_for
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import os
import re
from difflib import get_close_matches

load_dotenv()
app = Flask(__name__)

def get_db_connection():
    return psycopg2.connect(
        user=os.getenv("user"),
        password=os.getenv("password"),
        host=os.getenv("host"),
        port=os.getenv("port"),
        dbname=os.getenv("dbname"),
        cursor_factory=RealDictCursor
    )

@app.route('/')
def index():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM weddies')
    rows = cur.fetchall()
    cur.close()
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
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO weddies (winners, score, team_1, team_2) VALUES (%s, %s, %s, %s)',
            (winners, score, team_1, team_2)
        )
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for('add_game'))
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM weddies')
    rows = cur.fetchall()
    cur.close()
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
            cur = conn.cursor()

            cur.execute('SELECT DISTINCT team_1 FROM weddies')
            all_teams = [r['team_1'].lower() for r in cur.fetchall()]
            cur.execute('SELECT DISTINCT team_2 FROM weddies')
            all_teams += [r['team_2'].lower() for r in cur.fetchall()]
            all_teams = list(set(all_teams))

            cur.execute(
                "SELECT score, team_1, team_2, winners FROM weddies WHERE LOWER(team_1) LIKE %s OR LOWER(team_2) LIKE %s",
                (f'%{t1}%', f'%{t1}%')
            )
            rows1 = cur.fetchall()

            cur.execute(
                "SELECT score, team_1, team_2, winners FROM weddies WHERE LOWER(team_1) LIKE %s OR LOWER(team_2) LIKE %s",
                (f'%{t2}%', f'%{t2}%')
            )
            rows2 = cur.fetchall()

            if len(rows1) == 0 and len(rows2) == 0:
                matches1 = get_close_matches(t1, all_teams, n=1, cutoff=0.6)
                matches2 = get_close_matches(t2, all_teams, n=1, cutoff=0.6)
                suggestion1 = matches1[0].title() if matches1 else None
                suggestion2 = matches2[0].title() if matches2 else None
                message = "No matches found. Suggestion:" if (suggestion1 or suggestion2) else "No matches found for these teams"
            elif len(rows1) == 0:
                matches1 = get_close_matches(t1, all_teams, n=1, cutoff=0.6)
                suggestion1 = matches1[0].title() if matches1 else None
                if suggestion1:
                    message = f"Team 1 not found. Did you mean {suggestion1}?"
                else:
                    rows1 = rows2
            elif len(rows2) == 0:
                matches2 = get_close_matches(t2, all_teams, n=1, cutoff=0.6)
                suggestion2 = matches2[0].title() if matches2 else None
                if suggestion2:
                    message = f"Team 2 not found. Did you mean {suggestion2}?"
                else:
                    rows2 = rows1

            if rows1 or rows2:
                rows = list(rows1) + list(rows2)
                total_goals1 = total_goals2 = 0
                count = wins1 = wins2 = 0
                score_pattern = re.compile(r'^\s*(\d+)[‑–-](\d+)\s*$')

                for row in rows:
                    m = score_pattern.match(row['score'])
                    if not m:
                        continue
                    g1, g2 = int(m.group(1)), int(m.group(2))
                    if t1 in row['team_1'].lower():
                        goals_team1, goals_team2 = g1, g2
                    else:
                        goals_team1, goals_team2 = g2, g1
                    total_goals1 += goals_team1
                    total_goals2 += goals_team2
                    count += 1
                    winner = row['winners'].lower()
                    if winner == t1:
                        wins1 += 1
                    elif winner == t2:
                        wins2 += 1

                if count > 0:
                    pred1 = round(total_goals1 / count)
                    pred2 = round(total_goals2 / count)
                    if pred1 == pred2:
                        message = f"The game will tie with {pred1}-{pred2} (based on {count} games)"
                    else:
                        winner_name = team1_input.title() if wins1 > wins2 else team2_input.title()
                        message = f"{winner_name} wins with a score of {pred1}-{pred2} (based on {count} games)"

            cur.close()
            conn.close()

    return render_template('calculate_game.html', message=message, suggestion1=suggestion1, suggestion2=suggestion2, team1=team1_input, team2=team2_input)

@app.route('/information')
def information():
    return render_template('information.html')

if __name__ == '__main__':
    app.run(debug=True)
