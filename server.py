import os
from sqlalchemy import *
import datetime
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, jsonify, make_response, after_this_request
import string
import random
import logging
from datetime import datetime, timedelta

tmpl_dir = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)

s_user = os.environ.get('USERNAME')
s_pass = os.environ.get('PASSWORD')

DATABASEURI = f"postgresql://hw2910:2608@34.75.94.195/proj1part2"
engine = create_engine(DATABASEURI)

@app.before_request
def before_request():
    try:
        g.conn = engine.connect()
    except:
        print("uh oh, problem connecting to database")
        import traceback
        traceback.print_exc()
        g.conn = None

@app.teardown_request
def teardown_request(exception):
    try:
        g.conn.close()
    except Exception as e:
        pass

########## URIS ##########

# Home page
@app.route('/')
def index():
    uid = request.args.get("uid")
    if not uid: uid = 0 # sanity check
    
    FEATURED_RENTALS = """
    SELECT DISTINCT on (P.pid) P.pid, size, uid_host, start_date, end_date, first_name, last_name, addr, city, state, postal_code 
    FROM owned_properties P, is_available A, locates_addresses L, Users U
    WHERE P.pid = A.pid AND L.pid = P.pid AND U.uid = P.uid_host AND P.uid_host <> '{}'
    LIMIT 4;
  """.format(uid)

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

# List of rentings page 
@app.route('/rentals')
def rentals():
    uid = request.args.get("uid")
    if not uid: uid = 0 # sanity check
    start_from = request.args.get("from")
    end_at = request.args.get("to")
    order_by = request.args.get("order_by")
    sort_by = request.args.get("sort_by")
    has_swimming_pool = request.args.get('amenity1') == "true"
    has_gym = request.args.get('amenity2') == "true"

    MIN_FROM = """
    SELECT MIN(start_date) as start_date 
    FROM is_available
  """

    MAX_TO = """
    SELECT MAX(end_date) as end_date 
    FROM is_available
  """

    # Hideous filtering for amenity
    if not has_swimming_pool and not has_gym:
        RENTALS = """
      Select DISTINCT ON(P.{}) P.pid, size, uid_host, start_date, end_date, first_name, last_name, addr, city, state, postal_code
      FROM owned_properties P, is_available A, locates_addresses L, Users U
      WHERE P.pid = A.pid AND L.pid = P.pid AND U.uid = P.uid_host AND A.start_date >= '{}' AND A.end_date <= '{}' AND P.uid_host <> '{}'
      ORDER BY P.{} {}
      """.format(order_by, start_from, end_at, uid, order_by, sort_by)
    elif has_swimming_pool and has_gym:
        RENTALS = """
      Select DISTINCT ON(P.{}) P.pid, size, uid_host, start_date, end_date, first_name, last_name, addr, city, state, postal_code
      FROM owned_properties P, is_available A, locates_addresses L, Users U, equip_amenities E1,  equip_amenities E2
      WHERE P.pid = A.pid AND L.pid = P.pid AND U.uid = P.uid_host AND A.start_date >= '{}' AND A.end_date <= '{}' AND P.uid_host <> '{}'
      AND E1.pid = P.pid AND E1.amenity_type = 1 AND E2.amenity_type = 2 AND E1.pid = E2.pid
      ORDER BY P.{} {}
      """.format(order_by, start_from, end_at, uid, order_by, sort_by)
    elif has_swimming_pool:
        RENTALS = """
      Select DISTINCT ON(P.{}) P.pid, size, uid_host, start_date, end_date, first_name, last_name, addr, city, state, postal_code
      FROM owned_properties P, is_available A, locates_addresses L, Users U, equip_amenities E
      WHERE P.pid = A.pid AND L.pid = P.pid AND U.uid = P.uid_host AND A.start_date >= '{}' AND A.end_date <= '{}' AND P.uid_host <> '{}'
      AND E.pid = P.pid AND amenity_type = 1
      ORDER BY P.{} {}
      """.format(order_by, start_from, end_at, uid, order_by, sort_by)
    else:
        RENTALS = """
      Select DISTINCT ON(P.{}) P.pid, size, uid_host, start_date, end_date, first_name, last_name, addr, city, state, postal_code
      FROM owned_properties P, is_available A, locates_addresses L, Users U, equip_amenities E
      WHERE P.pid = A.pid AND L.pid = P.pid AND U.uid = P.uid_host AND A.start_date >= '{}' AND A.end_date <= '{}' AND P.uid_host <> '{}'
      AND E.pid = P.pid AND amenity_type = 2
      ORDER BY P.{} {}
      """.format(order_by, start_from, end_at, uid, order_by, sort_by)

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

# User login
@app.route('/login')
def login():
    return render_template("login.html")

# User sign up
@app.route('/create')
def create():
    return render_template("create.html", duplicate=False, error=False)

