# Laporan Hasil Pengujian API (API Testing Documentation)
## SkillBridge E-Learning Platform

> **Status Dokumen**: Final & Terverifikasi  
> **Tanggal Pengujian**: 26 Oktober 2026  
> **Target Environment**: `http://127.0.0.1:8000` (FastAPI + PostgreSQL)  
> **Metode Pengujian**: Automated Black-Box & Integration Security Testing  
> **Tingkat Kelulusan**: **100% (38/38 Test Cases PASSED)**

---

## 1. Ringkasan Eksekutif (Executive Summary)

Pengujian menyeluruh telah dilakukan pada seluruh endpoint backend **SkillBridge API**. Skenario pengujian mencakup verifikasi fungsionalitas utama (*happy path*), penanganan *edge cases*, validasi input data, kontrol akses berbasis peran (*Role-Based Access Control / RBAC*), integritas transaksi atomik (*ACID transactions*), keamanan pembayaran berbasis *webhook callback secret*, serta pencegahan celah keamanan *Privilege Escalation* dan *Insecure Direct Object References (IDOR)*.

### Metrik Utama Pengujian

| Indikator Metrik | Nilai | Keterangan |
|---|:---:|---|
| **Total Kasus Uji** | **38** | Seluruh modul sistem ter-cover |
| **Kasus Uji Lolos (Passed)** | **38** | **100% Sesuai Spesifikasi** |
| **Kasus Uji Gagal (Failed)** | **0** | 0 Cacat/Bug ditemukan |
| **Rata-rata Waktu Respon** | **412.27 ms** | Performa respon sangat responsif |
| **Tingkat Keberhasilan** | **100.0%** | Siap untuk produksi / integrasi frontend |

### Distribusi Pengujian Per Modul

| Modul Sistem | Total TC | Lolos | Gagal | Rata-rata Latensi | Status |
|---|:---:|:---:|:---:|:---:|:---:|
| **Authentication** | 10 | 10 | 0 | 551.72 ms | ✅ **PASSED** |
| **Courses** | 6 | 6 | 0 | 343.01 ms | ✅ **PASSED** |
| **Enrollments** | 5 | 5 | 0 | 359.99 ms | ✅ **PASSED** |
| **Payments** | 7 | 7 | 0 | 353.82 ms | ✅ **PASSED** |
| **Learning Progress** | 6 | 6 | 0 | 332.85 ms | ✅ **PASSED** |
| **Security & Isolation** | 4 | 4 | 0 | 454.28 ms | ✅ **PASSED** |

---

## 2. Standar Desain API & Pengujian

Seluruh endpoint SkillBridge API menerapkan format pembungkus respons (*standard envelope*) yang konsisten:

```json
{
  "message": "Deskripsi status operasi",
  "data": { ... }, // Objek atau list hasil (null jika gagal)
  "errors": null    // Array detail error jika ada validasi gagal
}
```

- **Autentikasi Pengguna**: Menggunakan protokol JSON Web Token (JWT) dengan skema `Bearer <token>` pada header `Authorization`.
- **Keamanan Webhook Gateway**: Menggunakan proteksi header `X-Callback-Token` yang dicocokkan dengan `PAYMENT_CALLBACK_SECRET` melalui perbandingan waktu konstan (*constant-time comparison*) `hmac.compare_digest`.
- **Prinsip Multi-Tenancy**: Mengembalikan status HTTP `404 Not Found` (alih-alih `403 Forbidden`) saat user mencoba mengakses resource milik pengguna lain, guna mencegah pembocoran keberadaan data (*information leakage*).

---

## 3. Dokumentasi Hasil Pengujian Lengkap Per Modul

### 📦 Modul: Authentication

#### `TC-AUTH-01`: Registrasi Akun Siswa Baru (Normal)

- **Status Hasil**: ✅ **PASSED**
- **Endpoint & Method**: `POST /auth/register`
- **HTTP Status Code**: Expected `201` | Actual `201`
- **Response Latency**: `633.63 ms`
- **Deskripsi & Analisis**: Mendaftarkan siswa baru dengan email unik dan format data valid.

**Request Headers:**
```json
{
  "Content-Type": "application/json"
}
```

**Request Body (Payload):**
```json
{
  "full_name": "Budi Santoso",
  "email": "budi.santoso.d56dc6@mail.com",
  "password": "Rahasia123!"
}
```

**Response Body:**
```json
{
  "message": "Registrasi berhasil",
  "data": {
    "id": "faadc776-1b6f-4229-99fe-57d0fd2bfde7",
    "full_name": "Budi Santoso",
    "email": "budi.santoso.d56dc6@mail.com",
    "role": "student"
  },
  "errors": null
}
```

---

#### `TC-AUTH-02`: Registrasi Email yang Sudah Terdaftar (Duplikat)

- **Status Hasil**: ✅ **PASSED**
- **Endpoint & Method**: `POST /auth/register`
- **HTTP Status Code**: Expected `409` | Actual `409`
- **Response Latency**: `555.67 ms`
- **Deskripsi & Analisis**: Sistem menolak registrasi email yang sudah ada dengan response HTTP 409 Conflict.

**Request Headers:**
```json
{
  "Content-Type": "application/json"
}
```

**Request Body (Payload):**
```json
{
  "full_name": "Budi Kloning",
  "email": "budi.santoso.d56dc6@mail.com",
  "password": "PasswordLain123!"
}
```

**Response Body:**
```json
{
  "message": "Email sudah terdaftar",
  "data": null,
  "errors": null
}
```

---

#### `TC-AUTH-03`: Registrasi Mencoba Injeksi Role Admin

- **Status Hasil**: ✅ **PASSED**
- **Endpoint & Method**: `POST /auth/register`
- **HTTP Status Code**: Expected `201` | Actual `201`
- **Response Latency**: `776.83 ms`
- **Deskripsi & Analisis**: Sistem mengabaikan input role dan memaksa role selalu 'student' untuk keamanan.

**Request Headers:**
```json
{
  "Content-Type": "application/json"
}
```

**Request Body (Payload):**
```json
{
  "full_name": "Attacker Role",
  "email": "attacker.862cc1@mail.com",
  "password": "Password123!",
  "role": "admin"
}
```

**Response Body:**
```json
{
  "message": "Registrasi berhasil",
  "data": {
    "id": "5dd0f563-3999-4d26-9aca-707da7a6cc21",
    "full_name": "Attacker Role",
    "email": "attacker.862cc1@mail.com",
    "role": "student"
  },
  "errors": null
}
```

---

#### `TC-AUTH-04`: Registrasi dengan Format Email dan Password Tidak Valid

- **Status Hasil**: ✅ **PASSED**
- **Endpoint & Method**: `POST /auth/register`
- **HTTP Status Code**: Expected `422` | Actual `422`
- **Response Latency**: `364.37 ms`
- **Deskripsi & Analisis**: Pydantic menangkap format email tidak valid dan panjang password kurang dari batas minimal.

**Request Headers:**
```json
{
  "Content-Type": "application/json"
}
```

**Request Body (Payload):**
```json
{
  "full_name": "",
  "email": "bukan-sebuah-email",
  "password": "123"
}
```

