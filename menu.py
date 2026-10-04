"""
เมนู CLI สำหรับผู้ใช้งาน (Add/Update/Delete/View/Report/Exit)
"""
import books
import members
import rentals
import report
import storage
 
# ---------------------------------------------------------------------------
# ค่า status ของ rentals (ปรับให้ตรงกับ config.py ของทีมถ้าต่างกัน)
# ---------------------------------------------------------------------------
RENT_STATUS_ACTIVE = 1      # กำลังเช่า
RENT_STATUS_RETURNED = 2    # คืนแล้ว
 
LINE = "=" * 64
 
 
# ---------------------------------------------------------------------------
# Helper: รับค่า / แสดงผล
# ---------------------------------------------------------------------------
def _input_str(prompt, allow_empty=False):
    while True:
        value = input(prompt).strip()
        if value or allow_empty:
            return value
        print("  ! ห้ามเว้นว่าง กรุณากรอกใหม่")
 
 
def _input_int(prompt, min_value=None, allow_empty=False):
    """รับเลขจำนวนเต็ม; ถ้า allow_empty=True และกด Enter เฉย ๆ คืน None"""
    while True:
        raw = input(prompt).strip()
        if raw == "" and allow_empty:
            return None
        try:
            value = int(raw)
        except ValueError:
            print("  ! กรุณากรอกเป็นตัวเลขจำนวนเต็ม")
            continue
        if min_value is not None and value < min_value:
            print(f"  ! ต้องมีค่าอย่างน้อย {min_value}")
            continue
        return value
 
 
def _confirm(prompt):
    return input(f"{prompt} (y/n): ").strip().lower() == "y"
 
 
def _pause():
    input("\nกด Enter เพื่อกลับเมนู...")
 
 
def _fmt_ts(ts):
    """แปลง epoch เป็นข้อความ; ถ้าไม่มีค่า (0/None) แสดง '-'"""
    if not ts:
        return "-"
    return storage.ts_to_str(ts)
 
 
def _print_header(title):
    print(f"\n{LINE}\n  {title}\n{LINE}")
 
 
def _print_stats(data):
    if not data:
        print("  (ไม่มีข้อมูล)")
        return
    for key, value in data.items():
        print(f"  {key}: {value}")
 
 
# ---------------------------------------------------------------------------
# เมนูจัดการหนังสือ
# ---------------------------------------------------------------------------
def _print_books(rows):
    if not rows:
        print("  (ไม่พบข้อมูลหนังสือ)")
        return
    print(f"  {'ID':<5}{'ชื่อเรื่อง':<28}{'ผู้แต่ง':<18}{'ประเภท':<12}{'คงเหลือ/ทั้งหมด'}")
    print("  " + "-" * 70)
    for b in rows:
        print(f"  {b['book_id']:<5}{b['title']:<28}{b['author']:<18}"
              f"{b['genre']:<12}{b['stock_available']}/{b['stock_total']}")
 
 
def _book_add():
    _print_header("เพิ่มหนังสือ")
    title = _input_str("ชื่อเรื่อง: ")
    author = _input_str("ผู้แต่ง: ")
    genre = _input_str("ประเภท: ")
    stock_total = _input_int("จำนวนเล่มทั้งหมด: ", min_value=1)
    book_id = books.add(title, author, genre, stock_total)
    print(f"\n  ✓ เพิ่มหนังสือสำเร็จ (book_id = {book_id})")
 
 
def _book_list():
    _print_header("รายการหนังสือทั้งหมด")
    _print_books(books.list_all(active_only=True))
 
 
def _book_filter():
    _print_header("ค้นหา/กรองหนังสือ")
    genre = _input_str("ประเภท (เว้นว่าง = ทุกประเภท): ", allow_empty=True) or None
    available_only = _confirm("แสดงเฉพาะเล่มที่ยังว่างให้เช่า?")
    rows = books.filter_books(genre=genre, available_only=available_only)
    print()
    _print_books(rows)
 
 
def _book_update():
    _print_header("แก้ไขข้อมูลหนังสือ")
    book_id = _input_int("book_id ที่ต้องการแก้ไข: ", min_value=1)
    current = books.get(book_id)
    if current is None:
        print("  ! ไม่พบหนังสือนี้")
        return
    _print_books([current])
    print("\n  (กด Enter เพื่อคงค่าเดิม)")
    title = _input_str("ชื่อเรื่องใหม่: ", allow_empty=True) or None
    author = _input_str("ผู้แต่งใหม่: ", allow_empty=True) or None
    genre = _input_str("ประเภทใหม่: ", allow_empty=True) or None
    stock_total = _input_int("จำนวนเล่มทั้งหมดใหม่: ", min_value=1, allow_empty=True)
    ok = books.update(book_id, title=title, author=author,
                      genre=genre, stock_total=stock_total)
    print("  ✓ แก้ไขสำเร็จ" if ok else "  ! แก้ไขไม่สำเร็จ")
 
 
