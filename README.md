🔐 Secure File Management & Sharing API

A production-style Secure File Management API built using FastAPI with authentication, role-based access control, file validation, background scanning, and secure sharing using pre-signed URLs.

🚀 Features

- 🔑 JWT Authentication

- 👥 Role-Based Access Control (Admin, User)

- 📤 Async File Upload (aiofiles)

- 📥 Secure File Download

- 📦 File Metadata Stored in Database

- 🦠 Background Mock Virus Scan

- 🔗 Pre-Signed URL Support (Expiring Download Links)

- 🚦 Rate Limiting (Upload & Download)

- 📏 File Size & Type Validation

- ⚠️ Proper HTTP Status Codes & Error Handling

🏗 Tech Stack

- FastAPI

- Async SQLAlchemy

- SQLite (Development)

- Passlib (bcrypt hashing)

- python-jose (JWT)

- SlowAPI (Rate Limiting)

- aiofiles (Async File Handling)

📂 Project Structure
app/
 ├── api/routes/
 │    ├── auth.py
 │    ├── files.py
 ├── core/
 │    ├── config.py
 │    ├── security.py
 ├── db/
 │    ├── session.py
 │    ├── base.py
 ├── models/
 │    ├── user.py
 │    ├── file.py
 ├── services/
 │    ├── storage.py
 │    ├── scan.py
 │    ├── signing.py
 ├── schemas/
 │    ├── user.py
 │    ├── file.py

🔐 Authentication Flow
1️⃣ Register

POST /auth/register

2️⃣ Login

POST /auth/login

Returns:

{
  "access_token": "...",
  "token_type": "bearer"
}


Use in Swagger:

Bearer <access_token>

📁 File Operations
📤 Upload File

POST /files/upload

- Async upload

- Validates file type

- Validates file size

- Stores metadata

- Triggers background scan

📋 List Files

GET /files

- Admin → View all files

- User → View own files only

📥 Secure Download (JWT Protected)

GET /files/{id}/download

- Owner OR Admin allowed

🔗 Pre-Signed URL (Expiring)

Generate:
POST /files/{id}/signed-url

Returns:

/files/token-download?token=...


Download:
GET /files/token-download

- Works for Owner

- Works for Other Admins

- Expires in 5 minutes

🦠 Background Virus Scan

- Runs asynchronously

- If filename contains "virus"

    - File marked as INFECTED

    - Download blocked (403)

🚦 Rate Limiting
Endpoint	Limit
Upload	     5/min
Download	30/min

Returns:

429 Too Many Requests

📏 File Validation
Validation	             Status Code
Unsupported Type	      415
File Too Large	          413
Scan Pending	          409
Infected	              403
Unauthorized	          401
Forbidden	              403

⚙️ Setup Instructions
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload


Open Swagger:

http://127.0.0.1:8000/docs

🧪 Testing Checklist

- User cannot access others’ files

- Admin can access all files

- Virus file blocks download

- Rate limiting triggers 429

- Pre-signed URL expires correctly

- Size/type validation enforced

📈 Production Improvements (Future Scope)

- Replace SQLite with PostgreSQL

- Store files in AWS S3

- Add Redis for distributed rate limiting

- Integrate real antivirus engine

- Add file encryption at rest

✅ Status

All requirements implemented successfully:

- Authentication

- Role-based access

- Async file handling

- Metadata storage

- Background tasks

- Secure downloads

- Pre-signed URLs

- Rate limiting

- Proper error handling