**Response Body:**
```json
{
  "message": "Validasi gagal",
  "data": null,
  "errors": [
    {
      "field": "full_name",
      "message": "String should have at least 2 characters"
    },
    {
      "field": "email",
      "message": "value is not a valid email address: An email address must have an @-sign."
    },
    {
      "field": "password",
      "message": "String should have at least 8 characters"
    }
  ]
}
```

---

#### `TC-AUTH-05`: Login Siswa dengan Kredensial Valid

- **Status Hasil**: ✅ **PASSED**
- **Endpoint & Method**: `POST /auth/login`
- **HTTP Status Code**: Expected `200` | Actual `200`
- **Response Latency**: `629.47 ms`
- **Deskripsi & Analisis**: Mengembalikan JWT access_token bertipe Bearer dan objek user.

**Request Headers:**
```json
{
  "Content-Type": "application/json"
}
```

**Request Body (Payload):**
```json
{
  "email": "budi.santoso.d56dc6@mail.com",
  "password": "Rahasia123!"
}
```

**Response Body:**
```json
{
  "message": "Login berhasil",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJmYWFkYzc3Ni0xYjZmLTQyMjktOTlmZS01N2QwZmQyYmZkZTciLCJyb2xlIjoic3R1ZGVudCIsImV4cCI6MTc5Mjk5OTI4MX0.IawObKxctkCZ8-8RAS11-PALqBvkdQTxSU2ExcRCYTI",
    "token_type": "bearer",
    "user": {
      "id": "faadc776-1b6f-4229-99fe-57d0fd2bfde7",
      "full_name": "Budi Santoso",
      "email": "budi.santoso.d56dc6@mail.com",
      "role": "student"
    }
  },
  "errors": null
}
```

---

#### `TC-AUTH-06`: Login Akun Admin Seed

- **Status Hasil**: ✅ **PASSED**
- **Endpoint & Method**: `POST /auth/login`
- **HTTP Status Code**: Expected `200` | Actual `200`
- **Response Latency**: `591.8 ms`
- **Deskripsi & Analisis**: Login akun default admin dari seed database.

**Request Headers:**
```json
{
  "Content-Type": "application/json"
}
```

**Request Body (Payload):**
```json
{
  "email": "admin@skillbridge.id",
  "password": "Admin123!"
}
```

**Response Body:**
```json
{
  "message": "Login berhasil",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1ZGUzNWIzMC03YzY5LTRlYzAtOTU2OC05YWMyMmQ2NzkyNDIiLCJyb2xlIjoiYWRtaW4iLCJleHAiOjE3OTI5OTkyODJ9.00U5qA_8vwZuyAp_x-XacGGU3Iu-4A5jMihqSsIiZiA",
    "token_type": "bearer",
    "user": {
      "id": "5de35b30-7c69-4ec0-9568-9ac22d679242",
      "full_name": "Admin SkillBridge",
      "email": "admin@skillbridge.id",
      "role": "admin"
    }
  },
  "errors": null
}
```

---

#### `TC-AUTH-07`: Login Akun Instruktur Seed

- **Status Hasil**: ✅ **PASSED**
- **Endpoint & Method**: `POST /auth/login`
- **HTTP Status Code**: Expected `200` | Actual `200`
- **Response Latency**: `574.76 ms`
- **Deskripsi & Analisis**: Login akun default instructor dari seed database.

**Request Headers:**
```json
{
  "Content-Type": "application/json"
}
```

**Request Body (Payload):**
```json
{
  "email": "instructor@skillbridge.id",
  "password": "Instruktur123!"
}
```

**Response Body:**
```json
{
  "message": "Login berhasil",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJmM2FjNjlkNy1mODExLTQxZTEtYjNlNy00Y2Q1ZDY5YmJiOGYiLCJyb2xlIjoiaW5zdHJ1Y3RvciIsImV4cCI6MTc5Mjk5OTI4Mn0.WUfiOI2o4umqi2H-LFOcI03hNv05Y7-1N7H9vR3wFho",
    "token_type": "bearer",
    "user": {
      "id": "f3ac69d7-f811-41e1-b3e7-4cd5d69bbb8f",
      "full_name": "Instruktur Satu",
      "email": "instructor@skillbridge.id",
      "role": "instructor"
    }
  },
  "errors": null
}
```

---

#### `TC-AUTH-08`: Login dengan Password Salah

- **Status Hasil**: ✅ **PASSED**
- **Endpoint & Method**: `POST /auth/login`
- **HTTP Status Code**: Expected `401` | Actual `401`
- **Response Latency**: `703.1 ms`
- **Deskripsi & Analisis**: Menghasilkan pesan generik 'Email atau password salah' untuk mencegah user enumeration.

**Request Headers:**
```json
{
  "Content-Type": "application/json"
}
```

**Request Body (Payload):**
```json
{
  "email": "budi.santoso.d56dc6@mail.com",
  "password": "PasswordSalahTotal!"
}
```

**Response Body:**
```json
{
  "message": "Email atau password salah",
  "data": null,
  "errors": null
}
```

---

#### `TC-AUTH-09`: Mendapatkan Data Profil Pengguna Aktif (/auth/me)

- **Status Hasil**: ✅ **PASSED**
- **Endpoint & Method**: `GET /auth/me`
- **HTTP Status Code**: Expected `200` | Actual `200`
- **Response Latency**: `351.09 ms`
- **Deskripsi & Analisis**: Memvalidasi header Authorization Bearer token dan mengembalikan info profil pemilik token.

**Request Headers:**
```json
{
  "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJmYWFkYzc3Ni0xYjZmLTQyMjktOTlmZS01N2QwZmQyYmZkZTciLCJyb2xlIjoic3R1ZGVudCIsImV4cCI6MTc5Mjk5OTI4MX0.IawObKxctkCZ8-8RAS11-PALqBvkdQTxSU2ExcRCYTI",
  "Content-Type": "application/json"
}
```

**Response Body:**
```json
{
  "message": "Berhasil",
  "data": {
    "id": "faadc776-1b6f-4229-99fe-57d0fd2bfde7",
    "full_name": "Budi Santoso",
    "email": "budi.santoso.d56dc6@mail.com",
    "role": "student"
  },
  "errors": null
}
```

---

#### `TC-AUTH-10`: Mengakses /auth/me Tanpa Bearer Token

- **Status Hasil**: ✅ **PASSED**
- **Endpoint & Method**: `GET /auth/me`
- **HTTP Status Code**: Expected `401` | Actual `401`
- **Response Latency**: `336.47 ms`
- **Deskripsi & Analisis**: Endpoint menolak permintaan anonim yang tidak membawa header otorisasi.

**Response Body:**
```json
{
  "message": "Token tidak dikirim",
  "data": null,
  "errors": null
}
```

---

### 📦 Modul: Courses

#### `TC-CRS-01`: Mendapatkan Katalog Kursus Terpublikasi (/courses)

- **Status Hasil**: ✅ **PASSED**
- **Endpoint & Method**: `GET /courses`
- **HTTP Status Code**: Expected `200` | Actual `200`
- **Response Latency**: `326.87 ms`
- **Deskripsi & Analisis**: Mengembalikan daftar kursus aktif dengan status is_published=true.

