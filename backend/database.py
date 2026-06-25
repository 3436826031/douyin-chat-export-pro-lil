"""Database access layer for the web backend."""
import sqlite3
import json
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "chat.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_conversations(search=None, page=1, page_size=50):
    conn = get_db()
    offset = (page - 1) * page_size

    if search:
        rows = conn.execute(
            """SELECT * FROM conversations
               WHERE name LIKE ?
               ORDER BY last_message_time DESC
               LIMIT ? OFFSET ?""",
            (f"%{search}%", page_size, offset),
        ).fetchall()
        total = conn.execute(
            "SELECT COUNT(*) FROM conversations WHERE name LIKE ?",
            (f"%{search}%",),
        ).fetchone()[0]
    else:
        rows = conn.execute(
            """SELECT * FROM conversations
               ORDER BY last_message_time DESC
               LIMIT ? OFFSET ?""",
            (page_size, offset),
        ).fetchall()
        total = conn.execute("SELECT COUNT(*) FROM conversations").fetchone()[0]

    conn.close()
    return [dict(r) for r in rows], total


def get_conversation(conv_id):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM conversations WHERE conv_id = ?", (conv_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_messages(conv_id, page_size=100, before_seq=None, after_seq=None):
    conn = get_db()

    if before_seq:
        # 加载更早的消息（向上滚动时调用）
        rows = conn.execute(
            """SELECT * FROM messages
               WHERE conv_id = ? AND seq < ?
               ORDER BY seq DESC
               LIMIT ?""",
            (conv_id, before_seq, page_size),
        ).fetchall()
        rows = list(reversed(rows))
    elif after_seq is not None:
        # 从指定 seq 开始向后加载（跳到开头时调用，after_seq=0 即从头）
        rows = conn.execute(
            """SELECT * FROM messages
               WHERE conv_id = ? AND seq > ?
               ORDER BY seq ASC
               LIMIT ?""",
            (conv_id, after_seq, page_size),
        ).fetchall()
    else:
        # 初始加载：最新的100条
        rows = conn.execute(
            """SELECT * FROM messages
               WHERE conv_id = ?
               ORDER BY seq DESC
               LIMIT ?""",
            (conv_id, page_size),
        ).fetchall()
        rows = list(reversed(rows))

    total = conn.execute(
        "SELECT COUNT(*) FROM messages WHERE conv_id = ?", (conv_id,)
    ).fetchone()[0]

    conn.close()
    return [dict(r) for r in rows], total



