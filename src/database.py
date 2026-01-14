"""База данных SQLite."""
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from src.config import get_settings

# Путь к базе данных
DB_PATH = os.getenv("DB_PATH", "data/bot_data.db")


def _ensure_db_dir():
    """Убедиться, что директория для БД существует."""
    db_dir = Path(DB_PATH).parent
    db_dir.mkdir(parents=True, exist_ok=True)


@contextmanager
def get_db_connection():
    """Контекстный менеджер для работы с БД."""
    _ensure_db_dir()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_database():
    """Инициализация БД (создание таблиц)."""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Таблица пользователей бота
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bot_users (
                telegram_id INTEGER PRIMARY KEY,
                username TEXT,
                language TEXT DEFAULT 'ru',
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                trial_used BOOLEAN DEFAULT 0,
                referrer_id INTEGER,
                remnawave_user_uuid TEXT,
                auto_renewal BOOLEAN DEFAULT 0,
                last_renewal_notification TIMESTAMP,
                FOREIGN KEY (referrer_id) REFERENCES bot_users(telegram_id)
            )
        """)

        # Таблица промокодов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS promo_codes (
                code TEXT PRIMARY KEY,
                discount_percent INTEGER,
                bonus_days INTEGER,
                max_uses INTEGER,
                current_uses INTEGER DEFAULT 0,
                expires_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        """)

        # Таблица использования промокодов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS promo_code_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT,
                user_id INTEGER,
                used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (code) REFERENCES promo_codes(code),
                FOREIGN KEY (user_id) REFERENCES bot_users(telegram_id)
            )
        """)

        # Таблица рефералов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS referrals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER,
                referred_id INTEGER,
                bonus_days INTEGER DEFAULT 0,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (referrer_id) REFERENCES bot_users(telegram_id),
                FOREIGN KEY (referred_id) REFERENCES bot_users(telegram_id),
                UNIQUE(referrer_id, referred_id)
            )
        """)

        # Таблица платежей
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                stars INTEGER,
                amount_rub REAL,
                status TEXT DEFAULT 'pending',
                remnawave_user_uuid TEXT,
                invoice_payload TEXT,
                subscription_days INTEGER,
                promo_code TEXT,
                payment_method TEXT DEFAULT 'stars',
                yookassa_payment_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES bot_users(telegram_id)
            )
        """)


class BotUser:
    """Модель пользователя бота."""

    @staticmethod
    def get_or_create(telegram_id: int, username: Optional[str] = None) -> dict:
        """Получить или создать пользователя."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM bot_users WHERE telegram_id = ?",
                (telegram_id,)
            )
            row = cursor.fetchone()
            if row:
                return dict(row)

            cursor.execute(
                """INSERT INTO bot_users (telegram_id, username, language)
                   VALUES (?, ?, ?)""",
                (telegram_id, username, get_settings().DEFAULT_LOCALE)
            )
            cursor.execute(
                "SELECT * FROM bot_users WHERE telegram_id = ?",
                (telegram_id,)
            )
            return dict(cursor.fetchone())

    @staticmethod
    def update_language(telegram_id: int, language: str):
        """Обновить язык пользователя."""
        with get_db_connection() as conn:
            conn.execute(
                "UPDATE bot_users SET language = ? WHERE telegram_id = ?",
                (language, telegram_id)
            )

    @staticmethod
    def set_trial_used(telegram_id: int):
        """Отметить триал как использованный."""
        with get_db_connection() as conn:
            conn.execute(
                "UPDATE bot_users SET trial_used = 1 WHERE telegram_id = ?",
                (telegram_id,)
            )

    @staticmethod
    def set_referrer(telegram_id: int, referrer_id: int):
        """Установить реферера."""
        with get_db_connection() as conn:
            conn.execute(
                "UPDATE bot_users SET referrer_id = ? WHERE telegram_id = ?",
                (referrer_id, telegram_id)
            )

    @staticmethod
    def set_remnawave_uuid(telegram_id: int, uuid: str):
        """Сохранить UUID Remnawave."""
        with get_db_connection() as conn:
            conn.execute(
                "UPDATE bot_users SET remnawave_user_uuid = ? WHERE telegram_id = ?",
                (uuid, telegram_id)
            )

    @staticmethod
    def set_auto_renewal(telegram_id: int, enabled: bool):
        """Включить/выключить автопродление."""
        with get_db_connection() as conn:
            conn.execute(
                "UPDATE bot_users SET auto_renewal = ? WHERE telegram_id = ?",
                (1 if enabled else 0, telegram_id)
            )

    @staticmethod
    def get_auto_renewal(telegram_id: int) -> bool:
        """Получить статус автопродления."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT auto_renewal FROM bot_users WHERE telegram_id = ?",
                (telegram_id,)
            )
            row = cursor.fetchone()
            return bool(row[0]) if row else False

    @staticmethod
    def update_last_renewal_notification(telegram_id: int):
        """Обновить время последнего напоминания."""
        with get_db_connection() as conn:
            conn.execute(
                """UPDATE bot_users SET last_renewal_notification = ?
                   WHERE telegram_id = ?""",
                (datetime.now().isoformat(), telegram_id)
            )

    @staticmethod
    def get_users_with_auto_renewal() -> List[dict]:
        """Получить всех пользователей с автопродлением."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM bot_users WHERE auto_renewal = 1"
            )
            return [dict(row) for row in cursor.fetchall()]


