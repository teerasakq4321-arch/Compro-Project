"""
pack/unpack และ CRUD สำหรับ books.dat
"""
import struct
 
import storage
 
try:
    from config import BOOKS_FILE
except ImportError:
    # เผื่อ config.py ยังไม่พร้อม/ยังไม่ import ได้ตอน dev คนละไฟล์
    BOOKS_FILE = "books.dat"
 
# ---------------------------------------------------------------------------
# โครงสร้าง record
# ---------------------------------------------------------------------------
TITLE_SIZE = 100
AUTHOR_SIZE = 100
GENRE_SIZE = 50
 
# book_id(i) + title + author + genre + price(d) + stock_total(i)
# + stock_available(i) + status(i)
BOOK_FORMAT = f"<i{TITLE_SIZE}s{AUTHOR_SIZE}s{GENRE_SIZE}sdiii"
RECORD_SIZE = struct.calcsize(BOOK_FORMAT)
 
STATUS_DELETED = 0
STATUS_ACTIVE = 1
 
 
# ---------------------------------------------------------------------------
# pack / unpack
# ---------------------------------------------------------------------------
def pack_book(book_id, title, author, genre, price, stock_total, stock_available, status):
    """แปลงข้อมูลหนังสือเป็น bytes ขนาดคงที่ (fixed-length record)"""
    return struct.pack(
        BOOK_FORMAT,
        book_id,
        storage.encode_str(title, TITLE_SIZE),
        storage.encode_str(author, AUTHOR_SIZE),
        storage.encode_str(genre, GENRE_SIZE),
        float(price),
        int(stock_total),
        int(stock_available),
        int(status),
    )
 
 
def unpack_book(raw):
    """แปลง bytes กลับเป็น dict ข้อมูลหนังสือ"""
    (book_id, title_raw, author_raw, genre_raw, price,
     stock_total, stock_available, status) = struct.unpack(BOOK_FORMAT, raw)
 
    return {
        "book_id": book_id,
        "title": storage.decode_str(title_raw),
        "author": storage.decode_str(author_raw),
        "genre": storage.decode_str(genre_raw),
        "price": price,
        "stock_total": stock_total,
        "stock_available": stock_available,
        "status": status,
    }
 
 
# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------
def add(title, author, genre, stock_total):
    """เพิ่มหนังสือใหม่ -> คืน book_id ใหม่"""
    storage.ensure_file(BOOKS_FILE)
 
    new_id = storage.next_id(BOOKS_FILE, RECORD_SIZE, unpack_book, "book_id")
    stock_total = int(stock_total)
 
    raw = pack_book(
        book_id=new_id,
        title=title,
        author=author,
        genre=genre,
        price=0.0,
        stock_total=stock_total,
        stock_available=stock_total,
        status=STATUS_ACTIVE,
    )
    storage.append_record(BOOKS_FILE, raw)
    return new_id
 
 
def get(book_id):
    """คืนข้อมูลหนังสือ (dict) ถ้าพบและยังไม่ถูกลบ ไม่งั้นคืน None"""
    storage.ensure_file(BOOKS_FILE)
    _, record = storage.find_index_by_id(BOOKS_FILE, RECORD_SIZE, unpack_book, "book_id", book_id)
 
    if record is None or record["status"] == STATUS_DELETED:
        return None
    return record
 
 
def update(book_id, title=None, author=None, genre=None, stock_total=None):
    """แก้ไขข้อมูลหนังสือ (เฉพาะฟิลด์ที่ส่งมา) -> True/False"""
    storage.ensure_file(BOOKS_FILE)
    index, record = storage.find_index_by_id(BOOKS_FILE, RECORD_SIZE, unpack_book, "book_id", book_id)
 
    if record is None or record["status"] == STATUS_DELETED:
        return False
 
    new_title = title if title is not None else record["title"]
    new_author = author if author is not None else record["author"]
    new_genre = genre if genre is not None else record["genre"]
 
    new_stock_total = record["stock_total"]
    new_stock_available = record["stock_available"]
 
    if stock_total is not None:
        stock_total = int(stock_total)
        rented = record["stock_total"] - record["stock_available"]  # จำนวนที่ถูกยืมอยู่
        new_stock_total = stock_total
        # available ใหม่ = total ใหม่ - จำนวนที่ถูกยืมอยู่ (กันติดลบ)
        new_stock_available = max(0, new_stock_total - rented)
 
    raw = pack_book(
        book_id=book_id,
        title=new_title,
        author=new_author,
        genre=new_genre,
        price=record["price"],
        stock_total=new_stock_total,
        stock_available=new_stock_available,
        status=record["status"],
    )
    storage.overwrite_record_at_index(BOOKS_FILE, RECORD_SIZE, index, raw)
    return True
 
 
