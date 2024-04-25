from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from datetime import datetime
from flask_mysqldb import MySQL
from flask_mail import Mail, Message
import os
import urllib.parse
import ftplib
import base64
import qrcode
import requests
from PIL import Image
from pyzbar.pyzbar import decode
from QR_Generator import send_email_with_qr
import requests
from summary import main1


application = Flask(__name__)
application.secret_key = 'new'
application.config['MYSQL_HOST'] = 'localhost'
application.config['MYSQL_USER'] = 'root'
application.config['MYSQL_PASSWORD'] = 'admin'
application.config['MYSQL_DB'] = 'ehr_final'

mysql = MySQL(application)

application.config['MAIL_SERVER'] = 'smtp.gmail.com'
application.config['MAIL_PORT'] = 465
application.config['MAIL_USERNAME'] = 'senduserdetails369@gmail.com'
application.config['MAIL_PASSWORD'] = 'kbzarexwcjdzdywv'
application.config['MAIL_USE_TLS'] = False
application.config['MAIL_USE_SSL'] = True
mail = Mail(application)

HOSTNAME = "ftp.drivehq.com"
FTP_PORT = '21'

# -----------------------------------    Admin routes --------------------------------------------


@application.route('/')
@application.route('/admin_login', methods=['POST', 'GET'])
def admin_login():
    if "admin" not in session:
        if request.method == 'POST':
            admin_id = request.form["admin_id"]
            admin_pwd = request.form["admin_pwd"]
            cur = mysql.connection.cursor()
            cur.execute("select * from m_admin where admin_id=%s and admin_pwd=%s", (admin_id, admin_pwd))
            user = cur.fetchone()
            if user:
                session['admin'] = user[1]
                flash("Hello Admin ...", 'success')
                return redirect(url_for('admin_home'))
            else:
                msg = 'Invalid Login Details Try Again'
                return render_template('admin/login.html', msg=msg)
        return render_template('admin/login.html')
    return redirect(url_for('admin_home'))


@application.route('/admin_home', methods=['POST', 'GET'])
def admin_home():
    if "admin" in session:
        return render_template('admin/home.html')
    return redirect(url_for('admin_login'))

@application.route('/data_owner_list', methods=['POST', 'GET'])
def data_owner_list():
    if "admin" in session:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM m_dataowner")
        data = cur.fetchall()
        return render_template('admin/data_owner_list.html', data=data)
    return redirect(url_for('admin_login'))


@application.route('/all_files_list', methods=['POST', 'GET'])
def all_files_list():
    if "admin" in session:
        cur = mysql.connection.cursor()
        # cur.execute("SELECT * FROM m_file_upload")
        cur.execute("SELECT f_no,date,do_name,du_code, f_name,f_remarks FROM m_file_upload, m_dataowner "
                    "WHERE m_file_upload.do_code=m_dataowner.do_code")
        data = cur.fetchall()
        return render_template('admin/all_files_list.html', data=data)
    return redirect(url_for('admin_login'))


@application.route('/all_users_list', methods=['POST', 'GET'])
def all_users_list():
    if "admin" in session:
        cur = mysql.connection.cursor()
        # cur.execute("SELECT * FROM m_data_user")
        cur.execute("SELECT * FROM m_data_user"
                    )
        data = cur.fetchall()
        return render_template('admin/all_users_list.html', data=data)
    return redirect(url_for('admin_login'))


