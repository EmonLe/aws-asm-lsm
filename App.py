from flask import Flask, render_template, request
from pymysql import connections
import os
import boto3
from config import *

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


@app.route("/", methods=['GET', 'POST'])
def home():
    return render_template('AddEmp.html')


@app.route("/about", methods=['POST'])
def about():
    return render_template('www.intellipaat.com')


@app.route("/addemp", methods=['POST'])
def AddEmp():
    emp_id = request.form['emp_id']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    pri_skill = request.form['pri_skill']
    location = request.form['location']
    emp_image_file = request.files['emp_image_file']

    insert_sql = "INSERT INTO employee VALUES (%s, %s, %s, %s, %s)"
    cursor = db_conn.cursor()

    if emp_image_file.filename == "":
        return "Please select a file"

    try:
        cursor.execute(insert_sql, (emp_id, first_name, last_name, pri_skill, location))
        db_conn.commit()
        emp_name = "" + first_name + " " + last_name

        # Upload image file to S3 #
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

    print("all modifications done...")
    return render_template('AddEmpOutput.html', name=emp_name)


@app.route("/getemp", methods=['GET', 'POST'])
def GetEmp():
    if request.method == 'POST':
        emp_id = request.form['emp_id']
        print(emp_id)

        select_sql = "SELECT * FROM employee WHERE emp_id = %s"
        cursor = db_conn.cursor()

        try:
            cursor.execute(select_sql, (emp_id,))
            result = cursor.fetchall()

            if not result:
                return "Employee with ID: {} doesn't exist".format(emp_id)
            else:
                emp_data = result[0]
                emp_name = emp_data[1] + " " + emp_data[2]
                pri_skill = emp_data[3]
                location = emp_data[4]

                # Download image file from S3 #
                emp_image_file_name_in_s3 = "emp-id-" + str(emp_id) + "_image_file"
                s3 = boto3.resource('s3')

                try:
                    s3.Bucket(custombucket).download_file(emp_image_file_name_in_s3, emp_image_file_name_in_s3)
                    print("Image file downloaded from S3...")

                except Exception as e:
                    return str(e)

        finally:
            cursor.close()

        return render_template('GetEmpOutput.html', name=emp_name, pri_skill=pri_skill, location=location,
                               emp_image_file_name_in_s3=emp_image_file_name_in_s3)

    else:
        return render_template('GetEmp.html')
    
@app.route("/getempoutput", methods=['GET', 'POST'])
def GetEmpOutput():
    cursor = db_conn.cursor()
    select_sql = "SELECT * FROM employee"
    cursor.execute(select_sql)
    rows = cursor.fetchall()
    emp_data = []
    for row in rows:
        emp_dict = {}
        emp_dict['emp_id'] = row[0]
        emp_dict['first_name'] = row[1]
        emp_dict['last_name'] = row[2]
        emp_dict['pri_skill'] = row[3]
        emp_dict['location'] = row[4]
        emp_dict['emp_image_url'] = "https://{0}.s3.{1}.amazonaws.com/emp-id-{2}_image_file".format(
            bucket,
            region,
            str(row[0])
        )
        emp_data.append(emp_dict)

    return render_template('GetEmpOutput.html', emp_data=emp_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)