class PromoCode:
    """Модель промокода."""

    @staticmethod
    def create(
        code: str,
        discount_percent: int = 0,
        bonus_days: int = 0,
        max_uses: int = 0,
        expires_at: Optional[str] = None
    ):
        """Создать промокод."""
        with get_db_connection() as conn:
            conn.execute(
                """INSERT INTO promo_codes
                   (code, discount_percent, bonus_days, max_uses, expires_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (code, discount_percent, bonus_days, max_uses, expires_at)
            )

    @staticmethod
    def get(code: str) -> Optional[dict]:
        """Получить промокод."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM promo_codes WHERE code = ?",
                (code,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def can_use(code: str, user_id: int) -> Tuple[bool, Optional[str]]:
        """Проверить, можно ли использовать промокод."""
        promo = PromoCode.get(code)
        if not promo:
            return False, "Промокод не найден"

        if not promo["is_active"]:
            return False, "Промокод неактивен"

        if promo["expires_at"]:
            expires = datetime.fromisoformat(promo["expires_at"])
            if datetime.now() > expires:
                return False, "Промокод истек"

        if promo["max_uses"] > 0 and promo["current_uses"] >= promo["max_uses"]:
            return False, "Промокод исчерпан"

        # Проверка, использовал ли уже пользователь
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM promo_code_usage WHERE code = ? AND user_id = ?",
                (code, user_id)
            )
            if cursor.fetchone():
                return False, "Вы уже использовали этот промокод"

        return True, None

    @staticmethod
    def use(code: str, user_id: int):
        """Использовать промокод."""
        with get_db_connection() as conn:
            # Увеличить счетчик использований
            conn.execute(
                """UPDATE promo_codes SET current_uses = current_uses + 1
                   WHERE code = ?""",
                (code,)
            )
            # Записать использование
            conn.execute(
                """INSERT INTO promo_code_usage (code, user_id)
                   VALUES (?, ?)""",
                (code, user_id)
            )


class Referral:
    """Модель реферальной программы."""

    @staticmethod
    def create(referrer_id: int, referred_id: int, bonus_days: int = 0):
        """Создать реферальную запись."""
        with get_db_connection() as conn:
            try:
                conn.execute(
                    """INSERT INTO referrals (referrer_id, referred_id, bonus_days)
                       VALUES (?, ?, ?)""",
                    (referrer_id, referred_id, bonus_days)
                )
            except sqlite3.IntegrityError:
                # Уже существует
                pass

    @staticmethod
    def get_referrals_count(referrer_id: int) -> int:
        """Получить количество рефералов."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM referrals WHERE referrer_id = ?",
                (referrer_id,)
            )
            return cursor.fetchone()[0]

    @staticmethod
    def get_bonus_days(referrer_id: int) -> int:
        """Получить общее количество бонусных дней."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT SUM(bonus_days) FROM referrals WHERE referrer_id = ?",
                (referrer_id,)
            )
            result = cursor.fetchone()[0]
            return result if result else 0

    @staticmethod
    def grant_bonus(referrer_id: int, referred_id: int, bonus_days: int):
        """Начислить бонус."""
        Referral.create(referrer_id, referred_id, bonus_days)

    @staticmethod
    def update_bonus_days(referrer_id: int, referred_id: int, bonus_days: int):
        """Обновить бонусные дни."""
        with get_db_connection() as conn:
            conn.execute(
                """UPDATE referrals SET bonus_days = ?
                   WHERE referrer_id = ? AND referred_id = ?""",
                (bonus_days, referrer_id, referred_id)
            )

    @staticmethod
    def has_bonus_been_granted(referrer_id: int, referred_id: int) -> bool:
        """Проверить, начислен ли уже бонус."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT bonus_days FROM referrals
                   WHERE referrer_id = ? AND referred_id = ?""",
                (referrer_id, referred_id)
            )
            row = cursor.fetchone()
            return row is not None and row[0] > 0


