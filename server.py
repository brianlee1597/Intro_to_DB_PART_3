import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response
from dotenv import load_dotenv

load_dotenv()

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)

s_user = os.environ.get('USERNAME')
s_pass = os.environ.get('PASSWORD')

DATABASEURI = f"postgresql://{s_user}:{s_pass}@34.75.94.195/proj1part2"
engine = create_engine(DATABASEURI)

print(engine.table_names())

#
# Example of running queries in your database
# Note that this will probably not work if you already have a table named 'test' in your database, containing meaningful data. This is only an example showing you how to run queries in your database using SQLAlchemy.
#
# engine.execute("""CREATE TABLE IF NOT EXISTS test (
#   id serial,
#   name text
# );""")
# engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")


@app.before_request
def before_request():
  try:
    g.conn = engine.connect()
  except:
    print("uh oh, problem connecting to database")
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  try:
    g.conn.close()
  except Exception as e:
    pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to, for example, localhost:8111/foobar/ with POST or GET then you could use:
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
#
# see for routing: https://flask.palletsprojects.com/en/2.0.x/quickstart/?highlight=routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#
@app.route('/')
def index():
  """
  request is a special object that Flask provides to access web request information:

  request.method:   "GET" or "POST"
  request.form:     if the browser submitted a form, this contains the data in the form
  request.args:     dictionary of URL arguments, e.g., {a:1, b:2} for http://localhost?a=1&b=2

  See its API: https://flask.palletsprojects.com/en/2.0.x/api/?highlight=incoming%20request%20data

  """

  #
  # render_template looks in the templates/ folder for files.
  # for example, the below file reads template/index.html
  #
  
  user_results = g.conn.execute("SELECT * FROM Users LIMIT 4")
  users = []
  for result in user_results:
    users.append(result)
  user_results.close()

  # prop_results = g.conn.execute("SELECT * FROM Rentals LIMIT 4")
  # properties = []
  # for result in prop_results:
  #   properties.append(result)
  # prop_results.close()

  return render_template("index.html", users = users)

@app.route('/rentals')
def rentals():

  results = g.conn.execute("SELECT * FROM Rental")
  rentals = []
  for result in results:
    rentals.append(result)
  results.close()

  data = dict(data = rentals)

  return render_template("rentals.html")

@app.route('/users')
def users():

  category = request.args.get("category")  

  SQL_QUERY = "SELECT * FROM USERS u"

  if category == "hosts":
    SQL_QUERY += ", Hosts h WHERE u.uid = h.uid"
  
  if category == "renters":
    SQL_QUERY += ", Renters r WHERE u.uid = r.uid"

  results = g.conn.execute(SQL_QUERY)
  users = []
  for result in results:
    users.append(result)
  results.close()

  return render_template("users.html", users = users, category = category)

@app.route('/users/user')
def user():

  uid = request.args.get("uid")

  return render_template("user.html")

@app.route('/login')
def login():

  return render_template("login.html")

@app.route('/create')
def create():

  return render_template("create.html")


# Example of adding new data to the database
# @app.route('/add', methods=['POST'])
# def add():
#   name = request.form['name']
#   g.conn.execute('INSERT INTO test(name) VALUES (%s)', name)
#   return redirect('/')

# @app.route('/test', methods=['GET'])
# def test():
#   result = g.conn.execute('SELECT p.size from Properties p')

#   for row in result:
#     print(row)

#   return redirect('/')

if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)

  def run(debug, threaded, host, port):
    HOST, PORT = host, port
    print("running on %s:%d" % (HOST, PORT))
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)

  run()