@application.route('/create_dataOwner', methods=['POST', 'GET'])
def create_dataOwner():
    if "admin" in session:
        if request.method == 'POST':
            do_code = request.form['do_code']
            do_name = request.form['name']
            do_email = request.form['email']
            # do_phone = request.form['mobile']
            do_password = request.form['password']

            cursor = mysql.connection.cursor()
            cursor.execute("SELECT do_code FROM m_dataowner WHERE do_code=%s", (do_code,))
            d_code = cursor.fetchone()
            if not d_code:
                cursor.execute("SELECT do_email FROM m_dataowner WHERE do_email=%s", (do_email,))
                d_owner = cursor.fetchone()
                if not d_owner:
                    cursor.execute('INSERT INTO m_dataowner(do_code,do_password,do_name,do_email)'
                                   'VALUES(%s,%s,%s,%s)',
                                   (do_code, do_password, do_name, do_email))

                    mysql.connection.commit()
                    cursor.close()

                    with open('static/credentials.txt', 'w') as file:
                        file.write('Hello {}...\n You can use below Credentials to login into your account.\n\nYour id : {}\n'
                                   'User mail id: {}\nPassword : {}\n\n*Note : Do not forget to change your password after '
                                   'login. '.format(do_name, do_code, do_email, do_password))

                    try:
                        subject = 'Login Credentials'
                        msg = Message(subject, sender='smtp.gmail.com', recipients=[do_email])
                        msg.body = "Hello  " + do_name + "  You have been created as data owner.. Below file contains your credentials"
                        with application.open_resource("static/credentials.txt") as fp:
                            msg.attach("credentials.txt", "application/txt", fp.read())
                        mail.send(msg)
                    except Exception as e:
                        print(e)
                        print("Something went wrong")
                    flash("New Data Owner Created Successfully ...", 'success')
                    return redirect(url_for('data_owner_list'))
                msg2 = "This Email Id is already Registered"
                return render_template('admin/create_data_owner.html', msg1=msg2)
            msg2 = "This Code is not available to use.. try another.."
            return render_template('admin/create_data_owner.html', msg1=msg2)
        return render_template('admin/create_data_owner.html')
    return redirect(url_for('admin_login'))


@application.route('/edit_dataOwner', methods=['POST', 'GET'])
def edit_dataOwner():
    if "admin" in session:
        if request.method == 'POST':
            do_code = request.form['do_code']
            cursor = mysql.connection.cursor()
            cursor.execute("SELECT * FROM m_dataowner WHERE do_code=%s", (do_code,))
            data = cursor.fetchone()
            cursor.close()
            return render_template('admin/update_data_owner.html', data=data)
        return render_template('admin/update_data_owner.html')
    return redirect(url_for('admin_login'))


@application.route('/update_dataOwner', methods=['POST', 'GET'])
def update_dataOwner():
    if "admin" in session:
        if request.method == 'POST':
            do_id = request.form['do_id']
            do_code = request.form['do_id']
            do_name = request.form['do_name']
            do_email = request.form['do_email']

            cursor = mysql.connection.cursor()
            cursor.execute("SELECT do_name, do_email FROM m_dataowner WHERE do_id=%s", (do_id,))
            data1 = cursor.fetchone()

            if do_name == data1[0] and do_email == data1[1]:
                flash("No changes detected ...", 'success')
                return redirect(url_for('data_owner_list'))
            elif do_name != data1[0] and do_email == data1[1]:
                cursor.execute("UPDATE m_dataowner SET do_name=%s WHERE do_id = %s", (do_name, do_id))
                mysql.connection.commit()
                cursor.close()
                flash("Name successfully updated  ...", 'success')
                return redirect(url_for('data_owner_list'))
            elif do_name != data1[0] and do_email != data1[1]:
                cursor.execute("SELECT do_email FROM m_dataowner WHERE do_email=%s", (do_email,))
                d_owner = cursor.fetchone()
                if not d_owner:
                    cursor.execute("UPDATE m_dataowner SET do_name=%s, do_email=%s WHERE do_id = %s", (do_name, do_email, do_id))
                    mysql.connection.commit()
                    cursor.close()
                    flash("Name and Email successfully updated  ...", 'success')
                    return redirect(url_for('data_owner_list'))
                msg = 'This Email Id is already Existed'
                data = [do_id, do_code, '', do_name, do_email]
                return render_template('admin/update_data_owner.html', msg1=msg, data=data)

            elif do_name == data1[0] and do_email != data1[1]:
                cursor.execute("SELECT do_email FROM m_dataowner WHERE do_email=%s", (do_email,))
                d_owner = cursor.fetchone()
                if not d_owner:
                    cursor.execute("UPDATE m_dataowner SET do_email=%s WHERE do_id = %s", (do_email, do_id))
                    mysql.connection.commit()
                    cursor.close()
                    flash("Email successfully updated  ...", 'success')
                    return redirect(url_for('data_owner_list'))
                msg = 'This Email Id is already Existed'
                data = [do_id, do_code, '', do_name, do_email]
                return render_template('admin/update_data_owner.html', msg1=msg, data=data)
            return redirect(url_for('data_owner_list'))
        return render_template('admin/update_data_owner.html')
    return redirect(url_for('admin_login'))


