from flask import Flask, request, jsonify
import mysql.connector
import mysql_config as config

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
time: <str> 00:00
'''
@app.route('/show_at_time', methods=['GET'])
def show_at_time():
  connection = get_db_connection()
  cursor = connection.cursor(dictionary=True) 

  term = request.args.get('term')
  day = request.args.get('day')
  start_time_min = request.args.get('start_time_min')
  start_time_max = request.args.get('start_time_max')

  try:
    cursor.execute("""
    SELECT * FROM users 
    INNER JOIN show_user ON users.id = show_user.user_id
    INNER JOIN shows ON show_user.show_id = shows.id
    WHERE 
    shows.term_id = %s AND
    shows.published_day = %s AND
    shows.published_start > %s AND
    shows.published_start < %s""",
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