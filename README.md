# 🛣️ RoadPulse Backend

Welcome to the **backend** of the **RoadPulse** platform — your all-in-one solution for managing trucking trips and ELD logs 📋. Built with **Django** 🐍 and **Django REST Framework** ⚙️, this backend powers efficient trip tracking, duty monitoring, and compliance logging.

---

## 📚 Table of Contents

* ✨ [Features](#-features)
* 🎥 [Demo Videos](#-demo-videos)
* 🛠️ [Tech Stack](#-tech-stack)
* 🧰 [Setup Instructions](#-setup-instructions)
* 📡 [API Documentation](#-api-documentation)

  * 🔐 [Authentication](#-authentication)
  * 🚚 [Trips](#-trips)
  * ⏱️ [Duty Statuses](#-duty-statuses)
  * 📜 [ELD Logs](#-eld-logs)
* 🚀 [Deployment](#-deployment)
* 🤝 [Contributing](#-contributing)
* 📞 [Contact](#-contact)
Loom: [Loom Demo Part 1](https://www.loom.com/share/1d01ecc9970e4f94948b65467d4adde8?sid=4843aea9-bea3-431d-9191-cc82b4263af0) 
Loom: [Loom Demo Part 1](https://www.loom.com/share/4b596e59e84643ebb6e8f870037e8dbf?sid=1963c16f-6906-4e43-8bd4-902add4f99b2) 
---

## ✨ Features

* ➕ CRUD operations for trips
* 🧑‍✈️ Manage driver duty statuses (e.g., `DRIVING`, `OFF_DUTY`)
* 📊 Generate and retrieve ELD logs for FMCSA compliance
* 🔐 JWT-based authentication
* 📍 Geolocation support for pickup/dropoff

---

## 🎥 Demo Videos

See RoadPulse in action! These Loom videos walk you through key backend features and API usage.

* ▶️ **Loom Demo Part 1**: [Watch Video](https://www.loom.com/share/1d01ecc9970e4f94948b65467d4adde8?sid=4843aea9-bea3-431d-9191-cc82b4263af0)
* ▶️ **Loom Demo Part 2**: [Watch Video](https://www.loom.com/share/4b596e59e84643ebb6e8f870037e8dbf?sid=1963c16f-6906-4e43-8bd4-902add4f99b2)

---

## 🛠️ Tech Stack

* 🧱 **Framework**: Django, Django REST Framework
* 🗃️ **Database**: PostgreSQL
* 🔐 **Auth**: JSON Web Tokens (JWT)
* ☁️ **Deployment**: Railway
* 🗺️ **Other Tools**: Django GIS, Celery (optional)

---

## 🧰 Setup Instructions

### 🧾 Prerequisites

* 🐍 Python 3.11+
* 🐘 PostgreSQL 15+
* ♻️ Redis (optional for Celery)
* 🧬 Git
* 🚂 Railway CLI

### 🔧 Installation

#### 1. Clone the Repo 📁

```bash
git clone https://github.com/VitthalGund/roadpulse-backend.git
cd roadpulse-backend
```

#### 2. Create Virtual Environment 🐍

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

#### 3. Install Dependencies 📦

```bash
pip install -r requirements.txt
```

#### 4. Configure Environment 🌐

Create a `.env` file:

```env
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:password@localhost:5432/roadpulse
ALLOWED_HOSTS=localhost,127.0.0.1
```

#### 5. Apply Migrations 🧬

```bash
python manage.py makemigrations
python manage.py migrate
```

#### 6. Create Superuser 🧑‍💻

```bash
python manage.py createsuperuser
```

#### 7. Run Server 🚀

```bash
python manage.py runserver
```

🌐 Access API at: `http://127.0.0.1:8000/api/`

---

### 🧪 Testing

```bash
python manage.py test
```

---

## 📡 API Documentation

**Base URL:** `http://127.0.0.1:8000/api/`

> ⚠️ All endpoints (except `/auth/login/` & `/auth/refresh/`) require a Bearer token:

```
Authorization: Bearer <access_token>
```

---

### 🔐 Authentication

#### 🔑 POST `/auth/login/`

Login to get access and refresh tokens.

**Request:**

```json
{
  "username": "string",
  "password": "string"
}
```

**Response:**

```json
{
  "access": "string",
  "refresh": "string"
}
```

**Curl Example:**

```bash
curl -X POST http://127.0.0.1:8000/api/auth/login/ \
-H "Content-Type: application/json" \
-d '{"username": "admin", "password": "password123"}'
```

---

#### 🔄 POST `/auth/refresh/`

Refresh your access token.

**Request:**

```json
{
  "refresh": "string"
}
```

**Response:**

```json
{
  "access": "string"
}
```

**Curl Example:**

```bash
curl -X POST http://127.0.0.1:8000/api/auth/refresh/ \
-H "Content-Type: application/json" \
-d '{"refresh": "<refresh_token>"}'
```

---

### 🚚 Trips

#### 📋 GET `/trips/`

List all trips.

**Query Params:**

* `status` (e.g., PLANNED)
* `page`, `limit`

**Example:**

```bash
curl -X GET http://127.0.0.1:8000/api/trips/?status=PLANNED \
-H "Authorization: Bearer <access_token>"
```

---

#### 🆕 POST `/trips/`

Create a trip.

**Curl Example:**

```bash
curl -X POST http://127.0.0.1:8000/api/trips/ \
-H "Authorization: Bearer <access_token>" \
-H "Content-Type: application/json" \
-d '{"vehicle": 1, "current_location_input": [72.8692035, 19.054999], "current_location_name": "Mumbai, India", "pickup_location_input": [73.8545071, 18.5213738], "pickup_location_name": "Pune, India", "dropoff_location_input": [73.7902364, 20.0112475], "dropoff_location_name": "Nashik, India", "current_cycle_hours": 6.0, "start_time": "2025-06-27T17:16:00Z", "status": "PLANNED"}'
```

---

#### 🔍 GET `/trips/{id}/`

Retrieve trip details.

#### ✏️ PATCH `/trips/{id}/`

Update a trip (e.g., change status).

#### 🗑️ DELETE `/trips/{id}/`

Delete a trip.

---

### ⏱️ Duty Statuses

#### 📋 GET `/trips/{id}/duty-status/`

List duty statuses.

#### ➕ POST `/trips/{id}/duty-status/`

Add duty status.

**Curl Example:**

```bash
curl -X POST http://127.0.0.1:8000/api/trips/1/duty-status/ \
-H "Authorization: Bearer <access_token>" \
-H "Content-Type: application/json" \
-d '{"status": "DRIVING", "start_time": "2025-06-27T17:16:00Z", "end_time": "2025-06-27T18:16:00Z", "location_description": "Mumbai to Pune", "remarks": "Highway driving"}'
```

---

### 📜 ELD Logs

#### 📖 GET `/trips/{id}/eld-logs/`

List logs for a trip.

#### ⚙️ POST `/trips/{id}/eld-logs/generate/`

Generate ELD logs for a given date.

**Example:**

```bash
curl -X POST http://127.0.0.1:8000/api/trips/1/eld-logs/generate/ \
-H "Authorization: Bearer <access_token>" \
-H "Content-Type: application/json" \
-d '{"date": "2025-06-27"}'
```

---

## 🚀 Deployment

### 🚂 Set Up Railway

```bash
npm install -g railway
railway login
```

### 🔗 Link Project

```bash
railway link
```

### ⚙️ Set Environment Vars

```bash
railway variables set SECRET_KEY=your-secret-key
railway variables set DATABASE_URL=your-postgres-url
```

### ⬆️ Deploy

```bash
git push origin main
railway run python manage.py migrate
```

Access API via Railway-provided URL 🌍

---

## 🤝 Contributing

1. 🍴 Fork the repo
2. 🧪 Create a feature branch
3. 📝 Commit changes
4. 🚀 Push to origin
5. 🧵 Open Pull Request

---

## 📞 Contact

* 👨‍💻 **Author**: Vitthal Gund
* 🔗 **GitHub**: [VitthalGund](https://github.com/VitthalGund)
* 💼 **LinkedIn**: [Vitthal Gund](https://linkedin.com/in/vitthal-gund)
* 📧 **Email**: `vitthalgund@gmail.com`
