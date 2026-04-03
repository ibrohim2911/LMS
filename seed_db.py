#!/usr/bin/env python
"""
seed_db.py — Auto-fill db.sqlite3 with realistic sample data.

Usage (from the project root, where manage.py lives):
    python seed_db.py

The script sets up Django's environment automatically before importing
any models, so no extra steps are required.
"""

import os
import sys
import django
from datetime import date, timedelta

# ---------------------------------------------------------------------------
# Bootstrap Django
# ---------------------------------------------------------------------------
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

# ---------------------------------------------------------------------------
# Imports (after django.setup())
# ---------------------------------------------------------------------------
from django.utils import timezone
from django.db import transaction
from users.models import User, Notification
from books.models import (
    Category, subCategory, Tag, Author, Kitob,
    Reservation, Rating, Comment, Bookmark, Journals,
)
from news.models import News

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
def p(msg: str) -> None:
    print(f"  {msg}")


# ---------------------------------------------------------------------------
# Data pools
# ---------------------------------------------------------------------------

CATEGORIES = [
    ("Fiction",         "📖"),
    ("Science",         "🔬"),
    ("History",         "🏛️"),
    ("Technology",      "💻"),
    ("Philosophy",      "🤔"),
    ("Mathematics",     "📐"),
    ("Arts & Culture",  "🎨"),
    ("Biography",       "👤"),
]

SUBCATEGORIES = {
    "Fiction":        ["Classic Literature", "Fantasy", "Science Fiction", "Mystery & Thriller"],
    "Science":        ["Biology", "Physics", "Chemistry", "Astronomy"],
    "History":        ["Ancient History", "Modern History", "World Wars", "Asian History"],
    "Technology":     ["Programming", "Artificial Intelligence", "Networking", "Cybersecurity"],
    "Philosophy":     ["Ethics", "Metaphysics", "Logic", "Eastern Philosophy"],
    "Mathematics":    ["Algebra", "Calculus", "Statistics", "Number Theory"],
    "Arts & Culture": ["Painting", "Music Theory", "Architecture", "Cinema"],
    "Biography":      ["Scientists", "Politicians", "Artists", "Athletes"],
}

TAGS_LIST = [
    "bestseller", "classic", "award-winning", "recommended", "beginner-friendly",
    "advanced", "illustrated", "translated", "uzbek", "russian", "english",
    "hardcover", "paperback", "research", "textbook", "novel", "poetry",
]

AUTHORS = [
    "Leo Tolstoy", "Fyodor Dostoevsky", "Anton Chekhov",
    "Ernest Hemingway", "George Orwell", "Aldous Huxley",
    "Stephen Hawking", "Richard Feynman", "Carl Sagan",
    "Yuval Noah Harari", "Malcolm Gladwell", "Bill Bryson",
    "Abdulla Qodiriy", "Cho'lpon", "Oybek",
    "Alisher Navoiy", "Bobur Mirzo", "Hamid Sulaymon",
    "Donald Knuth", "Andrew Tanenbaum",
]

