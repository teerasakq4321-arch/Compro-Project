"""
pack/unpack และ CRUD สำหรับ books.dat
"""
import storage
from config import (
    BOOKS_FILE,
    BOOK_FORMAT,
    BOOK_SIZE,
    STATUS_ACTIVE,
    STATUS_DELETED,
    GENRE_PRICE,
)
 
import struct
 
 
# ---------------------------------------------------------------------------
# pack / unpack
# ---------------------------------------------------------------------------
def pack_book(book_id, title, author, genre, price, stock_total, stock_available, status):
    """แปลงข้อมูลหนังสือเป็น bytes ขนาดคงที่ (fixed-length record)"""
    # ขนาดฟิลด์ string ต้องอิงตาม BOOK_FORMAT ใน config.py เสมอ (45 / 35 / 15)
    title_size, author_size, genre_size = _string_field_sizes()
 
    return struct.pack(
        BOOK_FORMAT,
        book_id,
        storage.encode_str(title, title_size),
        storage.encode_str(author, author_size),
        storage.encode_str(genre, genre_size),
        float(price),
        int(stock_total),
        int(stock_available),
        int(status),
    )
 
 
def unpack_book(raw):
    """แปลง bytes กลับเป็น dict ข้อมูลหนังสือ (ใช้ key price_per_day ตามที่ตกลง)"""
    (book_id, title_raw, author_raw, genre_raw, price_per_day,
     stock_total, stock_available, status) = struct.unpack(BOOK_FORMAT, raw)
 
    return {
        "book_id": book_id,
        "title": storage.decode_str(title_raw),
        "author": storage.decode_str(author_raw),
        "genre": storage.decode_str(genre_raw),
        "price_per_day": price_per_day,
        "stock_total": stock_total,
        "stock_available": stock_available,
        "status": status,
    }
 
 
def _string_field_sizes():
    """ดึงขนาดฟิลด์ title/author/genre จาก BOOK_FORMAT ใน config.py โดยตรง
    (ไม่ hardcode ตัวเลขในไฟล์นี้ แกะขนาดจาก format string เช่น "<I45s35s15sfIII")"""
    import re
    sizes = [int(n) for n in re.findall(r"(\d+)s", BOOK_FORMAT)]
    return sizes[0], sizes[1], sizes[2]
 
 
# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------
def add(title, author, genre, stock_total):
    """เพิ่มหนังสือใหม่ -> คืน book_id ใหม่
    raise ValueError ถ้า genre ไม่อยู่ใน GENRE_PRICE"""
    if genre not in GENRE_PRICE:
        raise ValueError(f"genre ไม่ถูกต้อง: '{genre}' ต้องเป็นหนึ่งใน {list(GENRE_PRICE.keys())}")
 
    storage.ensure_file(BOOKS_FILE)
 
    new_id = storage.next_id(BOOKS_FILE, BOOK_SIZE, unpack_book, "book_id")
    stock_total = int(stock_total)
    price_per_day = GENRE_PRICE[genre]
 
    raw = pack_book(
        book_id=new_id,
        title=title,
        author=author,
        genre=genre,
        price=price_per_day,
        stock_total=stock_total,
        stock_available=stock_total,
        status=STATUS_ACTIVE,
    )
    storage.append_record(BOOKS_FILE, raw)
    return new_id
 
 
def get(book_id):
    """คืนข้อมูลหนังสือ (dict) ถ้าพบและยังไม่ถูกลบ ไม่งั้นคืน None"""
    storage.ensure_file(BOOKS_FILE)
    _, record = storage.find_index_by_id(BOOKS_FILE, BOOK_SIZE, unpack_book, "book_id", book_id)
 
    if record is None or record["status"] == STATUS_DELETED:
        return None
    return record
 
 
def update(book_id, title=None, author=None, genre=None, stock_total=None):
    """แก้ไขข้อมูลหนังสือ (เฉพาะฟิลด์ที่ส่งมา) -> True/False
    ถ้าส่ง genre ใหม่มา ราคาต่อวันจะถูกดึงจาก GENRE_PRICE ใหม่ตามไปด้วย"""
    storage.ensure_file(BOOKS_FILE)
    index, record = storage.find_index_by_id(BOOKS_FILE, BOOK_SIZE, unpack_book, "book_id", book_id)
 
    if record is None or record["status"] == STATUS_DELETED:
        return False
 
    if genre is not None and genre not in GENRE_PRICE:
        raise ValueError(f"genre ไม่ถูกต้อง: '{genre}' ต้องเป็นหนึ่งใน {list(GENRE_PRICE.keys())}")
 
    new_title = title if title is not None else record["title"]
    new_author = author if author is not None else record["author"]
    new_genre = genre if genre is not None else record["genre"]
    new_price = GENRE_PRICE[new_genre] if genre is not None else record["price_per_day"]
 
    new_stock_total = record["stock_total"]
    new_stock_available = record["stock_available"]
 
    if stock_total is not None:
        stock_total = int(stock_total)
        rented = record["stock_total"] - record["stock_available"]  # จำนวนที่ถูกยืมอยู่
        new_stock_total = stock_total
        new_stock_available = max(0, new_stock_total - rented)
 
    raw = pack_book(
        book_id=book_id,
        title=new_title,
        author=new_author,
        genre=new_genre,
        price=new_price,
        stock_total=new_stock_total,
        stock_available=new_stock_available,
        status=record["status"],
    )
    storage.overwrite_record_at_index(BOOKS_FILE, BOOK_SIZE, index, raw)
    return True
 
 