@application.route('/admin_password_change', methods=['POST', 'GET'])
def admin_password_change():
    if "admin" in session:
        if request.method == 'POST':
            current_pass = request.form['old']
            new_pass = request.form['new']
            verify_pass = request.form['verify']
            cur = mysql.connection.cursor()
            cur.execute("select admin_pwd from m_admin")
            user = cur.fetchone()
            if user:
                if user[0] == current_pass:
                    if new_pass == verify_pass:
                        msg = 'Password changed successfully'
                        cur.execute("UPDATE m_admin SET admin_pwd = %s ", (new_pass,))
                        mysql.connection.commit()
                        return render_template('admin/admin_password_change.html', msg1=msg)
                    else:
                        msg = 'Re-entered password is not matched'
                        return render_template('admin/admin_password_change.html', msg2=msg)
                else:
                    msg = 'Incorrect password'
                    return render_template('admin/admin_password_change.html', msg3=msg)
            else:
                msg = 'Incorrect password'
                return render_template('admin/admin_password_change.html', msg3=msg)
        return render_template('admin/admin_password_change.html')
    return redirect(url_for('admin_login'))


@application.route('/admin_logout')
def admin_logout():
    if "admin" in session:
        session.pop('admin')
        msg = 'Admin logged out', 'success'
        return redirect(url_for('admin_login', msg=msg))
    return redirect(url_for('admin_login'))


# -----------------------------------    Data Owner routes --------------------------------------------


@application.route('/dataOwner_login', methods=['POST', 'GET'])
def dataOwner_login():
    if 'dataOwner_name' not in session:
        if request.method == 'POST':
            do_email = request.form["admin_id"]
            do_pwd = request.form["admin_pwd"]
            cur = mysql.connection.cursor()
            cur.execute("select * from m_dataowner where do_email=%s and do_password=%s", (do_email, do_pwd))
            user = cur.fetchone()
            if user:
                session['dataOwner_name'] = user[3]
                session['dataOwner_code'] = user[1]
                wish_msg = "Hello " + user[3]
                flash(wish_msg, 'success')
                return redirect(url_for('dataOwner_home'))
            else:
                msg = 'Invalid Login Details Try Again'
                return render_template('dataOwner/login.html', msg=msg)
        return render_template('dataOwner/login.html')
    return redirect(url_for('dataOwner_home'))


@application.route('/dataOwner_home', methods=['POST', 'GET'])
def dataOwner_home():
    if 'dataOwner_name' in session:
        return render_template('dataOwner/home.html', dataOwner_name=session['dataOwner_name'])
    return render_template('dataOwner/login.html')


@application.route('/users_list', methods=['POST', 'GET'])
def users_list():
    if 'dataOwner_name' in session:
        cur = mysql.connection.cursor()
        cur.execute("SELECT du_id,du_name,du_email,a_name,do_name FROM m_data_user, m_attribute, m_dataowner "
                    "WHERE m_data_user.du_attribute=m_attribute.a_code and m_dataowner.do_code=m_data_user.do_code and"
                    " m_data_user.do_code=%s", (session['dataOwner_code'],))
        data = cur.fetchall()
        return render_template('dataOwner/users_list.html', data=data, dataOwner_name=session['dataOwner_name'])
    return redirect(url_for('dataOwner_login'))


