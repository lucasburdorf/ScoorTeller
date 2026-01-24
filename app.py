from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import re

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
        score   = request.form['score']
        team_1  = request.form['team_1']
        team_2  = request.form['team_2']

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

    if request.method == 'POST':
        team1 = request.form.get('team1', '').strip()
        team2 = request.form.get('team2', '').strip()

        # simpele input‑check
        if not team1 or not team2:
            message = "wrong input try again"
        else:
            conn = get_db_connection()
        
            rows = conn.execute(
                """
                SELECT score, team_1, team_2, winners
                FROM weddies
                WHERE (team_1 = ? AND team_2 = ?)
                   OR (team_1 = ? AND team_2 = ?)
                """,
                (team1, team2, team2, team1)
            ).fetchall()
            conn.close()

            if not rows:
                message = "wrong input try again"
            else:
                # scores parsen en gemiddelde berekenen
                total_goals1 = 0
                total_goals2 = 0
                count = 0
                wins1 = 0
                wins2 = 0

                score_pattern = re.compile(r'^\s*(\d+)\s*[-–]\s*(\d+)\s*$')

                for row in rows:
                    m = score_pattern.match(row['score'])
                    if not m:
                        continue  # sla rare scores over

                    g1 = int(m.group(1))
                    g2 = int(m.group(2))

             
                    if row['team_1'] == team1:
                        goals_team1 = g1
                        goals_team2 = g2
                    else:
                        goals_team1 = g2
                        goals_team2 = g1

                    total_goals1 += goals_team1
                    total_goals2 += goals_team2
                    count += 1

                    if row['winners'] == team1:
                        wins1 += 1
                    elif row['winners'] == team2:
                        wins2 += 1

                if count == 0:
                    message = "wrong input try again"
                else:
                    avg1 = total_goals1 / count
                    avg2 = total_goals2 / count


                    from math import floor
                    pred1 = round(avg1)
                    pred2 = round(avg2)

                    if wins1 > wins2:
                        winner = team1
                    elif wins2 > wins1:
                        winner = team2
                    else:
                        winner = team1 if pred1 >= pred2 else team2

                    message = f"{winner} will win with a score of {pred1}-{pred2}"

    return render_template('calculate_game.html', message=message)
@app.route('/information')
def information():
    return render_template('information.html')

if __name__ == '__main__':
    app.run(debug=True)

