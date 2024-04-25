from flask_mail import Mail, Message
from flask import Flask, render_template, request

application = Flask(__name__)

application.config['MAIL_SERVER'] = 'smtp.gmail.com'
application.config['MAIL_PORT'] = 465
application.config['MAIL_USERNAME'] = 'senduserdetails369@gmail.com'
application.config['MAIL_PASSWORD'] = 'kbzarexwcjdzdywv'
application.config['MAIL_USE_TLS'] = False
application.config['MAIL_USE_SSL'] = True

mail = Mail(application)

def send_email_with_qr(username, recipient_email, qr_code_image_path, user_id, password):
    try:
        sender_email = application.config['MAIL_USERNAME']  # Sender's email address
        subject = 'QR Code Attachment'
        message = f"Hello {user_id},\n\nYou are Successfully Registered in Electronic Patient Health System\n\nYour user_name: {username}\n\nYour Password: {password}\n\nPlease find your Secure QR code attached below."

        # Create message object
        msg = Message(subject, sender=sender_email, recipients=[recipient_email])
        msg.body = message

        # Attach QR code image
        with open(qr_code_image_path, 'rb') as qr_file:
            qr_attachment = qr_file.read()
            msg.attach(f"{username}.png", "image/png", qr_attachment)

        # Send email
        mail.send(msg)
        print("Email sent successfully!")

    except Exception as e:
        print("Something went wrong:", e)

# Your other code follows...

if __name__ == "__main__":
    application.run(debug=True)