**Response Body:**
```json
{
  "message": "Berhasil",
  "data": [
    {
      "id": "11bce27b-7552-4295-98ce-5f27694c4f6e",
      "category_id": "7cbdc67e-082c-428c-a9dd-e9473680cafb",
      "instructor_id": "f3ac69d7-f811-41e1-b3e7-4cd5d69bbb8f",
      "title": "REST API dengan FastAPI",
      "description": "Dari nol sampai API siap produksi.",
      "price": "150000.00",
      "is_published": true
    }
  ],
  "errors": null
}
```

---

#### `TC-CRS-02`: Mendapatkan Detail Kursus (REST API dengan FastAPI)

- **Status Hasil**: ✅ **PASSED**
- **Endpoint & Method**: `GET /courses/11bce27b-7552-4295-98ce-5f27694c4f6e`
- **HTTP Status Code**: Expected `200` | Actual `200`
- **Response Latency**: `348.23 ms`
- **Deskripsi & Analisis**: Mengembalikan detail kursus lengkap dengan daftar modul pembelajaran (eager loaded).

**Response Body:**
```json
{
  "message": "Berhasil",
  "data": {
    "id": "11bce27b-7552-4295-98ce-5f27694c4f6e",
    "category_id": "7cbdc67e-082c-428c-a9dd-e9473680cafb",
    "instructor_id": "f3ac69d7-f811-41e1-b3e7-4cd5d69bbb8f",
    "title": "REST API dengan FastAPI",
    "description": "Dari nol sampai API siap produksi.",
    "price": "150000.00",
    "is_published": true,
    "modules": [
      {
        "id": "37b00b44-ffc1-48d2-977e-22387b561735",
        "title": "Pengenalan REST",
        "position": 1
      },
      {
        "id": "078b919a-eb3a-4444-81dd-1b7c3bb45abc",
        "title": "Routing dan Validasi",
        "position": 2
      },
      {
        "id": "f4deb50e-d230-463e-a7ef-8a0edb0c2786",
        "title": "Database dan ORM",
        "position": 3
      },
      {
        "id": "0f5d89dc-17fb-4e82-9297-379b967efaef",
        "title": "Autentikasi JWT",
        "position": 4
      }
    ]
  },
  "errors": null
}
```

---

#### `TC-CRS-03`: Mendapatkan Detail Kursus dengan UUID Acak yang Tidak Ada

- **Status Hasil**: ✅ **PASSED**
- **Endpoint & Method**: `GET /courses/006cbac3-7e48-4236-92ba-65237ff1bc86`
- **HTTP Status Code**: Expected `404` | Actual `404`
- **Response Latency**: `332.81 ms`
- **Deskripsi & Analisis**: Sistem mengembalikan 404 Not Found dengan format pesan error terstandar.

**Response Body:**
```json
{
  "message": "Kursus tidak ditemukan",
  "data": null,
  "errors": null
}
```

---

#### `TC-CRS-04`: Mendapatkan Detail Kursus dengan Parameter Bukan UUID

- **Status Hasil**: ✅ **PASSED**
- **Endpoint & Method**: `GET /courses/bukan-format-uuid-valid`
- **HTTP Status Code**: Expected `422` | Actual `422`
- **Response Latency**: `345.93 ms`
- **Deskripsi & Analisis**: Pydantic memvalidasi path parameter dan menolak format non-UUID dengan HTTP 422.

**Response Body:**
```json
{
  "message": "Validasi gagal",
  "data": null,
  "errors": [
    {
      "field": "course_id",
      "message": "Input should be a valid UUID, invalid character: found `u` at 1"
    }
  ]
}
```

---

#### `TC-CRS-05`: Membuat Kursus Baru oleh Instruktur (Role Instructor)

- **Status Hasil**: ✅ **PASSED**
- **Endpoint & Method**: `POST /courses`
- **HTTP Status Code**: Expected `201` | Actual `201`
- **Response Latency**: `347.17 ms`
- **Deskripsi & Analisis**: Role instructor diizinkan membuat kursus baru.

**Request Headers:**
```json
{
  "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJmM2FjNjlkNy1mODExLTQxZTEtYjNlNy00Y2Q1ZDY5YmJiOGYiLCJyb2xlIjoiaW5zdHJ1Y3RvciIsImV4cCI6MTc5Mjk5OTI4Mn0.WUfiOI2o4umqi2H-LFOcI03hNv05Y7-1N7H9vR3wFho",
  "Content-Type": "application/json"
}
```

**Request Body (Payload):**
```json
{
  "category_id": "7cbdc67e-082c-428c-a9dd-e9473680cafb",
  "title": "Arsitektur Microservices dengan Python",
  "description": "Membangun sistem microservices berskala tinggi menggunakan FastAPI dan Docker.",
  "price": "250000.00"
}
```

**Response Body:**
```json
{
  "message": "Kursus berhasil dibuat",
  "data": {
    "id": "61312474-dc6d-4385-8300-15553ffc0963",
    "category_id": "7cbdc67e-082c-428c-a9dd-e9473680cafb",
    "instructor_id": "f3ac69d7-f811-41e1-b3e7-4cd5d69bbb8f",
    "title": "Arsitektur Microservices dengan Python",
    "description": "Membangun sistem microservices berskala tinggi menggunakan FastAPI dan Docker.",
    "price": "250000.00",
    "is_published": true
  },
  "errors": null
}
```

---

#### `TC-CRS-06`: Siswa Mencoba Membuat Kursus Baru (Role Student)

- **Status Hasil**: ✅ **PASSED**
- **Endpoint & Method**: `POST /courses`
- **HTTP Status Code**: Expected `403` | Actual `403`
- **Response Latency**: `357.07 ms`
- **Deskripsi & Analisis**: RBAC menolak aksi pembuatan kursus oleh role student dengan HTTP 403 Forbidden.

**Request Headers:**
```json
{
  "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJmYWFkYzc3Ni0xYjZmLTQyMjktOTlmZS01N2QwZmQyYmZkZTciLCJyb2xlIjoic3R1ZGVudCIsImV4cCI6MTc5Mjk5OTI4MX0.IawObKxctkCZ8-8RAS11-PALqBvkdQTxSU2ExcRCYTI",
  "Content-Type": "application/json"
}
```

**Request Body (Payload):**
```json
{
  "category_id": "7cbdc67e-082c-428c-a9dd-e9473680cafb",
  "title": "Kursus Terlarang oleh Siswa",
  "price": "50000.00"
}
```

**Response Body:**
```json
{
  "message": "Anda tidak punya akses ke resource ini",
  "data": null,
  "errors": null
}
```

---

### 📦 Modul: Enrollments

#### `TC-ENR-01`: Pendaftaran Kursus oleh Siswa (Auto Order & Invoice)

- **Status Hasil**: ✅ **PASSED**
- **Endpoint & Method**: `POST /enrollments`
- **HTTP Status Code**: Expected `201` | Actual `201`
- **Response Latency**: `395.39 ms`
- **Deskripsi & Analisis**: Dalam satu transaksi database: dibuat Order, Invoice (status unpaid), dan Enrollment (pending_payment).

**Request Headers:**
```json
{
  "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJmYWFkYzc3Ni0xYjZmLTQyMjktOTlmZS01N2QwZmQyYmZkZTciLCJyb2xlIjoic3R1ZGVudCIsImV4cCI6MTc5Mjk5OTI4MX0.IawObKxctkCZ8-8RAS11-PALqBvkdQTxSU2ExcRCYTI",
  "Content-Type": "application/json"
}
```

