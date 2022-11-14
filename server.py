import os
from sqlalchemy import *
import datetime
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

@app.route('/')
def index():

  FEATURED_RENTALS = """
    SELECT DISTINCT ON(P.pid) * 
    FROM owned_properties P, is_available A 
    WHERE P.pid  = A.pid 
    LIMIT 4
  """

  MIN_FROM = """
    SELECT MIN(start_date) as start_date 
    FROM is_available
  """

  MAX_TO = """
    SELECT MAX(end_date) as end_date 
    FROM is_available
  """

  results = g.conn.execute(MIN_FROM)
  min_start = results.one()['start_date']

  results = g.conn.execute(MAX_TO)
  max_to = results.one()['end_date']

  results = g.conn.execute(FEATURED_RENTALS)
  rentals = []
  for result in results:
    rentals.append(result)

  results.close()

  return render_template("index.html", rentals=rentals, min_start=min_start, max_to=max_to)

@app.route('/rentals')
def rentals():

  start_from = request.args.get("from")
  end_at = request.args.get("to")
  order_by = request.args.get("order_by")
  sort_by = request.args.get("sort_by")

  MIN_FROM = """
    SELECT MIN(start_date) as start_date 
    FROM is_available
  """

  MAX_TO = """
    SELECT MAX(end_date) as end_date 
    FROM is_available
  """

  RENTALS = """
    Select DISTINCT ON(P.{}) * 
    FROM owned_properties P, is_available A 
    WHERE P.pid  = A.pid AND A.start_date >= '{}' AND A.end_date <= '{}'
    ORDER BY P.{} {}
  """.format(order_by, start_from, end_at, order_by, sort_by)

  order_html = [
    [order_by == 'pid', 'pid', "Property ID"],
    [order_by == 'size', 'size', "Property Size"]
  ]

  sort_html = [
    [sort_by == 'ASC', 'ASC', "Ascending"],
    [sort_by == 'DESC', 'DESC', "Descending"]
  ]

  results = g.conn.execute(MIN_FROM)
  min_start = results.one()['start_date']

  results = g.conn.execute(MAX_TO)
  max_to = results.one()['end_date']

  results = g.conn.execute(RENTALS)
  rentals = []
  for result in results:
    rentals.append(result)
    
  results.close()

  return render_template(
    "rentals.html", 
    rentals=rentals, 
    min_start=min_start, 
    max_to=max_to, 
    curr_start=start_from, 
    curr_end=end_at,
    order_html=order_html,
    sort_html=sort_html
  )

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
