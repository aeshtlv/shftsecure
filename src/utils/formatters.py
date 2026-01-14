"""Форматирование данных для отображения."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from aiogram.utils.i18n import gettext as _


def format_bytes(value: int) -> str:
    """Форматировать байты (B, KB, MB, GB, TB)."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if value < 1024.0:
            return f"{value:.2f} {unit}"
        value /= 1024.0
    return f"{value:.2f} PB"


def format_datetime(dt_str: str) -> str:
    """Форматировать дату/время."""
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return dt_str


def format_uptime(seconds: int) -> str:
    """Форматировать время работы."""
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    return f"{days}d {hours}h {minutes}m"


def escape_markdown(text: str) -> str:
    """Экранировать Markdown символы."""
    if not text:
        return ""
    return (
        str(text)
        .replace("_", "\\_")
        .replace("*", "\\*")
        .replace("[", "\\[")
        .replace("]", "\\]")
        .replace("(", "\\(")
        .replace(")", "\\)")
        .replace("~", "\\~")
        .replace("`", "\\`")
        .replace(">", "\\>")
        .replace("#", "\\#")
        .replace("+", "\\+")
        .replace("-", "\\-")
        .replace("=", "\\=")
        .replace("|", "\\|")
        .replace("{", "\\{")
        .replace("}", "\\}")
        .replace(".", "\\.")
        .replace("!", "\\!")
    )


def build_user_summary(user: Dict[str, Any], t) -> str:
    """Построить сводку пользователя."""
    username = escape_markdown(user.get("username", "N/A"))
    uuid = escape_markdown(user.get("uuid", "N/A"))
    status = escape_markdown(user.get("status", "N/A"))
    expire_at = format_datetime(user.get("expire_at", ""))
    telegram_id = user.get("telegram_id", "N/A")

    return f"""*{t('user.summary.title')}*

*{t('user.summary.username')}:* `{username}`
*{t('user.summary.uuid')}:* `{uuid}`
*{t('user.summary.status')}:* `{status}`
*{t('user.summary.telegram_id')}:* `{telegram_id}`
*{t('user.summary.expire_at')}:* `{expire_at}`"""


def build_node_summary(node: Dict[str, Any], t) -> str:
    """Построить сводку ноды."""
    name = escape_markdown(node.get("name", "N/A"))
    uuid = escape_markdown(node.get("uuid", "N/A"))
    address = escape_markdown(node.get("address", "N/A"))
    status = escape_markdown(node.get("status", "N/A"))

    return f"""*{t('node.summary.title')}*

*{t('node.summary.name')}:* `{name}`
*{t('node.summary.uuid')}:* `{uuid}`
*{t('node.summary.address')}:* `{address}`
*{t('node.summary.status')}:* `{status}`"""


def build_host_summary(host: Dict[str, Any], t) -> str:
    """Построить сводку хоста."""
    remark = escape_markdown(host.get("remark", "N/A"))
    uuid = escape_markdown(host.get("uuid", "N/A"))
    address = escape_markdown(host.get("address", "N/A"))
    port = host.get("port", "N/A")
    status = escape_markdown(host.get("status", "N/A"))

    return f"""*{t('host.summary.title')}*

*{t('host.summary.remark')}:* `{remark}`
*{t('host.summary.uuid')}:* `{uuid}`
*{t('host.summary.address')}:* `{address}:{port}`
*{t('host.summary.status')}:* `{status}`"""


def build_subscription_summary(sub: Dict[str, Any], t) -> str:
    """Построить сводку подписки."""
    short_uuid = escape_markdown(sub.get("short_uuid", "N/A"))
    expire_at = format_datetime(sub.get("expire_at", ""))

    return f"""*{t('subscription.summary.title')}*

*{t('subscription.summary.short_uuid')}:* `{short_uuid}`
*{t('subscription.summary.expire_at')}:* `{expire_at}`"""


def build_tokens_list(tokens: List[Dict], t) -> str:
    """Построить список токенов."""
    if not tokens:
        return t("tokens.empty")

    lines = [t("tokens.list_title")]
    for token in tokens:
        name = escape_markdown(token.get("name", "N/A"))
        uuid = escape_markdown(token.get("uuid", "N/A"))
        lines.append(f"• `{name}` - `{uuid}`")

    return "\n".join(lines)


def build_templates_list(templates: List[Dict], t) -> str:
    """Построить список шаблонов."""
    if not templates:
        return t("templates.empty")

    lines = [t("templates.list_title")]
    for template in templates:
        name = escape_markdown(template.get("name", "N/A"))
        uuid = escape_markdown(template.get("uuid", "N/A"))
        template_type = escape_markdown(template.get("type", "N/A"))
        lines.append(f"• `{name}` ({template_type}) - `{uuid}`")

    return "\n".join(lines)


def build_snippets_list(snippets: List[Dict], t) -> str:
    """Построить список сниппетов."""
    if not snippets:
        return t("snippets.empty")

    lines = [t("snippets.list_title")]
    for snippet in snippets:
        name = escape_markdown(snippet.get("name", "N/A"))
        lines.append(f"• `{name}`")

    return "\n".join(lines)


def build_config_profiles_list(profiles: List[Dict], t) -> str:
    """Построить список профилей конфигурации."""
    if not profiles:
        return t("configs.empty")

    lines = [t("configs.list_title")]
    for profile in profiles:
        name = escape_markdown(profile.get("name", "N/A"))
        uuid = escape_markdown(profile.get("uuid", "N/A"))
        lines.append(f"• `{name}` - `{uuid}`")

    return "\n".join(lines)


def build_billing_history(records: List[Dict], t) -> str:
    """Построить историю биллинга."""
    if not records:
        return t("billing.history.empty")

    lines = [t("billing.history.title")]
    for record in records:
        provider_name = escape_markdown(record.get("provider_name", "N/A"))
        amount = record.get("amount", 0)
        billed_at = format_datetime(record.get("billed_at", ""))
        lines.append(f"• {provider_name}: {amount} ₽ ({billed_at})")

    return "\n".join(lines)


def build_infra_providers(providers: List[Dict], t) -> str:
    """Построить список провайдеров."""
    if not providers:
        return t("providers.empty")

    lines = [t("providers.list_title")]
    for provider in providers:
        name = escape_markdown(provider.get("name", "N/A"))
        uuid = escape_markdown(provider.get("uuid", "N/A"))
        lines.append(f"• `{name}` - `{uuid}`")

    return "\n".join(lines)


def build_billing_nodes(data: List[Dict], t) -> str:
    """Построить биллинг нод."""
    if not data:
        return t("billing.nodes.empty")

    lines = [t("billing.nodes.title")]
    for item in data:
        node_name = escape_markdown(item.get("node_name", "N/A"))
        provider_name = escape_markdown(item.get("provider_name", "N/A"))
        next_billing_at = format_datetime(item.get("next_billing_at", ""))
        lines.append(f"• {node_name} ({provider_name}) - {next_billing_at}")

    return "\n".join(lines)