@application.route('/create_user_page', methods=['POST', 'GET'])
def create_user_page():
    # if 'dataOwner_name' in session:
    if "admin" in session:
        # domain_list1 = domain_list()
        if request.method == 'POST':
            user_id = request.form['user_id']
            username = request.form['username']
            DOJ = request.form['date']
            Age = request.form['age']
            Gender = request.form['gender']
            email = request.form['email']
            Password = request.form['password']
            cursor = mysql.connection.cursor()
            cursor.execute("SELECT du_email FROM m_data_user WHERE du_email=%s", (email,))
            user = cursor.fetchone()
            if not user:
                # QR code generations

                qr_code = main(username, Password)
                print("generated qrcode:", qr_code)
                cursor = mysql.connection.cursor()
                cursor.execute("INSERT INTO m_data_user (du_id, du_name,du_doj, du_age, du_gender, du_email,du_password,do_code,du_url) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                               (user_id, username, DOJ, Age, Gender, email, Password, str(session['admin']), qr_code))
                mysql.connection.commit()
                cursor.close()

                qr_code_filename = f"{username}.png"
                qr_code_image_path = os.path.join(os.getcwd(), qr_code_filename)

                print("Generated QR code111:", qr_code_filename)

                send_email_with_qr(username, email, qr_code_image_path, user_id, Password)

                flash("New User Successfully Created...", "success")
                return redirect(url_for('all_users_list'))
            msg2 = "This Email Id is already Registered"
            return render_template('admin/create_user_page.html', msg1=msg2, admin=session['admin'])
        return render_template('admin/create_user_page.html', admin=session['admin'])
    return redirect(url_for('all_users_list'))


@application.route('/generate_summary', methods=['POST'])
def generate_summary():
    uploaded_file = request.files['file']
    summary = main1(uploaded_file)
    return jsonify({'summary': summary})

@application.route('/dataOwner_files_list', methods=['POST', 'GET'])
def dataOwner_files_list():
    if 'dataOwner_name' in session:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM m_file_upload WHERE do_code=%s", (session['dataOwner_code'],))
        data = cur.fetchall()
        return render_template('dataOwner/user_files_list.html', data=data, dataOwner_name=session['dataOwner_name'])
    return redirect(url_for('dataOwner_login'))

@application.route('/data_owner_file_upload', methods=['POST', 'GET'])
def data_owner_file_upload():
    if 'dataOwner_name' in session:
        if request.method == 'POST':
            file = request.files['file']
            du_code = request.form["du_code"]
            time = datetime.today().date()
            original_filename = file.filename

            gs = main1(file)
            print("generated summary app.py: ", gs)

            cursor = mysql.connection.cursor()
            cursor.execute("SELECT du_id FROM m_data_user WHERE du_code = %s", (du_code,))
            user_id = cursor.fetchone()[0]

            cursor = mysql.connection.cursor()
            try:
                cursor.execute('INSERT INTO m_file_upload(date,do_code,f_name,f_remarks, du_code) '
                               'VALUES(%s,%s,%s,%s,%s)', (str(time), session['dataOwner_code'], original_filename, gs, du_code))
                mysql.connection.commit()
            except Exception as e:
                msg = e.args
                if msg[0] == 1062:
                    msg = "{} is already Presented in database".format(original_filename)
                    flash(msg, "error")
                    return redirect(url_for('data_owner_file_upload'))

            cursor.execute("SELECT f_no FROM m_file_upload WHERE f_name=%s", (original_filename,))
            f_no = cursor.fetchone()[0]

            # Save the file to a folder
            upload_folder = "static/upload"
            file_path = os.path.join(upload_folder, original_filename)
            file.save(file_path)

            f_size = os.path.getsize(file_path)

            # Convert file size to KB and store it as a string
            f_size1 = str(f_size / 1024) + ' KB'

            new_filename = original_filename
            # file.seek(0)  # Reset the file pointer back to the beginning

            try:
                cursor = mysql.connection.cursor()
                cursor.execute("SELECT du_name, du_password FROM m_data_user WHERE du_code = %s", (du_code,))
                user_data = cursor.fetchone()
                print("ftp_user: ", user_id)

                username, password = user_data
                print("Username:", username)
                print("Password:", password)

                ftp_server = ftplib.FTP(HOSTNAME, username, password)
                ftp_server.storbinary(f"STOR {new_filename}", file)
                ftp_server.encoding = "utf-8"

                cursor.execute("UPDATE m_file_upload SET cloud_f_name=%s,f_size=%s  WHERE f_no = %s",
                               (new_filename, f_size1, f_no))
                mysql.connection.commit()
                cursor.close()

                flash("New File Uploaded Successfully...", "success")
                return redirect(url_for('dataOwner_files_list'))
            except Exception as e:
                msg = "File Not Uploaded :" + str(e)
                cursor = mysql.connection.cursor()
                cursor.execute("DELETE FROM m_file_upload WHERE f_no=%s", [f_no])
                mysql.connection.commit()
                flash(msg, "error")
                return redirect(url_for('data_owner_file_upload'))
        else:
            cursor = mysql.connection.cursor()
            cursor.execute("SELECT du_code, du_id FROM m_data_user")
            users = cursor.fetchall()
            return render_template("dataOwner/file_upload.html", users=users, dataOwner_name=session['dataOwner_name'])

    return redirect(url_for('dataOwner_login'))
@application.route('/get_user_id', methods=['POST'])
def get_user_id():
    du_code = request.form['du_code']
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT du_id FROM m_data_user WHERE du_code = %s", (du_code,))
    result = cursor.fetchone()  # Fetch the result
    if result:  # Check if result is not None
        user_id = result[0]
        return str(user_id)
    else:
        return "User ID not found"  # Return an error message or handle as appropriate




def delete_file(file_name):
    # Connect to DriveHQ
    try:
        ftp_server = ftplib.FTP(HOSTNAME, USERNAME, PASSWORD)
        # Delete the file from DriveHQ
        ftp_server.delete(file_name)
        print("File deleted successfully from DriveHQ.")
        ftp_server.quit()
    except Exception as e:
        print("Error deleting file from DriveHQ:", e)


@application.route('/dataOwner_file_delete', methods=['POST', 'GET'])
def dataOwner_file_delete():
    if 'dataOwner_name' in session:
        if request.method == 'POST':
            f_no = request.form['file_num']
            file_name = request.form['cloud_file_name']

            pickle_file_name = file_name.split('.')[0] + '.pkl'
            pickle_file_name = 'static/pickle_files/' + pickle_file_name

            cursor = mysql.connection.cursor()
            cursor.execute("DELETE FROM m_file_upload WHERE f_no = %s ", [f_no])
            mysql.connection.commit()
            cursor.close()

            cloud_file_name = 'static/download/' + file_name
            delete_file(cloud_file_name)
            os.remove(pickle_file_name)
            flash("File Deleted Successfully", "success")
            return redirect(url_for('dataOwner_files_list'))
        return redirect(url_for('dataOwner_files_list'))
    return redirect(url_for('dataOwner_login'))


@application.route('/dataOwner_password_change', methods=['POST', 'GET'])
def dataOwner_password_change():
    if 'dataOwner_name' in session:
        if request.method == 'POST':
            current_pass = request.form['old']
            new_pass = request.form['new']
            verify_pass = request.form['verify']
            cur = mysql.connection.cursor()
            cur.execute("select do_password from m_dataowner WHERE do_code=%s", (session['dataOwner_code'],))
            user = cur.fetchone()
            if user:
                if user[0] == current_pass:
                    if new_pass == verify_pass:
                        msg = 'Password changed successfully'
                        cur.execute("UPDATE m_dataowner SET do_password=%s WHERE do_code=%s", (new_pass, session['dataOwner_code']))
                        mysql.connection.commit()
                        return render_template('dataOwner/dataOwner_password_change.html', msg1=msg,
                                               dataOwner_name=session['dataOwner_name'])
                    else:
                        msg = 'Re-entered password is not matched'
                        return render_template('dataOwner/dataOwner_password_change.html', msg2=msg,
                                               dataOwner_name=session['dataOwner_name'])
                else:
                    msg = 'Incorrect password'
                    return render_template('dataOwner/dataOwner_password_change.html', msg3=msg,
                                           dataOwner_name=session['dataOwner_name'])
            else:
                msg = 'Incorrect password'
                return render_template('dataOwner/dataOwner_password_change.html', msg3=msg,
                                       dataOwner_name=session['dataOwner_name'])
        return render_template('dataOwner/dataOwner_password_change.html',
                               dataOwner_name=session['dataOwner_name'])
    return redirect(url_for('dataOwner_login'))


@application.route('/dataOwner_user_edit', methods=['POST', 'GET'])
def dataOwner_user_edit():
    if 'admin' in session:
        if request.method == 'POST':
            u_id = request.form['user_id']
            cursor = mysql.connection.cursor()
            cursor.execute("SELECT * FROM m_data_user WHERE du_id=%s", (u_id,))
            data = cursor.fetchone()
            cursor.close()
            return render_template('admin/update_user_page.html', data=data)
        return render_template('admin/update_user_page.html')
    return redirect(url_for('all_users_list'))


@application.route('/dataOwner_user_update', methods=['POST', 'GET'])
def dataOwner_user_update():
    if 'admin' in session:
        if request.method == 'POST':
            du_id = request.form['du_id']
            du_name = request.form['du_name']
            du_email = request.form['du_email']

            cursor = mysql.connection.cursor()
            cursor.execute("SELECT du_name, du_email FROM m_data_user WHERE du_id=%s", (du_id,))
            data1 = cursor.fetchone()

            if du_name == data1[0] and du_email == data1[1]:
                flash("No changes detected ...", 'success')
                return redirect(url_for('users_list'))
            elif du_name != data1[0] and du_email == data1[1]:
                cursor.execute("UPDATE m_data_user SET du_name=%s WHERE du_id = %s", (du_name, du_id))
                mysql.connection.commit()
                cursor.close()
                flash("User Name successfully updated  ...", 'success')
                return redirect(url_for('all_users_list'))
            elif du_name != data1[0] and du_email != data1[1]:
                cursor.execute("SELECT du_email FROM m_data_user WHERE du_email=%s", (du_email,))
                d_user = cursor.fetchone()
                if not d_user:
                    cursor.execute("UPDATE m_data_user SET du_name=%s, du_email=%s WHERE du_id = %s", (du_name, du_email, du_id))
                    mysql.connection.commit()
                    cursor.close()
                    flash("User Name and Email successfully updated  ...", 'success')
                    return redirect(url_for('all_users_list'))
                msg = 'This Email Id is already Existed'
                data = [du_id, du_name, du_email]
                return render_template('dataOwner/update_user_page.html', msg1=msg, data=data)

            elif du_name == data1[0] and du_email != data1[1]:
                cursor.execute("SELECT du_email FROM m_data_user WHERE du_email=%s", (du_email,))
                d_user = cursor.fetchone()
                if not d_user:
                    cursor.execute("UPDATE m_data_user SET du_email=%s WHERE du_id = %s", (du_email, du_id))
                    mysql.connection.commit()
                    cursor.close()
                    flash("Email successfully updated  ...", 'success')
                    return redirect(url_for('users_list'))
                msg = 'This Email Id is already Existed'
                data = [du_id, du_name, du_email]
                return render_template('admin/update_user_page.html', msg1=msg, data=data)
            return redirect(url_for('all_users_list'))
        return render_template('admin/update_user_page.html')
    return redirect(url_for('admin_login'))


@application.route('/dataOwner_user_delete', methods=['POST', 'GET'])
def admin_user_delete():
    if 'admin' in session:
        if request.method == 'POST':
            user_id = request.form['user_id']

            cursor = mysql.connection.cursor()
            cursor.execute("DELETE FROM m_data_user WHERE du_id = %s ", [user_id])
            mysql.connection.commit()
            cursor.close()
            flash("User Deleted Successfully", 'success')
            return redirect(url_for('all_users_list'))
        return render_template('admin/all_users_list.html')
    return redirect(url_for('admin_login'))


@application.route('/dataOwner_profile', methods=['POST', 'GET'])
def dataOwner_profile():
    if 'dataOwner_name' in session:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM m_dataowner WHERE do_code=%s ", (session['dataOwner_code'],))
        data = cursor.fetchone()
        cursor.close()
        return render_template('dataOwner/profile.html', data=data, dataOwner_name=session['dataOwner_name'])
    return redirect(url_for('dataOwner_login'))


# @application.route('/test', methods=['POST', 'GET'])
# def test():
#     cursor = mysql.connection.cursor()
#     # cursor.execute("SELECT TOP 1 * FROM m_file_upload")
#     data = cursor.fetchall()
#     for i in data:
#         print(i)
#     return redirect(url_for('dataOwner_home'))


@application.route('/dataOwner_logout')
def dataOwner_logout():
    if 'dataOwner_name' in session:
        do_name = session['dataOwner_name']
        session.pop('dataOwner_name')
        session.pop('dataOwner_code')
        msg = 'See you soon {}'.format(do_name)
        return render_template('dataOwner/login.html', msg=msg)
        # return redirect(url_for('dataOwner_login'))
    return redirect(url_for('dataOwner_login'))


# -------------------------------------    User routes  -------------------------------------

def shorten_url(long_url):
    api_url = "https://tinyurl.com/api-create.php"
    params = {"url": long_url}
    response = requests.get(api_url, params=params)
    if response.status_code == 200:
        return response.text.strip()
    else:
        print("Failed to shorten URL:", response.text)
        return None

def generate_drivehq_url(username, password, filename):
    base_url = "http://localhost:5000/run_selenium_code"
    encoded_username = urllib.parse.quote(username)
    encoded_password = urllib.parse.quote(password)
    full_url = f"{base_url}?username={encoded_username}&password={encoded_password}"
    print("fullurl", full_url)
    short_url = shorten_url(full_url)
    print("url", short_url)

    if short_url is not None:
        with open(filename, 'w') as file:
            file.write(short_url)
    else:
        print("Failed to shorten the URL. Cannot write None to file.")
    return short_url
def generate_qr_code(url, save_path):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    qr_image = qr.make_image(fill_color="black", back_color="white")
    qr_image.save(save_path)

    return qr_image


# def decode_qr_code(qr_code_image_path):
#     # qr_code_image = Image.open(qr_code_image_path)
#     qr_code_image = Image.open(qr_code_image_path, mode='r', formats=None)
#     decoded_objects = decode(qr_code_image)
#     decoded_url = decoded_objects[0].data.decode("utf-8")
#
#     return decoded_url

def main(username, password):

    access_token = '0ec7b9316700676d5d232d04226bc0cfb9c0a96d'
    filename = "shortened_url.txt"

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT du_code FROM ehr_final.m_data_user ORDER BY du_code DESC LIMIT 1;")
    result = cursor.fetchone()  # Fetch the result

    if result is not None:
        user_id = result[0] + 1
        print("user_id is:", user_id)
    else:
        user_id = 1
        print("No user code found in the database. Setting user_id to 1.")

    # Generate shortened URL and QR code
    shortened_url = generate_drivehq_url(username, password, filename)
    if shortened_url:
        print("Shortened URL:", shortened_url)
        qr_code_filename = f"{username}.png"
        qr_code_content = f"{user_id} # {shortened_url}"
        qr_code_image = generate_qr_code(qr_code_content, qr_code_filename)
        # Further processing with qr_code_image
    else:
        print("Failed to generate shortened URL.")
    return shortened_url


if __name__ == '__main__':
    application.run(port=5002, debug=True)
