"""
สร้างไฟล์รายงานสรุป report.txt
"""
"""
สร้างไฟล์รายงานสรุป report.txt
"""
import books
import members
import rentals
import storage
from config import (
    APP_NAME,
    APP_VERSION,
    REPORT_FILE,
    STATUS_DELETED,
    STATUS_BORROWING,
    STATUS_RETURNED,
)

LINE = "=" * 60
SUB = "-" * 60


def _books_section():
    s = books.stats()
    lines = [
        "[1] สรุปหนังสือ",
        SUB,
        f"จำนวนชื่อเรื่อง (ใช้งาน)  : {s['active_titles']}",
        f"จำนวนชื่อเรื่อง (ถูกลบ)   : {s['deleted_titles']}",
        f"จำนวนเล่มทั้งหมด          : {s['total_copies']}",
        f"ถูกยืมอยู่                : {s['currently_borrowed']}",
        f"พร้อมให้ยืม               : {s['available_now']}",
        f"ราคาเช่า/วัน ต่ำสุด       : {s['price_min']:.2f} บาท",
        f"ราคาเช่า/วัน สูงสุด       : {s['price_max']:.2f} บาท",
        f"ราคาเช่า/วัน เฉลี่ย       : {s['price_avg']:.2f} บาท",
        "",
        "จำนวนเรื่องแยกตามประเภท:",
    ]
    if s["genre_count"]:
        for genre, n in sorted(s["genre_count"].items()):
            lines.append(f"  - {genre}: {n}")
    else:
        lines.append("  (ไม่มีข้อมูล)")

    lines += ["", "รายการหนังสือ (ID | ชื่อ | ผู้แต่ง | ประเภท | ราคา/วัน | ว่าง/ทั้งหมด):"]
    items = books.list_all(active_only=True)
    if items:
        for b in items:
            lines.append(
                f"  {b['book_id']} | {b['title']} | {b['author']} | {b['genre']} | "
                f"{b['price_per_day']:.2f} | {b['stock_available']}/{b['stock_total']}"
            )
    else:
        lines.append("  (ไม่มีข้อมูล)")
    return lines


def _members_section():
    items = members.list_all(active_only=True)
    lines = [
        "[2] สรุปสมาชิก",
        SUB,
        f"จำนวนสมาชิก (ใช้งาน): {len(items)}",
        "",
        "รายชื่อสมาชิก (ID | ชื่อ | เบอร์โทร | วันที่สมัคร):",
    ]
    if items:
        for m in items:
            lines.append(
                f"  {m['member_id']} | {m['name']} | {m['phone']} | "
                f"{storage.ts_to_str(m['join_date'])}"
            )
    else:
        lines.append("  (ไม่มีข้อมูล)")
    return lines


def _rentals_section():
    # คำนวณจาก list_all() เอง ไม่พึ่ง key ของ rentals.stats()
    # และกรอง record ที่ถูกลบออกอีกชั้นเพื่อความปลอดภัย
    items = [r for r in rentals.list_all() if r["status"] != STATUS_DELETED]
    now = storage.now_ts()

    borrowing = [r for r in items if r["status"] == STATUS_BORROWING]
    returned = [r for r in items if r["status"] == STATUS_RETURNED]
    overdue = [r for r in borrowing if r["due_date"] < now]
    total_fine = sum(r["fine_amount"] for r in returned)

    book_title = {b["book_id"]: b["title"] for b in books.list_all(active_only=False)}
    member_name = {m["member_id"]: m["name"] for m in members.list_all(active_only=False)}

    lines = [
        "[3] สรุปการเช่า",
        SUB,
        f"จำนวนรายการเช่าทั้งหมด : {len(items)}",
        f"ยังไม่คืน              : {len(borrowing)}",
        f"  - เกินกำหนดแล้ว      : {len(overdue)}",
        f"คืนแล้ว                : {len(returned)}",
        f"ค่าปรับรวม (ที่คืนแล้ว) : {total_fine:.2f} บาท",
        "",
        "รายการเช่า (ID | หนังสือ | สมาชิก | วันเช่า | กำหนดคืน | วันคืน | ค่าปรับ | สถานะ):",
    ]
    if items:
        for r in items:
            if r["status"] == STATUS_RETURNED:
                state = "คืนแล้ว"
            elif r["due_date"] < now:
                state = "เกินกำหนด"
            else:
                state = "กำลังยืม"
            lines.append(
                f"  {r['rent_id']} | {book_title.get(r['book_id'], '?')} | "
                f"{member_name.get(r['member_id'], '?')} | "
                f"{storage.ts_to_str(r['rent_date'])} | "
                f"{storage.ts_to_str(r['due_date'])} | "
                f"{storage.ts_to_str(r['return_date'])} | "
                f"{r['fine_amount']:.2f} | {state}"
            )
    else:
        lines.append("  (ไม่มีข้อมูล)")
    return lines


def generate():
    """สร้าง report.txt แล้วคืน path ของไฟล์"""
    lines = [
        LINE,
        f"{APP_NAME} v{APP_VERSION}",
        "รายงานสรุป",
        f"สร้างเมื่อ: {storage.ts_to_str(storage.now_ts())}",
        LINE,
        "",
    ]
    lines += _books_section() + [""]
    lines += _members_section() + [""]
    lines += _rentals_section() + [""]
    lines += [LINE, "จบรายงาน", LINE]

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return REPORT_FILE
