"""MiniMax LLM client (OpenAI-compatible) with streaming + tolerant JSON parsing."""
# Daniel Design

import asyncio
import json
import re
from collections.abc import Awaitable, Callable

import httpx
from openai import APIConnectionError, APITimeoutError, AsyncOpenAI

from .config import get_settings


def repair_json(text: str) -> dict:
    """Best-effort extraction of a JSON object from an LLM response.

    Handles reasoning-model ``<think>`` blocks, markdown fences, leading/trailing
    prose, and minor noise. Raises ``json.JSONDecodeError`` if no valid object
    can be recovered.
    """
    text = text.strip()
    # Drop reasoning blocks emitted by reasoning models (e.g. MiniMax-M3).
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    # Strip a ```json ... ``` (or bare ```) fence if present.
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence:
        text = fence.group(1)
    # Grab the first balanced-looking object block.
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        text = match.group(0)
    return json.loads(text)


DeltaCallback = Callable[[str], Awaitable[None]]

# Errors that mean "the endpoint is unreachable right now" — worth retrying.
_RETRYABLE = (APIConnectionError, APITimeoutError, httpx.ConnectError, httpx.TimeoutException)


class LLMClient:
    """Async wrapper around MiniMax via the OpenAI SDK.

    Streaming tokens are forwarded to ``on_delta`` for live UI; the fully
    accumulated text is parsed into a dict. Connection/timeout errors are
    retried with backoff (MiniMax can be intermittently unreachable), but only
    while nothing has been streamed yet so the UI never sees duplicated tokens.
    """

    # Seconds to wait before each connection-error retry.
    _BACKOFFS = (2, 5, 10)

    def __init__(self) -> None:
        s = get_settings()
        self._client = AsyncOpenAI(
            base_url=s.minimax_base_url,
            api_key=s.minimax_api_key or "missing",
            max_retries=2,
            timeout=60.0,
        )
        self.model = s.minimax_model

    async def stream_json(
        self,
        system: str,
        user: str,
        on_delta: DeltaCallback | None = None,
    ) -> dict:
        last_exc: Exception | None = None
        for attempt in range(len(self._BACKOFFS) + 1):
            streamed = False

            async def _on_delta(delta: str) -> None:
                nonlocal streamed
                streamed = True
                if on_delta:
                    await on_delta(delta)

            try:
                return await self._run(system, user, stream=True, on_delta=_on_delta)
            except json.JSONDecodeError:
                # Model produced non-JSON — one silent non-stream retry to recover.
                return await self._run(system, user, stream=False)
            except _RETRYABLE as e:
                last_exc = e
                # Don't retry if tokens already went out (would duplicate), or if
                # we're out of attempts.
                if streamed or attempt == len(self._BACKOFFS):
                    raise
                await asyncio.sleep(self._BACKOFFS[attempt])
        assert last_exc is not None
        raise last_exc

    async def _run(
        self,
        system: str,
        user: str,
        *,
        stream: bool,
        on_delta: DeltaCallback | None = None,
    ) -> dict:
        resp = await self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            response_format={"type": "json_object"},
            stream=stream,
            temperature=0.3,
        )
        if stream:
            chunks: list[str] = []
            async for chunk in resp:  # type: ignore[union-attr]
                delta = chunk.choices[0].delta.content
                if delta:
                    chunks.append(delta)
                    if on_delta:
                        await on_delta(delta)
            text = "".join(chunks)
        else:
            text = resp.choices[0].message.content or ""  # type: ignore[union-attr]
        return repair_json(text)
