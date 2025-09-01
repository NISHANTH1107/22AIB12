import logging
import uuid
import time
import requests
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, HttpUrl, Field
import uvicorn
from collections import defaultdict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("url_shortener.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("url_shortener")

app = FastAPI(title="URL Shortener Microservice", version="1.0.0")

url_mapping = {}
click_stats = defaultdict(list)


ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJNYXBDbGFpbXMiOnsiYXVkIjoiaHR0cDovLzIwLjI0NC41Ni4xNDQvZXZhbHVhdGlvbi1zZXJ2aWNlIiwiZW1haWwiOiJuaXNoYW50aF8yMmFpYjEyQGtna2l0ZS5hYy5pbiIsImV4cCI6MTc1NjcwNDg5NywiaWF0IjoxNzU2NzAzOTk3LCJpc3MiOiJBZmZvcmQgTWVkaWNhbCBUZWNobm9sb2dpZXMgUHJpdmF0ZSBMaW1pdGVkIiwianRpIjoiMmI5ZGU3NTAtZWU4NS00Yzk3LTg1NmItYmFiOTJlMjNkNGZhIiwibG9jYWxlIjoiZW4tSU4iLCJuYW1lIjoibmlzaGFudGgiLCJzdWIiOiIyZTRhMDYwMi03NTNhLTQ3NjItYWQ2ZC1lYzkwMWI1YWZlZjMifSwiZW1haWwiOiJuaXNoYW50aF8yMmFpYjEyQGtna2l0ZS5hYy5pbiIsIm5hbWUiOiJuaXNoYW50aCIsInJvbGxObyI6IjIyYWliMTIiLCJhY2Nlc3NDb2RlIjoiZHFYdXdaIiwiY2xpZW50SUQiOiIyZTRhMDYwMi03NTNhLTQ3NjItYWQ2ZC1lYzkwMWI1YWZlZjMiLCJjbGllbnRTZWNyZXQiOiJYdURUeUFKVXNzVGhyRWJFIn0.VY5hAr_BLzUGxaSDuYs8wgK-yuF3z2XAbVORzEo54XY"
LOG_API_URL = "http://20.244.56.144/evaluation-service/logs"

def Log(stack: str, level: str, package: str, message: str):
    allowed_stacks = ["backend"]
    allowed_levels = ["debug", "info", "warn", "error", "fatal"]
    allowed_backend_packages = ["cache", "controller", "cron_job", "db", "domain", "handler", "repository", "route", "service"]
    allowed_common_packages = ["auth", "config", "middleware", "utils"]  
    
    if stack not in allowed_stacks:
        return
    
    if level not in allowed_levels:
        return
    
   
    if stack == "backend" and package not in allowed_backend_packages + allowed_common_packages:
        return
    
    try:
        payload = {
            "stack": stack,
            "level": level,
            "package": package,
            "message": message
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {ACCESS_TOKEN}"
        }
        
        response = requests.post(LOG_API_URL, json=payload, headers=headers)
        
        if response.status_code == 200:
            response_data = response.json()
            log_id = response_data.get("logID")
            
            logger.debug(f"Log sent successfully. Log ID: {log_id}")
        else:
            logger.error(f"Log API returned status {response.status_code}: {response.text}")
        
    except Exception as e:
        logger.error(f"Failed to send log to external server: {str(e)}")

class ShortURLRequest(BaseModel):
    url: HttpUrl
    validity: Optional[int] = Field(default=30, ge=1)
    shortcode: Optional[str] = Field(default=None, min_length=4, max_length=10, pattern="^[a-zA-Z0-9_-]+$")

class ShortURLResponse(BaseModel):
    shortlink: str
    expiry: datetime

class ClickData(BaseModel):
    timestamp: datetime
    referrer: Optional[str] = None
    location: Optional[str] = None

class ShortURLStats(BaseModel):
    original_url: str
    creation_date: datetime
    expiry_date: datetime
    total_clicks: int
    click_details: List[ClickData]

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    formatted_process_time = f"{process_time:.2f}"
    
    logger.info(
        f"Method={request.method} "
        f"Path={request.url.path} "
        f"Status={response.status_code} "
        f"ProcessTime={formatted_process_time}ms"
    )
    
    Log("backend", "info", "route", f"{request.method} {request.url.path} - {response.status_code} - {formatted_process_time}ms")
    
    return response

def generate_shortcode() -> str:
    return str(uuid.uuid4())[:8]

def is_shortcode_available(shortcode: str) -> bool:
    return shortcode not in url_mapping

@app.post("/shorturls", response_model=ShortURLResponse, status_code=status.HTTP_201_CREATED)
async def create_short_url(request_data: ShortURLRequest, request: Request):
    try:
        if request_data.shortcode:
            if not is_shortcode_available(request_data.shortcode):
                Log("backend", "error", "handler", f"Shortcode collision: {request_data.shortcode}")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Shortcode already exists"
                )
            shortcode = request_data.shortcode
        else:
            shortcode = generate_shortcode()
            while not is_shortcode_available(shortcode):
                shortcode = generate_shortcode()
        
        expiry_time = datetime.now() + timedelta(minutes=request_data.validity)
        
        url_mapping[shortcode] = {
            "original_url": str(request_data.url),
            "created_at": datetime.now(),
            "expires_at": expiry_time
        }
        
        base_url = f"{request.url.scheme}://{request.url.hostname}"
        if request.url.port:
            base_url += f":{request.url.port}"
        shortlink = f"{base_url}/{shortcode}"
        
        Log("backend", "info", "service", f"Created short URL: {shortlink} -> {request_data.url}")
        
        return ShortURLResponse(
            shortlink=shortlink,
            expiry=expiry_time
        )
    
    except HTTPException:
        raise
    except Exception as e:
        Log("backend", "error", "handler", f"Error creating short URL: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@app.get("/{shortcode}")
async def redirect_to_url(shortcode: str, request: Request):
    try:
        if shortcode not in url_mapping:
            Log("backend", "warn", "handler", f"Shortcode not found: {shortcode}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Short URL not found"
            )
        
        url_data = url_mapping[shortcode]
        
        if datetime.now() > url_data["expires_at"]:
            Log("backend", "warn", "handler", f"Expired shortcode accessed: {shortcode}")
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Short URL has expired"
            )
        
        click_data = {
            "timestamp": datetime.now(),
            "referrer": request.headers.get("referer"),
            "location": request.headers.get("x-forwarded-for", request.client.host)
        }
        click_stats[shortcode].append(click_data)
        
        Log("backend", "info", "route", f"Redirecting: {shortcode} -> {url_data['original_url']}")
        
        return RedirectResponse(url=url_data["original_url"])
    
    except HTTPException:
        raise
    except Exception as e:
        Log("backend", "error", "handler", f"Error redirecting: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@app.get("/shorturls/{shortcode}", response_model=ShortURLStats)
async def get_shorturl_stats(shortcode: str):
    try:
        if shortcode not in url_mapping:
            Log("backend", "warn", "handler", f"Shortcode not found for stats: {shortcode}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Short URL not found"
            )
        
        url_data = url_mapping[shortcode]
        clicks = click_stats.get(shortcode, [])
        
        click_details = [
            ClickData(
                timestamp=click["timestamp"],
                referrer=click["referrer"],
                location=click["location"]
            )
            for click in clicks
        ]
        
        Log("backend", "info", "service", f"Retrieved stats for shortcode: {shortcode}")
        
        return ShortURLStats(
            original_url=url_data["original_url"],
            creation_date=url_data["created_at"],
            expiry_date=url_data["expires_at"],
            total_clicks=len(clicks),
            click_details=click_details
        )
    
    except HTTPException:
        raise
    except Exception as e:
        Log("backend", "error", "handler", f"Error retrieving stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
    
    
    