# User profile 
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

        USER_PROP_QUERY = g.conn.execute("""
      SELECT U.addr, U.city, U.state, U.postal_code, U.pid
      FROM (
        SELECT addr, city, state, postal_code, P.pid as pid
        FROM owned_properties P, locates_addresses A
        WHERE P.uid_host = {} AND A.pid = P.pid
      ) as U
    """.format(uid))

        RECORD_QUERY = g.conn.execute("""
      SELECT R.pid, from_date, to_date, L.addr, L.city, L.state
      FROM record R, locates_addresses L
      WHERE uid_renter = %s AND R.pid = L.pid
    """, uid)

        try:
            prop_info = USER_PROP_QUERY.all()
            user_props = []
            for info in prop_info:
                user_props.append(info)

            USER_PROP_QUERY.close()

            record = []
            for rec in RECORD_QUERY:
                record.append(rec)

            return render_template("user.html", user=user, user_props=user_props, record=record)

        except:
            logging.exception("")
            return render_template('405.html')

    except:
        logging.exception('')
        return render_template('405.html')

########## URIS ##########

########## API ENDPOINTS ##########

# Get current availability
@app.route('/available_times', methods=['GET'])
def available_times():
    try:
        pid = request.args.get('pid')

        current_availability = get_curr_availability(pid)
        tmp = list(map(list, current_availability))

        data = {'message': 'TIMES FETCHED', 'code': 'SUCCESS', 'times': tmp}
        return make_response(jsonify(data), 200)
    except:
        logging.exception("")
        data = {'message': 'FAILED FETCH', 'code': 'FAIL'}
        return make_response(jsonify(data), 404)

# User creation
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

# Login authentication 
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

# Property creation
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

            data = {
                'message': 'Address filled wrongly or already exists', 'code': 'FAIL'}
            return make_response(jsonify(data), 401)
    except:
        logging.exception('')
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

# Property deletion
@app.route('/delete_prop', methods=['POST'])
def delete_prop():
    pid = request.form['pid']

    # Need show response msg on front end

    try:
        g.conn.execute("""
      DELETE FROM owned_properties WHERE pid = %s
    """, pid)
        data = {'message': 'delete prop successful', 'code': 'SUCCESS'}
        return make_response(jsonify(data), 200)

    except:
        data = {
            'message': 'delete prop fail: since it has been rented to someone', 'code': 'FAIL'}
        return make_response(jsonify(data), 200)

# Add availability
@app.route('/add_availability', methods=["POST"])
# will need to know which prop (pid) for host
def add_availability():
    pid = request.form.get("pid")
    start_from = request.form.get("start_from")
    end_at = request.form.get("end_at")

    start_from = datetime.strptime(start_from, '%Y-%m-%d').date()
    end_at = datetime.strptime(end_at, '%Y-%m-%d').date()

    # check user input actually affect the rental dates
    rental_dates = get_rental_dates(pid)
    tmp = list(map(list, rental_dates))
    tmp.append([start_from, end_at])

    new_rental_dates = remove_availability_helper(tmp, [start_from, end_at])
    rental_dates = list(map(list, rental_dates))

    if rental_dates != new_rental_dates:
        data = {
            'message': ' update availability fail: conflict rental dates from other users', 'code': 'FAIL'}
        return make_response(jsonify(data), 200)

    # check if user input actually change the current_availability
    current_availability = get_curr_availability(pid)
    tmp = list(map(list, current_availability))
    tmp.append([start_from, end_at])

    new_availability = add_availability_helper(tmp)
    current_availability = list(map(list, current_availability))

    if new_availability == current_availability:
        data = {'message': ' update availability fail: invalid input', 'code': 'FAIL'}
        return make_response(jsonify(data), 200)
    else:
        modify_availability(new_availability, pid)
        g.conn.close()
        data = {'message': ' update availability successful', 'code': 'SUCCESS'}
        return make_response(jsonify(data), 200)

    # redirect('/user?uid=' + uid)

# Remove availability
@app.route('/remove_availability', methods=['POST'])
# will need to know which prop (pid) for host
def remove_availability():
    pid = request.form.get("pid")
    start_from = request.form.get("start_from")
    end_at = request.form.get("end_at")

    start_from = datetime.strptime(
        start_from, '%a, %d %b %Y %H:%M:%S %Z').date()
    end_at = datetime.strptime(end_at, '%a, %d %b %Y %H:%M:%S %Z').date()

    current_availability = get_curr_availability(pid)
    tmp = list(map(list, current_availability))

    new_availability = remove_availability_helper(tmp, [start_from, end_at])
    current_availability = list(map(list, current_availability))

    # check if user input actually change the current_availability
    if new_availability == current_availability:
        data = {'message': ' remove availability fail: invalid input', 'code': 'FAIL'}
        return make_response(jsonify(data), 200)
    else:
        modify_availability(new_availability, pid)
        g.conn.close()
        data = {'message': ' remove availability successful', 'code': 'SUCCESS'}
        return make_response(jsonify(data), 200)

    # redirect('/user?uid=' + uid)

