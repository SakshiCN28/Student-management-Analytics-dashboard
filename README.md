# Deploy a Full-Stack Analytics App

This is an easy full-stack analytics project for beginners. It uses only Python, HTML, CSS, and JavaScript. The app has login/register, student data management, KPI cards, charts, and a protected backend API.

## Features

- Python backend API using built-in libraries
- Login and register with password hashing
- Simple JWT-style token authentication
- Add, edit, and delete student records
- Dashboard metrics for total students, average marks, pass percentage, and top performer
- Charts drawn with JavaScript canvas
- Local JSON files for data storage
- No external Python packages required

## Project Structure

```text
Deploy a full-stack analytics app/
  backend/
    app.py
  data/
    students.json
    users.json
  frontend/
    index.html
    styles.css
    app.js
  requirements.txt
  README.md
```

## Step-by-Step Setup

### 1. Open the project folder

Open this folder in VS Code or PowerShell:

```bash
Deploy a full-stack analytics app
```

### 2. Check Python

```bash
python --version
```

Python is the only requirement. You do not need to install Flask, Django, Node, or React.

### 3. Run the app

```bash
python backend/app.py
```

### 4. Open in browser

Visit:

```text
http://127.0.0.1:8000
```

### 5. Create your first account

Click **Register**, enter your name, email, and a password with at least 6 characters.

After registration, the dashboard will open automatically.

## How It Works

1. `frontend/index.html` creates the page layout.
2. `frontend/styles.css` makes the app look professional and responsive.
3. `frontend/app.js` handles login, API calls, table updates, forms, and charts.
4. `backend/app.py` runs the Python web server.
5. The backend reads and writes JSON files in the `data` folder.
6. The frontend sends requests to API routes like `/api/dashboard` and `/api/students`.
7. The backend returns JSON data.
8. JavaScript updates the dashboard without reloading the page.

## Main API Routes

- `POST /api/auth/register` creates a new user.
- `POST /api/auth/login` logs in a user.
- `GET /api/me` checks the current user.
- `GET /api/dashboard` returns analytics.
- `POST /api/students` adds a student.
- `PUT /api/students/{id}` updates a student.
- `DELETE /api/students/{id}` deletes a student.

## Explain This Project in Your Viva

This project is a full-stack student analytics app. The frontend is built with HTML, CSS, and JavaScript. The backend is built with Python. The user registers or logs in, then manages student records. The backend stores students in JSON files and calculates analytics like average marks, pass percentage, top performers, and monthly admissions. The frontend displays those analytics using cards, charts, and a data table.

## Easy Deployment Idea

For a simple project demo, run it locally using:

```bash
python backend/app.py
```

For online deployment, you can host it on PythonAnywhere, Render, or Railway. If deploying online, change `JWT_SECRET` in `backend/app.py` to a stronger private value.
