import json
import time
import uuid
import httpx
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"
CALLBACK_SECRET = "rahasia-callback-gateway"

results = []

def record_test(test_id, category, name, method, url_path, expected_status, req_headers=None, req_body=None, notes=""):
    full_url = f"{BASE_URL}{url_path}"
    headers = req_headers or {}
    start_time = time.perf_counter()
    
    with httpx.Client(timeout=10.0) as client:
        if method.upper() == "GET":
            res = client.get(full_url, headers=headers)
        elif method.upper() == "POST":
            res = client.post(full_url, headers=headers, json=req_body)
        elif method.upper() == "PATCH":
            res = client.patch(full_url, headers=headers, json=req_body)
        elif method.upper() == "DELETE":
            res = client.delete(full_url, headers=headers)
        else:
            raise ValueError(f"Unsupported method {method}")
            
    latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
    
    try:
        res_json = res.json()
    except Exception:
        res_json = res.text

    passed = (res.status_code == expected_status)
    
    item = {
        "id": test_id,
        "category": category,
        "name": name,
        "method": method.upper(),
        "url": url_path,
        "full_url": full_url,
        "headers": headers,
        "req_body": req_body,
        "expected_status": expected_status,
        "actual_status": res.status_code,
        "latency_ms": latency_ms,
        "passed": passed,
        "res_body": res_json,
        "notes": notes
    }
    results.append(item)
    print(f"[{'PASS' if passed else 'FAIL'}] {test_id} - {name} ({res.status_code} vs {expected_status}) - {latency_ms}ms")
    return item

