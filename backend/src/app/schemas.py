"""
Pydantic-схемы для валидации данных, передаваемых по WebSocket.

Определяет структуру сообщений, которыми обмениваются клиент и сервер.
"""

from typing import Any, Dict, Literal

from pydantic import BaseModel, Field


class ClientMessage(BaseModel):
    """Схема для сообщений, приходящих от клиента."""

    type: Literal["POSE_DATA", "START_SESSION", "END_SESSION"]
    payload: Dict[str, Any] = Field(default_factory=dict)


class ServerMessage(BaseModel):
    """Схема для сообщений, отправляемых сервером клиенту."""

    type: Literal["FEEDBACK", "REPORT", "ERROR", "INFO"]
    payload: Dict[str, Any]
