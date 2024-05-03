from flask import Flask, render_template, redirect, url_for, request
from windows_tools.installed_software import get_installed_software
import pymysql
import schedule
import socket
import time
import platform
import psutil

app = Flask(__name__)

# MySQL database connection
global connection;
connection = pymysql.connect(host='127.0.0.5', user='root', password='akash0920', database='soft')
cursor = connection.cursor(pymysql.cursors.DictCursor)
if connection:
    print("Connection established successfully!")
else:
    print("Failed to establish connection!")

def dbconnection(name, version, publisher):
    # Check if the record already exists
    select_query = "SELECT * FROM soft WHERE NAME = %s AND VERSION = %s AND PUBLISHER = %s"
    cursor.execute(select_query, (name, version, publisher))
    existing_record = cursor.fetchone()

    if not existing_record:
        # If the record does not exist, insert into MySQL
        insert_query = "INSERT INTO soft (NAME, VERSION, PUBLISHER) VALUES (%s, %s, %s)"
        cursor.execute(insert_query, (name, version, publisher))
        connection.commit()

def scheduled_task():
    installed_software = [software['name'] for software in get_installed_software()]
    for software in get_installed_software():
        name = software['name']
        version = software['version']
        publisher = software['publisher']
        # Insert into MySQL
        dbconnection(name, version, publisher)

        # Delete records from the database if the software is not installed
        cursor.execute("SELECT SI, NAME, VERSION, PUBLISHER FROM soft")
        existing_records = cursor.fetchall()
        for record in existing_records:
            if record not in installed_software:
                delete_query = "DELETE FROM soft WHERE NAME = %s AND VERSION = %s AND PUBLISHER = %s"
                cursor.execute(delete_query, (record['name'], record['version'], record['publisher']))
                dbconnection.commit()


# Schedule the task to run every 5 minutes
schedule.every(1).minute.do(scheduled_task)



# Function to save system information to the database
def save_system_info():
    my_system = platform.uname()

    # Insert system information into the database
    cursor.execute("""
        INSERT INTO system_info (system_name, node, release_name, version, machine, processor) 
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (my_system.system, my_system.node, my_system.release, my_system.version, my_system.machine, my_system.processor))
    connection.commit()

# Disk Information retrieval function
def get_disk_information():
    disk_info = []
    partitions = psutil.disk_partitions()
    for partition in partitions:
        try:
            partition_usage = psutil.disk_usage(partition.mountpoint)
        except PermissionError:
            continue
        disk_info.append({
            'device': partition.device,
            'mountpoint': partition.mountpoint,
            'fstype': partition.fstype,
            'total_size': partition_usage.total / (1024 ** 3),
            'used_size': partition_usage.used / (1024 ** 3),
            'free_size': partition_usage.free / (1024 ** 3),
            'percentage': partition_usage.percent
        })
    return disk_info

# Insert disk information into the database
def insert_disk_info_into_db():
    disk_info = get_disk_information()

    # Delete old records from the storage table
    cursor.execute("DELETE FROM storage")

    connection.commit()
    for info in disk_info:
        cursor.execute("""
            INSERT INTO storage (device, mountpoint, fstype, total_size, used_size, free_size, percentage)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            info['device'],
            info['mountpoint'],
            info['fstype'],
            info['total_size'],
            info['used_size'],
            info['free_size'],
            info['percentage']
        ))
        connection.commit()

# Route for accessing cmdb.html and redirecting to msi.html
@app.route('/')
def cmdb():
    return render_template('cmdb.html')
# Route to render laptop.html
@app.route('/laptop')
def laptop():
    return render_template('laptop.html')

# Route to render document.html
@app.route('/document')
def document():
    return render_template('document.html')
# Route to render msi.html
@app.route('/msi')
def msi():
    return render_template('msi.html')

# Route for scanning and inserting into MySQL
@app.route('/scanning')
def scanning():
    # Get installed software and insert into MySQL
    for software in get_installed_software():
        name = software['name']
        version = software['version']
        publisher = software['publisher']
        # Insert into MySQL
        dbconnection(name, version, publisher)
    # Redirect to software_info.html after scanning is complete
    return redirect(url_for('display_installed_software'))

def scanning1():
    # Get installed software and insert into MySQL
    for software in get_installed_software():
        name = 'joe'
        version = '899'
        publisher = software['publisher']
        # Insert into MySQL
        dbconnection(name, version, publisher)
    # Redirect to software_info.html after scanning is complete
    return redirect(url_for('display_installed_software'))








# Route for displaying installed software with filter and search options
@app.route('/Scanning', methods=['GET', 'POST'])
def display_installed_software():
    # Handle filter and search form submission
    if request.method == 'POST':
        selected_publisher = request.form.get('publisher')
        search_value = request.form.get('search')
        if selected_publisher:
            # Filter by publisher
            cursor.execute("SELECT * FROM soft WHERE PUBLISHER = %s ORDER BY SI ASC, NAME", (selected_publisher,))
            software_list = cursor.fetchall()
        elif search_value:
            # Search for similar records in the name column
            cursor.execute("SELECT * FROM soft WHERE NAME LIKE %s ORDER BY SI ASC, NAME", (search_value + '%',))
            software_list = cursor.fetchall()
        else:
            # Display all records when no filter or search is applied
            cursor.execute("SELECT * FROM soft ORDER BY SI ASC, NAME")
            software_list = cursor.fetchall()
    else:
        # Display all records when no form submission
        cursor.execute("SELECT * FROM soft ORDER BY SI ASC, NAME")
        software_list = cursor.fetchall()

    # Get unique publishers for the filter dropdown
    cursor.execute("SELECT DISTINCT PUBLISHER FROM soft")
    publishers = [row['PUBLISHER'] for row in cursor.fetchall()]

    # Close the cursor and connection after executing all queries
    return render_template('software_info.html', software_list=software_list, publishers=publishers)

# Route for displaying storage information
@app.route('/storage')
def display_storage_info():
    # Insert disk information into the database
    insert_disk_info_into_db()

    # Retrieve stored storage information from the database
    cursor.execute("SELECT * FROM storage")
    storage_info = cursor.fetchall()

    return render_template('storage_info.html', storage_info=storage_info)

@app.route('/user')
def display_user_info():
    # Fetch system information
    my_system = platform.uname()

    # Save system information to the database
    save_system_info()

    computer_name = socket.gethostname()
    ipadd = socket.gethostbyname(computer_name)
    return render_template('user_info.html', computer_name=computer_name, ipadd=ipadd, system_info=my_system)

if __name__ == '__main__':
    app.run(debug=True)