**Request Body (Payload):**
```json
{
  "course_id": "11bce27b-7552-4295-98ce-5f27694c4f6e"
}
```

**Response Body:**
```json
{
  "message": "Enrollment dibuat, silakan lakukan pembayaran",
  "data": {
    "enrollment": {
      "id": "4c055b75-c3de-4d16-8d52-df8777eea324",
      "course_id": "11bce27b-7552-4295-98ce-5f27694c4f6e",
      "order_id": "b7ffb08a-eeda-4f6a-89c2-d1dd1aec7dbd",
      "status": "pending_payment",
      "created_at": "2026-10-26T06:21:26.631999Z"
    },
    "order": {
      "id": "b7ffb08a-eeda-4f6a-89c2-d1dd1aec7dbd",
      "total_amount": "150000.00",
      "status": "pending"
    },
    "invoice": {
      "id": "3f2a0629-8cf8-4a12-88f0-5f2651514461",
      "invoice_number": "INV-20261026-B7FFB08A",
      "amount": "150000.00",
      "status": "unpaid"
    }
  },
  "errors": null
}
```

---

#### `TC-ENR-02`: Siswa Mendaftar Ulang ke Kursus yang Sama (Duplikasi)

- **Status Hasil**: ✅ **PASSED**
- **Endpoint & Method**: `POST /enrollments`
- **HTTP Status Code**: Expected `409` | Actual `409`
- **Response Latency**: `357.42 ms`
- **Deskripsi & Analisis**: Mencegah duplikasi enrollment untuk kursus dan siswa yang sama.

**Request Headers:**
```json
{
  "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJmYWFkYzc3Ni0xYjZmLTQyMjktOTlmZS01N2QwZmQyYmZkZTciLCJyb2xlIjoic3R1ZGVudCIsImV4cCI6MTc5Mjk5OTI4MX0.IawObKxctkCZ8-8RAS11-PALqBvkdQTxSU2ExcRCYTI",
  "Content-Type": "application/json"
}
```

**Request Body (Payload):**
```json
{
  "course_id": "11bce27b-7552-4295-98ce-5f27694c4f6e"
}
```

**Response Body:**
```json
{
  "message": "Anda sudah terdaftar di kursus ini",
  "data": null,
  "errors": null
}
```

---

#### `TC-ENR-03`: Admin Mencoba Mendaftar Kursus (Non-Student)

- **Status Hasil**: ✅ **PASSED**
- **Endpoint & Method**: `POST /enrollments`
- **HTTP Status Code**: Expected `403` | Actual `403`
- **Response Latency**: `356.24 ms`
- **Deskripsi & Analisis**: Hanya akun dengan role student yang diperbolehkan mendaftar kursus.

**Request Headers:**
```json
{
  "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1ZGUzNWIzMC03YzY5LTRlYzAtOTU2OC05YWMyMmQ2NzkyNDIiLCJyb2xlIjoiYWRtaW4iLCJleHAiOjE3OTI5OTkyODJ9.00U5qA_8vwZuyAp_x-XacGGU3Iu-4A5jMihqSsIiZiA",
  "Content-Type": "application/json"
}
```

**Request Body (Payload):**
```json
{
  "course_id": "11bce27b-7552-4295-98ce-5f27694c4f6e"
}
```

**Response Body:**
```json
{
  "message": "Anda tidak punya akses ke resource ini",
  "data": null,
  "errors": null
}
```

---

#### `TC-ENR-04`: Mengecek /enrollments/mycourses Sebelum Pembayaran

- **Status Hasil**: ✅ **PASSED**
- **Endpoint & Method**: `GET /enrollments/mycourses`
- **HTTP Status Code**: Expected `200` | Actual `200`
- **Response Latency**: `357.75 ms`
- **Deskripsi & Analisis**: Memastikan kursus terdaftar muncul di daftar kursus siswa dengan status pending_payment.

**Request Headers:**
```json
{
  "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJmYWFkYzc3Ni0xYjZmLTQyMjktOTlmZS01N2QwZmQyYmZkZTciLCJyb2xlIjoic3R1ZGVudCIsImV4cCI6MTc5Mjk5OTI4MX0.IawObKxctkCZ8-8RAS11-PALqBvkdQTxSU2ExcRCYTI",
  "Content-Type": "application/json"
}
```

**Response Body:**
```json
{
  "message": "Berhasil",
  "data": [
    {
      "enrollment_id": "4c055b75-c3de-4d16-8d52-df8777eea324",
      "course_id": "11bce27b-7552-4295-98ce-5f27694c4f6e",
      "title": "REST API dengan FastAPI",
      "status": "pending_payment",
      "completed_modules": 0,
      "total_modules": 4,
      "progress_percentage": 0.0
    }
  ],
  "errors": null
}
```

---

#### `TC-ENR-05`: Siswa Mencoba Memperbarui Progress Modul Sebelum Melunasi Pembayaran

- **Status Hasil**: ✅ **PASSED**
- **Endpoint & Method**: `PATCH /enrollments/4c055b75-c3de-4d16-8d52-df8777eea324/progress`
- **HTTP Status Code**: Expected `403` | Actual `403`
- **Response Latency**: `333.14 ms`
- **Deskripsi & Analisis**: Akses materi/progress terkunci sampai invoice berhasil dibayar.

**Request Headers:**
```json
{
  "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJmYWFkYzc3Ni0xYjZmLTQyMjktOTlmZS01N2QwZmQyYmZkZTciLCJyb2xlIjoic3R1ZGVudCIsImV4cCI6MTc5Mjk5OTI4MX0.IawObKxctkCZ8-8RAS11-PALqBvkdQTxSU2ExcRCYTI",
  "Content-Type": "application/json"
}
```

**Request Body (Payload):**
```json
{
  "module_id": "37b00b44-ffc1-48d2-977e-22387b561735",
  "status": "completed"
}
```

**Response Body:**
```json
{
  "message": "Enrollment belum aktif, selesaikan pembayaran terlebih dahulu",
  "data": null,
  "errors": null
}
```

---

### 📦 Modul: Payments

#### `TC-PAY-01`: Inisiasi Pembayaran Invoice (Bank Transfer)

- **Status Hasil**: ✅ **PASSED**
- **Endpoint & Method**: `POST /payments`
- **HTTP Status Code**: Expected `201` | Actual `201`
- **Response Latency**: `338.92 ms`
- **Deskripsi & Analisis**: Membuat record Payment berstatus pending dan menghasilkan external_ref unik.

**Request Headers:**
```json
{
  "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJmYWFkYzc3Ni0xYjZmLTQyMjktOTlmZS01N2QwZmQyYmZkZTciLCJyb2xlIjoic3R1ZGVudCIsImV4cCI6MTc5Mjk5OTI4MX0.IawObKxctkCZ8-8RAS11-PALqBvkdQTxSU2ExcRCYTI",
  "Content-Type": "application/json"
}
```

**Request Body (Payload):**
```json
{
  "invoice_id": "3f2a0629-8cf8-4a12-88f0-5f2651514461",
  "method": "bank_transfer"
}
```