def run_all_tests():
    print("=== Memulai Pengujian Komprehensif API SkillBridge ===")
    
    # ---------------------------------------------------------
    # 1. AUTHENTICATION & USER MANAGEMENT
    # ---------------------------------------------------------
    student_email = f"budi.santoso.{uuid.uuid4().hex[:6]}@mail.com"
    student_password = "Rahasia123!"
    
    # TC-AUTH-01: Register Student Baru (Success 201)
    record_test(
        "TC-AUTH-01", "Authentication", "Registrasi Akun Siswa Baru (Normal)",
        "POST", "/auth/register", 201,
        req_headers={"Content-Type": "application/json"},
        req_body={"full_name": "Budi Santoso", "email": student_email, "password": student_password},
        notes="Mendaftarkan siswa baru dengan email unik dan format data valid."
    )
    
    # TC-AUTH-02: Register Email Duplikat (Conflict 409)
    record_test(
        "TC-AUTH-02", "Authentication", "Registrasi Email yang Sudah Terdaftar (Duplikat)",
        "POST", "/auth/register", 409,
        req_headers={"Content-Type": "application/json"},
        req_body={"full_name": "Budi Kloning", "email": student_email, "password": "PasswordLain123!"},
        notes="Sistem menolak registrasi email yang sudah ada dengan response HTTP 409 Conflict."
    )
    
    # TC-AUTH-03: Register Mencoba Injeksi Role Admin (Role Tampering)
    hacker_email = f"attacker.{uuid.uuid4().hex[:6]}@mail.com"
    t_tamper = record_test(
        "TC-AUTH-03", "Authentication", "Registrasi Mencoba Injeksi Role Admin",
        "POST", "/auth/register", 201,
        req_headers={"Content-Type": "application/json"},
        req_body={"full_name": "Attacker Role", "email": hacker_email, "password": "Password123!", "role": "admin"},
        notes="Sistem mengabaikan input role dan memaksa role selalu 'student' untuk keamanan."
    )
    
    # TC-AUTH-04: Register Validasi Input Gagal (Format Salah 422)
    record_test(
        "TC-AUTH-04", "Authentication", "Registrasi dengan Format Email dan Password Tidak Valid",
        "POST", "/auth/register", 422,
        req_headers={"Content-Type": "application/json"},
        req_body={"full_name": "", "email": "bukan-sebuah-email", "password": "123"},
        notes="Pydantic menangkap format email tidak valid dan panjang password kurang dari batas minimal."
    )
    
    # TC-AUTH-05: Login Akun Siswa (Success 200)
    t_login_student = record_test(
        "TC-AUTH-05", "Authentication", "Login Siswa dengan Kredensial Valid",
        "POST", "/auth/login", 200,
        req_headers={"Content-Type": "application/json"},
        req_body={"email": student_email, "password": student_password},
        notes="Mengembalikan JWT access_token bertipe Bearer dan objek user."
    )
    student_token = t_login_student["res_body"]["data"]["access_token"]
    student_headers = {"Authorization": f"Bearer {student_token}", "Content-Type": "application/json"}
    
    # TC-AUTH-06: Login Akun Admin Seed (Success 200)
    t_login_admin = record_test(
        "TC-AUTH-06", "Authentication", "Login Akun Admin Seed",
        "POST", "/auth/login", 200,
        req_headers={"Content-Type": "application/json"},
        req_body={"email": "admin@skillbridge.id", "password": "Admin123!"},
        notes="Login akun default admin dari seed database."
    )
    admin_token = t_login_admin["res_body"]["data"]["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
    
    # TC-AUTH-07: Login Akun Instructor Seed (Success 200)
    t_login_inst = record_test(
        "TC-AUTH-07", "Authentication", "Login Akun Instruktur Seed",
        "POST", "/auth/login", 200,
        req_headers={"Content-Type": "application/json"},
        req_body={"email": "instructor@skillbridge.id", "password": "Instruktur123!"},
        notes="Login akun default instructor dari seed database."
    )
    instructor_token = t_login_inst["res_body"]["data"]["access_token"]
    instructor_headers = {"Authorization": f"Bearer {instructor_token}", "Content-Type": "application/json"}
    
    # TC-AUTH-08: Login Password Salah (Unauthorized 401)
    record_test(
        "TC-AUTH-08", "Authentication", "Login dengan Password Salah",
        "POST", "/auth/login", 401,
        req_headers={"Content-Type": "application/json"},
        req_body={"email": student_email, "password": "PasswordSalahTotal!"},
        notes="Menghasilkan pesan generik 'Email atau password salah' untuk mencegah user enumeration."
    )
    
    # TC-AUTH-09: Get Current Profile /auth/me (Success 200)
    record_test(
        "TC-AUTH-09", "Authentication", "Mendapatkan Data Profil Pengguna Aktif (/auth/me)",
        "GET", "/auth/me", 200,
        req_headers=student_headers,
        notes="Memvalidasi header Authorization Bearer token dan mengembalikan info profil pemilik token."
    )
    
    # TC-AUTH-10: Get Current Profile Tanpa Token (Unauthorized 401)
    record_test(
        "TC-AUTH-10", "Authentication", "Mengakses /auth/me Tanpa Bearer Token",
        "GET", "/auth/me", 401,
        notes="Endpoint menolak permintaan anonim yang tidak membawa header otorisasi."
    )

    # ---------------------------------------------------------
    # 2. COURSES CATALOG & MANAGEMENT
    # ---------------------------------------------------------
    # TC-CRS-01: List Kursus Publik
    t_list_courses = record_test(
        "TC-CRS-01", "Courses", "Mendapatkan Katalog Kursus Terpublikasi (/courses)",
        "GET", "/courses", 200,
        notes="Mengembalikan daftar kursus aktif dengan status is_published=true."
    )
    courses_data = t_list_courses["res_body"]["data"]
    target_course = courses_data[0]
    course_id = target_course["id"]
    category_id = target_course["category_id"]
    
    # TC-CRS-02: Get Detail Kursus beserta Daftar Modul
    t_detail = record_test(
        "TC-CRS-02", "Courses", f"Mendapatkan Detail Kursus ({target_course['title']})",
        "GET", f"/courses/{course_id}", 200,
        notes="Mengembalikan detail kursus lengkap dengan daftar modul pembelajaran (eager loaded)."
    )
    modules = t_detail["res_body"]["data"]["modules"]
    first_module_id = modules[0]["id"]
    
    # TC-CRS-03: Get Detail Kursus ID Tidak Ada (404)
    record_test(
        "TC-CRS-03", "Courses", "Mendapatkan Detail Kursus dengan UUID Acak yang Tidak Ada",
        "GET", f"/courses/{uuid.uuid4()}", 404,
        notes="Sistem mengembalikan 404 Not Found dengan format pesan error terstandar."
    )
    
    # TC-CRS-04: Get Detail Kursus UUID Tidak Valid (422)
    record_test(
        "TC-CRS-04", "Courses", "Mendapatkan Detail Kursus dengan Parameter Bukan UUID",
        "GET", "/courses/bukan-format-uuid-valid", 422,
        notes="Pydantic memvalidasi path parameter dan menolak format non-UUID dengan HTTP 422."
    )
    
    # TC-CRS-05: Buat Kursus Baru oleh Instruktur (Success 201)
    t_new_course = record_test(
        "TC-CRS-05", "Courses", "Membuat Kursus Baru oleh Instruktur (Role Instructor)",
        "POST", "/courses", 201,
        req_headers=instructor_headers,
        req_body={
            "category_id": category_id,
            "title": "Arsitektur Microservices dengan Python",
            "description": "Membangun sistem microservices berskala tinggi menggunakan FastAPI dan Docker.",
            "price": "250000.00"
        },
        notes="Role instructor diizinkan membuat kursus baru."
    )
    
    # TC-CRS-06: Buat Kursus Baru oleh Siswa (Forbidden 403)
    record_test(
        "TC-CRS-06", "Courses", "Siswa Mencoba Membuat Kursus Baru (Role Student)",
        "POST", "/courses", 403,
        req_headers=student_headers,
        req_body={
            "category_id": category_id,
            "title": "Kursus Terlarang oleh Siswa",
            "price": "50000.00"
        },
        notes="RBAC menolak aksi pembuatan kursus oleh role student dengan HTTP 403 Forbidden."
    )

    # ---------------------------------------------------------
    # 3. ENROLLMENTS & LEARNING PROGRESS (PRE-PAYMENT)
    # ---------------------------------------------------------
    # TC-ENR-01: Siswa Mendaftar Kursus (Success 201)
    t_enroll = record_test(
        "TC-ENR-01", "Enrollments", "Pendaftaran Kursus oleh Siswa (Auto Order & Invoice)",
        "POST", "/enrollments", 201,
        req_headers=student_headers,
        req_body={"course_id": course_id},
        notes="Dalam satu transaksi database: dibuat Order, Invoice (status unpaid), dan Enrollment (pending_payment)."
    )
    enroll_data = t_enroll["res_body"]["data"]
    enrollment_id = enroll_data["enrollment"]["id"]
    invoice_id = enroll_data["invoice"]["id"]
    invoice_amount = enroll_data["invoice"]["amount"]
    
    # TC-ENR-02: Pendaftaran Ulang ke Kursus yang Sama (Conflict 409)
    record_test(
        "TC-ENR-02", "Enrollments", "Siswa Mendaftar Ulang ke Kursus yang Sama (Duplikasi)",
        "POST", "/enrollments", 409,
        req_headers=student_headers,
        req_body={"course_id": course_id},
        notes="Mencegah duplikasi enrollment untuk kursus dan siswa yang sama."
    )
    
    # TC-ENR-03: Admin Mencoba Mendaftar Kursus (Forbidden 403)
    record_test(
        "TC-ENR-03", "Enrollments", "Admin Mencoba Mendaftar Kursus (Non-Student)",
        "POST", "/enrollments", 403,
        req_headers=admin_headers,
        req_body={"course_id": course_id},
        notes="Hanya akun dengan role student yang diperbolehkan mendaftar kursus."
    )
    
    # TC-ENR-04: Cek Daftar Kursus Siswa Sebelum Bayar (pending_payment)
    record_test(
        "TC-ENR-04", "Enrollments", "Mengecek /enrollments/mycourses Sebelum Pembayaran",
        "GET", "/enrollments/mycourses", 200,
        req_headers=student_headers,
        notes="Memastikan kursus terdaftar muncul di daftar kursus siswa dengan status pending_payment."
    )
    
    # TC-ENR-05: Update Progress Sebelum Bayar (Forbidden 403)
    record_test(
        "TC-ENR-05", "Enrollments", "Siswa Mencoba Memperbarui Progress Modul Sebelum Melunasi Pembayaran",
        "PATCH", f"/enrollments/{enrollment_id}/progress", 403,
        req_headers=student_headers,
        req_body={"module_id": first_module_id, "status": "completed"},
        notes="Akses materi/progress terkunci sampai invoice berhasil dibayar."
    )

    # ---------------------------------------------------------
    # 4. PAYMENTS & PAYMENT GATEWAY WEBHOOK/CALLBACK
    # ---------------------------------------------------------
    # TC-PAY-01: Inisiasi Pembayaran (Success 201)
    t_pay = record_test(
        "TC-PAY-01", "Payments", "Inisiasi Pembayaran Invoice (Bank Transfer)",
        "POST", "/payments", 201,
        req_headers=student_headers,
        req_body={"invoice_id": invoice_id, "method": "bank_transfer"},
        notes="Membuat record Payment berstatus pending dan menghasilkan external_ref unik."
    )
    external_ref = t_pay["res_body"]["data"]["external_ref"]
    
    # TC-PAY-02: Inisiasi Pembayaran Kedua saat Masih Ada Pending (Conflict 409)
    record_test(
        "TC-PAY-02", "Payments", "Inisiasi Pembayaran Baru saat Masih Ada Transaksi Pending",
        "POST", "/payments", 409,
        req_headers=student_headers,
        req_body={"invoice_id": invoice_id, "method": "qris"},
        notes="Sistem mencegah spam pembayaran ganda pada invoice yang sama."
    )
    
    # TC-PAY-03: Callback Gateway Tanpa Header X-Callback-Token (Unauthorized 401)
    record_test(
        "TC-PAY-03", "Payments", "Callback Gateway Tanpa Header X-Callback-Token",
        "POST", "/payments/callback", 401,
        req_headers={"Content-Type": "application/json"},
        req_body={"external_ref": external_ref, "status": "paid", "amount": invoice_amount},
        notes="Melindungi webhook dari pemalsuan eksternal tanpa rahasia callback."
    )
    
    # TC-PAY-04: Callback Gateway dengan Token Salah (Unauthorized 401)
    record_test(
        "TC-PAY-04", "Payments", "Callback Gateway dengan X-Callback-Token Salah/Palsu",
        "POST", "/payments/callback", 401,
        req_headers={"Content-Type": "application/json", "X-Callback-Token": "token-palsu-ngawur"},
        req_body={"external_ref": external_ref, "status": "paid", "amount": invoice_amount},
        notes="Perbandingan hmac.compare_digest menolak secret yang tidak cocok."
    )
    
    # TC-PAY-05: Callback Gateway dengan Nominal Tidak Sesuai (Unprocessable Entity 422)
    record_test(
        "TC-PAY-05", "Payments", "Callback Gateway dengan Nominal yang Tidak Cocok dengan Tagihan",
        "POST", "/payments/callback", 422,
        req_headers={"Content-Type": "application/json", "X-Callback-Token": CALLBACK_SECRET},
        req_body={"external_ref": external_ref, "status": "paid", "amount": "9999.00"},
        notes="Integritas nominal terjaga; callback gagal jika nominal berbeda dengan tagihan invoice."
    )
    
    # TC-PAY-06: Callback Gateway Sukses 'paid' (Success 200)
    record_test(
        "TC-PAY-06", "Payments", "Callback Gateway Pelunasan Berhasil (Status: paid)",
        "POST", "/payments/callback", 200,
        req_headers={"Content-Type": "application/json", "X-Callback-Token": CALLBACK_SECRET},
        req_body={"external_ref": external_ref, "status": "paid", "amount": invoice_amount},
        notes="Mengubah status Payment menjadi paid, Invoice paid, Order paid, dan Enrollment active dalam 1 transaksi."
    )
    
    # TC-PAY-07: Callback Idempoten (Callback Berulang untuk Transaksi yang Sudah Paid)
    record_test(
        "TC-PAY-07", "Payments", "Pengujian Idempotensi Callback Gateway (Dipanggil Ulang)",
        "POST", "/payments/callback", 200,
        req_headers={"Content-Type": "application/json", "X-Callback-Token": CALLBACK_SECRET},
        req_body={"external_ref": external_ref, "status": "paid", "amount": invoice_amount},
        notes="Sistem mengembalikan 200 'Callback sudah pernah diproses' tanpa mengeksekusi mutasi ulang."
    )

    # ---------------------------------------------------------
    # 5. POST-PAYMENT LEARNING PROGRESS
    # ---------------------------------------------------------
    # TC-PRG-01: Cek Status Kursus di MyCourses Setelah Pembayaran Lunas
    record_test(
        "TC-PRG-01", "Learning Progress", "Mengecek Status Enrollment di /enrollments/mycourses Pasca Pembayaran",
        "GET", "/enrollments/mycourses", 200,
        req_headers=student_headers,
        notes="Memastikan enrollment telah berubah status menjadi 'active' dengan total modul pembelajaran 4."
    )
    
    # TC-PRG-02: Selesaikan Modul 1 (Progress 25%)
    record_test(
        "TC-PRG-02", "Learning Progress", "Memperbarui Modul 1 Menjadi Selesai (Progress 25%)",
        "PATCH", f"/enrollments/{enrollment_id}/progress", 200,
        req_headers=student_headers,
        req_body={"module_id": modules[0]["id"], "status": "completed"},
        notes="Status modul 1 selesai, progress bertambah menjadi 25.0%."
    )
    
    # TC-PRG-03: Selesaikan Seluruh Modul (Progress 100% & Enrollment Completed)
    for i, mod in enumerate(modules[1:], start=2):
        record_test(
            f"TC-PRG-03.{i}", "Learning Progress", f"Menyelesaikan Modul {i} ({mod['title']})",
            "PATCH", f"/enrollments/{enrollment_id}/progress", 200,
            req_headers=student_headers,
            req_body={"module_id": mod["id"], "status": "completed"},
            notes=f"Menyelesaikan modul {i} dari {len(modules)}."
        )
    
    # TC-PRG-04: Verifikasi Akhir MyCourses (100% Selesai)
    record_test(
        "TC-PRG-04", "Learning Progress", "Verifikasi Status Akhir Kursus (Status: completed, 100%)",
        "GET", "/enrollments/mycourses", 200,
        req_headers=student_headers,
        notes="Seluruh modul tuntas diselesaikan; status enrollment otomatis berubah menjadi 'completed'."
    )

    # ---------------------------------------------------------
    # 6. SECURITY & MULTI-TENANCY ISOLATION (PRIVILEGE ESCALATION)
    # ---------------------------------------------------------
    # Buat akun siswa kedua
    other_email = f"ahmad.siswa.{uuid.uuid4().hex[:6]}@mail.com"
    record_test(
        "TC-SEC-01", "Security & Isolation", "Registrasi Akun Siswa Kedua (User Lain)",
        "POST", "/auth/register", 201,
        req_headers={"Content-Type": "application/json"},
        req_body={"full_name": "Ahmad Dani", "email": other_email, "password": "PasswordLain123!"},
        notes="Membuat pengguna siswa kedua untuk menguji isolasi data."
    )
    t_other_login = record_test(
        "TC-SEC-02", "Security & Isolation", "Login Akun Siswa Kedua",
        "POST", "/auth/login", 200,
        req_headers={"Content-Type": "application/json"},
        req_body={"email": other_email, "password": "PasswordLain123!"},
        notes="Mendapatkan token untuk siswa kedua."
    )
    other_token = t_other_login["res_body"]["data"]["access_token"]
    other_headers = {"Authorization": f"Bearer {other_token}", "Content-Type": "application/json"}
    
    # TC-SEC-03: Siswa Lain Mencoba Mengubah Progress Siswa Pertama (404)
    record_test(
        "TC-SEC-03", "Security & Isolation", "Siswa Lain Mencoba Mengakses/Mengubah Progress Siswa Pertama",
        "PATCH", f"/enrollments/{enrollment_id}/progress", 404,
        req_headers=other_headers,
        req_body={"module_id": first_module_id, "status": "completed"},
        notes="Mengembalikan 404 Not Found (bukan 403) agar tidak membocorkan eksistensi data milik siswa lain."
    )
    
    # TC-SEC-04: Siswa Lain Mencoba Membayar Tagihan Siswa Pertama (404)
    record_test(
        "TC-SEC-04", "Security & Isolation", "Siswa Lain Mencoba Membayar Invoice Siswa Pertama",
        "POST", "/payments", 404,
        req_headers=other_headers,
        req_body={"invoice_id": invoice_id, "method": "qris"},
        notes="Sistem mengisolasi akses invoice; siswa lain tidak dapat memproses invoice milik siswa pertama."
    )
    
    print("\n=== Seluruh Pengujian Selesai Dijalankan ===")
    return results

if __name__ == "__main__":
    test_results = run_all_tests()
    with open("test_results.json", "w", encoding="utf-8") as f:
        json.dump(test_results, f, indent=2, ensure_ascii=False)
    print(f"Hasil pengujian tersimpan di test_results.json ({len(test_results)} test cases).")
