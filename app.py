import datetime
from flask import Flask, config, render_template, request, redirect, send_from_directory, session,  url_for
import mysql.connector
import os
from datetime import datetime 

app = Flask(__name__)
app.secret_key = 'your_secret_key'
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Database Connection

def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='Harish@9494',
        database='car_rental_db'
    )
conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='Harish@9494',
    database='car_rental_db'
)

cursor = conn.cursor()

@app.route('/')
def index():
    return redirect(url_for('login'))
# Signup Route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        role = request.form['role']
        
        if password != confirm_password:
            return "Passwords do not match!"
        
        cursor.execute("INSERT INTO users (username, email, password, role) VALUES (%s, %s, %s, %s)",
                       (username, email, password, role))
        conn.commit()
        return redirect('/login')
    return render_template('signup.html')

# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        cursor.execute("SELECT * FROM users WHERE email=%s AND password=%s", (email, password))
        user = cursor.fetchone()
        
        if user:
            session['user_id'] = user[0]
            session['role'] = user[4]
            
            if user[4] == 'admin':
                return redirect('/admin_home')
            else:
                return redirect('/customer_home')
        else:
            return "Invalid Credentials!"
    return render_template('login.html')

# Admin Home
@app.route('/admin_home')
def admin_home():
    if 'role' in session and session['role'] == 'admin':
        cursor.execute("SELECT * FROM cars")
        cars = cursor.fetchall()
        return render_template('admin_home.html', cars=cars)
    return redirect('/login')