BOOKS = [
    # (name, category, subcategory, authors, tags, isbn, qty, pages, desc, published_date)
    ("War and Peace",          "Fiction",      "Classic Literature",   ["Leo Tolstoy"],           ["classic", "novel"],            "978-0-14-044793-4", 5, 1296, "Epic novel set during Napoleon's invasion of Russia.",       date(1869, 1, 1)),
    ("Crime and Punishment",   "Fiction",      "Classic Literature",   ["Fyodor Dostoevsky"],     ["classic", "novel", "translated"],"978-0-14-044913-6", 4, 656,  "A psychological novel about guilt and redemption.",          date(1866, 1, 1)),
    ("1984",                   "Fiction",      "Science Fiction",      ["George Orwell"],         ["classic", "bestseller"],        "978-0-45-228423-4", 6, 328,  "A dystopian social science fiction novel.",                  date(1949, 6, 8)),
    ("Brave New World",        "Fiction",      "Science Fiction",      ["Aldous Huxley"],         ["classic", "award-winning"],     "978-0-06-085052-4", 3, 311,  "A dystopian novel set in a futuristic World State.",         date(1932, 1, 1)),
    ("A Brief History of Time","Science",      "Astronomy",            ["Stephen Hawking"],       ["bestseller", "recommended"],    "978-0-55-305340-1", 7, 212,  "Cosmology for general audiences by Stephen Hawking.",        date(1988, 4, 1)),
    ("The Feynman Lectures",   "Science",      "Physics",              ["Richard Feynman"],       ["textbook", "recommended"],      "978-0-46-502327-9", 4, 1552, "The definitive physics textbook series.",                    date(1964, 1, 1)),
    ("Cosmos",                 "Science",      "Astronomy",            ["Carl Sagan"],            ["bestseller", "illustrated"],    "978-0-34-539107-7", 5, 365,  "Personal voyage through the universe.",                     date(1980, 10, 1)),
    ("Sapiens",                "History",      "Modern History",       ["Yuval Noah Harari"],     ["bestseller", "recommended"],    "978-0-06-231609-7", 8, 443,  "A brief history of humankind.",                              date(2011, 1, 1)),
    ("Outliers",               "Biography",    "Scientists",           ["Malcolm Gladwell"],      ["bestseller"],                   "978-0-31-601792-3", 5, 309,  "The story of success.",                                      date(2008, 11, 18)),
    ("O'tgan kunlar",          "Fiction",      "Classic Literature",   ["Abdulla Qodiriy"],       ["classic", "uzbek"],             "978-9943-03-001-1", 6, 374,  "Birinchi o'zbek romani.",                                    date(1926, 1, 1)),
    ("Kecha va kunduz",        "Fiction",      "Classic Literature",   ["Oybek"],                 ["classic", "uzbek"],             "978-9943-03-002-1", 4, 320,  "O'zbek adabiyotining durdonasi.",                            date(1936, 1, 1)),
    ("The Art of Computer Programming", "Technology", "Programming",   ["Donald Knuth"],          ["textbook", "advanced"],         "978-0-20-189683-1", 3, 3168, "Comprehensive monograph covering algorithms.",               date(1968, 1, 1)),
    ("Computer Networks",      "Technology",   "Networking",           ["Andrew Tanenbaum"],      ["textbook", "recommended"],      "978-0-13-212695-3", 5, 960,  "Industry-standard networking textbook.",                     date(2010, 3, 19)),
    ("Calculus",               "Mathematics",  "Calculus",             ["Donald Knuth"],          ["textbook", "beginner-friendly"],"978-0-07-294244-5", 6, 1152, "A complete introduction to calculus.",                       date(2005, 1, 1)),
    ("Ethics",                 "Philosophy",   "Ethics",               ["Aristotle"],             ["classic", "philosophy"],        "978-0-14-044949-5", 4, 329,  "Aristotle's foundational work on ethics.",                   date(1998, 1, 1)),
    ("The Republic",           "Philosophy",   "Metaphysics",          ["Plato"],                 ["classic", "philosophy"],        "978-0-14-045511-3", 4, 416,  "Plato's foundational work on justice and politics.",         date(1998, 1, 1)),
    ("Hamletdan Hamletgacha",  "Biography",    "Artists",              ["Hamid Sulaymon"],        ["uzbek"],                        "978-9943-03-010-1", 3, 280,  "O'zbek tanqidchiligi namunasi.",                             date(2001, 1, 1)),
    ("Devonu lug'otit turk",   "History",      "Asian History",        ["Alisher Navoiy"],        ["classic", "uzbek", "research"], "978-9943-03-020-1", 2, 560,  "Turkiy tillar lug'ati.",                                     date(2003, 1, 1)),
    ("Machine Learning",       "Technology",   "Artificial Intelligence", ["Andrew Tanenbaum"],   ["textbook", "advanced"],         "978-0-26-204361-1", 5, 688,  "A comprehensive guide to machine learning.",                 date(2020, 1, 1)),
    ("Algebra",                "Mathematics",  "Algebra",              ["Donald Knuth"],          ["textbook", "beginner-friendly"],"978-0-07-100578-0", 7, 450,  "Fundamentals of algebra.",                                   date(2015, 1, 1)),
]

