"""Static constants and enumerations."""
from enum import Enum


class UserRole(str, Enum):
    USER = "user"
    DEALER = "dealer"
    ADMIN = "admin"


class PaymentMethod(str, Enum):
    FREE = "free"
    STARS = "stars"
    CRYPTO = "crypto"


class PlanType(str, Enum):
    DAYS_7 = "7_days"
    DAYS_30 = "30_days"
    DAILY = "daily"


class InvoiceStatus(str, Enum):
    ACTIVE = "active"
    PAID = "paid"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    ERROR = "error"


# ── Message templates ──────────────────────────────
WELCOME_MSG = (
    "👋 Привет, {name}!\n"
    "{online_line}"
    "Выберите действие в меню:"
)

SUB_ACTIVATED_MSG = (
    "✅ Подписка активирована!\n"
    "📅 Срок: {days} дн.\n\n"
    "🔗 **Ссылка на подписку** (обновляется автоматически):\n"
    "`{link}`\n\n"
    "📲 Отсканируйте QR код для быстрого добавления в клиент."
)

EXPIRY_WARNING_MSG = (
    "⚠️ **Уведомление об истечении подписки**\n"
    "📝 Клиент: {name}\n"
    "⏰ Осталось дней: {days_left}\n"
    "📅 Истекает: {expiry_date}\n"
    "Продлите подписку, чтобы не потерять доступ!"
)