def _book_delete():
    _print_header("ลบหนังสือ")
    book_id = _input_int("book_id ที่ต้องการลบ: ", min_value=1)
    current = books.get(book_id)
    if current is None:
        print("  ! ไม่พบหนังสือนี้")
        return
    _print_books([current])
    if _confirm("ยืนยันการลบ?"):
        print("  ✓ ลบสำเร็จ" if books.delete(book_id) else "  ! ลบไม่สำเร็จ")
    else:
        print("  ยกเลิกการลบ")
 
 
def _book_stats():
    _print_header("สถิติหนังสือ")
    _print_stats(books.stats())
 
 
def _books_menu():
    actions = {
        "1": _book_add,
        "2": _book_list,
        "3": _book_filter,
        "4": _book_update,
        "5": _book_delete,
        "6": _book_stats,
    }
    _run_submenu("จัดการหนังสือ", [
        "1. เพิ่มหนังสือ",
        "2. แสดงหนังสือทั้งหมด",
        "3. ค้นหา/กรองหนังสือ",
        "4. แก้ไขข้อมูลหนังสือ",
        "5. ลบหนังสือ",
        "6. สถิติหนังสือ",
        "0. กลับเมนูหลัก",
    ], actions)
 
 
# ---------------------------------------------------------------------------
# เมนูจัดการสมาชิก
# ---------------------------------------------------------------------------
def _print_members(rows):
    if not rows:
        print("  (ไม่พบข้อมูลสมาชิก)")
        return
    print(f"  {'ID':<5}{'ชื่อ':<26}{'เบอร์โทร':<16}{'วันที่สมัคร'}")
    print("  " + "-" * 64)
    for m in rows:
        print(f"  {m['member_id']:<5}{m['name']:<26}{m['phone']:<16}"
              f"{_fmt_ts(m['join_date'])}")
 
 
def _member_add():
    _print_header("เพิ่มสมาชิก")
    name = _input_str("ชื่อ-นามสกุล: ")
    phone = _input_str("เบอร์โทร: ")
    member_id = members.add(name, phone)
    print(f"\n  ✓ เพิ่มสมาชิกสำเร็จ (member_id = {member_id})")
 
 
def _member_list():
    _print_header("รายชื่อสมาชิกทั้งหมด")
    _print_members(members.list_all(active_only=True))
 
 
def _member_update():
    _print_header("แก้ไขข้อมูลสมาชิก")
    member_id = _input_int("member_id ที่ต้องการแก้ไข: ", min_value=1)
    current = members.get(member_id)
    if current is None:
        print("  ! ไม่พบสมาชิกนี้")
        return
    _print_members([current])
    print("\n  (กด Enter เพื่อคงค่าเดิม)")
    name = _input_str("ชื่อใหม่: ", allow_empty=True) or None
    phone = _input_str("เบอร์โทรใหม่: ", allow_empty=True) or None
    ok = members.update(member_id, name=name, phone=phone)
    print("  ✓ แก้ไขสำเร็จ" if ok else "  ! แก้ไขไม่สำเร็จ")
 
 
def _member_delete():
    _print_header("ลบสมาชิก")
    member_id = _input_int("member_id ที่ต้องการลบ: ", min_value=1)
    current = members.get(member_id)
    if current is None:
        print("  ! ไม่พบสมาชิกนี้")
        return
    _print_members([current])
    if _confirm("ยืนยันการลบ?"):
        print("  ✓ ลบสำเร็จ" if members.delete(member_id) else "  ! ลบไม่สำเร็จ")
    else:
        print("  ยกเลิกการลบ")
 
 
def _members_menu():
    actions = {
        "1": _member_add,
        "2": _member_list,
        "3": _member_update,
        "4": _member_delete,
    }
    _run_submenu("จัดการสมาชิก", [
        "1. เพิ่มสมาชิก",
        "2. แสดงสมาชิกทั้งหมด",
        "3. แก้ไขข้อมูลสมาชิก",
        "4. ลบสมาชิก",
        "0. กลับเมนูหลัก",
    ], actions)
 
 
# ---------------------------------------------------------------------------
# เมนูการเช่า/คืน
# ---------------------------------------------------------------------------
def _print_rentals(rows):
    if not rows:
        print("  (ไม่พบข้อมูลการเช่า)")
        return
    print(f"  {'ID':<5}{'หนังสือ':<9}{'สมาชิก':<9}{'วันที่เช่า':<18}"
          f"{'กำหนดคืน':<18}{'วันที่คืน':<18}{'ค่าปรับ':<9}{'สถานะ'}")
    print("  " + "-" * 100)
    for r in rows:
        if r['status'] == RENT_STATUS_ACTIVE:
            status_text = "กำลังเช่า"
        elif r['status'] == RENT_STATUS_RETURNED:
            status_text = "คืนแล้ว"
        else:
            status_text = str(r['status'])
        print(f"  {r['rent_id']:<5}{r['book_id']:<9}{r['member_id']:<9}"
              f"{_fmt_ts(r['rent_date']):<18}{_fmt_ts(r['due_date']):<18}"
              f"{_fmt_ts(r['return_date']):<18}{r['fine_amount']:<9.2f}{status_text}")
 
 