JOURNALS = [
    ("Nature",         "Springer Nature",           "One of the world's leading scientific journals.",   "1476-4687", date(2020, 1, 1),  date(2024, 12, 31)),
    ("Science",        "AAAS",                      "Peer-reviewed journal covering all sciences.",      "1095-9203", date(2019, 1, 1),  date(2024, 12, 31)),
    ("IEEE Spectrum",  "IEEE",                      "Technology news and analysis.",                     "0018-9235", date(2021, 1, 1),  date(2025, 12, 31)),
    ("Lancet",         "Elsevier",                  "Leading medical journal.",                          "1474-547X", date(2020, 6, 1),  date(2025, 6, 30)),
    ("Zamin ilmi",     "O'zbekiston Fanlar Akad.", "O'zbek ilmiy jurnali.",                             "2181-0001", date(2022, 1, 1),  date(2026, 12, 31)),
]

USERS = [
    # (username, first_name, last_name, email, password, role, phone)
    ("admin",        "Admin",     "Superuser",  "admin@library.uz",        "Admin@12345",     "admin",     "+998901234560"),
    ("librarian1",   "Nodira",    "Yusupova",   "nodira@library.uz",       "Librarian@123",   "librarian", "+998901234561"),
    ("librarian2",   "Jasur",     "Toshmatov",  "jasur@library.uz",        "Librarian@456",   "librarian", "+998901234562"),
    ("student1",     "Dilnoza",   "Karimova",   "dilnoza@student.uz",      "Student@1234",    "student",   "+998901234563"),
    ("student2",     "Bobur",     "Rahimov",    "bobur@student.uz",        "Student@5678",    "student",   "+998901234564"),
    ("student3",     "Malika",    "Saidova",    "malika@student.uz",       "Student@9012",    "student",   "+998901234565"),
    ("student4",     "Sardor",    "Xasanov",    "sardor@student.uz",       "Student@3456",    "student",   "+998901234566"),
    ("student5",     "Zulfiya",   "Nazarova",   "zulfiya@student.uz",      "Student@7890",    "student",   "+998901234567"),
    ("teacher1",     "Alisher",   "Ergashev",   "alisher.t@library.uz",    "Teacher@1234",    "teacher",   "+998901234568"),
    ("teacher2",     "Mohira",    "Tursunova",  "mohira.t@library.uz",     "Teacher@5678",    "teacher",   "+998901234569"),
    ("teacher3",     "Rustam",    "Mirzayev",   "rustam.t@library.uz",     "Teacher@9012",    "teacher",   "+998901234570"),
]

NEWS_ITEMS = [
    # (title, main, author_username, new_column)
    ("Library reopens after renovation",
     "We are excited to announce that the main library building has reopened after a 3-month renovation. "
     "New reading halls, modern equipment, and an expanded digital resource centre await you.",
     "admin", 1),
    ("New book arrivals — Spring 2024",
     "Over 200 new titles have arrived this season, spanning fiction, science, technology, and Uzbek literature. "
     "Visit the new arrivals shelf or browse the catalogue online.",
     "librarian1", 2),
    ("Reading marathon results",
     "Congratulations to all participants of the annual reading marathon! "
     "This year 540 students took part, collectively reading 3 200 books in 30 days.",
     "librarian2", 3),
    ("Digital resources now available 24/7",
     "Students and teachers can now access our full e-book and journal collection around the clock "
     "through the library portal. Log in with your university credentials.",
     "admin", 4),
    ("Summer reading challenge starts June 1",
     "Sign up for the summer reading challenge and win exciting prizes. "
     "Read at least 5 books between June 1 and August 31 to qualify.",
     "teacher1", 5),
]

COMMENT_TEXTS = [
    "Absolutely loved this book! A must-read for everyone.",
    "Very informative and well-written. Highly recommended.",
    "A classic that never gets old. Read it twice already.",
    "Challenging read but definitely worth the effort.",
    "Changed my perspective on the subject completely.",
    "Clear explanations and great examples throughout.",
    "One of the best books I've ever read.",
    "A bit dense at times, but packed with valuable information.",
    "Perfect for beginners and experts alike.",
    "The author's writing style is captivating and engaging.",
]