**Response Body:**
```json
{
  "message": "Pembayaran dibuat, menunggu konfirmasi gateway",
  "data": {
    "id": "e52311a7-93a0-498c-bb96-38f4aea9d4f7",
    "invoice_id": "3f2a0629-8cf8-4a12-88f0-5f2651514461",
    "method": "bank_transfer",
    "external_ref": "SB-EA451674739A",
    "amount": "150000.00",
    "status": "pending"
  },
  "errors": null
}
```

---

#### `TC-PAY-02`: Inisiasi Pembayaran Baru saat Masih Ada Transaksi Pending

- **Status Hasil**: ✅ **PASSED**
- **Endpoint & Method**: `POST /payments`
- **HTTP Status Code**: Expected `409` | Actual `409`
- **Response Latency**: `349.96 ms`
- **Deskripsi & Analisis**: Sistem mencegah spam pembayaran ganda pada invoice yang sama.

**Request Headers:**
```json
{
  "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJmYWFkYzc3Ni0xYjZmLTQyMjktOTlmZS01N2QwZmQyYmZkZTciLCJyb2xlIjoic3R1ZGVudCIsImV4cCI6MTc5Mjk5OTI4MX0.IawObKxctkCZ8-8RAS11-PALqBvkdQTxSU2ExcRCYTI",
  "Content-Type": "application/json"
}
```

**Request Body (Payload):**
```json
{
  "invoice_id": "3f2a0629-8cf8-4a12-88f0-5f2651514461",
  "method": "qris"
}
```

**Response Body:**
```json
{
  "message": "Masih ada pembayaran yang menunggu untuk invoice ini",
  "data": null,
  "errors": null
}
```

---

#### `TC-PAY-03`: Callback Gateway Tanpa Header X-Callback-Token

- **Status Hasil**: ✅ **PASSED**
- **Endpoint & Method**: `POST /payments/callback`
- **HTTP Status Code**: Expected `401` | Actual `401`
- **Response Latency**: `305.37 ms`
- **Deskripsi & Analisis**: Melindungi webhook dari pemalsuan eksternal tanpa rahasia callback.

**Request Headers:**
```json
{
  "Content-Type": "application/json"
}
```

**Request Body (Payload):**
```json
{
  "external_ref": "SB-EA451674739A",
  "status": "paid",
  "amount": "150000.00"
}
```

**Response Body:**
```json
{
  "message": "Callback token tidak valid",
  "data": null,
  "errors": null
}
```

---

#### `TC-PAY-04`: Callback Gateway dengan X-Callback-Token Salah/Palsu

- **Status Hasil**: ✅ **PASSED**
- **Endpoint & Method**: `POST /payments/callback`
- **HTTP Status Code**: Expected `401` | Actual `401`
- **Response Latency**: `340.14 ms`
- **Deskripsi & Analisis**: Perbandingan hmac.compare_digest menolak secret yang tidak cocok.

**Request Headers:**
```json
{
  "Content-Type": "application/json",
  "X-Callback-Token": "token-palsu-ngawur"
}
```

**Request Body (Payload):**
```json
{
  "external_ref": "SB-EA451674739A",
  "status": "paid",
  "amount": "150000.00"
}
```

**Response Body:**
```json
{
  "message": "Callback token tidak valid",
  "data": null,
  "errors": null
}
```

---

#### `TC-PAY-05`: Callback Gateway dengan Nominal yang Tidak Cocok dengan Tagihan

- **Status Hasil**: ✅ **PASSED**
- **Endpoint & Method**: `POST /payments/callback`
- **HTTP Status Code**: Expected `422` | Actual `422`
- **Response Latency**: `321.63 ms`
- **Deskripsi & Analisis**: Integritas nominal terjaga; callback gagal jika nominal berbeda dengan tagihan invoice.

**Request Headers:**
```json
{
  "Content-Type": "application/json",
  "X-Callback-Token": "rahasia-callback-gateway"
}
```

**Request Body (Payload):**
```json
{
  "external_ref": "SB-EA451674739A",
  "status": "paid",
  "amount": "9999.00"
}
```

**Response Body:**
```json
{
  "message": "Nominal callback tidak sesuai dengan tagihan",
  "data": null,
  "errors": null
}
```

---

#### `TC-PAY-06`: Callback Gateway Pelunasan Berhasil (Status: paid)

- **Status Hasil**: ✅ **PASSED**
- **Endpoint & Method**: `POST /payments/callback`
- **HTTP Status Code**: Expected `200` | Actual `200`
- **Response Latency**: `431.54 ms`
- **Deskripsi & Analisis**: Mengubah status Payment menjadi paid, Invoice paid, Order paid, dan Enrollment active dalam 1 transaksi.

**Request Headers:**
```json
{
  "Content-Type": "application/json",
  "X-Callback-Token": "rahasia-callback-gateway"
}
```

**Request Body (Payload):**
```json
{
  "external_ref": "SB-EA451674739A",
  "status": "paid",
  "amount": "150000.00"
}
```

**Response Body:**
```json
{
  "message": "Pembayaran berhasil, enrollment aktif",
  "data": {
    "id": "e52311a7-93a0-498c-bb96-38f4aea9d4f7",
    "invoice_id": "3f2a0629-8cf8-4a12-88f0-5f2651514461",
    "method": "bank_transfer",
    "external_ref": "SB-EA451674739A",
    "amount": "150000.00",
    "status": "paid"
  },
  "errors": null
}
```

---

#### `TC-PAY-07`: Pengujian Idempotensi Callback Gateway (Dipanggil Ulang)

- **Status Hasil**: ✅ **PASSED**
- **Endpoint & Method**: `POST /payments/callback`
- **HTTP Status Code**: Expected `200` | Actual `200`
- **Response Latency**: `389.15 ms`
- **Deskripsi & Analisis**: Sistem mengembalikan 200 'Callback sudah pernah diproses' tanpa mengeksekusi mutasi ulang.

**Request Headers:**
```json
{
  "Content-Type": "application/json",
  "X-Callback-Token": "rahasia-callback-gateway"
}
```

**Request Body (Payload):**
```json
{
  "external_ref": "SB-EA451674739A",
  "status": "paid",
  "amount": "150000.00"
}
```

**Response Body:**
```json
{
  "message": "Callback sudah pernah diproses",
  "data": {
    "id": "e52311a7-93a0-498c-bb96-38f4aea9d4f7",
    "invoice_id": "3f2a0629-8cf8-4a12-88f0-5f2651514461",
    "method": "bank_transfer",
    "external_ref": "SB-EA451674739A",
    "amount": "150000.00",
    "status": "paid"
  },
  "errors": null
}
```

---

### 📦 Modul: Learning Progress

#### `TC-PRG-01`: Mengecek Status Enrollment di /enrollments/mycourses Pasca Pembayaran

- **Status Hasil**: ✅ **PASSED**
- **Endpoint & Method**: `GET /enrollments/mycourses`
- **HTTP Status Code**: Expected `200` | Actual `200`
- **Response Latency**: `331.83 ms`
- **Deskripsi & Analisis**: Memastikan enrollment telah berubah status menjadi 'active' dengan total modul pembelajaran 4.

