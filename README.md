# Easy Rental

This repository holds the Flask / Jinja stack with server.py serving SQL table queries from
REST API Endpoints. And the HTML with Jinja Templates and CSS files are in the templates folder.

## Application Summary

The application is a mockup of AirBnb using PostgreSQL Relational Database Schemas.
It consists of pages such as rentals, users, and property modals, and has functionalities like
create user, login user, create a property, set availabilities for a property, book a rental, and much more.

## Submission Information

1. PostgreSQL Account:
- username: hw2910
- password: 2608

2. Our deployment on GCP: http://34.75.2.5:8111/

3. Description 
- Implemented features as proposed
    - Hosts can check a number of properties they own, and manage them by addition and deletion (if it has not been rented out)
    - Hosts allow to add new availabilities or remove existing ones for the properties
    - Renters can book a rental online
    - Users can review their history as renters, while as hosts, they were only allowed to see existing availabilities changed if bookings are made 
    - Properties are created with associations of amenities, sizes and location
    - Current properties, they can be filtered/sorted in terms of amenities, sizes, and availabilities
- Unimplemented features although proposed
    - For properties that are listed, one can filter for properties within the zone (eg. state) they like. We decided this would not be a significant feature along our development, due to a small volume of data we have. 
- New features not included from proposal
    - A simple user login/sign up interface, so that visitors cannot book a property while being allowed to browse through the site

4. Two Interesting Pages and queries:
- rentals.html (main page)
    - **Filter/Sort Combined Parameters**: the rentals page requires a URL Parameters of multiple filter/sort categories in order to show it on the front end, including but not limited to start-end dates, amenity types and sizes, as well as order by property size ascending or descending.
    - This does not come from a AJAX call or a form, rather it is built into the URL, and server-side rendered.
    - So when a user clicks the submit button with a different filter, it fetches the rentals in appropriate filtered order thereafter.
    - There are more than 6 variables and filters in play, as modelled by our SQL logic can be seen in server.py.

- rentals.html (once clicked house picture) / user.html (profile page, and clicked an owned property)
    - **Property modal** 
        - An elegant window built on top of existing page where hosts can update availability and renters can book
    - **Booking Query** 
        - Check whether the start-end date is valid and available, and if so, books the user for the slot.
        - Also update the overall availabilities of the property. Say a renter only books an in-between dates within the current availability, then new availability would be spitted into piecewise date intervals.
        - The booking query is done through an AJAX call from a button on a property popup modal.
        - This function posts a /book endpoint with parameters of property id, start and end date. 
    - **Update Availability Query**
        - Availability operations for addition and deletion
        - Merge with the current availabilities for valid addition
        - Allow deletion of previous availabilities, as shown in the popup modal    
        - The update query is done through an AJAX call from a button on a property popup modal.
        - This function posts /add_availability or /remove_availability endpoint with parameters of property id, start and end date. 

## Installation

To get this project up and running on your local environment:

First, if you don't have postgresql installed on your OS, install brew (if you haven't already), then run:

```bash
  brew install postgresql
```

Then run:

```bash
  python3 -m venv venv
  . venv/bin/activate
  pip install flask
```

Then try running using

```bash
python3 server.py
```

if you are getting an error after this step, execute code below on terminal then try again:

```bash
pip install psycopg2
```

After this point, the server should get running, and you will be able to see the
HTML pages in the templates folder.

## API Reference

#### Pages

```http
  GET /
```

Returns index page with 4 rentals to show.

&nbsp;

```http
  GET /rentals
```

| Parameter  | Type      | Description                     |
| :--------- | :-------- | :------------------------------ |
| `from`     | `string`  | **Required**. Start Date Filter |
| `to`       | `string`  | **Required**. End Date Filter   |
| `order_by` | `string`  | **Required**. Order Category    |
| `sort_by`  | `string`  | **Required**. ASC or DESC       |
| `amenity1` | `boolean` | Swimming Pool inclusion         |
| `amenity2` | `boolean` | Gym inclusion                   |

Returns the rental page with filters enabled

&nbsp;

```http
  GET /login
```

Returns the login form page

&nbsp;

```http
  GET /create
```

Returns the create user form page

&nbsp;

```http
  GET /user
```

