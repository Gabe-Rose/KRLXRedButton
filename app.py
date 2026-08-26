'''
Flask app has:
an api endpoint (/api/show_at_time) that returns json of a show at time queried
has a homepage
'''

from flask import Flask, abort, request, render_template, jsonify
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import mysql.connector
import mysql_config as config

'''
CURL w GET:
curl -G http://mc.krlx.org:5212/api/show_at_time \
  -d "term=2026-SP" \
  -d "day=Monday" \
  -d "time=13:10"
'''

db_config = {
  'host': config.HOST,
  'user': config.USERNAME,
  'password': config.PASSWORD,
  'database': config.DATABASE
}

def get_db_connection():
    #Establishes and returns a database connection
    return mysql.connector.connect(**db_config)

def query_db(term, day, current_time):
  connection = get_db_connection()
  cursor = connection.cursor(dictionary=True) 
  try:
    days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    day_i = days.index(day)
    prev_day = days[day_i -1]
    cursor.execute("SET @query_day = %s, @query_prev_day = %s, @query_time = %s", (day, prev_day, current_time))
    cursor.execute(
      """
      SELECT 
      GROUP_CONCAT(users.name SEPARATOR '; ') AS names,
      GROUP_CONCAT(users.year SEPARATOR '; ') AS years,
      GROUP_CONCAT(users.email SEPARATOR '; ') AS emails,
      GROUP_CONCAT(users.phone_number SEPARATOR '; ') AS phone_numbers,
      GROUP_CONCAT(users.pronouns SEPARATOR '; ') AS pronouns,
      shows.title,
      shows.term_id,
      shows.published_day,
      shows.published_start,
      shows.published_end
      FROM shows 
      LEFT JOIN show_user ON shows.id = show_user.show_id
      LEFT JOIN users ON show_user.user_id = users.id
      WHERE 
      shows.term_id = %s AND
      (
      (shows.published_start <= shows.published_end AND
      shows.published_day = @query_day COLLATE utf8mb4_unicode_ci AND
      shows.published_start <= @query_time COLLATE utf8mb4_unicode_ci AND
      shows.published_end > @query_time COLLATE utf8mb4_unicode_ci)
      OR
      (shows.published_day = @query_day COLLATE utf8mb4_unicode_ci AND
      shows.published_start <= @query_time COLLATE utf8mb4_unicode_ci AND
      shows.published_start > shows.published_end)
      OR
      (shows.published_day = @query_prev_day COLLATE utf8mb4_unicode_ci AND
      shows.published_end >= @query_time COLLATE utf8mb4_unicode_ci AND
      shows.published_start > shows.published_end)
      )
      GROUP BY shows.id
      ORDER BY shows.published_start ASC
      """, [term])

    row = cursor.fetchone()
    #clear remaining rows (there shouldnt be any)
    cursor.fetchall()
    if row is None:
      return {"error" : "empty"}
    return row
      
  except mysql.connector.Error as err:
    return {"error": str(err)}
         
  finally:
    cursor.close()
    connection.close()


'''
gets the most recent term
'''
def get_current_term():
  connection = get_db_connection()
  cursor = connection.cursor(dictionary=True) 
  try:
    cursor.execute(
      """
      SELECT id FROM terms
      WHERE on_air <= NOW()
      ORDER BY on_air DESC
      LIMIT 1
      """)
    row = cursor.fetchone()
    if row is None:
      return {"error" : "empty"}
    return row
       
  except mysql.connector.Error as err:
    return {"error": str(err)}
        
  finally:
    cursor.close()
    connection.close()
     

#Parameters used for development mode
PORT=5212
HOST='0.0.0.0'

app = Flask(__name__)

@app.route('/', methods=['GET'])
def index_page():
  title = None
  term = None
  day = None
  start = None
  end = None
  hosts = None
  redirect = False
  if request.args.get('query') == 'True':
    utc = datetime.now(timezone.utc)
    mn_time = utc.astimezone(ZoneInfo("America/Chicago"))
    current_term = get_current_term()
    #return current_term
    if current_term.get("error") is not None:
      abort(500)

    term_in = current_term.get("id")
    day_in = mn_time.strftime("%A")
    time_in = mn_time.strftime("%H:%M")
    show = query_db(term_in, day_in, time_in)
    #return show
    if show.get("error") is not None:
      abort(500)

    title = show['title']
    term = show['term_id']
    day = show['published_day']
    start = show['published_start']
    end = show['published_end']

    names = show['names'].split(';')
    years = show['years'].split(';')
    emails = show['emails'].split(';')
    phone_numbers = show['phone_numbers'].split(';')
    pronouns = show['pronouns'].split(';')
    hosts = []
    for i in range(0, len(names)):
      hosts.append(names[i] + \
      '\n   Class of ' + years[i] + \
      '\n   Email: ' + emails[i] + \
      '\n   Phone: ' + phone_numbers[i] + \
      '\n   Pronouns: ' + pronouns[i])

    redirect = True
    
  return render_template('index.html', 
    hosts = hosts,
    title = title,
    term = term, 
    day = day,
    start = start,
    end = end,
    redirect = redirect)

'''
GET:
term: <str> 20xx-(SP,WI,FA)
day: <str> (Monday,...)
time: <str> 00:00
'''
@app.route('/api/show_at_time', methods=['GET'])
def show_at_time():
  term = request.args.get('term')
  day = request.args.get('day')
  current_time = request.args.get('time')
  return jsonify(query_db(term, day, current_time))

@app.errorhandler(404)
def page_not_found(error):
    # Pass the 404 status code explicitly at the end of the return statement
    return "404 page not found"

@app.errorhandler(500)
def page_not_found(error):
    # Pass the 404 status code explicitly at the end of the return statement
    return "500 there was an error"

if __name__ == '__main__':
    app.run(host=HOST, port=PORT)