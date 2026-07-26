import httpx
import json
import webbrowser
from pathlib import Path
from mymommy.config.settings import settings

class LicenseService:
    def __init__(self):
        self.license_path = settings.dot_path / "license.json"

    def get_local_license(self) -> dict | None:
        if self.license_path.exists():
            return json.loads(self.license_path.read_text())
        return None

    def save_license(self, license_data: dict):
        self.license_path.write_text(json.dumps(license_data))

    async def initiate_payment(self, user_id: str):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.BACKEND_URL}/license/create-payment",
                json={"user_id": user_id}
            )
            return response.json()

    async def check_payment_status(self, payment_id: str):
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.BACKEND_URL}/license/status/{payment_id}")
            return response.json()

    def is_pro(self) -> bool:
        license_data = self.get_local_license()
        if license_data and license_data.get("plan") == "PRO":
            return True
        return False
