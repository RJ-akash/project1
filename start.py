from flask import Flask, render_template, redirect, url_for, request
from windows_tools.installed_software import get_installed_software
from flask import jsonify
import pymysql
import schedule
import time
import psutil
from datetime import datetime


app = Flask(__name__)

# MySQL database connection
connection = pymysql.connect(host='127.0.0.5', user='root', password='akash0920', database='soft')
cursor = connection.cursor(pymysql.cursors.DictCursor)


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
                connection.commit()

# Schedule the task to run every 5 minutes
schedule.every(5).minutes.do(scheduled_task)

# Route for scanning and inserting into MySQL
@app.route('/')
def scanning():
    # Get installed software and insert into MySQL
    for software in get_installed_software():
        name = software['name']
        version = software['version']
        publisher = software['publisher']
        # Insert into MySQL
        dbconnection(name, version, publisher)

    # Redirect to page1.html after scanning is complete
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
    return render_template('page1.html', software_list=software_list, publishers=publishers)

if __name__ == '__main__':
    app.run(debug=True)