# Book function
@app.route('/book', methods=["POST"])
# will need to know which prop (pid) for renter
# prop owner should not be able to book his prop, could hide it from public listing of props
def book():
    largest_transcation_id = g.conn.execute("""
    SELECT MAX(transcation_id) as transcation_id
    FROM record
  """)

    transcation_id = largest_transcation_id.one()['transcation_id']
    largest_transcation_id.close()
    transcation_id = int(transcation_id) + 1

    uid_host = request.form['uid_host']
    uid_renter = request.form["uid_renter"]
    pid = request.form["pid"]
    start_from = request.form["start_from"]
    end_at = request.form["end_at"]

    print(uid_host, uid_renter, pid, start_from, end_at)

    # check for legit book
    CAN_BOOK = g.conn.execute(
        """
    SELECT start_date, end_date
    FROM is_available
    WHERE pid = '{}' AND start_date <= '{}' AND '{}' <= end_date
    """.format(pid, start_from, end_at))
    between_interval = CAN_BOOK.all()
    CAN_BOOK.close()

    if len(between_interval) != 1:
        data = {
            'message': ' booking fail: invalid input', 'code': 'FAIL'}
        return make_response(jsonify(data), 200)

    # remove logic like above
    start_from = datetime.strptime(start_from, '%Y-%m-%d').date()
    end_at = datetime.strptime(end_at, '%Y-%m-%d').date() - timedelta(days=1)

    current_availability = get_curr_availability(pid)
    tmp = list(map(list, current_availability))

    new_availability = remove_availability_helper(tmp, [start_from, end_at])
    current_availability = list(map(list, current_availability))

    # check if user input actually change the current_availability
    if new_availability == current_availability:
        data = {
            'message': ' booking fail: invalid input', 'code': 'FAIL'}
        return make_response(jsonify(data), 200)
    else:
        modify_availability(new_availability, pid)
        
    try:
      g.conn.execute("""
      INSERT INTO record (uid_host, uid_renter, pid, transcation_id, from_date, to_date)
      VALUES (%s, %s, %s, %s, %s, %s)
      """, uid_host, uid_renter, pid, transcation_id, start_from, end_at)
    except:
      try:
        g.conn.execute("""
        INSERT INTO rent_to (uid_host, uid_renter, pid)
        VALUES (%s, %s, %s)
      """, uid_host, uid_renter, pid)

        g.conn.execute("""
        INSERT INTO record (uid_host, uid_renter, pid, transcation_id, from_date, to_date)
        VALUES (%s, %s, %s, %s, %s, %s)
      """, uid_host, uid_renter, pid, transcation_id, start_from, end_at)
      except:
        data = {'message': ' BOOK fail', 'code': 'FAIL'}
        return make_response(jsonify(data), 200)

    g.conn.close()

    data = {'message': ' BOOK successful', 'code': 'SUCCESS'}
    return make_response(jsonify(data), 200)
    # return redirect('/')

# merge interval helper
def add_availability_helper(intervals):
    res = []
    for i in sorted(intervals):
        if res and i[0] <= res[-1][1]:
            res[-1][1] = max(res[-1][1], i[1])
        else:
            res.append(i)
    return res

# remove interval helper
def remove_availability_helper(intervals, target):
    left, right = target
    return [[x, y] for a, b in intervals for x, y in ((a, min(b, left)), (max(a, right), b)) if x < y]

# Reinsertion of availability helper
def modify_availability(intervals, pid):
    g.conn.execute(
        """
    DELETE FROM is_available WHERE pid = '{}'
    """.format(pid))

    for start_date, end_date in intervals:
        g.conn.execute("""
      INSERT INTO is_available(start_date, end_date, pid)
      VALUES (%s, %s, %s)
    """, start_date, end_date, pid)

    # g.conn.close()

# Get current availability helper
def get_curr_availability(pid):
    AVAILABILITY_BY_PID = g.conn.execute(
        """
    SELECT start_date, end_date
    FROM is_available
    WHERE pid = '{}' ORDER BY start_date, end_date
    """.format(pid))

    res = AVAILABILITY_BY_PID.all()
    AVAILABILITY_BY_PID.close()
    return res

# Get exisiting rental dates that other booked
def get_rental_dates(pid):
    RENTAL_DATES_BY_PID = g.conn.execute(
        """
    SELECT from_date, to_date
    FROM record
    WHERE pid = '{}' ORDER BY from_date, from_date
    """.format(pid))

    res = RENTAL_DATES_BY_PID.all()
    RENTAL_DATES_BY_PID.close()
    return res
  
# Random generator for CHEQUE_ACCOUNT, CREDIT_CARD for simplicity, instead of asking for fake input
def str_generator(size, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

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
