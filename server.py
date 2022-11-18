import os
from sqlalchemy import *
import datetime
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, jsonify, make_response
from dotenv import load_dotenv
import string
import random
import pandas as pd

load_dotenv()

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)

s_user = os.environ.get('USERNAME')
s_pass = os.environ.get('PASSWORD')

DATABASEURI = f"postgresql://{s_user}:{s_pass}@34.75.94.195/proj1part2"
engine = create_engine(DATABASEURI)

print(engine.table_names())

#for CHEQUE_ACCOUNT, CREDIT_CARD
def str_generator(size, chars=string.ascii_uppercase + string.digits):
   return ''.join(random.choice(chars) for _ in range(size))

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

########## URIS ##########

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

@app.route('/login')
def login():
  return render_template("login.html")

@app.route('/create')
def create():
  return render_template("create.html", duplicate=False, error=False)

@app.route('/user')
def user():
  uid = request.args.get('uid')

  USER_QUERY = g.conn.execute("""
    SELECT uid, first_name, last_name, phone_number
    FROM Users
    WHERE uid = {}
  """.format(uid))

  try:
    user_info = USER_QUERY.one()
    user = []
    for info in user_info:
      user.append(info)
      
    USER_QUERY.close()
    
    # Need all user rentals query here, and g.conn.execute to get all rows
    # which you can for loop it and append it to user_rentals for display.

    USER_PROP_QUERY = g.conn.execute("""
      SELECT addr, city, state, postal_code, P.pid from owned_properties P, locates_addresses A
      WHERE P.uid_host = {} AND A.pid = P.pid
    """.format(uid))
    
    try:
      prop_info = USER_PROP_QUERY.all()
      user_props = []
      for info in prop_info:
        user_props.append(info)
        
      USER_PROP_QUERY.close()
      
      return render_template("user.html", user=user, user_props=user_props)

    except:
        return render_template('405.html')

  except:
    return render_template('405.html')

########## URIS ##########

########## API ENDPOINTS ##########

@app.route('/create_profile', methods=['POST'])
def createprofile():
  first_name = request.form['first_name']
  last_name = request.form['last_name']
  phone_number = request.form['phone_number']
  password = request.form['password']
  
  CHECK_QUERY = """
    SELECT uid
    FROM Users
    WHERE phone_number = '{}'
  """.format(phone_number)

  check_for_dup = g.conn.execute(CHECK_QUERY)

  if int(check_for_dup.rowcount) != 0:
    return render_template('/create.html', duplicate=True)

  check_for_dup.close()

  largest_uid = g.conn.execute("""
    SELECT MAX(uid) as uid
    FROM Users
  """)

  uid = largest_uid.one()['uid']
  largest_uid.close()

  uid = int(uid) + 1

  g.conn.execute("""
    INSERT INTO Users(uid, first_name, last_name, phone_number, password)
    VALUES (%s, %s, %s, %s, %s)
  """, uid, first_name, last_name, phone_number, password)

  g.conn.execute("""
    INSERT INTO Hosts(uid, cheque_account)
    VALUES(%s, %s)
  """, uid, str_generator(6))

  g.conn.execute("""
    INSERT INTO Renters(uid, credit_card)
    VALUES(%s, %s)
  """, uid, str_generator(16))

  return redirect('/login')

@app.route('/login_user', methods=['POST', 'GET'])
def login_user():
  if request.method == "POST":
    phone_number = request.form['phone_number']
    password = request.form['password']

    CHECK_USER_STATUS = """
      SELECT uid
      FROM Users
      WHERE phone_number = '{}' AND password = '{}'
    """.format(phone_number, password)

    user = g.conn.execute(CHECK_USER_STATUS)

    try:
      uid = user.one()['uid']
      data = {'message': 'Logged In', 'code': 'SUCCESS', 'uid': uid}
      return make_response(jsonify(data), 200)
    except:
      data = {'message': 'No User Found', 'code': 'FAIL'}
      return make_response(jsonify(data), 401)

  return redirect("/login")

@app.route('/create_prop', methods=['POST'])
def create_prop():
  
  # will need to distinguish renter and
  uid_host = request.form['uid']
  
  addr = request.form['addr']
  city = request.form['city']
  state = request.form['state']
  postal_code = request.form['postal_code']
  size = request.form['size']
  has_swimming_pool = request.form.get('amenity1')
  has_gym = request.form.get('amenity2')
  
  largest_pid = g.conn.execute("""
    SELECT MAX(pid) as pid
    FROM Owned_Properties
  """)

  pid = largest_pid.one()['pid']
  largest_pid.close()

  pid = int(pid) + 1

  try:
    g.conn.execute("""
      INSERT INTO owned_properties(pid, size, uid_host) 
      VALUES (%s, %s, %s)
    """, pid, size, uid_host)
    try:
      g.conn.execute("""
        INSERT INTO locates_addresses(addr, city, state, postal_code, pid)
        VALUES (%s, %s, %s, %s, %s)
      """, addr, city, state, postal_code, pid)
    except:
      g.conn.execute("""
        DELETE FROM owned_properties WHERE pid = %s
      """, pid)
      
      data = {'message': 'Address filled wrongly or already exists', 'code': 'FAIL'}
      return make_response(jsonify(data), 401)      
  except: 
      data = {'message': 'Size is not valid', 'code': 'FAIL'}
      return make_response(jsonify(data), 401) 
    
  if has_swimming_pool:
    g.conn.execute("""
      INSERT INTO equip_amenities(pid, amenity_type) 
      VALUES (%s, %s)
    """, pid, 1)
  if has_gym:
    g.conn.execute("""
      INSERT INTO equip_amenities(pid, amenity_type) 
      VALUES (%s, %s)
    """, pid, 2) 
    
  g.conn.close()

  return redirect('/user?uid=' + uid_host)

@app.route('/calendar', methods=['GET'])
def calendar():
  return render_template('calendar.html') 

########## API ENDPOINTS ##########

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
