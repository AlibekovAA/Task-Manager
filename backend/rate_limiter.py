from datetime import datetime, timedelta
from typing import Dict
import time

from fastapi import HTTPException, status

from .logger import setup_logger

logger = setup_logger(__name__)


class RateLimiter:
    def __init__(self):
        self.attempts: Dict[str, list] = {}
        self.blocked_until: Dict[str, datetime] = {}
        self.max_attempts = 5
        self.block_duration = timedelta(minutes=15)
        self.attempt_window = timedelta(minutes=5)
        self.progressive_delay = 2

    def check_rate_limit(self, email: str) -> None:
        current_time = datetime.now()

        if email in self.blocked_until:
            if current_time < self.blocked_until[email]:
                remaining_time = (self.blocked_until[email] - current_time).total_seconds()
                logger.warning(f"Login attempt from blocked email: {email}")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Слишком много попыток. Попробуйте через {int(remaining_time)} секунд"
                )
            else:
                del self.blocked_until[email]
                self.attempts[email] = []

        if email in self.attempts:
            self.attempts[email] = [
                attempt for attempt in self.attempts[email]
                if current_time - attempt < self.attempt_window
            ]

        if email in self.attempts:
            num_attempts = len(self.attempts[email])
            if num_attempts > 0:
                delay = self.progressive_delay ** (num_attempts - 1)
                logger.info(f"Applying progressive delay of {delay} seconds for {email}")
                time.sleep(delay)

            if num_attempts >= self.max_attempts:
                self.blocked_until[email] = current_time + self.block_duration
                logger.warning(f"Email {email} blocked due to too many attempts")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Слишком много попыток. Аккаунт заблокирован на {self.block_duration.seconds // 60} минут"
                )

    def add_attempt(self, email: str) -> None:
        current_time = datetime.now()
        if email not in self.attempts:
            self.attempts[email] = []
        self.attempts[email].append(current_time)
        logger.info(f"Added login attempt for {email}. Total attempts: {len(self.attempts[email])}")

    def reset_attempts(self, email: str) -> None:
        if email in self.attempts:
            del self.attempts[email]
        if email in self.blocked_until:
            del self.blocked_until[email]
        logger.info(f"Reset attempts for {email}")

    def reset(self, email: str = None) -> None:
        if email:
            self.reset_attempts(email)
        else:
            self.attempts.clear()
            self.blocked_until.clear()
            logger.info("Reset all rate limiting data")

    def reset_all(self):
        self.attempts.clear()
        self.blocked_until.clear()


rate_limiter = RateLimiter()
