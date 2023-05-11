from flask import Flask, render_template, request
from pymysql import connections
import os
import boto3
from config import *
import pymysql.cursors
from jinja2 import Environment, FileSystemLoader

app = Flask(__name__)

bucket = custombucket
region = customregion

db_conn = connections.Connection(
    host=customhost,
    port=3306,
    user=customuser,
    password=custompass,
    db=customdb

)
output = {}
table = 'employee'

# Create connection to S3 bucket
s3 = boto3.resource('s3')
bucket_name = 'leongshengmou-employee'
bucket = s3.Bucket(bucket_name)


@app.route("/", methods=['GET', 'POST'])
def home():
    return render_template('frontpage.html')

@app.route('/AddEmp.html')
def add_emp_page():
    return render_template('AddEmp.html')

@app.route('/GetEmp.html')
def getEmp():
    return render_template('/GetEmp.html')

@app.route("/about", methods=['POST'])
def about():
    return render_template('www.intellipaat.com')


@app.route("/addemp", methods=['POST'])
def AddEmp():
    emp_id = request.form['emp_id']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    gender = request.form['gender']
    pri_skill = request.form['pri_skill']
    location = request.form['location']
    emp_image_file = request.files['emp_image_file']

    insert_sql = "INSERT INTO employee VALUES (%s, %s, %s, %s, %s, %s)"
    cursor = db_conn.cursor()

    if emp_image_file.filename == "":
        return "Please select a file"

    try:

        cursor.execute(insert_sql, (emp_id, first_name, last_name, gender, pri_skill, location))
        db_conn.commit()
        emp_name = "" + first_name + " " + last_name
        # Uplaod image file in S3 #
        emp_image_file_name_in_s3 = "emp-id-" + str(emp_id) + "_image_file"
        s3 = boto3.resource('s3')

        try:
            print("Data inserted in MySQL RDS... uploading image to S3...")
            s3.Bucket(custombucket).put_object(Key=emp_image_file_name_in_s3, Body=emp_image_file)
            bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
            s3_location = (bucket_location['LocationConstraint'])

            if s3_location is None:
                s3_location = ''
            else:
                s3_location = '-' + s3_location

            object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                s3_location,
                custombucket,
                emp_image_file_name_in_s3)

        except Exception as e:
            return str(e)

    finally:
        cursor.close()
        
    print("all modification done...")
    return render_template('AddEmpOutput.html', name=emp_name)


@app.route('/GetEmpOutput.html')
def get_emp_page():
    return render_template('GetEmpOutput.html')

@app.route('/fetchdata', methods=['POST'])
def fetch_data():
    emp_id = request.form['emp_id']

    # Query the employee data from the HeidiSQL database
    conn = pymysql.connect(host=heidi_host, port=heidi_port, user=heidi_user, password=heidi_password, database=heidi_db)
    cur = conn.cursor()
    cur.execute(f"SELECT empid, first_name, last_name, gender, pri_skill, location FROM employees WHERE empid = '{emp_id}'")
    row = cur.fetchone()
    if row is None:
        error_msg = f'Employee with ID {emp_id} not found in database.'
        return render_template('GetEmpOutput.html', error_msg=error_msg)

    empid, first_name, last_name, pri_skill, location = row

    # Get the employee image file name from S3
    object_key = f'employees/{emp_id}.json'
    try:
        response = s3.get_object(Bucket=bucket_name, Key=object_key)
        employee_data = json.loads(response['Body'].read().decode('utf-8'))
        emp_image_file_name_in_s3 = employee_data.get('emp_image_file_name_in_s3')
    except s3.exceptions.NoSuchKey:
        emp_image_file_name_in_s3 = ''

    # Pass the employee data to the GetEmpOutput template
    return render_template('GetEmpOutput.html',
                           id=empid,
                           fname=first_name,
                           lname=last_name,
                           gender=gender,
                           skill=pri_skill,
                           location=location,
                           image_url=emp_image_file_name_in_s3)

@app.route('/UpdateEmp.html')
def getEmp():
    return render_template('/UpdateEmp.html')

@app.route('/updateemp', methods=['POST'])
def update_employee():
    emp_id = request.form['emp_id']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    gender = request.form['gender']
    pri_skill = request.form['pri_skill']
    location = request.form['location']
    emp_image_file = request.files.get('emp_image_file')

    # Here you can add your code to update the employee information in your database
    # using the values obtained from the form.

    return "Employee information updated successfully!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)

