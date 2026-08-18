from flask import Flask, request, jsonify
import mysql.connector
import mysql_config as config

'''
CURL w GET:
curl -G http://mc.krlx.org:5212/api/show_at_time \
  -d "term=2026-SP" \
  -d "day=Monday" \
  -d "start_time_min=12:00" \
  -d "start_time_max=13:00"
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


PORT=5212
HOST='0.0.0.0'

app = Flask(__name__)

'''
GET:
term: <str> 20xx-(SP,WI,FA)
day: <str> (Monday,...)
start_time_min: <str> 00:00
start_time_max: <str> 00:00
'''
@app.route('/api/show_at_time', methods=['GET'])
def show_at_time():
  connection = get_db_connection()
  cursor = connection.cursor(dictionary=True) 

  term = request.args.get('term')
  day = request.args.get('day')
  start_time_min = request.args.get('start_time_min')
  start_time_max = request.args.get('start_time_max')

  try:
    cursor.execute("""
    SELECT 
    GROUP_CONCAT(users.name SEPARATOR '; ') AS users
    GROUP_CONCAT(users.year SEPARATOR '; ') AS years
    GROUP_CONCAT(users.email SEPARATOR '; ') AS emails
    GROUP_CONCAT(users.phone_number SEPARATOR '; ') AS phone_numbers
    GROUP_CONCAT(users.pronouns SEPARATOR '; ') AS pronouns
    shows.title
    shows.term_id
    shows.published_day
    shows.published_start
    shows.published_end
    FROM shows 
    LEFT JOIN show_user ON shows.id = show_user.show_id
    LEFT JOIN users ON show_user.user_id = users.id
    WHERE 
    shows.term_id = %s AND
    shows.published_day = %s AND
    shows.published_start >= %s AND
    shows.published_start < %s
    GROUP BY shows.id
    ORDER BY shows.published_start ASC""",
    (term, day, start_time_min, start_time_max))

    users = cursor.fetchall()
    
    return jsonify(users)
      
  except mysql.connector.Error as err:
    return jsonify({"error": str(err)}), 500
      
  finally:
    cursor.close()
    connection.close()

if __name__ == '__main__':
    app.run(host=HOST, port=PORT)