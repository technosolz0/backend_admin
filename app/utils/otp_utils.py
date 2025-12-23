

# import random
# import smtplib
# from email.mime.text import MIMEText
# from email.mime.multipart import MIMEMultipart
# import os
# from venv import logger
# from dotenv import load_dotenv
# from datetime import datetime

# load_dotenv()

# def generate_otp() -> str:
#     return str(random.randint(100000, 999999))

# def send_email_otp(receiver_email: str, otp: str, template: str = "registration"):
#     """
#     Send OTP via email with different templates.
    
#     Args:
#         receiver_email (str): Recipient email
#         otp (str): OTP to send
#         template (str): Email template type ('registration' or 'password_reset')
#     """
#     sender_email = os.getenv("EMAIL_USERNAME")
#     sender_password = os.getenv("EMAIL_PASSWORD")

#     if template == "password_reset":
#         subject = "Password Reset Request - Your OTP Code"
#         text = f"Your OTP code for password reset is: {otp}"
#         html = f"""
#         <html>
#         <body style="font-family: Arial, sans-serif; margin:0; padding:0; background-color:#f9f9f9;">
#             <table align="center" width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;">
#                 <tr>
#                     <td style="background-color:#FAC94E; padding:20px; text-align:center; border-radius:8px 8px 0 0;">
#                         <h1 style="margin:0; color:#000;">Serwex</h1>
#                     </td>
#                 </tr>
#                 <tr>
#                     <td style="background-color:#ffffff; padding:30px; text-align:center; border:1px solid #eee;">
#                         <h2 style="color:#333;">Password Reset</h2>
#                         <p style="font-size:16px; color:#555;">
#                             You requested a password reset for your Serwex account.
#                         </p>
#                         <div style="display:inline-block; padding:15px 25px; margin:20px 0;
#                                     font-size:24px; font-weight:bold; color:#000;
#                                     background-color:#FFD97C; border-radius:6px;">
#                             {otp}
#                         </div>
#                         <p style="font-size:14px; color:#888;">
#                             This code will expire in 5 minutes. Use it to reset your password.
#                             If you didn't request this, please ignore this email.
#                         </p>
#                     </td>
#                 </tr>
#                 <tr>
#                     <td style="background-color:#FACC59; text-align:center; padding:15px; border-radius:0 0 8px 8px;">
#                         <p style="margin:0; font-size:12px; color:#333;">
#                             © {datetime.now().year} Serwex. All rights reserved.
#                         </p>
#                     </td>
#                 </tr>
#             </table>
#         </body>
#         </html>
#         """
#     else:  # default registration
#         subject = "Your Serwex OTP Code"
#         text = f"Your OTP code is: {otp}"
#         html = f"""
#         <html>
#         <body style="font-family: Arial, sans-serif; margin:0; padding:0; background-color:#f9f9f9;">
#             <table align="center" width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;">
#                 <tr>
#                     <td style="background-color:#FAC94E; padding:20px; text-align:center; border-radius:8px 8px 0 0;">
#                         <h1 style="margin:0; color:#000;">Serwex</h1>
#                     </td>
#                 </tr>
#                 <tr>
#                     <td style="background-color:#ffffff; padding:30px; text-align:center; border:1px solid #eee;">
#                         <h2 style="color:#333;">Your OTP Code</h2>
#                         <p style="font-size:16px; color:#555;">
#                             Please use the following OTP code to complete your verification:
#                         </p>
#                         <div style="display:inline-block; padding:15px 25px; margin:20px 0;
#                                     font-size:24px; font-weight:bold; color:#000;
#                                     background-color:#FFD97C; border-radius:6px;">
#                             {otp}
#                         </div>
#                         <p style="font-size:14px; color:#888;">
#                             This code will expire in 5 minutes. Please do not share it with anyone.
#                         </p>
#                     </td>
#                 </tr>
#                 <tr>
#                     <td style="background-color:#FACC59; text-align:center; padding:15px; border-radius:0 0 8px 8px;">
#                         <p style="margin:0; font-size:12px; color:#333;">
#                             © {datetime.now().year} Serwex. All rights reserved.
#                         </p>
#                     </td>
#                 </tr>
#             </table>
#         </body>
#         </html>
#         """

#     message = MIMEMultipart("alternative")
#     message["Subject"] = subject
#     message["From"] = sender_email
#     message["To"] = receiver_email

#     # Attach both plain text and HTML
#     message.attach(MIMEText(text, "plain"))
#     message.attach(MIMEText(html, "html"))

#     try:
#         with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
#             server.login(sender_email, sender_password)
#             server.sendmail(sender_email, receiver_email, message.as_string())
#         logger.info(f"OTP email sent successfully to {receiver_email} with template '{template}'")
#     except Exception as e:
#         logger.error(f"Failed to send OTP email to {receiver_email}: {str(e)}")
#         raise



import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from datetime import datetime
import logging
from app.models.service_provider_model import ServiceProvider as Vendor
from sqlalchemy.orm import Session
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

def generate_otp() -> str:
    """Generate a 6-digit OTP."""
    return str(random.randint(100000, 999999))

