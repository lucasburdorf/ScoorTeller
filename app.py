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
    use_suggestion1 = False
    use_suggestion2 = False
    
    if request.method == 'POST':
        team1_input = request.form.get('team1', '').strip().lower()
        team2_input = request.form.get('team2', '').strip().lower()
        
      
        if request.form.get('use_suggestion1'):
            team1_input = suggestion1.lower() if suggestion1 else team1_input
            use_suggestion1 = True
        if request.form.get('use_suggestion2'):
            team2_input = suggestion2.lower() if suggestion2 else team2_input
            use_suggestion2 = True
        
        if not team1_input or not team2_input:
            message = "Voer beide teamnamen in!"
        else:
            conn = get_db_connection()
            
      
            all_teams = [row['team_1'].lower() for row in conn.execute('SELECT DISTINCT team_1 FROM weddies').fetchall()]
            all_teams += [row['team_2'].lower() for row in conn.execute('SELECT DISTINCT team_2 FROM weddies').fetchall()]
            all_teams = list(set(all_teams))
            
         
            rows1 = conn.execute(
                "SELECT score, team_1, team_2, winners FROM weddies "
                "WHERE LOWER(team_1) LIKE ? OR LOWER(team_2) LIKE ?",
                (f'%{team1_input}%', f'%{team1_input}%')
            ).fetchall()
            
            rows2 = conn.execute(
                "SELECT score, team_1, team_2, winners FROM weddies "
                "WHERE LOWER(team_1) LIKE ? OR LOWER(team_2) LIKE ?",
                (f'%{team2_input}%', f'%{team2_input}%')
            ).fetchall()
            
            if len(rows1) == 0 and len(rows2) == 0:
                # Suggesties genereren
                matches1 = get_close_matches(team1_input, all_teams, n=1, cutoff=0.6)
                matches2 = get_close_matches(team2_input, all_teams, n=1, cutoff=0.6)
                suggestion1 = matches1[0].title() if matches1 else None
                suggestion2 = matches2[0].title() if matches2 else None
                
                if suggestion1 or suggestion2:
                    message = "Geen wedstrijden gevonden. Suggestie:"
                else:
                    message = "Geen wedstrijden gevonden voor deze teams."
            elif len(rows1) == 0:
                matches1 = get_close_matches(team1_input, all_teams, n=1, cutoff=0.6)
                suggestion1 = matches1[0].title() if matches1 else None
                if suggestion1:
                    message = f"Team 1 niet gevonden. Bedoel je {suggestion1}?"
                else:
                    rows1 = rows2  # Fallback
            elif len(rows2) == 0:
                matches2 = get_close_matches(team2_input, all_teams, n=1, cutoff=0.6)
                suggestion2 = matches2[0].title() if matches2 else None
                if suggestion2:
                    message = f"Team 2 niet gevonden. Bedoel je {suggestion2}?"
                else:
                    rows2 = rows1  # Fallback
            
        
            if rows1 and rows2 and (len(rows1) > 0 or len(rows2) > 0):
                rows = rows1 + rows2
                total_goals1 = 0
                total_goals2 = 0
                count = 0
                wins1 = 0
                wins2 = 0
                score_pattern = re.compile(r'^\s*(\d+)[‑–-](\d+)\s*$')
                
                for row in rows:
                    m = score_pattern.match(row['score'])
                    if not m: continue
                    g1, g2 = int(m.group(1)), int(m.group(2))
                    
                    # Bepaal welke team team1/team2 is
                    if row['team_1'].lower() == team1_input or team1_input in row['team_1'].lower():
                        goals_team1, goals_team2 = g1, g2
                        winner = row['winners']
                    else:
                        goals_team1, goals_team2 = g2, g1
                        winner = row['winners']
                    
                    total_goals1 += goals_team1
                    total_goals2 += goals_team2
                    count += 1
                    
                    if winner.lower() == team1_input:
                        wins1 += 1
                    elif winner.lower() == team2_input:
                        wins2 += 1
                
                if count > 0:
                    avg1 = total_goals1 / count
                    avg2 = total_goals2 / count
                    pred1 = round(avg1)
                    pred2 = round(avg2)
                    
                    winner = team1_input.title() if wins1 >= wins2 else team2_input.title()
                    message = f"{winner} wint met {pred1}-{pred2} (gebaseerd op {count} wedstrijden)"
            
            conn.close()
    
    return render_template('calculate_game.html', 
                         message=message, 
                         suggestion1=suggestion1,
                         suggestion2=suggestion2,
                         team1=request.form.get('team1', ''),
                         team2=request.form.get('team2', ''))

@app.route('/information')
def information():
    return render_template('information.html')

if __name__ == '__main__':
    app.run(debug=True)

