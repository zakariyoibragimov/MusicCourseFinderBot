"""
Rate limiting utilities
"""

import time
from typing import Dict, Optional


class RateLimiter:
    """Simple rate limiter using in-memory storage (for single instance)"""
    
    def __init__(self, requests: int = 5, window: int = 60):
        """
        Args:
            requests: Max requests allowed
            window: Time window in seconds
        """
        self.requests = requests
        self.window = window
        self.user_requests: Dict[int, list] = {}
    
    def is_allowed(self, user_id: int) -> bool:
        """Check if user is allowed to make request"""
        now = time.time()
        
        # Initialize user if not present
        if user_id not in self.user_requests:
            self.user_requests[user_id] = []
        
        # Remove old requests outside window
        self.user_requests[user_id] = [
            req_time for req_time in self.user_requests[user_id]
            if now - req_time < self.window
        ]
        
        # Check if allowed
        if len(self.user_requests[user_id]) < self.requests:
            self.user_requests[user_id].append(now)
            return True
        
        return False
    
    def get_retry_after(self, user_id: int) -> Optional[int]:
        """Get seconds until next request is allowed"""
        if not self.user_requests.get(user_id):
            return None
        
        oldest_request = min(self.user_requests[user_id])
        retry_after = int(self.window - (time.time() - oldest_request)) + 1
        return max(0, retry_after)


# Global rate limiter instance
rate_limiter = RateLimiter(requests=5, window=60)
