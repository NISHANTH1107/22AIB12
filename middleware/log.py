import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("logging-middleware")

class LoggingMiddleware:
    def __init__(self, auth_token):
        self.auth_token = auth_token
        self.log_api_url = "http://20.244.56.144/evaluation-service/logs"
    
    def log(self, stack: str, level: str, package: str, message: str):
        """Send log to evaluation server"""
        allowed_stacks = ["backend", "frontend"]
        allowed_levels = ["debug", "info", "warn", "error", "fatal"]
        allowed_backend_packages = ["cache", "controller", "cron_job", "db", "domain", "handler", "repository", "route", "service"]
        allowed_common_packages = ["auth", "config", "middleware", "utils"]
        
        
        if stack not in allowed_stacks:
            logger.warning(f"Invalid stack: {stack}")
            return False
        
        if level not in allowed_levels:
            logger.warning(f"Invalid level: {level}")
            return False
        
        valid_packages = allowed_backend_packages + allowed_common_packages
        if stack == "backend" and package not in valid_packages:
            logger.warning(f"Invalid package for backend: {package}")
            return False
        
        try:
            payload = {
                "stack": stack,
                "level": level,
                "package": package,
                "message": message
            }
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.auth_token}"
            }
            
            response = requests.post(self.log_api_url, json=payload, headers=headers, timeout=5)
            
            if response.status_code == 200:
                response_data = response.json()
                logger.debug(f"Log sent successfully. Log ID: {response_data.get('logID')}")
                return True
            else:
                logger.error(f"Log API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send log: {str(e)}")
            return False

if __name__ == "__main__":
    ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJNYXBDbGFpbXMiOnsiYXVkIjoiaHR0cDovLzIwLjI0NC41Ni4xNDQvZXZhbHVhdGlvbi1zZXJ2aWNlIiwiZW1haWwiOiJuaXNoYW50aF8yMmFpYjEyQGtna2l0ZS5hYy5pbiIsImV4cCI6MTc1NjcwNDg5NywiaWF0IjoxNzU2NzAzOTk3LCJpc3MiOiJBZmZvcmQgTWVkaWNhbCBUZWNobm9sb2dpZXMgUHJpdmF0ZSBMaW1pdGVkIiwianRpIjoiMmI5ZGU3NTAtZWU4NS00Yzk3LTg1NmItYmFiOTJlMjNkNGZhIiwibG9jYWxlIjoiZW4tSU4iLCJuYW1lIjoibmlzaGFudGgiLCJzdWIiOiIyZTRhMDYwMi03NTNhLTQ3NjItYWQ2ZC1lYzkwMWI1YWZlZjMifSwiZW1haWwiOiJuaXNoYW50aF8yMmFpYjEyQGtna2l0ZS5hYy5pbiIsIm5hbWUiOiJuaXNoYW50aCIsInJvbGxObyI6IjIyYWliMTIiLCJhY2Nlc3NDb2RlIjoiZHFYdXdaIiwiY2xpZW50SUQiOiIyZTRhMDYwMi03NTNhLTQ3NjItYWQ2ZC1lYzkwMWI1YWZlZjMiLCJjbGllbnRTZWNyZXQiOiJYdURUeUFKVXNzVGhyRWJFIn0.VY5hAr_BLzUGxaSDuYs8wgK-yuF3z2XAbVORzEo54XY"

    middleware = LoggingMiddleware(ACCESS_TOKEN)
    middleware.log("backend", "info", "middleware", "Logging middleware initialized")