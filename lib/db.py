"""
Connection pool manager for Neon PostgreSQL via psycopg2.
"""
import streamlit as st
import psycopg2
from psycopg2 import pool, extras


def _get_pool():
    """Return singleton ThreadedConnectionPool (cached in session_state)."""
    if "_db_pool" not in st.session_state:
        st.session_state._db_pool = pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=3,
            dsn=st.secrets["DATABASE_URL"],
        )
    return st.session_state._db_pool


def _reset_pool():
    """Close and recreate the connection pool."""
    old = st.session_state.pop("_db_pool", None)
    if old:
        try:
            old.closeall()
        except Exception:
            pass
    return _get_pool()


def _conn_is_alive(conn):
    """Check if a connection is still usable."""
    try:
        conn.reset()
        return True
    except Exception:
        return False


def _get_conn(p):
    """Get a connection from the pool, verifying it's alive."""
    conn = p.getconn()
    if conn.closed or not _conn_is_alive(conn):
        p.putconn(conn, close=True)
        p = _reset_pool()
        conn = p.getconn()
    return p, conn


def _execute(sql: str, params: tuple | None = None, *, returning: bool = False, returning_all: bool = False):
    """Low-level execute helper. Returns rows when requested."""
    p = _get_pool()
    p, conn = _get_conn(p)
    try:
        with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            if returning_all:
                result = [dict(r) for r in cur.fetchall()]
            elif returning:
                row = cur.fetchone()
                result = dict(row) if row else None
            else:
                result = None
            conn.commit()
            return result
    except psycopg2.OperationalError:
        conn.rollback()
        p.putconn(conn, close=True)
        p = _reset_pool()
        p, conn = _get_conn(p)
        try:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
                cur.execute(sql, params)
                if returning_all:
                    result = [dict(r) for r in cur.fetchall()]
                elif returning:
                    row = cur.fetchone()
                    result = dict(row) if row else None
                else:
                    result = None
                conn.commit()
                return result
        except Exception:
            conn.rollback()
            raise
        finally:
            p.putconn(conn)
    except Exception:
        conn.rollback()
        raise
    finally:
        try:
            p.putconn(conn)
        except Exception:
            pass


def fetch_all(sql: str, params: tuple | None = None) -> list[dict]:
    """SELECT multiple rows."""
    p = _get_pool()
    p, conn = _get_conn(p)
    try:
        with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            return [dict(r) for r in cur.fetchall()]
    except psycopg2.OperationalError:
        p.putconn(conn, close=True)
        p = _reset_pool()
        p, conn = _get_conn(p)
        try:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
                cur.execute(sql, params)
                return [dict(r) for r in cur.fetchall()]
        finally:
            p.putconn(conn)
    finally:
        try:
            p.putconn(conn)
        except Exception:
            pass


def fetch_one(sql: str, params: tuple | None = None) -> dict | None:
    """SELECT single row (or None)."""
    p = _get_pool()
    p, conn = _get_conn(p)
    try:
        with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
            return dict(row) if row else None
    except psycopg2.OperationalError:
        p.putconn(conn, close=True)
        p = _reset_pool()
        p, conn = _get_conn(p)
        try:
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
                cur.execute(sql, params)
                row = cur.fetchone()
                return dict(row) if row else None
        finally:
            p.putconn(conn)
    finally:
        try:
            p.putconn(conn)
        except Exception:
            pass


def execute(sql: str, params: tuple | None = None) -> None:
    """INSERT/UPDATE/DELETE with no return value."""
    _execute(sql, params)


def execute_returning(sql: str, params: tuple | None = None) -> dict | None:
    """INSERT/UPDATE/DELETE ... RETURNING * — returns single row."""
    return _execute(sql, params, returning=True)


def execute_returning_all(sql: str, params: tuple | None = None) -> list[dict]:
    """INSERT/UPDATE/DELETE ... RETURNING * — returns all rows."""
    return _execute(sql, params, returning_all=True) or []
