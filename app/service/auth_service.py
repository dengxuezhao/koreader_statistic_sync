import hashlib
from typing import Optional, List
from app.config import get_settings 
from app.entity.user import User, Device, UserCreate, DeviceCreate, UserSessionInfo # Added UserSessionInfo
# Potentially add UserRepository, DeviceRepository for DB interactions if not handled directly or via another service
from app.utils.security import verify_password, get_password_hash # Assuming these exist


class AuthService:
    def __init__(self):
        # In a real app, you'd inject repositories or a DB session here
        self.settings = get_settings()
        # 内存存储设备列表，仅用于演示
        self._devices = {}

    async def authenticate_admin(self, username: str, password: str) -> Optional[UserSessionInfo]:
        """
        Authenticates the admin user based on environment variable credentials.
        Returns a User-like object if authentication is successful, otherwise None.
        """
        # Directly use environment variables for admin authentication as per README
        admin_username = self.settings.AUTH_USERNAME
        admin_password = self.settings.AUTH_PASSWORD

        if username == admin_username and password == admin_password:
            # Return a UserSessionInfo object with admin details
            return UserSessionInfo(id="admin_user_001", username=username, is_superuser=True)
        return None

    async def check_device_password(self, device_name: str, password: str, plain: bool = False) -> bool:
        """
        Checks if the provided password is correct for the given device.
        If plain is True, it compares the password directly.
        Otherwise, it hashes the provided password and compares it with the stored hash.
        (This method was referenced in the webdav router)
        """
        if device_name in self._devices:
            stored_hash = self._devices[device_name]['hashed_password']
            if plain:
                # 如果是plain模式，需要对传入的密码进行MD5哈希后比较
                m = hashlib.md5()
                m.update(password.encode('utf-8'))
                provided_hash = m.hexdigest()
                return provided_hash == stored_hash
            else:
                # 否则直接比较密码
                return password == self._devices[device_name]['password']
        return False

    async def get_device_hashed_password(self, device_name: str) -> Optional[str]:
        # Placeholder: this should query your database for the device's hashed password
        # Example:
        # device = await DeviceModel.query.where(DeviceModel.name == device_name).gino.first()
        # return device.hashed_password if device else None
        print(f"[AuthService.get_device_hashed_password] Retrieving for {device_name} - Needs DB Impl.")
        # This is a conceptual placeholder for where MD5 hashes would be stored/retrieved
        # In a real scenario, these are in the DB.
        # This matches the dummy_device_db in check_device_password
        # If using DeviceModel from entity.user.py, it stores `hashed_password`.
        # The WebDAV setup implies this stored hash is MD5.
        if device_name == "koreader_device1" and False: # disabled example
            return "md5_hash_of_password123" # Example MD5 hash
        return None

    # Methods for device management (to be called by auth.py API endpoints)
    async def create_device(self, device_create: DeviceCreate, owner_username: str) -> Device:
        """
        Creates a new device and associates it with an owner (admin).
        The device password should be stored as an MD5 hash for KOReader compatibility.
        """
        # 对密码进行MD5哈希
        m = hashlib.md5()
        m.update(device_create.password.encode('utf-8'))
        hashed_password = m.hexdigest()
        
        # 存储设备信息
        device_name = device_create.name
        self._devices[device_name] = {
            'name': device_name,
            'hashed_password': hashed_password,
            'password': device_create.password,  # 存储原始密码用于返回给用户
            'owner': owner_username,
            'created_at': None  # 在实际应用中，这里应该是一个时间戳
        }
        
        # 返回设备实体
        return Device(name=device_name, hashed_password=hashed_password)

    async def get_devices_for_user(self, username: str) -> list[Device]:
        """
        Retrieves a list of devices associated with the given username.
        """
        devices = []
        for device_name, device_info in self._devices.items():
            if device_info['owner'] == username:
                devices.append(Device(
                    name=device_name,
                    hashed_password=device_info['hashed_password']
                ))
        return devices

    async def delete_device(self, device_name: str, owner_username: str) -> bool:
        """
        Deletes a device if it belongs to the owner_username.
        Returns True if deletion was successful, False otherwise.
        """
        if device_name in self._devices and self._devices[device_name]['owner'] == owner_username:
            del self._devices[device_name]
            return True
        return False
        
    # Placeholder for other methods if needed by auth.py (e.g., get_current_active_user for API tokens)
    # async def get_current_active_user(...) -> ...:
    #    pass

# Pydantic models used by AuthService or returned by it, if not defined in entity.user.py
# It's better to keep these in entity/user.py and import them.
# Ensure UserSchema here matches what CurrentUserResponse in auth.py expects.
# from pydantic import BaseModel # already imported if UserSchema is defined here