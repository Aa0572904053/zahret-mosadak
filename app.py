import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template_string, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

def init_db():
    conn = sqlite3.connect("log.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movement_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            date_only TEXT,
            category TEXT,
            movement_type TEXT,
            direction TEXT,
            floor TEXT,
            visitor_name TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            staff_name TEXT,
            action_type TEXT,
            shift_hours TEXT,
            timestamp TEXT,
            date_only TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS packages_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            resident_name TEXT,
            apartment TEXT,
            phone TEXT,
            delivery_name TEXT,
            filename TEXT,
            status TEXT,
            timestamp TEXT,
            date_only TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS maintenance_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            floor TEXT,
            filename TEXT,
            status TEXT,
            timestamp TEXT,
            date_only TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS furnished_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            apartment_no TEXT,
            tenant_name TEXT,
            filename TEXT,
            timestamp TEXT,
            date_only TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS meters_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meter_type TEXT,
            prev_reading REAL,
            curr_reading REAL,
            consumption REAL,
            unit_price REAL,
            total_cost REAL,
            timestamp TEXT,
            date_only TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

MAIN_LAYOUT = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>إدارة برج زهرة مصدق - اتحاد الملاك</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @keyframes pulse-slow {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.8; transform: scale(1.02); }
        }
        .dashboard-icon { animation: pulse-slow 2.5s infinite ease-in-out; }
        @media print {
            @page { size: A4; margin: 5mm; }
            body {
                background-color: #ffffff !important;
                color: #000000 !important;
                -webkit-print-color-adjust: exact;
                font-size: 10px !important;
            }
            .no-print { display: none !important; }
            .dashboard-card { border: 1px solid #cbd5e1 !important; background: #ffffff !important; box-shadow: none !important; margin-bottom: 8px !important; color: black !important; }
            table { font-size: 9px !important; width: 100% !important; border-collapse: collapse !important; }
            th, td { border: 1px solid #94a3b8 !important; padding: 4px 6px !important; color: black !important; }
            th { background-color: #e2e8f0 !important; }
        }
    </style>
</head>
<body class="bg-[#0f172a] text-slate-100 min-h-screen p-2 font-sans text-xs">
    <div class="max-w-4xl mx-auto space-y-2.5">
        <!-- الهيدر -->
        <div class="bg-gradient-to-r from-slate-900 via-[#1e293b] to-slate-900 border border-blue-500/30 p-2.5 rounded-2xl text-center shadow-xl no-print">
            <h1 class="text-sm font-extrabold text-white flex items-center justify-center gap-2">
                <i class="fa-solid fa-building-shield text-blue-400 dashboard-icon text-base"></i> اتحاد ملاك برج زهرة مصدق - لوحة الإدارة الذكية
            </h1>
            <p class="text-[10px] text-slate-400 mt-0.5">النظام المعتمد للرقابة الشاملة والتشغيل الإداري والأمني</p>
        </div>

        <!-- شريط التنقل -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-1.5 no-print">
            <a href="/" class="p-2 rounded-xl border text-center font-bold flex items-center justify-center gap-1.5 transition {% if mode == 'move' %}bg-blue-600 border-blue-500 text-white shadow-lg{% else %}bg-[#1e293b] border-slate-700 text-slate-300 hover:bg-slate-800{% endif %}">
                <i class="fa-solid fa-person-walking-arrow-right text-cyan-400"></i> حركات البرج
            </a>
            <a href="/packages_page" class="p-2 rounded-xl border text-center font-bold flex items-center justify-center gap-1.5 transition {% if mode == 'pkg' %}bg-blue-600 border-blue-500 text-white shadow-lg{% else %}bg-[#1e293b] border-slate-700 text-slate-300 hover:bg-slate-800{% endif %}">
                <i class="fa-solid fa-box-open text-indigo-400"></i> الطرود والأمانات
            </a>
            <a href="/maintenance_page" class="p-2 rounded-xl border text-center font-bold flex items-center justify-center gap-1.5 transition {% if mode == 'maint' %}bg-blue-600 border-blue-500 text-white shadow-lg{% else %}bg-[#1e293b] border-slate-700 text-slate-300 hover:bg-slate-800{% endif %}">
                <i class="fa-solid fa-screwdriver-wrench text-orange-400"></i> الصيانة والطوارئ
            </a>
            <a href="/furnished_page" class="p-2 rounded-xl border text-center font-bold flex items-center justify-center gap-1.5 transition {% if mode == 'furn' %}bg-blue-600 border-blue-500 text-white shadow-lg{% else %}bg-[#1e293b] border-slate-700 text-slate-300 hover:bg-slate-800{% endif %}">
                <i class="fa-solid fa-house-chimney text-emerald-400"></i> الشقق المفروشة
            </a>
            <a href="/meters_page" class="p-2 rounded-xl border text-center font-bold flex items-center justify-center gap-1.5 transition {% if mode == 'meters' %}bg-blue-600 border-blue-500 text-white shadow-lg{% else %}bg-[#1e293b] border-slate-700 text-slate-300 hover:bg-slate-800{% endif %}">
                <i class="fa-solid fa-gauge-high text-yellow-400"></i> العدادات
            </a>
            <a href="/attendance" class="p-2 rounded-xl border text-center font-bold flex items-center justify-center gap-1.5 transition {% if mode == 'att' %}bg-blue-600 border-blue-500 text-white shadow-lg{% else %}bg-[#1e293b] border-slate-700 text-slate-300 hover:bg-slate-800{% endif %}">
                <i class="fa-solid fa-fingerprint text-teal-400"></i> بصمة الأمن
            </a>
            <a href="/report_page" class="col-span-2 p-2 rounded-xl border text-center font-bold flex items-center justify-center gap-2 transition {% if mode == 'report' %}bg-blue-600 border-blue-500 text-white shadow-lg{% else %}bg-[#1e293b] border-slate-700 text-slate-300 hover:bg-slate-800{% endif %}">
                <i class="fa-solid fa-chart-pie text-pink-400 dashboard-icon"></i> التقرير الرسمي المعتمد لاتحاد الملاك (A4)
            </a>
        </div>

        {% if mode == 'move' %}
        <div class="dashboard-card bg-[#1e293b] border border-slate-700 p-3.5 rounded-2xl shadow-xl space-y-2.5">
            <h2 class="text-xs font-bold text-white flex items-center gap-2"><i class="fa-solid fa-person-walking-arrow-right text-cyan-400 text-sm"></i> تسجيل حركة جديدة بالبرج</h2>
            <form action="/add_movement" method="POST" class="space-y-2.5">
                <div class="grid grid-cols-2 gap-2">
                    <div>
                        <label class="text-[11px] text-slate-300 block mb-1">الفئة:</label>
                        <select name="category" required class="w-full bg-[#0f172a] border border-slate-700 p-2 rounded-xl text-white">
                            <option value="ساكن">ساكن</option>
                            <option value="زائر">زائر</option>
                            <option value="دليفري">دليفري</option>
                            <option value="عامل">عامل</option>
                        </select>
                    </div>
                    <div>
                        <label class="text-[11px] text-slate-300 block mb-1">اسم الزائر / الجهة:</label>
                        <input type="text" name="visitor_name" placeholder="اختياري..." class="w-full bg-[#0f172a] border border-slate-700 p-2 rounded-xl text-white">
                    </div>
                </div>
                <div class="grid grid-cols-3 gap-2">
                    <div>
                        <label class="text-[11px] text-slate-300 block mb-1">الوسيلة:</label>
                        <select name="movement_type" class="w-full bg-[#0f172a] border border-slate-700 p-2 rounded-xl text-white">
                            <option value="أسانسير">أسانسير</option>
                            <option value="سلم">سلم</option>
                        </select>
                    </div>
                    <div>
                        <label class="text-[11px] text-slate-300 block mb-1">الاتجاه:</label>
                        <select name="direction" class="w-full bg-[#0f172a] border border-slate-700 p-2 rounded-xl text-white">
                            <option value="صاعد">صاعد</option>
                            <option value="هابط">هابط</option>
                        </select>
                    </div>
                    <div>
                        <label class="text-[11px] text-slate-300 block mb-1">الدور:</label>
                        <input type="text" name="floor" placeholder="الدور الثاني" class="w-full bg-[#0f172a] border border-slate-700 p-2 rounded-xl text-white">
                    </div>
                </div>
                <button type="submit" class="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold p-2.5 rounded-xl shadow-md">حفظ الحركة</button>
            </form>

            <div class="mt-4 overflow-x-auto">
                <table class="w-full text-right text-xs">
                    <tr class="bg-slate-800 text-cyan-400">
                        <th class="p-2">الوقت</th>
                        <th class="p-2">الفئة</th>
                        <th class="p-2">الاسم</th>
                        <th class="p-2">الوسيلة/الاتجاه</th>
                        <th class="p-2">الدور</th>
                    </tr>
                    {% for row in move_data %}
                    <tr class="border-b border-slate-800">
                        <td class="p-2 text-slate-400">{{ row[1] }}</td>
                        <td class="p-2 text-cyan-300 font-bold">{{ row[3] }}</td>
                        <td class="p-2">{{ row[7] if row[7] else '-' }}</td>
                        <td class="p-2">{{ row[4] }} ({{ row[5] }})</td>
                        <td class="p-2">{{ row[6] }}</td>
                    </tr>
                    {% endfor %}
                </table>
            </div>
        </div>

        {% elif mode == 'pkg' %}
        <div class="dashboard-card bg-[#1e293b] border border-slate-700 p-3.5 rounded-2xl shadow-xl space-y-2.5">
            <h2 class="text-xs font-bold text-white flex items-center gap-2"><i class="fa-solid fa-box-open text-indigo-400 text-sm"></i> تسجيل وتتبع الطرود والأمانات</h2>
            <form action="/add_package" method="POST" enctype="multipart/form-data" class="space-y-2.5">
                <div class="grid grid-cols-2 gap-2">
                    <div>
                        <label class="text-[11px] text-slate-300 block mb-1">اسم الساكن:</label>
                        <input type="text" name="resident_name" required placeholder="اسم الساكن..." class="w-full bg-[#0f172a] border border-slate-700 p-2 rounded-xl text-white">
                    </div>
                    <div>
                        <label class="text-[11px] text-slate-300 block mb-1">رقم الشقة:</label>
                        <input type="text" name="apartment" required placeholder="شقة 301" class="w-full bg-[#0f172a] border border-slate-700 p-2 rounded-xl text-white">
                    </div>
                </div>
                <div class="grid grid-cols-2 gap-2">
                    <div>
                        <label class="text-[11px] text-slate-300 block mb-1">رقم الهاتف (واتساب):</label>
                        <input type="text" name="phone" placeholder="01xxxxxxxxx" class="w-full bg-[#0f172a] border border-slate-700 p-2 rounded-xl text-white">
                    </div>
                    <div>
                        <label class="text-[11px] text-slate-300 block mb-1">المندوب:</label>
                        <input type="text" name="delivery_name" placeholder="اسم الشركة..." class="w-full bg-[#0f172a] border border-slate-700 p-2 rounded-xl text-white">
                    </div>
                </div>
                <div>
                    <label class="text-[11px] text-slate-300 block mb-1">إرفاق صورة أو مستند للطرد:</label>
                    <input type="file" name="file" class="w-full bg-[#0f172a] border border-slate-700 p-1.5 rounded-xl text-slate-300 text-xs">
                </div>
                <button type="submit" class="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold p-2.5 rounded-xl shadow-md">حفظ الطرد</button>
            </form>

            <div class="mt-4 overflow-x-auto">
                <table class="w-full text-right text-xs">
                    <tr class="bg-slate-800 text-indigo-400">
                        <th class="p-2">الساكن</th>
                        <th class="p-2">الشقة</th>
                        <th class="p-2">المندوب</th>
                        <th class="p-2">المرفق</th>
                        <th class="p-2">الحالة</th>
                    </tr>
                    {% for row in pkg_data %}
                    <tr class="border-b border-slate-800">
                        <td class="p-2 font-bold">{{ row[1] }}</td>
                        <td class="p-2">{{ row[2] }}</td>
                        <td class="p-2">{{ row[4] }}</td>
                        <td class="p-2">
                            {% if row[5] %}
                            <a href="/uploads/{{ row[5] }}" target="_blank" class="text-blue-400 underline">عرض الملف</a>
                            {% else %}
                            بدون
                            {% endif %}
                        </td>
                        <td class="p-2 text-emerald-400">{{ row[6] }}</td>
                    </tr>
                    {% endfor %}
                </table>
            </div>
        </div>

        {% elif mode == 'maint' %}
        <div class="dashboard-card bg-[#1e293b] border border-slate-700 p-3.5 rounded-2xl shadow-xl space-y-2.5">
            <h2 class="text-xs font-bold text-white flex items-center gap-2"><i class="fa-solid fa-screwdriver-wrench text-orange-400 text-sm"></i> تسجيل الصيانة والطوارئ</h2>
            <form action="/add_maintenance" method="POST" enctype="multipart/form-data" class="space-y-2.5">
                <div class="grid grid-cols-2 gap-2">
                    <div>
                        <label class="text-[11px] text-slate-300 block mb-1">عنوان العطل:</label>
                        <input type="text" name="title" required placeholder="عطل الأسانسير" class="w-full bg-[#0f172a] border border-slate-700 p-2 rounded-xl text-white">
                    </div>
                    <div>
                        <label class="text-[11px] text-slate-300 block mb-1">الدور / المكان:</label>
                        <input type="text" name="floor" placeholder="الدور الثاني" class="w-full bg-[#0f172a] border border-slate-700 p-2 rounded-xl text-white">
                    </div>
                </div>
                <div>
                    <label class="text-[11px] text-slate-300 block mb-1">الوصف:</label>
                    <textarea name="description" rows="2" class="w-full bg-[#0f172a] border border-slate-700 p-2 rounded-xl text-white"></textarea>
                </div>
                <div>
                    <label class="text-[11px] text-slate-300 block mb-1">إرفاق صورة العطل:</label>
                    <input type="file" name="file" class="w-full bg-[#0f172a] border border-slate-700 p-1.5 rounded-xl text-slate-300 text-xs">
                </div>
                <button type="submit" class="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold p-2.5 rounded-xl shadow-md">حفظ بلاغ الصيانة</button>
            </form>

            <div class="mt-4 overflow-x-auto">
                <table class="w-full text-right text-xs">
                    <tr class="bg-slate-800 text-orange-400">
                        <th class="p-2">العطل</th>
                        <th class="p-2">المكان</th>
                        <th class="p-2">الوصف</th>
                        <th class="p-2">المرفق</th>
                        <th class="p-2">الحالة</th>
                    </tr>
                    {% for row in maint_data %}
                    <tr class="border-b border-slate-800">
                        <td class="p-2 font-bold">{{ row[1] }}</td>
                        <td class="p-2">{{ row[3] }}</td>
                        <td class="p-2">{{ row[2] }}</td>
                        <td class="p-2">
                            {% if row[4] %}
                            <a href="/uploads/{{ row[4] }}" target="_blank" class="text-blue-400 underline">صورة العطل</a>
                            {% else %}
                            بدون
                            {% endif %}
                        </td>
                        <td class="p-2 text-yellow-400">{{ row[5] }}</td>
                    </tr>
                    {% endfor %}
                </table>
            </div>
        </div>

        {% elif mode == 'furn' %}
        <div class="dashboard-card bg-[#1e293b] border border-slate-700 p-3.5 rounded-2xl shadow-xl space-y-2.5">
            <h2 class="text-xs font-bold text-white flex items-center gap-2"><i class="fa-solid fa-house-chimney text-emerald-400 text-sm"></i> الشقق المفروشة والعقود</h2>
            <form action="/add_furnished" method="POST" enctype="multipart/form-data" class="space-y-2.5">
                <div class="grid grid-cols-2 gap-2">
                    <div>
                        <label class="text-[11px] text-slate-300 block mb-1">رقم الشقة:</label>
                        <input type="text" name="apartment_no" required placeholder="شقة 402" class="w-full bg-[#0f172a] border border-slate-700 p-2 rounded-xl text-white">
                    </div>
                    <div>
                        <label class="text-[11px] text-slate-300 block mb-1">اسم المستأجر:</label>
                        <input type="text" name="tenant_name" required placeholder="الاسم رباعي" class="w-full bg-[#0f172a] border border-slate-700 p-2 rounded-xl text-white">
                    </div>
                </div>
                <div>
                    <label class="text-[11px] text-slate-300 block mb-1">إرفاق عقد الإيجار:</label>
                    <input type="file" name="file" class="w-full bg-[#0f172a] border border-slate-700 p-1.5 rounded-xl text-slate-300 text-xs">
                </div>
                <button type="submit" class="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold p-2.5 rounded-xl shadow-md">حفظ بيانات الشقة</button>
            </form>

            <div class="mt-4 overflow-x-auto">
                <table class="w-full text-right text-xs">
                    <tr class="bg-slate-800 te