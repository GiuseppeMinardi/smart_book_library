import datetime

from api.db import _normalize_author_date, save_author_record


class FakeCursor:
    def __init__(self):
        self.last_query = None
        self.last_params = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def execute(self, query, params=None):
        self.last_query = query
        self.last_params = params

    def fetchone(self):
        return {
            "id": 1,
            "name": self.last_params[0],
            "birth_date": self.last_params[1],
            "death_date": self.last_params[2],
            "nationality": self.last_params[3],
            "sex": self.last_params[4],
            "bio": self.last_params[5],
            "author_link": self.last_params[6],
        }


class FakeConnection:
    def __init__(self):
        self.cursor_obj = FakeCursor()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def cursor(self):
        return self.cursor_obj

    def commit(self):
        pass

    def rollback(self):
        pass


def test_normalize_author_date_accepts_iso_date_string():
    assert _normalize_author_date("1984-06-13") == datetime.date(1984, 6, 13)


def test_normalize_author_date_accepts_year_and_month():
    assert _normalize_author_date("1984-06") == datetime.date(1984, 6, 1)


def test_normalize_author_date_accepts_year_only():
    assert _normalize_author_date("1984") == datetime.date(1984, 1, 1)


def test_normalize_author_date_returns_none_for_bad_string():
    assert _normalize_author_date("circa 1984") is None
    assert _normalize_author_date("") is None


def test_save_author_record_ignores_invalid_dates():
    conn = FakeConnection()
    author_info = {
        "name": "Jane Doe",
        "birth_date": "circa 1820",
        "death_date": "unknown",
        "nationality": "Testland",
        "sex": "F",
        "biography": "Sample biography.",
        "url": "https://example.com/author",
    }

    result = save_author_record(author_info, conn=conn)

    assert result["name"] == "Jane Doe"
    assert conn.cursor_obj.last_params[1] is None
    assert conn.cursor_obj.last_params[2] is None
    assert conn.cursor_obj.last_params[3] == "Testland"
    assert conn.cursor_obj.last_params[4] == "F"
    assert conn.cursor_obj.last_params[5] == "Sample biography."
    assert conn.cursor_obj.last_params[6] == "https://example.com/author"