NOTIFICATION_TEMPLATES = [
    ("Book Available", "The book '{book}' that you reserved is now available for pickup."),
    ("Return Reminder", "Please return '{book}' by {date}. Overdue books may result in penalties."),
    ("Reservation Approved", "Your reservation for '{book}' has been approved. Please collect it within 24 hours."),
    ("Welcome to the Library", "Welcome, {name}! Your library account is active. Happy reading!"),
    ("New Arrivals", "New books have arrived in the '{category}' section. Check them out!"),
]


# ---------------------------------------------------------------------------
# Seeder functions
# ---------------------------------------------------------------------------

def create_users():
    p("Creating users …")
    created = {}
    for username, first, last, email, pwd, role, phone in USERS:
        user, new = User.objects.get_or_create(
            username=username,
            defaults=dict(
                first_name=first,
                last_name=last,
                email=email,
                role=role,
                phone_number=phone,
                max_allowed=5 if role in ("teacher", "librarian", "admin") else 3,
            ),
        )
        if new:
            if role == "admin":
                user.is_superuser = True
                user.is_staff = True
            user.set_password(pwd)
            user.save()
            p(f"  + {role:10s} {username}")
        created[username] = user
    return created


def create_categories():
    p("Creating categories …")
    cats = {}
    for name, icon in CATEGORIES:
        cat, _ = Category.objects.get_or_create(name=name, defaults={"icon": icon, "visible": True})
        cats[name] = cat

    subcats = {}
    for cat_name, sub_names in SUBCATEGORIES.items():
        cat = cats[cat_name]
        for sub_name in sub_names:
            sub, _ = subCategory.objects.get_or_create(
                name=sub_name, category=cat, defaults={"visible": True}
            )
            subcats[sub_name] = sub
    p(f"  {len(cats)} categories, {len(subcats)} subcategories created.")
    return cats, subcats


def create_tags():
    p("Creating tags …")
    tags = {}
    for name in TAGS_LIST:
        tag, _ = Tag.objects.get_or_create(name=name)
        tags[name] = tag
    # Add extra tags not in the predefined list (used by books)
    for extra in ["philosophy"]:
        tag, _ = Tag.objects.get_or_create(name=extra)
        tags[extra] = tag
    return tags


def create_authors():
    p("Creating authors …")
    authors = {}
    all_authors = AUTHORS + ["Aristotle", "Plato"]
    for name in all_authors:
        a, _ = Author.objects.get_or_create(name=name)
        authors[name] = a
    return authors


def create_books(cats, subcats, tags, authors):
    p("Creating books …")
    books = {}
    for (name, cat_name, sub_name, author_names, tag_names,
         isbn, qty, pages, desc, pub_date) in BOOKS:
        book, created = Kitob.objects.get_or_create(
            isbn=isbn,
            defaults=dict(
                name=name,
                category=cats.get(cat_name),
                subcategory=subcats.get(sub_name),
                quantity=qty,
                is_available=qty > 0,
                description=desc,
                pages=pages,
                published_date=pub_date,
                is_frequent=False,
                is_physical=True,
                visible=True,
                read_time=14,
                location=f"Shelf {chr(65 + (hash(name) % 8))}-{abs(hash(isbn)) % 20 + 1}",
            ),
        )
        if created:
            for aname in author_names:
                a = authors.get(aname)
                if a:
                    book.author.add(a)
            for tname in tag_names:
                t = tags.get(tname)
                if t:
                    book.tags.add(t)
            p(f"  + {name}")
        books[name] = book
    return books


def create_journals():
    p("Creating journals …")
    for name, publisher, desc, iccn, start, end in JOURNALS:
        Journals.objects.get_or_create(
            iccn=iccn,
            defaults=dict(name=name, publisher=publisher,
                          description=desc, start_date=start, end_date=end),
        )