**Request Headers:**
```json
{
  "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJmYWFkYzc3Ni0xYjZmLTQyMjktOTlmZS01N2QwZmQyYmZkZTciLCJyb2xlIjoic3R1ZGVudCIsImV4cCI6MTc5Mjk5OTI4MX0.IawObKxctkCZ8-8RAS11-PALqBvkdQTxSU2ExcRCYTI",
  "Content-Type": "application/json"
}
```

**Response Body:**
```json
{
  "message": "Berhasil",
  "data": [
    {
      "enrollment_id": "4c055b75-c3de-4d16-8d52-df8777eea324",
      "course_id": "11bce27b-7552-4295-98ce-5f27694c4f6e",
      "title": "REST API dengan FastAPI",
      "status": "active",
      "completed_modules": 0,
      "total_modules": 4,
      "progress_percentage": 0.0
    }
  ],
  "errors": null
}
```

---

#### `TC-PRG-02`: Memperbarui Modul 1 Menjadi Selesai (Progress 25%)

- **Status Hasil**: ✅ **PASSED**
- **Endpoint & Method**: `PATCH /enrollments/4c055b75-c3de-4d16-8d52-df8777eea324/progress`
- **HTTP Status Code**: Expected `200` | Actual `200`
- **Response Latency**: `341.51 ms`
- **Deskripsi & Analisis**: Status modul 1 selesai, progress bertambah menjadi 25.0%.

**Request Headers:**
```json
{
  "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJmYWFkYzc3Ni0xYjZmLTQyMjktOTlmZS01N2QwZmQyYmZkZTciLCJyb2xlIjoic3R1ZGVudCIsImV4cCI6MTc5Mjk5OTI4MX0.IawObKxctkCZ8-8RAS11-PALqBvkdQTxSU2ExcRCYTI",
  "Content-Type": "application/json"
}
```

**Request Body (Payload):**
```json
{
  "module_id": "37b00b44-ffc1-48d2-977e-22387b561735",
  "status": "completed"
}
```

**Response Body:**
```json
{
  "message": "Progress diperbarui",
  "data": {
    "enrollment_id": "4c055b75-c3de-4d16-8d52-df8777eea324",
    "enrollment_status": "active",
    "completed_modules": 1,
    "total_modules": 4,
    "progress_percentage": 25.0
  },
  "errors": null
}
```

---

#### `TC-PRG-03.2`: Menyelesaikan Modul 2 (Routing dan Validasi)

- **Status Hasil**: ✅ **PASSED**
- **Endpoint & Method**: `PATCH /enrollments/4c055b75-c3de-4d16-8d52-df8777eea324/progress`
- **HTTP Status Code**: Expected `200` | Actual `200`
- **Response Latency**: `349.47 ms`
- **Deskripsi & Analisis**: Menyelesaikan modul 2 dari 4.

**Request Headers:**
```json
{
  "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJmYWFkYzc3Ni0xYjZmLTQyMjktOTlmZS01N2QwZmQyYmZkZTciLCJyb2xlIjoic3R1ZGVudCIsImV4cCI6MTc5Mjk5OTI4MX0.IawObKxctkCZ8-8RAS11-PALqBvkdQTxSU2ExcRCYTI",
  "Content-Type": "application/json"
}
```

**Request Body (Payload):**
```json
{
  "module_id": "078b919a-eb3a-4444-81dd-1b7c3bb45abc",
  "status": "completed"
}
```

**Response Body:**
```json
{
  "message": "Progress diperbarui",
  "data": {
    "enrollment_id": "4c055b75-c3de-4d16-8d52-df8777eea324",
    "enrollment_status": "active",
    "completed_modules": 2,
    "total_modules": 4,
    "progress_percentage": 50.0
  },
  "errors": null
}
```

---

#### `TC-PRG-03.3`: Menyelesaikan Modul 3 (Database dan ORM)

- **Status Hasil**: ✅ **PASSED**
- **Endpoint & Method**: `PATCH /enrollments/4c055b75-c3de-4d16-8d52-df8777eea324/progress`
- **HTTP Status Code**: Expected `200` | Actual `200`
- **Response Latency**: `326.44 ms`
- **Deskripsi & Analisis**: Menyelesaikan modul 3 dari 4.

**Request Headers:**
```json
{
  "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJmYWFkYzc3Ni0xYjZmLTQyMjktOTlmZS01N2QwZmQyYmZkZTciLCJyb2xlIjoic3R1ZGVudCIsImV4cCI6MTc5Mjk5OTI4MX0.IawObKxctkCZ8-8RAS11-PALqBvkdQTxSU2ExcRCYTI",
  "Content-Type": "application/json"
}
```

**Request Body (Payload):**
```json
{
  "module_id": "f4deb50e-d230-463e-a7ef-8a0edb0c2786",
  "status": "completed"
}
```

**Response Body:**
```json
{
  "message": "Progress diperbarui",
  "data": {
    "enrollment_id": "4c055b75-c3de-4d16-8d52-df8777eea324",
    "enrollment_status": "active",
    "completed_modules": 3,
    "total_modules": 4,
    "progress_percentage": 75.0
  },
  "errors": null
}
```

---

#### `TC-PRG-03.4`: Menyelesaikan Modul 4 (Autentikasi JWT)

- **Status Hasil**: ✅ **PASSED**
- **Endpoint & Method**: `PATCH /enrollments/4c055b75-c3de-4d16-8d52-df8777eea324/progress`
- **HTTP Status Code**: Expected `200` | Actual `200`
- **Response Latency**: `328.5 ms`
- **Deskripsi & Analisis**: Menyelesaikan modul 4 dari 4.

**Request Headers:**
```json
{
  "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJmYWFkYzc3Ni0xYjZmLTQyMjktOTlmZS01N2QwZmQyYmZkZTciLCJyb2xlIjoic3R1ZGVudCIsImV4cCI6MTc5Mjk5OTI4MX0.IawObKxctkCZ8-8RAS11-PALqBvkdQTxSU2ExcRCYTI",
  "Content-Type": "application/json"
}
```

**Request Body (Payload):**
```json
{
  "module_id": "0f5d89dc-17fb-4e82-9297-379b967efaef",
  "status": "completed"
}
```

**Response Body:**
```json
{
  "message": "Progress diperbarui",
  "data": {
    "enrollment_id": "4c055b75-c3de-4d16-8d52-df8777eea324",
    "enrollment_status": "completed",
    "completed_modules": 4,
    "total_modules": 4,
    "progress_percentage": 100.0
  },
  "errors": null
}
```

---

#### `TC-PRG-04`: Verifikasi Status Akhir Kursus (Status: completed, 100%)

- **Status Hasil**: ✅ **PASSED**
- **Endpoint & Method**: `GET /enrollments/mycourses`
- **HTTP Status Code**: Expected `200` | Actual `200`
- **Response Latency**: `319.33 ms`
- **Deskripsi & Analisis**: Seluruh modul tuntas diselesaikan; status enrollment otomatis berubah menjadi 'completed'.

**Request Headers:**
```json
{
  "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJmYWFkYzc3Ni0xYjZmLTQyMjktOTlmZS01N2QwZmQyYmZkZTciLCJyb2xlIjoic3R1ZGVudCIsImV4cCI6MTc5Mjk5OTI4MX0.IawObKxctkCZ8-8RAS11-PALqBvkdQTxSU2ExcRCYTI",
  "Content-Type": "application/json"
}
```