def get_senders(conv_id):
    """获取会话中的所有发送者 UID 及消息数量。"""
    conn = get_db()
    rows = conn.execute(
        """SELECT sender_uid, COUNT(*) as msg_count
           FROM messages WHERE conv_id = ?
           GROUP BY sender_uid ORDER BY msg_count DESC""",
        (conv_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def search_messages(query, page=1, page_size=50):
    conn = get_db()
    offset = (page - 1) * page_size

    rows = conn.execute(
        """SELECT m.*, c.name as conv_name,
                  COALESCE(u.nickname, m.sender_name, '') as sender_display_name
           FROM messages m
           JOIN conversations c ON m.conv_id = c.conv_id
           LEFT JOIN users u ON m.sender_uid = u.uid
           WHERE m.content LIKE ?
           ORDER BY m.seq DESC
           LIMIT ? OFFSET ?""",
        (f"%{query}%", page_size, offset),
    ).fetchall()

    total = conn.execute(
        "SELECT COUNT(*) FROM messages WHERE content LIKE ?",
        (f"%{query}%",),
    ).fetchone()[0]

    conn.close()
    return [dict(r) for r in rows], total


def get_message(msg_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM messages WHERE msg_id = ?", (msg_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_user(uid):
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE uid = ?", (uid,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_users():
    conn = get_db()
    rows = conn.execute("SELECT * FROM users").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_stats():
    conn = get_db()
    stats = {
        "conversations": conn.execute("SELECT COUNT(*) FROM conversations").fetchone()[0],
        "messages": conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0],
        "users": conn.execute("SELECT COUNT(*) FROM users").fetchone()[0],
    }
    conn.close()
    return stats


def delete_conversation_messages(conv_id):
    """Delete all messages for a conversation (keep the conversation row)."""
    conn = get_db()
    cur = conn.execute("DELETE FROM messages WHERE conv_id = ?", (conv_id,))
    deleted = cur.rowcount
    conn.execute(
        "UPDATE conversations SET message_count = 0, last_message_time = 0 WHERE conv_id = ?",
        (conv_id,),
    )
    conn.commit()
    conn.close()
    return deleted


def delete_conversation(conv_id):
    """Delete a conversation and all its messages."""
    conn = get_db()
    msg_cur = conn.execute("DELETE FROM messages WHERE conv_id = ?", (conv_id,))
    msg_deleted = msg_cur.rowcount
    conv_cur = conn.execute("DELETE FROM conversations WHERE conv_id = ?", (conv_id,))
    conv_deleted = conv_cur.rowcount
    conn.commit()
    conn.close()
    return {"conversation_deleted": conv_deleted, "messages_deleted": msg_deleted}


def get_message_dates(conv_id):
    """获取会话中所有有消息的日期列表"""
    conn = get_db()
    rows = conn.execute(
        """SELECT DISTINCT DATE(timestamp, 'unixepoch', 'localtime') as date,
                  COUNT(*) as count
           FROM messages
           WHERE conv_id = ? AND timestamp > 0
           GROUP BY date
           ORDER BY date DESC""",
        (conv_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_messages_by_date(conv_id, date, page=1, page_size=100):
    """获取指定日期的消息"""
    conn = get_db()
    offset = (page - 1) * page_size

    rows = conn.execute(
        """SELECT * FROM messages
           WHERE conv_id = ?
             AND DATE(timestamp, 'unixepoch', 'localtime') = ?
           ORDER BY seq ASC
           LIMIT ? OFFSET ?""",
        (conv_id, date, page_size, offset),
    ).fetchall()

    total = conn.execute(
        """SELECT COUNT(*) FROM messages
           WHERE conv_id = ?
             AND DATE(timestamp, 'unixepoch', 'localtime') = ?""",
        (conv_id, date),
    ).fetchone()[0]

    conn.close()
    return [dict(r) for r in rows], total


def get_message_stats_by_period(conv_id, period='day'):
    """按时间段统计消息数量
    period: 'day', 'month', 'year'
    """
    conn = get_db()

    if period == 'day':
        group_expr = "DATE(timestamp, 'unixepoch', 'localtime')"
        format_expr = "DATE(timestamp, 'unixepoch', 'localtime')"
    elif period == 'month':
        group_expr = "strftime('%Y-%m', timestamp, 'unixepoch', 'localtime')"
        format_expr = "strftime('%Y-%m', timestamp, 'unixepoch', 'localtime')"
    else:  # year
        group_expr = "strftime('%Y', timestamp, 'unixepoch', 'localtime')"
        format_expr = "strftime('%Y', timestamp, 'unixepoch', 'localtime')"

    rows = conn.execute(
        f"""SELECT {format_expr} as period, COUNT(*) as count
            FROM messages
            WHERE conv_id = ? AND timestamp > 0
            GROUP BY {group_expr}
            ORDER BY period ASC""",
        (conv_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_sender_stats(conv_id):
    """统计每个发送者的消息数量"""
    conn = get_db()
    rows = conn.execute(
        """SELECT sender_uid,
                  COALESCE(u.nickname, m.sender_name, '未知') as nickname,
                  COUNT(*) as count
           FROM messages m
           LEFT JOIN users u ON m.sender_uid = u.uid
           WHERE m.conv_id = ?
           GROUP BY sender_uid
           ORDER BY count DESC""",
        (conv_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_media_stats(conv_id):
    """统计各类型消息数量"""
    conn = get_db()
    rows = conn.execute(
        """SELECT
              CASE
                WHEN msg_type = 0 THEN 'system'
                WHEN msg_type = 1 THEN 'text'
                WHEN msg_type = 2 THEN 'emoji'
                WHEN msg_type = 3 THEN
                  CASE WHEN media_local_path LIKE '%.mp4' THEN 'video' ELSE 'image' END
                WHEN msg_type = 4 THEN 'share'
                ELSE 'other'
              END as type,
              COUNT(*) as count
           FROM messages
           WHERE conv_id = ?
           GROUP BY type""",
        (conv_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_hourly_stats(conv_id):
    """按小时统计消息分布"""
    conn = get_db()
    rows = conn.execute(
        """SELECT CAST(strftime('%H', timestamp, 'unixepoch', 'localtime') AS INTEGER) as hour,
                  COUNT(*) as count
           FROM messages
           WHERE conv_id = ? AND timestamp > 0
           GROUP BY hour
           ORDER BY hour ASC""",
        (conv_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_media_messages(conv_id, msg_type=None, page=1, page_size=50):
    """获取媒体消息（图片、视频、语音等）"""
    conn = get_db()
    offset = (page - 1) * page_size

    # msg_type: 2=表情, 3=图片/视频, 4=分享
    if msg_type == 'image':
        condition = """(msg_type = 3 AND (media_local_path LIKE '%.jpg'
                       OR media_local_path LIKE '%.png'
                       OR media_local_path LIKE '%.webp'
                       OR media_local_path LIKE '%.gif'))
                       OR (msg_type = 2 AND media_url IS NOT NULL)"""
    elif msg_type == 'video':
        condition = "msg_type = 3 AND media_local_path LIKE '%.mp4'"
    elif msg_type == 'voice':
        condition = """(msg_type = 0 AND content LIKE '%resource_url%')
                       OR (msg_type = 1 AND content LIKE '%resource_url%')"""
    elif msg_type == 'share':
        condition = "msg_type = 4"
    else:
        # 所有媒体类型
        condition = """msg_type IN (2, 3, 4)
                       OR (msg_type = 0 AND content LIKE '%resource_url%')
                       OR (msg_type = 1 AND content LIKE '%resource_url%')"""

    rows = conn.execute(
        f"""SELECT * FROM messages
            WHERE conv_id = ? AND ({condition})
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?""",
        (conv_id, page_size, offset),
    ).fetchall()

    total = conn.execute(
        f"""SELECT COUNT(*) FROM messages
            WHERE conv_id = ? AND ({condition})""",
        (conv_id,),
    ).fetchone()[0]

    conn.close()
    return [dict(r) for r in rows], total