def create_reservations(users_map, books_map):
    p("Creating reservations …")
    now = timezone.now()

    reservation_specs = [
        # (username, book_name, status, days_ago_reserved, days_held)
        ("student1", "War and Peace",              "returned",     60, 14),
        ("student1", "1984",                       "given",        10,  0),
        ("student2", "Sapiens",                    "returned",     45, 14),
        ("student2", "Cosmos",                     "given",         5,  0),
        ("student3", "O'tgan kunlar",              "returned",     30, 14),
        ("student3", "Crime and Punishment",       "given",         3,  0),
        ("student4", "A Brief History of Time",    "returned",     20, 14),
        ("student4", "Brave New World",            "given",         7,  0),
        ("student5", "Outliers",                   "returned",     50, 14),
        ("student5", "Machine Learning",           "given",         2,  0),
        ("teacher1", "The Art of Computer Programming", "returned", 40, 14),
        ("teacher1", "Computer Networks",          "given",         8,  0),
        ("teacher2", "Calculus",                   "returned",     35, 14),
        ("teacher2", "Algebra",                    "given",         4,  0),
        ("teacher3", "Ethics",                     "returned",     25, 14),
        ("teacher3", "The Republic",               "given",         6,  0),
        # A few pending
        ("student1", "The Feynman Lectures",       "pending",       1,  0),
        ("student2", "Kecha va kunduz",            "pending",       2,  0),
        ("student3", "Devonu lug'otit turk",       "pending",       3,  0),
    ]

    created_count = 0
    for username, book_name, target_status, days_ago, days_held in reservation_specs:
        user = users_map.get(username)
        book = books_map.get(book_name)
        if not user or not book:
            continue

        exists = Reservation.objects.filter(user=user, book=book).exists()
        if exists:
            continue

        reserved_from = now - timedelta(days=days_ago)
        reserved_until = reserved_from + timedelta(days=book.read_time or 14)

        # Create as 'pending' first (signals handle queue)
        r = Reservation(user=user, book=book, status="pending")
        r.save()

        # Advance to target status using direct DB updates to avoid
        # re-triggering the complex signal chain for historical data
        if target_status == "approved":
            Reservation.objects.filter(pk=r.pk).update(
                status="approved", place=None, approved_at=reserved_from,
            )
        elif target_status == "given":
            Reservation.objects.filter(pk=r.pk).update(
                status="given", place=None,
                approved_at=reserved_from,
                reserved_from=reserved_from,
                reserved_until=reserved_until,
            )
        elif target_status == "returned":
            returned_at = reserved_from + timedelta(days=days_held)
            Reservation.objects.filter(pk=r.pk).update(
                status="returned", place=None,
                approved_at=reserved_from,
                reserved_from=reserved_from,
                reserved_until=reserved_until,
                returned_at=returned_at,
            )

        created_count += 1

    p(f"  {created_count} reservations created.")


def create_ratings_and_comments(users_map, books_map):
    p("Creating ratings and comments …")
    rating_specs = [
        # (username, book_name, score, comment_text)
        ("student1", "War and Peace",           5, COMMENT_TEXTS[0]),
        ("student1", "1984",                    5, COMMENT_TEXTS[1]),
        ("student2", "Sapiens",                 4, COMMENT_TEXTS[2]),
        ("student2", "Cosmos",                  5, COMMENT_TEXTS[3]),
        ("student3", "O'tgan kunlar",           5, COMMENT_TEXTS[4]),
        ("student3", "Crime and Punishment",    4, COMMENT_TEXTS[5]),
        ("student4", "A Brief History of Time", 5, COMMENT_TEXTS[6]),
        ("student4", "Brave New World",         4, COMMENT_TEXTS[7]),
        ("student5", "Outliers",                4, COMMENT_TEXTS[8]),
        ("student5", "Machine Learning",        5, COMMENT_TEXTS[9]),
        ("teacher1", "The Art of Computer Programming", 5, COMMENT_TEXTS[0]),
        ("teacher1", "Computer Networks",       4, COMMENT_TEXTS[1]),
        ("teacher2", "Calculus",                5, COMMENT_TEXTS[2]),
        ("teacher2", "Algebra",                 4, COMMENT_TEXTS[3]),
        ("teacher3", "Ethics",                  5, COMMENT_TEXTS[4]),
        ("teacher3", "The Republic",            5, COMMENT_TEXTS[5]),
    ]

    for username, book_name, score, text in rating_specs:
        user = users_map.get(username)
        book = books_map.get(book_name)
        if not user or not book:
            continue

        if Rating.objects.filter(book=book, user=user).exists():
            continue

        # Create comment first (rating references comment)
        comment = Comment.objects.create(book=book, user=user, content=text)
        Rating.objects.create(book=book, user=user, score=score, comment=comment)

    p(f"  {len(rating_specs)} rating/comment pairs processed.")


