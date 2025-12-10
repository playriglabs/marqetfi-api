from pydantic_settings import BaseSettings
from functools import lru_cache
from ostium_python_sdk import OstiumSDK, NetworkConfig

class Settings(BaseSettings):
    # API Settings
    port: int = 8000
    environment: str = "development"
    
    # Ostium Settings
    private_key: str
    rpc_url: str
    network: str = "testnet"
    ostium_verbose: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    def get_ostium_network_config(self):
        """Get Ostium network config"""
        if self.network.lower() == "testnet":
            return NetworkConfig.testnet()
        return NetworkConfig.mainnet()
    
    def create_ostium_sdk(self):
        """Create Ostium SDK instance"""
        config = self.get_ostium_network_config()
        return OstiumSDK(
            config,
            self.private_key,
            self.rpc_url,
            verbose=self.ostium_verbose
        )

@lru_cache()
def get_settings():
    return Settings()