| Parameter | Type     | Description           |
| :-------- | :------- | :-------------------- |
| `uid`     | `string` | **Required**. User ID |

Returns the user page with uid specified in parameter

&nbsp;

#### API References

```http
  GET /available_times
```

| Parameter | Type     | Description               |
| :-------- | :------- | :------------------------ |
| `pid`     | `string` | **Required**. Property ID |

Get's all available times for a particular property

&nbsp;

```http
  POST /create_profile
```

| Parameter      | Type     | Description                |
| :------------- | :------- | :------------------------- |
| `first_name`   | `string` | **Required**.First Name    |
| `last_name`    | `string` | **Required**. Last Name    |
| `phone_number` | `string` | **Required**. Phone Number |
| `password`     | `string` | **Required**. Password     |

Create's a user profile with parameters above

&nbsp;

```http
  POST /login_user
```

| Parameter      | Type     | Description                |
| :------------- | :------- | :------------------------- |
| `phone_number` | `string` | **Required**. Phone Number |
| `password`     | `string` | **Required**. Password     |

Log's in user if parameters are correct

&nbsp;

```http
  POST /create_prop
```

| Parameter  | Type      | Description                 |
| :--------- | :-------- | :-------------------------- |
| `uid`      | `string`  | **Required**. User ID       |
| `addr`     | `string`  | **Required**. Address       |
| `city`     | `string`  | **Required**. City          |
| `state`    | `string`  | **Required**. State         |
| `size`     | `string`  | **Required**. Property Size |
| `amenity1` | `boolean` | Swimming Pool               |
| `amenity2` | `boolean` | Gym                         |

Creates a property under a certain user's id

&nbsp;

```http
  POST /delete_prop
```

| Parameter | Type     | Description               |
| :-------- | :------- | :------------------------ |
| `pid`     | `string` | **Required**. Property ID |

Deletes a property

&nbsp;

```http
  POST /add_availability
```

| Parameter    | Type     | Description               |
| :----------- | :------- | :------------------------ |
| `pid`        | `string` | **Required**. Property ID |
| `start_from` | `string` | **Required**. Start Date  |
| `end_at`     | `string` | **Required**. End Date    |

Creates an availability row for a particular property

&nbsp;

```http
  POST /remove_availability
```

| Parameter    | Type     | Description               |
| :----------- | :------- | :------------------------ |
| `pid`        | `string` | **Required**. Property ID |
| `start_from` | `string` | **Required**. Start Date  |
| `end_at`     | `string` | **Required**. End Date    |

Removes an availability row for a particular property

&nbsp;

```http
  POST /book
```

| Parameter    | Type     | Description                    |
| :----------- | :------- | :----------------------------- |
| `pid`        | `string` | **Required**. Property ID      |
| `uid_host`   | `string` | **Required**. Host's User ID   |
| `uid_renter` | `string` | **Required**. Renter's User ID |
| `start_from` | `string` | **Required**. Start Date       |
| `end_at`     | `string` | **Required**. End Date         |

Book's a rental slot for someone else's property under their available times

## AJAX Calls from Front End

    1. index.html / line 176:
    - /available_times GET AJAX call. Get's all available times for a property.
      on success, appends html to the page showing available times.
    
    2. index.html / line 244:
    - /book POST AJAX call, for when a user books a rental.
      Reloads on successful book.
    
    3. login.html / line 50:
    - /login_user POST AJAX call, for logging in a user.
      Redirects to the user page after successful 200 status.
    
    4. rentals.html / line 215:
    - /available_times GET AJAX call. Get's all available times for a property.
      on success, appends html to the page showing available times.
    
    5. rentals.html / line 283:
    - /book POST AJAX call, for when a user books a rental.
      Reloads on successful book.
    
    6. user.html / line 204:
    - /book POST AJAX call, for when a user books a rental.
      Reloads on successful book.
    
    7. user.html / line 220:
    - /delete_prop POST AJAX call, remove's a user's property
      Reloads page on success.
    
    8. user.html / line 348:
    - /available_times GET AJAX call. Get's all available times for a property.
      on success, appends html to the page showing available times.
    
    9. user.html / line 399:
    - /remove_availability POST AJAX call. Removes a particular availability from a property.
      Removes the HTML for the removed available time on success.