class Payment:
    """Модель платежа."""

    @staticmethod
    def create(
        user_id: int,
        stars: int,
        amount_rub: float,
        invoice_payload: str,
        subscription_days: int,
        promo_code: Optional[str] = None,
        remnawave_user_uuid: Optional[str] = None,
        payment_method: str = "stars",
        yookassa_payment_id: Optional[str] = None
    ) -> int:
        """Создать платеж."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO payments
                   (user_id, stars, amount_rub, invoice_payload, subscription_days,
                    promo_code, remnawave_user_uuid, payment_method, yookassa_payment_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (user_id, stars, amount_rub, invoice_payload, subscription_days,
                 promo_code, remnawave_user_uuid, payment_method, yookassa_payment_id)
            )
            return cursor.lastrowid

    @staticmethod
    def get_by_payload(invoice_payload: str) -> Optional[dict]:
        """Получить платеж по payload."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM payments WHERE invoice_payload = ?",
                (invoice_payload,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def get_by_yookassa_payment_id(yookassa_payment_id: str) -> Optional[dict]:
        """Получить платеж по YooKassa ID."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM payments WHERE yookassa_payment_id = ?",
                (yookassa_payment_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def update_yookassa_payment_id(payment_id: int, yookassa_payment_id: str):
        """Обновить YooKassa ID."""
        with get_db_connection() as conn:
            conn.execute(
                """UPDATE payments SET yookassa_payment_id = ?
                   WHERE id = ?""",
                (yookassa_payment_id, payment_id)
            )

    @staticmethod
    def update_status(
        payment_id: int,
        status: str,
        remnawave_uuid: Optional[str] = None
    ):
        """Обновить статус платежа."""
        with get_db_connection() as conn:
            completed_at = datetime.now().isoformat() if status == "completed" else None
            if remnawave_uuid:
                conn.execute(
                    """UPDATE payments SET status = ?, remnawave_user_uuid = ?,
                       completed_at = ? WHERE id = ?""",
                    (status, remnawave_uuid, completed_at, payment_id)
                )
            else:
                conn.execute(
                    "UPDATE payments SET status = ?, completed_at = ? WHERE id = ?",
                    (status, completed_at, payment_id)
                )

    @staticmethod
    def get(payment_id: int) -> Optional[dict]:
        """Получить платеж по ID."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM payments WHERE id = ?",
                (payment_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