def delete(book_id):
    """Soft-delete หนังสือ (เปลี่ยน status เป็น STATUS_DELETED) -> True/False"""
    storage.ensure_file(BOOKS_FILE)
    index, record = storage.find_index_by_id(BOOKS_FILE, BOOK_SIZE, unpack_book, "book_id", book_id)
 
    if record is None or record["status"] == STATUS_DELETED:
        return False
 
    raw = pack_book(
        book_id=record["book_id"],
        title=record["title"],
        author=record["author"],
        genre=record["genre"],
        price=record["price_per_day"],
        stock_total=record["stock_total"],
        stock_available=record["stock_available"],
        status=STATUS_DELETED,
    )
    storage.overwrite_record_at_index(BOOKS_FILE, BOOK_SIZE, index, raw)
    return True
 
 
# ---------------------------------------------------------------------------
# เรียกใช้จาก rentals.py เท่านั้น (ห้ามไฟล์อื่นแก้ books.dat ตรง ๆ)
# ---------------------------------------------------------------------------
def decrement_stock(book_id):
    """ลด stock_available ลง 1 ตอนมีการยืมหนังสือ -> True/False"""
    storage.ensure_file(BOOKS_FILE)
    index, record = storage.find_index_by_id(BOOKS_FILE, BOOK_SIZE, unpack_book, "book_id", book_id)
 
    if record is None or record["status"] == STATUS_DELETED:
        return False
    if record["stock_available"] <= 0:
        return False
 
    raw = pack_book(
        book_id=record["book_id"],
        title=record["title"],
        author=record["author"],
        genre=record["genre"],
        price=record["price_per_day"],
        stock_total=record["stock_total"],
        stock_available=record["stock_available"] - 1,
        status=record["status"],
    )
    storage.overwrite_record_at_index(BOOKS_FILE, BOOK_SIZE, index, raw)
    return True
 
 
def increment_stock(book_id):
    """เพิ่ม stock_available ขึ้น 1 ตอนมีการคืนหนังสือ -> True/False"""
    storage.ensure_file(BOOKS_FILE)
    index, record = storage.find_index_by_id(BOOKS_FILE, BOOK_SIZE, unpack_book, "book_id", book_id)
 
    if record is None:
        return False
 
    new_available = min(record["stock_total"], record["stock_available"] + 1)
 
    raw = pack_book(
        book_id=record["book_id"],
        title=record["title"],
        author=record["author"],
        genre=record["genre"],
        price=record["price_per_day"],
        stock_total=record["stock_total"],
        stock_available=new_available,
        status=record["status"],
    )
    storage.overwrite_record_at_index(BOOKS_FILE, BOOK_SIZE, index, raw)
    return True
 
 
# ---------------------------------------------------------------------------
# List / Filter / Stats
# ---------------------------------------------------------------------------
def list_all(active_only=True):
    """คืนรายการหนังสือทั้งหมด (กรอง deleted ออกถ้า active_only=True)"""
    storage.ensure_file(BOOKS_FILE)
    records = storage.read_all(BOOKS_FILE, BOOK_SIZE, unpack_book)
 
    if active_only:
        return [r for r in records if r["status"] != STATUS_DELETED]
    return records
 
 
def filter_books(genre=None, available_only=False):
    """กรองหนังสือตามประเภท (ไม่สนตัวพิมพ์เล็ก/ใหญ่) และ/หรือ เฉพาะที่มีสต็อกว่าง
    (ไม่รวม deleted)"""
    records = list_all(active_only=True)
 
    if genre is not None:
        genre_lower = genre.strip().lower()
        records = [r for r in records if r["genre"].strip().lower() == genre_lower]
    if available_only:
        records = [r for r in records if r["stock_available"] > 0]
 
    return records
 
 
def stats():
    """สรุปสถิติหนังสือ ตาม key ที่ตกลงกัน:
    active_titles, deleted_titles, total_copies, currently_borrowed,
    available_now, price_min, price_max, price_avg, genre_count"""
    all_records = list_all(active_only=False)
    active_records = [r for r in all_records if r["status"] != STATUS_DELETED]
    deleted_records = [r for r in all_records if r["status"] == STATUS_DELETED]
 
    total_copies = sum(r["stock_total"] for r in active_records)
    available_now = sum(r["stock_available"] for r in active_records)
    currently_borrowed = total_copies - available_now
 
    prices = [r["price_per_day"] for r in active_records]
    if prices:
        price_min = min(prices)
        price_max = max(prices)
        price_avg = sum(prices) / len(prices)
    else:
        price_min = 0.0
        price_max = 0.0
        price_avg = 0.0
 
    genre_count = {}
    for r in active_records:
        genre_count[r["genre"]] = genre_count.get(r["genre"], 0) + 1
 
    return {
        "total_titles": len(all_records),
        "active_titles": len(active_records),
        "deleted_titles": len(deleted_records),
        "total_copies": total_copies,
        "currently_borrowed": currently_borrowed,
        "available_now": available_now,
        "price_min": price_min,
        "price_max": price_max,
        "price_avg": price_avg,
        "genre_count": genre_count,
    }