**Response Body:**
```json
{
  "message": "Berhasil",
  "data": [
    {
      "enrollment_id": "4c055b75-c3de-4d16-8d52-df8777eea324",
      "course_id": "11bce27b-7552-4295-98ce-5f27694c4f6e",
      "title": "REST API dengan FastAPI",
      "status": "completed",
      "completed_modules": 4,
      "total_modules": 4,
      "progress_percentage": 100.0
    }
  ],
  "errors": null
}
```

---

### 📦 Modul: Security & Isolation

#### `TC-SEC-01`: Registrasi Akun Siswa Kedua (User Lain)

- **Status Hasil**: ✅ **PASSED**
- **Endpoint & Method**: `POST /auth/register`
- **HTTP Status Code**: Expected `201` | Actual `201`
- **Response Latency**: `584.19 ms`
- **Deskripsi & Analisis**: Membuat pengguna siswa kedua untuk menguji isolasi data.

**Request Headers:**
```json
{
  "Content-Type": "application/json"
}
```

**Request Body (Payload):**
```json
{
  "full_name": "Ahmad Dani",
  "email": "ahmad.siswa.1f1206@mail.com",
  "password": "PasswordLain123!"
}
```

**Response Body:**
```json
{
  "message": "Registrasi berhasil",
  "data": {
    "id": "3d26206b-dcf5-4b34-81e1-2057ad76e6fd",
    "full_name": "Ahmad Dani",
    "email": "ahmad.siswa.1f1206@mail.com",
    "role": "student"
  },
  "errors": null
}
```

---

#### `TC-SEC-02`: Login Akun Siswa Kedua

- **Status Hasil**: ✅ **PASSED**
- **Endpoint & Method**: `POST /auth/login`
- **HTTP Status Code**: Expected `200` | Actual `200`
- **Response Latency**: `578.44 ms`
- **Deskripsi & Analisis**: Mendapatkan token untuk siswa kedua.

**Request Headers:**
```json
{
  "Content-Type": "application/json"
}
```

**Request Body (Payload):**
```json
{
  "email": "ahmad.siswa.1f1206@mail.com",
  "password": "PasswordLain123!"
}
```

**Response Body:**
```json
{
  "message": "Login berhasil",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIzZDI2MjA2Yi1kY2Y1LTRiMzQtODFlMS0yMDU3YWQ3NmU2ZmQiLCJyb2xlIjoic3R1ZGVudCIsImV4cCI6MTc5Mjk5OTI5M30.ujzMvU8FJL23p4Fpd-GS23cpHd1_0zoPMylqXiq0Ttg",
    "token_type": "bearer",
    "user": {
      "id": "3d26206b-dcf5-4b34-81e1-2057ad76e6fd",
      "full_name": "Ahmad Dani",
      "email": "ahmad.siswa.1f1206@mail.com",
      "role": "student"
    }
  },
  "errors": null
}
```

---

#### `TC-SEC-03`: Siswa Lain Mencoba Mengakses/Mengubah Progress Siswa Pertama

- **Status Hasil**: ✅ **PASSED**
- **Endpoint & Method**: `PATCH /enrollments/4c055b75-c3de-4d16-8d52-df8777eea324/progress`
- **HTTP Status Code**: Expected `404` | Actual `404`
- **Response Latency**: `313.97 ms`
- **Deskripsi & Analisis**: Mengembalikan 404 Not Found (bukan 403) agar tidak membocorkan eksistensi data milik siswa lain.

**Request Headers:**
```json
{
  "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIzZDI2MjA2Yi1kY2Y1LTRiMzQtODFlMS0yMDU3YWQ3NmU2ZmQiLCJyb2xlIjoic3R1ZGVudCIsImV4cCI6MTc5Mjk5OTI5M30.ujzMvU8FJL23p4Fpd-GS23cpHd1_0zoPMylqXiq0Ttg",
  "Content-Type": "application/json"
}
```

**Request Body (Payload):**
```json
{
  "module_id": "37b00b44-ffc1-48d2-977e-22387b561735",
  "status": "completed"
}
```

**Response Body:**
```json
{
  "message": "Enrollment tidak ditemukan",
  "data": null,
  "errors": null
}
```

---

#### `TC-SEC-04`: Siswa Lain Mencoba Membayar Invoice Siswa Pertama

- **Status Hasil**: ✅ **PASSED**
- **Endpoint & Method**: `POST /payments`
- **HTTP Status Code**: Expected `404` | Actual `404`
- **Response Latency**: `340.53 ms`
- **Deskripsi & Analisis**: Sistem mengisolasi akses invoice; siswa lain tidak dapat memproses invoice milik siswa pertama.

**Request Headers:**
```json
{
  "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIzZDI2MjA2Yi1kY2Y1LTRiMzQtODFlMS0yMDU3YWQ3NmU2ZmQiLCJyb2xlIjoic3R1ZGVudCIsImV4cCI6MTc5Mjk5OTI5M30.ujzMvU8FJL23p4Fpd-GS23cpHd1_0zoPMylqXiq0Ttg",
  "Content-Type": "application/json"
}
```

**Request Body (Payload):**
```json
{
  "invoice_id": "3f2a0629-8cf8-4a12-88f0-5f2651514461",
  "method": "qris"
}
```

**Response Body:**
```json
{
  "message": "Invoice tidak ditemukan",
  "data": null,
  "errors": null
}
```

---

## 4. Tabel Rekapitulasi 38 Kasus Uji (Test Case Matrix)