def send_email(receiver_email: str, otp: str = None, template: str = "otp", booking=None, payment=None, name: str = None):
    """
    Send email with different templates (otp, password_reset, receipt, welcome).
    
    Args:
        receiver_email (str): Recipient email
        otp (str, optional): OTP to send (for otp and password_reset templates)
        template (str): Email template type ('otp', 'password_reset', 'receipt', 'welcome')
        booking: Booking object (for receipt template)
        payment: Payment object (for receipt template)
        name (str, optional): User name (for welcome template)
    """
    sender_email = os.getenv("EMAIL_USERNAME")
    sender_password = os.getenv("EMAIL_PASSWORD")
    smtp_host = os.getenv("SMTP_HOST")

    if not sender_email or not sender_password:
        logger.error("EMAIL_USERNAME or EMAIL_PASSWORD not set")
        raise ValueError("Email configuration missing")

    if template == "password_reset":
        subject = "Password Reset Request - Your OTP Code"
        text = f"Your OTP code for password reset is: {otp}"
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; margin:0; padding:0; background-color:#f9f9f9;">
            <table align="center" width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;">
                <tr>
                    <td style="background-color:#FAC94E; padding:20px; text-align:center; border-radius:8px 8px 0 0;">
                        <h1 style="margin:0; color:#000;">Serwex</h1>
                    </td>
                </tr>
                <tr>
                    <td style="background-color:#ffffff; padding:30px; text-align:center; border:1px solid #eee;">
                        <h2 style="color:#333;">Password Reset</h2>
                        <p style="font-size:16px; color:#555;">
                            You requested a password reset for your Serwex account.
                        </p>
                        <div style="display:inline-block; padding:15px 25px; margin:20px 0;
                                    font-size:24px; font-weight:bold; color:#000;
                                    background-color:#FFD97C; border-radius:6px;">
                            {otp}
                        </div>
                        <p style="font-size:14px; color:#888;">
                            This code will expire in 5 minutes. Use it to reset your password.
                            If you didn't request this, please ignore this email.
                        </p>
                    </td>
                </tr>
                <tr>
                    <td style="background-color:#FACC59; text-align:center; padding:15px; border-radius:0 0 8px 8px;">
                        <p style="margin:0; font-size:12px; color:#333;">
                            © {datetime.now().year} Serwex. All rights reserved.
                        </p>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
    elif template == "receipt":
        from app.crud import category, subcategory
        session = booking._sa_instance_state.session if booking else None
        cat = category.get_category_by_id(session, booking.category_id) if session and booking else None
        subcat = subcategory.get_subcategory_by_id(session, booking.subcategory_id) if session and booking else None
        vendor = session.query(Vendor).filter(Vendor.id == booking.serviceprovider_id).first() if session and booking else None

        subject = f"Receipt for Booking #{booking.id}"
        text = f"""
        Your booking #{booking.id} has been completed. Here are the details:
        Booking ID: {booking.id}
        Category: {cat.name if cat else 'N/A'}
        Subcategory: {subcat.name if subcat else 'N/A'}
        Vendor: {vendor.name if vendor else 'N/A'}
        Date: {booking.created_at.strftime('%Y-%m-%d %H:%M:%S') if booking else 'N/A'}
        Payment Amount: {payment.amount if payment else 'N/A'}
        Payment Method: {payment.payment_method if payment else 'N/A'}
        Transaction ID: {payment.transaction_id if payment and payment.transaction_id else 'N/A'}
        """
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; margin:0; padding:0; background-color:#f9f9f9;">
            <table align="center" width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;">
                <tr>
                    <td style="background-color:#FAC94E; padding:20px; text-align:center; border-radius:8px 8px 0 0;">
                        <h1 style="margin:0; color:#000;">Serwex</h1>
                    </td>
                </tr>
                <tr>
                    <td style="background-color:#ffffff; padding:30px; border:1px solid #eee;">
                        <h2 style="color:#333;">Booking Receipt</h2>
                        <p style="font-size:16px; color:#555;">
                            Thank you for using Serwex! Your booking #{booking.id} has been completed. Below are the details:
                        </p>
                        <table style="width:100%; font-size:14px; color:#333; margin:20px 0;">
                            <tr>
                                <td style="padding:8px; font-weight:bold;">Booking ID:</td>
                                <td style="padding:8px;">#{booking.id}</td>
                            </tr>
                            <tr>
                                <td style="padding:8px; font-weight:bold;">Category:</td>
                                <td style="padding:8px;">{cat.name if cat else 'N/A'}</td>
                            </tr>
                            <tr>
                                <td style="padding:8px; font-weight:bold;">Subcategory:</td>
                                <td style="padding:8px;">{subcat.name if subcat else 'N/A'}</td>
                            </tr>
                            <tr>
                                <td style="padding:8px; font-weight:bold;">Vendor:</td>
                                <td style="padding:8px;">{vendor.name if vendor else 'N/A'}</td>
                            </tr>
                            <tr>
                                <td style="padding:8px; font-weight:bold;">Date:</td>
                                <td style="padding:8px;">{booking.created_at.strftime('%Y-%m-%d %H:%M:%S') if booking else 'N/A'}</td>
                            </tr>
                            <tr>
                                <td style="padding:8px; font-weight:bold;">Payment Amount:</td>
                                <td style="padding:8px;">{payment.amount if payment else 'N/A'}</td>
                            </tr>
                            <tr>
                                <td style="padding:8px; font-weight:bold;">Payment Method:</td>
                                <td style="padding:8px;">{payment.payment_method if payment else 'N/A'}</td>
                            </tr>
                            <tr>
                                <td style="padding:8px; font-weight:bold;">Transaction ID:</td>
                                <td style="padding:8px;">{payment.transaction_id if payment and payment.transaction_id else 'N/A'}</td>
                            </tr>
                        </table>
                        <p style="font-size:14px; color:#888;">
                            If you have any questions, please contact our support team.
                        </p>
                    </td>
                </tr>
                <tr>
                    <td style="background-color:#FACC59; text-align:center; padding:15px; border-radius:0 0 8px 8px;">
                        <p style="margin:0; font-size:12px; color:#333;">
                            © {datetime.now().year} Serwex. All rights reserved.
                        </p>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
    elif template == "welcome":
        subject = "Welcome to Serwex!"
        text = f"""
        Dear {name or 'User'},
        Welcome to Serwex! Your account ({receiver_email}) has been successfully verified.
        Explore our services and start booking today!
        Best regards,
        The Serwex Team
        """
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; margin:0; padding:0; background-color:#f9f9f9;">
            <table align="center" width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;">
                <tr>
                    <td style="background-color:#FAC94E; padding:20px; text-align:center; border-radius:8px 8px 0 0;">
                        <h1 style="margin:0; color:#000;">Serwex</h1>
                    </td>
                </tr>
                <tr>
                    <td style="background-color:#ffffff; padding:30px; text-align:center; border:1px solid #eee;">
                        <h2 style="color:#333;">Welcome to Serwex!</h2>
                        <p style="font-size:16px; color:#555;">
                            Dear {name or 'User'},<br>
                            Thank you for joining Serwex! Your account ({receiver_email}) has been successfully verified.
                        </p>
                        <p style="font-size:16px; color:#555;">
                            Explore our wide range of services and start booking today!
                        </p>
                        <a href="https://www.serwex.com" style="display:inline-block; padding:10px 20px; margin:20px 0;
                            font-size:16px; color:#fff; background-color:#FAC94E; text-decoration:none; border-radius:6px;">
                            Get Started
                        </a>
                        <p style="font-size:14px; color:#888;">
                            If you have any questions, please contact our support team.
                        </p>
                    </td>
                </tr>
                <tr>
                    <td style="background-color:#FACC59; text-align:center; padding:15px; border-radius:0 0 8px 8px;">
                        <p style="margin:0; font-size:12px; color:#333;">
                            © {datetime.now().year} Serwex. All rights reserved.
                        </p>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """
    else:  # default otp template
        subject = "Your Serwex OTP Code"
        text = f"Your OTP code is: {otp}"
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; margin:0; padding:0; background-color:#f9f9f9;">
            <table align="center" width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;">
                <tr>
                    <td style="background-color:#FAC94E; padding:20px; text-align:center; border-radius:8px 8px 0 0;">
                        <h1 style="margin:0; color:#000;">Serwex</h1>
                    </td>
                </tr>
                <tr>
                    <td style="background-color:#ffffff; padding:30px; text-align:center; border:1px solid #eee;">
                        <h2 style="color:#333;">Your OTP Code</h2>
                        <p style="font-size:16px; color:#555;">
                            Please use the following OTP code to complete your verification:
                        </p>
                        <div style="display:inline-block; padding:15px 25px; margin:20px 0;
                                    font-size:24px; font-weight:bold; color:#000;
                                    background-color:#FFD97C; border-radius:6px;">
                            {otp}
                        </div>
                        <p style="font-size:14px; color:#888;">
                            This code will expire in 5 minutes. Please do not share it with anyone.
                        </p>
                    </td>
                </tr>
                <tr>
                    <td style="background-color:#FACC59; text-align:center; padding:15px; border-radius:0 0 8px 8px;">
                        <p style="margin:0; font-size:12px; color:#333;">
                            © {datetime.now().year} Serwex. All rights reserved.
                        </p>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = sender_email
    message["To"] = receiver_email

    message.attach(MIMEText(text, "plain"))
    message.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP_SSL(smtp_host, 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, message.as_string())
        logger.info(f"Email sent successfully to {receiver_email} with template '{template}'")
    except Exception as e:
        logger.error(f"Failed to send email to {receiver_email}: {str(e)}")
        # Log error but do not raise to avoid interrupting main action

def send_receipt_email(db: Session, booking, payment, receiver_email: str):
    """
    Send receipt email to user with booking and payment details.
    
    Args:
        db (Session): Database session
        booking: Booking object
        payment: Payment object
        receiver_email (str): Recipient email
    """
    send_email(receiver_email=receiver_email, template="receipt", booking=booking, payment=payment)