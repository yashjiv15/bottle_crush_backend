from fastapi import APIRouter, HTTPException, UploadFile, Form, Depends
from fastapi.responses import JSONResponse
from typing import List, Optional
from pydantic import EmailStr
from email.message import EmailMessage
import smtplib
import os
from app.core.email_settings import MAIL_USERNAME, MAIL_PASSWORD, MAIL_PORT, MAIL_SERVER

router = APIRouter()

# Define a utility function to validate file size
def validate_file_size(file: UploadFile, max_size_mb: int = 5):
    file.file.seek(0, os.SEEK_END)  # Move to the end of the file
    size = file.file.tell()  # Get the size
    file.file.seek(0)  # Reset the file pointer
    if size > max_size_mb * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File size exceeds {max_size_mb} MB limit")


@router.post("/send-email", tags=["Email"])
async def send_email(
    to_email: EmailStr = Form(...),
    subject: str = Form(...),
    message: str = Form(...),
    attachments: Optional[List[UploadFile]] = None,
):
    """
    Send an email with optional PDF or Excel attachments.
    """
  

    # Validate attachment sizes
    if attachments:
        for file in attachments:
            validate_file_size(file)

    # Create the email message
    email_msg = EmailMessage()
    email_msg["From"] = f"Bottle Crush <{MAIL_USERNAME}>" 
    email_msg["To"] = to_email
    email_msg["Subject"] = f"Bottle Crush {subject}"
    email_msg.set_content(message)

    # Add attachments
    if attachments:
        for file in attachments:
            file_data = await file.read()
            email_msg.add_attachment(
                file_data,
                maintype="application",
                subtype=file.content_type.split("/")[-1],
                filename=file.filename,
            )

    # SMTP configuration
    smtp_server = MAIL_SERVER
    smtp_port = MAIL_PORT
    smtp_username = MAIL_USERNAME
    smtp_password = MAIL_PASSWORD

    try:
        # Send the email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(email_msg)
    except smtplib.SMTPException as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")

    return JSONResponse(content={"message": "Email sent successfully"})