def delete(book_id):
    """Soft-delete หนังสือ (เปลี่ยน status เป็น 0) -> True/False"""
    storage.ensure_file(BOOKS_FILE)
    index, record = storage.find_index_by_id(BOOKS_FILE, RECORD_SIZE, unpack_book, "book_id", book_id)
 
    if record is None or record["status"] == STATUS_DELETED:
        return False
 
    raw = pack_book(
        book_id=record["book_id"],
        title=record["title"],
        author=record["author"],
        genre=record["genre"],
        price=record["price"],
        stock_total=record["stock_total"],
        stock_available=record["stock_available"],
        status=STATUS_DELETED,
    )
    storage.overwrite_record_at_index(BOOKS_FILE, RECORD_SIZE, index, raw)
    return True
 
 
# ---------------------------------------------------------------------------
# เรียกใช้จาก rentals.py เท่านั้น (ห้ามไฟล์อื่นแก้ books.dat ตรง ๆ)
# ---------------------------------------------------------------------------
def decrement_stock(book_id):
    """ลด stock_available ลง 1 ตอนมีการยืมหนังสือ -> True/False"""
    storage.ensure_file(BOOKS_FILE)
    index, record = storage.find_index_by_id(BOOKS_FILE, RECORD_SIZE, unpack_book, "book_id", book_id)
 
    if record is None or record["status"] == STATUS_DELETED:
        return False
    if record["stock_available"] <= 0:
        return False
 
    raw = pack_book(
        book_id=record["book_id"],
        title=record["title"],
        author=record["author"],
        genre=record["genre"],
        price=record["price"],
        stock_total=record["stock_total"],
        stock_available=record["stock_available"] - 1,
        status=record["status"],
    )
    storage.overwrite_record_at_index(BOOKS_FILE, RECORD_SIZE, index, raw)
    return True
 
 
def increment_stock(book_id):
    """เพิ่ม stock_available ขึ้น 1 ตอนมีการคืนหนังสือ -> True/False"""
    storage.ensure_file(BOOKS_FILE)
    index, record = storage.find_index_by_id(BOOKS_FILE, RECORD_SIZE, unpack_book, "book_id", book_id)
 
    if record is None:
        return False
 
    new_available = min(record["stock_total"], record["stock_available"] + 1)
 
    raw = pack_book(
        book_id=record["book_id"],
        title=record["title"],
        author=record["author"],
        genre=record["genre"],
        price=record["price"],
        stock_total=record["stock_total"],
        stock_available=new_available,
        status=record["status"],
    )
    storage.overwrite_record_at_index(BOOKS_FILE, RECORD_SIZE, index, raw)
    return True
 
 
# ---------------------------------------------------------------------------
# List / Filter / Stats
# ---------------------------------------------------------------------------
def list_all(active_only=True):
    """คืนรายการหนังสือทั้งหมด (กรอง deleted ออกถ้า active_only=True)"""
    storage.ensure_file(BOOKS_FILE)
    records = storage.read_all(BOOKS_FILE, RECORD_SIZE, unpack_book)
 
    if active_only:
        return [r for r in records if r["status"] != STATUS_DELETED]
    return records
 
 
def filter_books(genre=None, available_only=False):
    """กรองหนังสือตามประเภท และ/หรือ เฉพาะที่มีสต็อกว่าง (ไม่รวม deleted)"""
    records = list_all(active_only=True)
 
    if genre is not None:
        records = [r for r in records if r["genre"] == genre]
    if available_only:
        records = [r for r in records if r["stock_available"] > 0]
 
    return records
 
 
def stats():
    """สรุปสถิติหนังสือทั้งหมด (ไม่นับ deleted)"""
    records = list_all(active_only=True)
 
    total_titles = len(records)
    total_stock_total = sum(r["stock_total"] for r in records)
    total_stock_available = sum(r["stock_available"] for r in records)
    total_rented = total_stock_total - total_stock_available
 
    by_genre = {}
    for r in records:
        genre = r["genre"]
        by_genre[genre] = by_genre.get(genre, 0) + 1
 
    return {
        "total_titles": total_titles,
        "total_stock_total": total_stock_total,
        "total_stock_available": total_stock_available,
        "total_rented": total_rented,
        "by_genre": by_genre,
    }