# Add Car Route (With Image Upload)
@app.route('/add_car', methods=['GET', 'POST'])
def add_car():
    if 'role' in session and session['role'] == 'admin':
        if request.method == 'POST':
            car_name = request.form['car_name']
            brand_name = request.form['brand_name']
            model_year = request.form['model_year']
            color = request.form['color']
            transmission = request.form['transmission']
            price = request.form['price']

            # Handle Image Upload
            image = request.files['image']
            if image:
                image_filename = f"{car_name}_{brand_name}.jpg"
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
                image.save(image_path)
            else:
                image_filename = "default.jpg"  # Fallback image

            cursor.execute("INSERT INTO cars (car_name, brand_name, image, model_year, color, transmission, price) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                           (car_name, brand_name, image_filename, model_year, color, transmission, price))
            conn.commit()
            return redirect('/admin_home')
        return render_template('add_car.html')
    return redirect('/login')

# Route to Serve Uploaded Images
@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# Update & Delete Car
@app.route('/update_car/<int:car_id>', methods=['GET', 'POST'])
def update_car(car_id):
    if 'role' in session and session['role'] == 'admin':
        if request.method == 'POST':
            car_name = request.form['car_name']
            brand_name = request.form['brand_name']
            image = request.form['image']
            model_year = request.form['model_year']
            color = request.form['color']
            transmission = request.form['transmission']
            price = request.form['price']
            
            cursor.execute("UPDATE cars SET car_name=%s, brand_name=%s, image=%s, model_year=%s, color=%s, transmission=%s, price=%s WHERE id=%s", 
                           (car_name, brand_name, image, model_year, color, transmission, price, car_id))
            conn.commit()
            return redirect('/admin_home')
        cursor.execute("SELECT * FROM cars WHERE id=%s", (car_id,))
        car = cursor.fetchone()
        return render_template('update_car.html', car=car)
    return redirect('/login')

@app.route('/delete_car/<int:car_id>')
def delete_car(car_id):
    if 'role' in session and session['role'] == 'admin':
        cursor.execute("DELETE FROM cars WHERE id=%s", (car_id,))
        conn.commit()
        return redirect('/admin_home')
    return redirect('/login')

@app.route('/view_customers')
def view_customers():
    if 'role' in session and session['role'] == 'admin':
        db_config = {
            'host': 'localhost',
            'user': 'root',
            'password': 'Harish@9494',
            'database': 'car_rental_db'
        }
        
        connection = mysql.connector.connect(**db_config)  # Correct usage of **db_config
        cursor = connection.cursor(dictionary=True)
        cursor.execute('SELECT username, email FROM users WHERE role = "customer"')
        customers = cursor.fetchall()
        cursor.close()
        connection.close()
        return render_template('view_customers.html', customers=customers)
    
    return redirect(url_for('login'))


# Bookings Management
@app.route('/bookings')
def bookings():
    if 'role' in session and session['role'] == 'admin':
        cursor.execute("SELECT * FROM bookings")
        bookings = cursor.fetchall()
        return render_template('bookings.html', bookings=bookings)
    return redirect('/login')

# Search Cars
@app.route('/search', methods=['GET', 'POST'])
def search():
    if 'role' in session and session['role'] == 'admin':
        if request.method == 'POST':
            brand_name = request.form.get('brand_name', '')
            car_name = request.form.get('car_name', '')
            transmission = request.form.get('transmission', '')
            model_year = request.form.get('model_year', '')
            color = request.form.get('color', '')
            
            query = "SELECT * FROM cars WHERE 1=1"
            params = []
            
            if brand_name:
                query += " AND brand_name LIKE %s"
                params.append(f'%{brand_name}%')
            if car_name:
                query += " AND car_name LIKE %s"
                params.append(f'%{car_name}%')
            if transmission:
                query += " AND transmission LIKE %s"
                params.append(f'%{transmission}%')
            if model_year:
                query += " AND model_year LIKE %s"
                params.append(f'%{model_year}%')
            if color:
                query += " AND color LIKE %s"
                params.append(f'%{color}%')
            
            cursor.execute(query, tuple(params))
            cars = cursor.fetchall()
            return render_template('search_results.html', cars=cars)
        
        return render_template('search.html')
    
    return redirect('/login')

# Customer Search
@app.route('/customer_search', methods=['GET', 'POST'])
def customer_search():
    if 'role' in session and session['role'] == 'customer':
        if request.method == 'POST':
            brand_name = request.form.get('brand_name', '')
            car_name = request.form.get('car_name', '')
            transmission = request.form.get('transmission', '')
            model_year = request.form.get('model_year', '')
            color = request.form.get('color', '')
            
            query = "SELECT * FROM cars WHERE 1=1"
            params = []
            
            if brand_name:
                query += " AND brand_name LIKE %s"
                params.append(f'%{brand_name}%')
            if car_name:
                query += " AND car_name LIKE %s"
                params.append(f'%{car_name}%')
            if transmission:
                query += " AND transmission LIKE %s"
                params.append(f'%{transmission}%')
            if model_year:
                query += " AND model_year LIKE %s"
                params.append(f'%{model_year}%')
            if color:
                query += " AND color LIKE %s"
                params.append(f'%{color}%')
            
            cursor.execute(query, tuple(params))
            cars = cursor.fetchall()
            return render_template('customer_search_results.html', cars=cars)
        
        return render_template('customer_search.html')
    
    return redirect('/login')





# Customer Home
@app.route('/customer_home')
def customer_home():
    if 'role' in session and session['role'] == 'customer':
        cursor.execute("SELECT * FROM cars")
        cars = cursor.fetchall()
        return render_template('customer_home.html', cars=cars)
    return redirect('/login')

# Book a Car
@app.route('/book_car/<int:car_id>', methods=['GET', 'POST'])
def book_car(car_id):
    if 'role' in session and session['role'] == 'customer':
        if request.method == 'POST':
            start_date = request.form['start_date']
            end_date = request.form['end_date']
            customer_id = session['user_id']
            
            cursor.execute("SELECT price FROM cars WHERE id=%s", (car_id,))
            price_per_day = cursor.fetchone()[0]
            
            days = (datetime.strptime(end_date, "%Y-%m-%d") - datetime.strptime(start_date, "%Y-%m-%d")).days
            total_price = price_per_day * days
            
            cursor.execute("INSERT INTO bookings (customer_id, car_id, start_date, end_date, total_price, status) VALUES (%s, %s, %s, %s, %s, %s)",
                           (customer_id, car_id, start_date, end_date, total_price, 'Pending'))
            conn.commit()
            return redirect('/mybookings')
        cursor.execute("SELECT * FROM cars WHERE id=%s", (car_id,))
        car = cursor.fetchone()
        return render_template('book_car.html', car=car)
    return redirect('/login')

@app.route('/mybookings')
def mybookings():
    if 'user_id' in session:
        customer_id = session['user_id']
        
        # Fetch only bookings for the logged-in customer
        cursor.execute("SELECT bookings.id, users.username, cars.car_name, cars.brand_name, bookings.start_date, bookings.end_date, bookings.total_price, bookings.status FROM bookings JOIN users ON bookings.customer_id = users.id JOIN cars ON bookings.car_id = cars.id WHERE bookings.customer_id = %s", (customer_id,))
        mybookings = cursor.fetchall()
        
        print("Fetched MyBookings:", mybookings)  # Debugging line

        return render_template('mybookings.html', mybookings=mybookings)

    return redirect('/login')


@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        email = request.form['email']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if new_password != confirm_password:
            return "Passwords do not match"

        connection = get_db_connection()
        cursor = connection.cursor()
        try:
            cursor.execute(
                'UPDATE users SET password = %s WHERE email = %s',
                (new_password, email)
            )
            connection.commit()
        except mysql.connector.Error as e:
            return f"An error occurred: {e}"
        finally:
            connection.close()

        return "Password reset successfully"

    return render_template('reset_password.html')


# Admin Booking Management
@app.route('/admin_bookings')
def admin_bookings():
    if 'role' in session and session['role'] == 'admin':
        cursor.execute("SELECT bookings.id, users.username, cars.car_name, cars.brand_name, bookings.start_date, bookings.end_date, bookings.total_price, bookings.status FROM bookings JOIN users ON bookings.customer_id = users.id JOIN cars ON bookings.car_id = cars.id")
        bookings = cursor.fetchall()
        return render_template('admin_bookings.html', bookings=bookings)
    return redirect('/login')

@app.route('/update_booking/<int:booking_id>/<status>')
def update_booking(booking_id, status):
    if 'role' in session and session['role'] == 'admin':
        if status in ["Approved", "Rejected"]:
            cursor.execute("UPDATE bookings SET status = %s WHERE id = %s", (status, booking_id))
            conn.commit()
    return redirect('/bookings')  # Redirect back to bookings page




# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)