def _rental_add():
    _print_header("ทำรายการเช่าหนังสือ")
    book_id = _input_int("book_id: ", min_value=1)
    member_id = _input_int("member_id: ", min_value=1)
    rent_days = _input_int("จำนวนวันที่เช่า (Enter = 7 วัน): ",
                           min_value=1, allow_empty=True) or 7
    try:
        rent_id = rentals.add(book_id, member_id, rent_days)
    except ValueError as e:
        print(f"\n  ! เช่าไม่สำเร็จ: {e}")
        return
    print(f"\n  ✓ เช่าสำเร็จ (rent_id = {rent_id}, {rent_days} วัน)")
 
 
def _rental_return():
    _print_header("คืนหนังสือ")
    rent_id = _input_int("rent_id: ", min_value=1)
    try:
        fine = rentals.return_book(rent_id)
    except ValueError as e:
        print(f"\n  ! คืนไม่สำเร็จ: {e}")
        return
    print("\n  ✓ คืนหนังสือสำเร็จ")
    if fine > 0:
        print(f"  ค่าปรับที่ต้องชำระ: {fine:.2f} บาท")
    else:
        print("  ไม่มีค่าปรับ")
 
 
def _rental_list():
    _print_header("รายการเช่า")
    print("  1. ทั้งหมด")
    print("  2. กำลังเช่า")
    print("  3. คืนแล้ว")
    choice = input("เลือก (Enter = ทั้งหมด): ").strip()
    status = {"2": RENT_STATUS_ACTIVE, "3": RENT_STATUS_RETURNED}.get(choice)
    print()
    _print_rentals(rentals.list_all(status=status))
 
 
def _rental_delete():
    _print_header("ลบรายการเช่า")
    rent_id = _input_int("rent_id ที่ต้องการลบ: ", min_value=1)
    if _confirm("ยืนยันการลบ?"):
        print("  ✓ ลบสำเร็จ" if rentals.delete(rent_id) else "  ! ไม่พบรายการนี้ / ลบไม่สำเร็จ")
    else:
        print("  ยกเลิกการลบ")
 
 
def _rental_stats():
    _print_header("สถิติการเช่า")
    _print_stats(rentals.stats())
 
 
def _rentals_menu():
    actions = {
        "1": _rental_add,
        "2": _rental_return,
        "3": _rental_list,
        "4": _rental_delete,
        "5": _rental_stats,
    }
    _run_submenu("เช่า/คืนหนังสือ", [
        "1. เช่าหนังสือ",
        "2. คืนหนังสือ",
        "3. แสดงรายการเช่า",
        "4. ลบรายการเช่า",
        "5. สถิติการเช่า",
        "0. กลับเมนูหลัก",
    ], actions)
 
 
# ---------------------------------------------------------------------------
# รายงาน
# ---------------------------------------------------------------------------
def _report():
    _print_header("สร้างรายงาน")
    path = report.generate()
    print(f"  ✓ สร้างรายงานสำเร็จ: {path}")
 
 
# ---------------------------------------------------------------------------
# ตัวช่วยรันเมนูย่อย + เมนูหลัก
# ---------------------------------------------------------------------------
def _run_submenu(title, option_lines, actions):
    """วนลูปเมนูย่อย จนกว่าผู้ใช้เลือก 0; จับ error ไม่ให้โปรแกรมหลุด"""
    while True:
        _print_header(title)
        for line in option_lines:
            print("  " + line)
        choice = input("\nเลือกเมนู: ").strip()
        if choice == "0":
            return
        action = actions.get(choice)
        if action is None:
            print("  ! ไม่มีเมนูนี้ กรุณาเลือกใหม่")
            continue
        try:
            action()
        except Exception as e:  # กันโปรแกรมล่มจากบั๊กในโมดูลอื่น
            print(f"\n  ! เกิดข้อผิดพลาด: {e}")
        _pause()
 
 
def main_menu():
    """ลูปหลักของโปรแกรม"""
    actions = {
        "1": _books_menu,
        "2": _members_menu,
        "3": _rentals_menu,
        "4": lambda: (_report(), _pause()),
    }
    while True:
        print(f"\n{LINE}")
        print("        M&N Rental Shop - ระบบร้านเช่าหนังสือ")
        print(LINE)
        print("  1. จัดการหนังสือ")
        print("  2. จัดการสมาชิก")
        print("  3. เช่า/คืนหนังสือ")
        print("  4. สร้างรายงาน (report.txt)")
        print("  0. ออกจากโปรแกรม")
        choice = input("\nเลือกเมนู: ").strip()
 
        if choice == "0":
            print("\nขอบคุณที่ใช้บริการ M&N Rental Shop")
            return
        action = actions.get(choice)
        if action is None:
            print("  ! ไม่มีเมนูนี้ กรุณาเลือกใหม่")
            continue
        try:
            action()
        except Exception as e:
            print(f"\n  ! เกิดข้อผิดพลาด: {e}")
            _pause()
 
 
if __name__ == "__main__":
    main_menu()