def create_bookmarks(users_map, books_map):
    p("Creating bookmarks …")
    bookmark_specs = [
        ("student1", ["1984", "Sapiens", "A Brief History of Time"]),
        ("student2", ["War and Peace", "Cosmos", "Outliers"]),
        ("student3", ["O'tgan kunlar", "Crime and Punishment", "Machine Learning"]),
        ("student4", ["Brave New World", "Computer Networks", "Calculus"]),
        ("student5", ["The Feynman Lectures", "Algebra", "Ethics"]),
        ("teacher1", ["The Art of Computer Programming", "Machine Learning"]),
        ("teacher2", ["Calculus", "Algebra", "The Republic"]),
        ("teacher3", ["Ethics", "Sapiens", "Cosmos"]),
    ]

    count = 0
    for username, book_names in bookmark_specs:
        user = users_map.get(username)
        for bname in book_names:
            book = books_map.get(bname)
            if user and book:
                Bookmark.objects.get_or_create(user=user, book=book)
                count += 1

    p(f"  {count} bookmarks created.")


def create_notifications(users_map, books_map):
    p("Creating notifications …")
    specs = [
        ("student1", "Book Available",      "The book '1984' that you reserved is now available for pickup."),
        ("student1", "Return Reminder",     "Please return 'War and Peace' by next Friday. Overdue books may result in penalties."),
        ("student2", "Reservation Approved","Your reservation for 'Sapiens' has been approved. Please collect it within 24 hours."),
        ("student3", "Welcome to the Library", "Welcome, Malika! Your library account is active. Happy reading!"),
        ("student4", "New Arrivals",        "New books have arrived in the 'Technology' section. Check them out!"),
        ("student5", "Return Reminder",     "Please return 'Outliers' by next Monday. Overdue books may result in penalties."),
        ("teacher1", "New Arrivals",        "New books have arrived in the 'Science' section. Check them out!"),
        ("teacher2", "Reservation Approved","Your reservation for 'Calculus' has been approved. Please collect it within 24 hours."),
        ("teacher3", "Book Available",      "The book 'Ethics' that you reserved is now available for pickup."),
        ("librarian1", "New Arrivals",      "New books have arrived. Please update the catalogue accordingly."),
    ]

    count = 0
    for username, title, message in specs:
        user = users_map.get(username)
        if user:
            Notification.objects.get_or_create(
                user=user, title=title, message=message
            )
            count += 1

    p(f"  {count} notifications created.")


def create_news(users_map):
    p("Creating news …")
    for title, main, author_username, new_column in NEWS_ITEMS:
        user = users_map.get(author_username)
        if user:
            News.objects.get_or_create(
                title=title,
                defaults=dict(main=main, user=user, new_column=new_column),
            )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("  LMS Database Seeder")
    print("=" * 60)

    with transaction.atomic():
        users_map   = create_users()
        cats, subcats = create_categories()
        tags        = create_tags()
        authors     = create_authors()
        books_map   = create_books(cats, subcats, tags, authors)
        create_journals()
        create_reservations(users_map, books_map)
        create_ratings_and_comments(users_map, books_map)
        create_bookmarks(users_map, books_map)
        create_notifications(users_map, books_map)
        create_news(users_map)

    print("=" * 60)
    print("  Done! Database seeded successfully.")
    print("=" * 60)
    print()
    print("  Credentials created:")
    print()
    for username, _, _, email, pwd, role, _ in USERS:
        print(f"    {role:10s}  username={username:12s}  password={pwd}")
    print()


if __name__ == "__main__":
    main()