| No | Test ID | Modul | Method | Endpoint Path | Status Harapan | Status Aktual | Latensi | Hasil |
|:--:|:---|:---|:---:|:---|:---:|:---:|:---:|:---:|
| 1 | `TC-AUTH-01` | Authentication | `POST` | `/auth/register` | `201` | `201` | 633.63 ms | ✅ PASS |
| 2 | `TC-AUTH-02` | Authentication | `POST` | `/auth/register` | `409` | `409` | 555.67 ms | ✅ PASS |
| 3 | `TC-AUTH-03` | Authentication | `POST` | `/auth/register` | `201` | `201` | 776.83 ms | ✅ PASS |
| 4 | `TC-AUTH-04` | Authentication | `POST` | `/auth/register` | `422` | `422` | 364.37 ms | ✅ PASS |
| 5 | `TC-AUTH-05` | Authentication | `POST` | `/auth/login` | `200` | `200` | 629.47 ms | ✅ PASS |
| 6 | `TC-AUTH-06` | Authentication | `POST` | `/auth/login` | `200` | `200` | 591.8 ms | ✅ PASS |
| 7 | `TC-AUTH-07` | Authentication | `POST` | `/auth/login` | `200` | `200` | 574.76 ms | ✅ PASS |
| 8 | `TC-AUTH-08` | Authentication | `POST` | `/auth/login` | `401` | `401` | 703.1 ms | ✅ PASS |
| 9 | `TC-AUTH-09` | Authentication | `GET` | `/auth/me` | `200` | `200` | 351.09 ms | ✅ PASS |
| 10 | `TC-AUTH-10` | Authentication | `GET` | `/auth/me` | `401` | `401` | 336.47 ms | ✅ PASS |
| 11 | `TC-CRS-01` | Courses | `GET` | `/courses` | `200` | `200` | 326.87 ms | ✅ PASS |
| 12 | `TC-CRS-02` | Courses | `GET` | `/courses/11bce27b-7552-4295-98ce-5f27694c4f6e` | `200` | `200` | 348.23 ms | ✅ PASS |
| 13 | `TC-CRS-03` | Courses | `GET` | `/courses/006cbac3-7e48-4236-92ba-65237ff1bc86` | `404` | `404` | 332.81 ms | ✅ PASS |
| 14 | `TC-CRS-04` | Courses | `GET` | `/courses/bukan-format-uuid-valid` | `422` | `422` | 345.93 ms | ✅ PASS |
| 15 | `TC-CRS-05` | Courses | `POST` | `/courses` | `201` | `201` | 347.17 ms | ✅ PASS |
| 16 | `TC-CRS-06` | Courses | `POST` | `/courses` | `403` | `403` | 357.07 ms | ✅ PASS |
| 17 | `TC-ENR-01` | Enrollments | `POST` | `/enrollments` | `201` | `201` | 395.39 ms | ✅ PASS |
| 18 | `TC-ENR-02` | Enrollments | `POST` | `/enrollments` | `409` | `409` | 357.42 ms | ✅ PASS |
| 19 | `TC-ENR-03` | Enrollments | `POST` | `/enrollments` | `403` | `403` | 356.24 ms | ✅ PASS |
| 20 | `TC-ENR-04` | Enrollments | `GET` | `/enrollments/mycourses` | `200` | `200` | 357.75 ms | ✅ PASS |
| 21 | `TC-ENR-05` | Enrollments | `PATCH` | `/enrollments/4c055b75-c3de-4d16-8d52-df8777eea324/progress` | `403` | `403` | 333.14 ms | ✅ PASS |
| 22 | `TC-PAY-01` | Payments | `POST` | `/payments` | `201` | `201` | 338.92 ms | ✅ PASS |
| 23 | `TC-PAY-02` | Payments | `POST` | `/payments` | `409` | `409` | 349.96 ms | ✅ PASS |
| 24 | `TC-PAY-03` | Payments | `POST` | `/payments/callback` | `401` | `401` | 305.37 ms | ✅ PASS |
| 25 | `TC-PAY-04` | Payments | `POST` | `/payments/callback` | `401` | `401` | 340.14 ms | ✅ PASS |
| 26 | `TC-PAY-05` | Payments | `POST` | `/payments/callback` | `422` | `422` | 321.63 ms | ✅ PASS |
| 27 | `TC-PAY-06` | Payments | `POST` | `/payments/callback` | `200` | `200` | 431.54 ms | ✅ PASS |
| 28 | `TC-PAY-07` | Payments | `POST` | `/payments/callback` | `200` | `200` | 389.15 ms | ✅ PASS |
| 29 | `TC-PRG-01` | Learning Progress | `GET` | `/enrollments/mycourses` | `200` | `200` | 331.83 ms | ✅ PASS |
| 30 | `TC-PRG-02` | Learning Progress | `PATCH` | `/enrollments/4c055b75-c3de-4d16-8d52-df8777eea324/progress` | `200` | `200` | 341.51 ms | ✅ PASS |
| 31 | `TC-PRG-03.2` | Learning Progress | `PATCH` | `/enrollments/4c055b75-c3de-4d16-8d52-df8777eea324/progress` | `200` | `200` | 349.47 ms | ✅ PASS |
| 32 | `TC-PRG-03.3` | Learning Progress | `PATCH` | `/enrollments/4c055b75-c3de-4d16-8d52-df8777eea324/progress` | `200` | `200` | 326.44 ms | ✅ PASS |
| 33 | `TC-PRG-03.4` | Learning Progress | `PATCH` | `/enrollments/4c055b75-c3de-4d16-8d52-df8777eea324/progress` | `200` | `200` | 328.5 ms | ✅ PASS |
| 34 | `TC-PRG-04` | Learning Progress | `GET` | `/enrollments/mycourses` | `200` | `200` | 319.33 ms | ✅ PASS |
| 35 | `TC-SEC-01` | Security & Isolation | `POST` | `/auth/register` | `201` | `201` | 584.19 ms | ✅ PASS |
| 36 | `TC-SEC-02` | Security & Isolation | `POST` | `/auth/login` | `200` | `200` | 578.44 ms | ✅ PASS |
| 37 | `TC-SEC-03` | Security & Isolation | `PATCH` | `/enrollments/4c055b75-c3de-4d16-8d52-df8777eea324/progress` | `404` | `404` | 313.97 ms | ✅ PASS |
| 38 | `TC-SEC-04` | Security & Isolation | `POST` | `/payments` | `404` | `404` | 340.53 ms | ✅ PASS |

---

## 5. Analisis Temuan Keamanan & Integritas Bisnis

1. **Pencegahan Role Tampering (TC-AUTH-03)**:
   - Saat pengguna mencoba menyisipkan atribut `"role": "admin"` pada payload registrasi, sistem secara tegas mengabaikan nilai tersebut dan memaksa role tersimpan sebagai `student`. Hal ini mencegah celah *privilege escalation* saat pendaftaran akun.
2. **Integritas Transaksi Atomik (TC-ENR-01 & TC-PAY-06)**:
   - Pendaftaran kursus dieksekusi dalam satu transaksi database: `Order`, `Invoice` (status `unpaid`), dan `Enrollment` (status `pending_payment`) dibuat secara bersamaan (*atomic transaction*). Jika salah satu gagal, seluruh transaksi di-*rollback*.
   - Saat pelunasan via webhook, sistem secara simultan memperbarui status `Payment` -> `paid`, `Invoice` -> `paid`, `Order` -> `paid`, dan `Enrollment` -> `active`.
3. **Idempotensi Webhook Gateway (TC-PAY-07)**:
   - Pemanggilan webhook callback yang berulang untuk transaksi yang sudah lunas tidak menyebabkan duplikasi data maupun *error 500*. Sistem mengenali status transaksi dan mengembalikan respons `200 OK` dengan pesan konfirmasi bahwa transaksi telah diproses sebelumnya.
4. **Proteksi IDOR & Isolasi Data Multi-Tenant (TC-SEC-03 & TC-SEC-04)**:
   - Ketika seorang siswa mencoba memperbarui progress belajar atau membayar tagihan kursus milik siswa lain, API merespons dengan `404 Not Found`. Hal ini adalah *best practice* keamanan agar pihak penyerang tidak dapat mengetahui apakah ID tersebut valid atau milik pengguna lain (*preventing enumeration*).
5. **Validasi Input Ketat (TC-AUTH-04 & TC-CRS-04)**:
   - Skema Pydantic berhasil memfilter input yang tidak sesuai aturan (seperti format email tidak valid, panjang password, dan UUID tidak valid) dengan respon standar `422 Unprocessable Entity`.

## 6. Kesimpulan

Seluruh rangkaian pengujian API SkillBridge (38 kasus uji) berhasil diselesaikan dengan hasil **100% Passed**. API telah memenuhi seluruh kualifikasi fungsional, performa respon yang cepat (<500ms rata-rata), kehandalan transaksi keuangan, dan standar keamanan yang kuat. Sistem dinyatakan **layak dan siap untuk tahap selanjutnya (integrasi frontend dan deployment)**.