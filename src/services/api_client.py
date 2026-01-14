"""Клиент Remnawave API."""
import asyncio
from typing import Any, Dict, List, Optional

import httpx
from src.config import get_settings


class ApiClientError(Exception):
    """Общая ошибка API."""

    pass


class NotFoundError(ApiClientError):
    """404 ошибка."""

    pass


class UnauthorizedError(ApiClientError):
    """401/403 ошибка."""

    pass


class RemnawaveApiClient:
    """Клиент Remnawave API."""

    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.API_BASE_URL.rstrip("/")
        self.token = self.settings.API_TOKEN
        self.timeout = httpx.Timeout(30.0, connect=10.0)

    def _get_headers(self) -> Dict[str, str]:
        """Получить заголовки запроса."""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    async def _request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        retries: int = 3,
    ) -> Any:
        """Выполнить HTTP запрос с retry."""
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()

        for attempt in range(retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.request(
                        method, url, headers=headers, json=json_data, params=params
                    )

                    if response.status_code == 404:
                        raise NotFoundError(f"Not found: {endpoint}")
                    if response.status_code in (401, 403):
                        raise UnauthorizedError(f"Unauthorized: {endpoint}")

                    response.raise_for_status()
                    data = response.json()

                    # Remnawave может возвращать {"response": {...}}
                    if isinstance(data, dict) and "response" in data:
                        return data["response"]
                    return data

            except httpx.TimeoutException:
                if attempt == retries - 1:
                    raise ApiClientError(f"Timeout: {endpoint}")
                await asyncio.sleep(2 ** attempt)

            except httpx.HTTPStatusError as e:
                if e.response.status_code in (401, 403, 404):
                    raise
                if attempt == retries - 1:
                    raise ApiClientError(f"HTTP error: {e.response.status_code}")
                await asyncio.sleep(2 ** attempt)

            except Exception as e:
                if attempt == retries - 1:
                    raise ApiClientError(f"Request failed: {str(e)}")
                await asyncio.sleep(2 ** attempt)

    # Методы для работы с пользователями
    async def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Получить пользователя по username."""
        try:
            return await self._request("GET", f"/api/users?username={username}")
        except NotFoundError:
            return None

    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[Dict]:
        """Получить пользователя по telegram_id."""
        try:
            return await self._request("GET", f"/api/users?telegram_id={telegram_id}")
        except NotFoundError:
            return None

    async def get_user_by_uuid(self, user_uuid: str) -> Dict:
        """Получить пользователя по UUID."""
        return await self._request("GET", f"/api/users/{user_uuid}")

    async def get_users(self, start: int = 0, size: int = 100) -> Dict:
        """Получить список пользователей."""
        return await self._request("GET", f"/api/users?start={start}&size={size}")

    async def create_user(
        self,
        username: str,
        expire_at: str,
        telegram_id: Optional[int] = None,
        external_squad_uuid: Optional[str] = None,
        internal_squad_uuids: Optional[List[str]] = None,
    ) -> Dict:
        """Создать пользователя."""
        data = {
            "username": username,
            "expire_at": expire_at,
        }
        if telegram_id:
            data["telegram_id"] = telegram_id
        if external_squad_uuid:
            data["external_squad_uuid"] = external_squad_uuid
        if internal_squad_uuids:
            data["internal_squad_uuids"] = internal_squad_uuids

        return await self._request("POST", "/api/users", json_data=data)

    async def update_user(self, user_uuid: str, **fields) -> Dict:
        """Обновить пользователя."""
        return await self._request("PATCH", f"/api/users/{user_uuid}", json_data=fields)

    async def disable_user(self, user_uuid: str) -> Dict:
        """Выключить пользователя."""
        return await self._request("POST", f"/api/users/{user_uuid}/actions/disable")

    async def enable_user(self, user_uuid: str) -> Dict:
        """Включить пользователя."""
        return await self._request("POST", f"/api/users/{user_uuid}/actions/enable")

    async def reset_user_traffic(self, user_uuid: str) -> Dict:
        """Сбросить трафик пользователя."""
        return await self._request(
            "POST", f"/api/users/{user_uuid}/actions/reset-traffic"
        )

    async def revoke_user_subscription(self, user_uuid: str, short_uuid: str) -> Dict:
        """Отозвать подписку пользователя."""
        return await self._request(
            "POST",
            f"/api/users/{user_uuid}/actions/revoke",
            json_data={"short_uuid": short_uuid},
        )

    # Методы для работы с нодами
    async def get_nodes(self) -> List[Dict]:
        """Получить список нод."""
        return await self._request("GET", "/api/nodes")

    async def get_node(self, node_uuid: str) -> Dict:
        """Получить ноду по UUID."""
        return await self._request("GET", f"/api/nodes/{node_uuid}")

    async def create_node(
        self,
        name: str,
        address: str,
        config_profile_uuid: str,
        **kwargs
    ) -> Dict:
        """Создать ноду."""
        data = {
            "name": name,
            "address": address,
            "config_profile_uuid": config_profile_uuid,
            **kwargs
        }
        return await self._request("POST", "/api/nodes", json_data=data)

    async def update_node(self, node_uuid: str, **fields) -> Dict:
        """Обновить ноду."""
        return await self._request("PATCH", f"/api/nodes/{node_uuid}", json_data=fields)

    async def delete_node(self, node_uuid: str) -> Dict:
        """Удалить ноду."""
        return await self._request("DELETE", f"/api/nodes/{node_uuid}")

    async def enable_node(self, node_uuid: str) -> Dict:
        """Включить ноду."""
        return await self._request("POST", f"/api/nodes/{node_uuid}/actions/enable")

    async def disable_node(self, node_uuid: str) -> Dict:
        """Выключить ноду."""
        return await self._request("POST", f"/api/nodes/{node_uuid}/actions/disable")

    async def restart_node(self, node_uuid: str) -> Dict:
        """Перезапустить ноду."""
        return await self._request("POST", f"/api/nodes/{node_uuid}/actions/restart")

    async def reset_node_traffic(self, node_uuid: str) -> Dict:
        """Сбросить трафик ноды."""
        return await self._request(
            "POST", f"/api/nodes/{node_uuid}/actions/reset-traffic"
        )

    async def get_nodes_realtime_usage(self) -> Dict:
        """Получить статистику использования нод в реальном времени."""
        return await self._request("GET", "/api/nodes/realtime-usage")

    async def get_nodes_usage_range(
        self, start: str, end: str, top_nodes_limit: int = 10
    ) -> Dict:
        """Получить статистику использования нод за период."""
        return await self._request(
            "GET",
            f"/api/nodes/usage-range?start={start}&end={end}&top_nodes_limit={top_nodes_limit}",
        )

    # Методы для работы с хостами
    async def get_hosts(self) -> List[Dict]:
        """Получить список хостов."""
        return await self._request("GET", "/api/hosts")

    async def get_host(self, host_uuid: str) -> Dict:
        """Получить хост по UUID."""
        return await self._request("GET", f"/api/hosts/{host_uuid}")

    async def create_host(
        self, remark: str, address: str, port: int, **kwargs
    ) -> Dict:
        """Создать хост."""
        data = {"remark": remark, "address": address, "port": port, **kwargs}
        return await self._request("POST", "/api/hosts", json_data=data)

    async def update_host(self, host_uuid: str, **fields) -> Dict:
        """Обновить хост."""
        return await self._request("PATCH", f"/api/hosts/{host_uuid}", json_data=fields)

    async def enable_hosts(self, host_uuids: List[str]) -> Dict:
        """Включить хосты."""
        return await self._request(
            "POST", "/api/hosts/actions/enable", json_data={"uuids": host_uuids}
        )

    async def disable_hosts(self, host_uuids: List[str]) -> Dict:
        """Выключить хосты."""
        return await self._request(
            "POST", "/api/hosts/actions/disable", json_data={"uuids": host_uuids}
        )

    # Методы для работы с ресурсами
    async def get_tokens(self) -> List[Dict]:
        """Получить список токенов."""
        return await self._request("GET", "/api/tokens")

    async def create_token(self, token_name: str) -> Dict:
        """Создать токен."""
        return await self._request(
            "POST", "/api/tokens", json_data={"name": token_name}
        )

    async def delete_token(self, token_uuid: str) -> Dict:
        """Удалить токен."""
        return await self._request("DELETE", f"/api/tokens/{token_uuid}")

    async def get_templates(self) -> List[Dict]:
        """Получить список шаблонов."""
        return await self._request("GET", "/api/templates")

    async def get_template(self, template_uuid: str) -> Dict:
        """Получить шаблон по UUID."""
        return await self._request("GET", f"/api/templates/{template_uuid}")

    async def create_template(self, name: str, template_type: str) -> Dict:
        """Создать шаблон."""
        return await self._request(
            "POST",
            "/api/templates",
            json_data={"name": name, "type": template_type},
        )

    async def update_template(
        self, template_uuid: str, name: str, template_json: Dict
    ) -> Dict:
        """Обновить шаблон."""
        return await self._request(
            "PATCH",
            f"/api/templates/{template_uuid}",
            json_data={"name": name, "template": template_json},
        )

    async def delete_template(self, template_uuid: str) -> Dict:
        """Удалить шаблон."""
        return await self._request("DELETE", f"/api/templates/{template_uuid}")

    async def reorder_templates(self, uuids_in_order: List[str]) -> Dict:
        """Изменить порядок шаблонов."""
        return await self._request(
            "POST",
            "/api/templates/reorder",
            json_data={"uuids_in_order": uuids_in_order},
        )

    async def get_snippets(self) -> List[Dict]:
        """Получить список сниппетов."""
        return await self._request("GET", "/api/snippets")

    async def create_snippet(self, name: str, snippet: str) -> Dict:
        """Создать сниппет."""
        return await self._request(
            "POST", "/api/snippets", json_data={"name": name, "snippet": snippet}
        )

    async def update_snippet(self, name: str, snippet: str) -> Dict:
        """Обновить сниппет."""
        return await self._request(
            "PATCH", f"/api/snippets/{name}", json_data={"snippet": snippet}
        )

    async def delete_snippet(self, name: str) -> Dict:
        """Удалить сниппет."""
        return await self._request("DELETE", f"/api/snippets/{name}")

    async def get_config_profiles(self) -> List[Dict]:
        """Получить список профилей конфигурации."""
        return await self._request("GET", "/api/config-profiles")

    async def get_config_profile_computed(self, profile_uuid: str) -> Dict:
        """Получить вычисленную конфигурацию профиля."""
        return await self._request(
            "GET", f"/api/config-profiles/{profile_uuid}/computed"
        )

    # Методы для биллинга
    async def get_infra_billing_history(self) -> List[Dict]:
        """Получить историю биллинга."""
        return await self._request("GET", "/api/infra/billing/history")

    async def get_infra_providers(self) -> List[Dict]:
        """Получить список провайдеров."""
        return await self._request("GET", "/api/infra/providers")

    async def get_infra_provider(self, provider_uuid: str) -> Dict:
        """Получить провайдера по UUID."""
        return await self._request("GET", f"/api/infra/providers/{provider_uuid}")

    async def create_infra_provider(
        self, name: str, favicon_link: str, login_url: str
    ) -> Dict:
        """Создать провайдера."""
        return await self._request(
            "POST",
            "/api/infra/providers",
            json_data={"name": name, "favicon_link": favicon_link, "login_url": login_url},
        )

    async def update_infra_provider(self, provider_uuid: str, **fields) -> Dict:
        """Обновить провайдера."""
        return await self._request(
            "PATCH", f"/api/infra/providers/{provider_uuid}", json_data=fields
        )

    async def delete_infra_provider(self, provider_uuid: str) -> Dict:
        """Удалить провайдера."""
        return await self._request("DELETE", f"/api/infra/providers/{provider_uuid}")

    async def create_infra_billing_record(
        self, provider_uuid: str, amount: float, billed_at: str
    ) -> Dict:
        """Создать запись биллинга."""
        return await self._request(
            "POST",
            "/api/infra/billing/history",
            json_data={
                "provider_uuid": provider_uuid,
                "amount": amount,
                "billed_at": billed_at,
            },
        )

    async def delete_infra_billing_record(self, record_uuid: str) -> Dict:
        """Удалить запись биллинга."""
        return await self._request(
            "DELETE", f"/api/infra/billing/history/{record_uuid}"
        )

    async def get_infra_billing_nodes(self) -> List[Dict]:
        """Получить биллинг нод."""
        return await self._request("GET", "/api/infra/billing/nodes")

    async def create_infra_billing_node(
        self, provider_uuid: str, node_uuid: str, next_billing_at: str
    ) -> Dict:
        """Создать биллинг ноду."""
        return await self._request(
            "POST",
            "/api/infra/billing/nodes",
            json_data={
                "provider_uuid": provider_uuid,
                "node_uuid": node_uuid,
                "next_billing_at": next_billing_at,
            },
        )

    async def update_infra_billing_nodes(
        self, uuids: List[str], next_billing_at: str
    ) -> Dict:
        """Обновить биллинг ноды."""
        return await self._request(
            "PATCH",
            "/api/infra/billing/nodes",
            json_data={"uuids": uuids, "next_billing_at": next_billing_at},
        )

    async def delete_infra_billing_node(self, record_uuid: str) -> Dict:
        """Удалить биллинг ноду."""
        return await self._request(
            "DELETE", f"/api/infra/billing/nodes/{record_uuid}"
        )

    # Массовые операции
    async def bulk_delete_users(self, uuids: List[str]) -> Dict:
        """Массовое удаление пользователей."""
        return await self._request(
            "POST", "/api/users/bulk/delete", json_data={"uuids": uuids}
        )

    async def bulk_revoke_subscriptions(self, uuids: List[str]) -> Dict:
        """Массовый отзыв подписок."""
        return await self._request(
            "POST", "/api/users/bulk/revoke", json_data={"uuids": uuids}
        )

    async def bulk_reset_traffic_users(self, uuids: List[str]) -> Dict:
        """Массовый сброс трафика пользователей."""
        return await self._request(
            "POST", "/api/users/bulk/reset-traffic", json_data={"uuids": uuids}
        )

    async def bulk_extend_users(self, uuids: List[str], days: int) -> Dict:
        """Массовое продление подписок."""
        return await self._request(
            "POST",
            "/api/users/bulk/extend",
            json_data={"uuids": uuids, "days": days},
        )

    async def bulk_extend_all_users(self, days: int) -> Dict:
        """Продление подписок всем пользователям."""
        return await self._request(
            "POST", "/api/users/bulk/extend-all", json_data={"days": days}
        )

    async def bulk_update_users_status(self, uuids: List[str], status: str) -> Dict:
        """Массовое изменение статуса пользователей."""
        return await self._request(
            "POST",
            "/api/users/bulk/update-status",
            json_data={"uuids": uuids, "status": status},
        )

    async def bulk_delete_users_by_status(self, status: str) -> Dict:
        """Удаление пользователей по статусу."""
        return await self._request(
            "POST", "/api/users/bulk/delete-by-status", json_data={"status": status}
        )

    async def bulk_reset_traffic_all_users(self) -> Dict:
        """Сброс трафика всем пользователям."""
        return await self._request("POST", "/api/users/bulk/reset-traffic-all")

    async def bulk_enable_hosts(self, uuids: List[str]) -> Dict:
        """Массовое включение хостов."""
        return await self._request(
            "POST", "/api/hosts/bulk/enable", json_data={"uuids": uuids}
        )

    async def bulk_disable_hosts(self, uuids: List[str]) -> Dict:
        """Массовое выключение хостов."""
        return await self._request(
            "POST", "/api/hosts/bulk/disable", json_data={"uuids": uuids}
        )

    async def bulk_delete_hosts(self, uuids: List[str]) -> Dict:
        """Массовое удаление хостов."""
        return await self._request(
            "POST", "/api/hosts/bulk/delete", json_data={"uuids": uuids}
        )

    async def bulk_nodes_profile_modification(
        self, node_uuids: List[str], profile_uuid: str, inbound_uuids: List[str]
    ) -> Dict:
        """Массовое изменение профиля нод."""
        return await self._request(
            "POST",
            "/api/nodes/bulk/profile-modification",
            json_data={
                "node_uuids": node_uuids,
                "profile_uuid": profile_uuid,
                "inbound_uuids": inbound_uuids,
            },
        )

    # Системные методы
    async def get_health(self) -> Dict:
        """Проверка здоровья системы."""
        return await self._request("GET", "/api/system/health")

    async def get_stats(self) -> Dict:
        """Получить общую статистику."""
        return await self._request("GET", "/api/system/stats")

    async def get_bandwidth_stats(self) -> Dict:
        """Получить статистику трафика."""
        return await self._request("GET", "/api/system/bandwidth")

    async def get_subscription_info(self, short_uuid: str) -> Dict:
        """Получить информацию о подписке."""
        return await self._request("GET", f"/api/sub/{short_uuid}/info")

    async def encrypt_happ_crypto_link(self, link_to_encrypt: str) -> Dict:
        """Зашифровать ссылку Happ Crypto."""
        return await self._request(
            "POST",
            "/api/system/encrypt-happ-crypto-link",
            json_data={"link_to_encrypt": link_to_encrypt},
        )

    # Статистика пользователей
    async def get_user_subscription_request_history(self, user_uuid: str) -> List[Dict]:
        """Получить историю запросов подписок пользователя."""
        return await self._request(
            "GET", f"/api/users/{user_uuid}/subscription-request-history"
        )

    async def get_user_traffic_stats(
        self, user_uuid: str, start: str, end: str, top_nodes_limit: int = 10
    ) -> Dict:
        """Получить статистику трафика пользователя."""
        return await self._request(
            "GET",
            f"/api/users/{user_uuid}/traffic-stats?start={start}&end={end}&top_nodes_limit={top_nodes_limit}",
        )

    async def get_user_traffic_stats_legacy(
        self, user_uuid: str, start: str, end: str
    ) -> Dict:
        """Получить статистику трафика пользователя (legacy)."""
        return await self._request(
            "GET",
            f"/api/users/{user_uuid}/traffic-stats-legacy?start={start}&end={end}",
        )

    async def get_user_accessible_nodes(self, user_uuid: str) -> List[Dict]:
        """Получить доступные ноды пользователя."""
        return await self._request("GET", f"/api/users/{user_uuid}/accessible-nodes")

    async def get_node_users_usage(
        self, node_uuid: str, start: str, end: str, top_users_limit: int = 10
    ) -> Dict:
        """Получить использование ноды пользователями."""
        return await self._request(
            "GET",
            f"/api/nodes/{node_uuid}/users-usage?start={start}&end={end}&top_users_limit={top_users_limit}",
        )

    # HWID
    async def get_hwid_devices_stats(self) -> Dict:
        """Получить статистику HWID устройств."""
        return await self._request("GET", "/api/hwid/devices/stats")

    async def get_all_hwid_devices(self, start: int = 0, size: int = 100) -> Dict:
        """Получить все HWID устройства."""
        return await self._request("GET", f"/api/hwid/devices?start={start}&size={size}")

    async def get_user_hwid_devices(self, user_uuid: str) -> List[Dict]:
        """Получить HWID устройства пользователя."""
        return await self._request("GET", f"/api/users/{user_uuid}/hwid-devices")

    async def create_user_hwid_device(self, user_uuid: str, hwid: str) -> Dict:
        """Создать HWID устройство для пользователя."""
        return await self._request(
            "POST",
            f"/api/users/{user_uuid}/hwid-devices",
            json_data={"hwid": hwid},
        )

    async def delete_user_hwid_device(self, user_uuid: str, hwid: str) -> Dict:
        """Удалить HWID устройство пользователя."""
        return await self._request(
            "DELETE", f"/api/users/{user_uuid}/hwid-devices/{hwid}"
        )

    async def delete_all_user_hwid_devices(self, user_uuid: str) -> Dict:
        """Удалить все HWID устройства пользователя."""
        return await self._request(
            "DELETE", f"/api/users/{user_uuid}/hwid-devices"
        )

    async def get_top_users_by_hwid_devices(self, limit: int = 10) -> List[Dict]:
        """Получить топ пользователей по количеству HWID устройств."""
        return await self._request(
            "GET", f"/api/hwid/devices/top-users?limit={limit}"
        )

    # Сквады
    async def get_internal_squads(self) -> List[Dict]:
        """Получить список внутренних сквадов."""
        return await self._request("GET", "/api/squads/internal")

    async def get_external_squads(self) -> List[Dict]:
        """Получить список внешних сквадов."""
        return await self._request("GET", "/api/squads/external")

