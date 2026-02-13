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
                "SELECT score, team_1, team_2, winners FROM weddies "
                "WHERE LOWER(team_1) LIKE ? OR LOWER(team_2) LIKE ?",
                (f'%{team1_input}%', f'%{team1_input}%')
            ).fetchall()
            
            rows2 = conn.execute(
                "SELECT score, team_1, team_2, winners FROM weddies "
                "WHERE LOWER(team_1) LIKE ? OR LOWER(team_2) LIKE ?",
                (f'%{team2_input}%', f'%{team2_input}%')
            ).fetchall()
            
            # Suggestie logic (volledig)
            if len(rows1) == 0 and len(rows2) == 0:
                matches1 = get_close_matches(team1_input.lower(), all_teams, n=1, cutoff=0.6)
                matches2 = get_close_matches(team2_input.lower(), all_teams, n=1, cutoff=0.6)
                suggestion1 = matches1[0].title() if matches1 else None
                suggestion2 = matches2[0].title() if matches2 else None
                if suggestion1 or suggestion2:
                    message = "No matches found. Suggestion:"
                else:
                    message = "No matches found for these teams"
            elif len(rows1) == 0:
                matches1 = get_close_matches(team1_input.lower(), all_teams, n=1, cutoff=0.6)
                suggestion1 = matches1[0].title() if matches1 else None
                if suggestion1:
                    message = f"Team 1 not found. Did you mean {suggestion1}?"
                else:
                    rows1 = rows2
            elif len(rows2) == 0:
                matches2 = get_close_matches(team2_input.lower(), all_teams, n=1, cutoff=0.6)
                suggestion2 = matches2[0].title() if matches2 else None
                if suggestion2:
                    message = f"Team 2 not found. Did you mean {suggestion2}?"
                else:
                    rows2 = rows1
            
            # Berekeningen
            if rows1 or rows2:
                rows = rows1 + rows2
                total_goals1 = total_goals2 = count = wins1 = wins2 = 0
                score_pattern = re.compile(r'^\s*(\d+)[‑–-](\d+)\s*$')  # ✅ FIXED
                
                for row in rows:
                    m = score_pattern.match(row['score'])
                    if not m: continue
                    g1, g2 = int(m.group(1)), int(m.group(2))
                    
                    if row['team_1'].lower() == t1 or t1 in row['team_1'].lower():  # ✅ FIXED
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
                        winner = team1_input.title() if wins1 > wins2 else team2_input.title()
                        message = f"{winner} wins with a score of {pred1}-{pred2} (based on {count} games)"
            
            conn.close()
    
    return render_template('calculate_game.html', 
                         message=message, 
                         suggestion1=suggestion1, 
                         suggestion2=suggestion2,
                         team1=team1_input,
                         team2=team2_input)


