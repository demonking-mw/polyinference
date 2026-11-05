"""A bounded filesystem worker; cancellation joins a submitted mutation."""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial


class BlockingIO:
    def __init__(self):
        # Serialize copies and their aggregate disk-budget checks. Never put SQLite
        # or other coordinator state on this thread.
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="polyinference-fs")
        self.gate = asyncio.Lock()

    async def run(self, function, *args):
        async with self.gate:
            future = asyncio.get_running_loop().run_in_executor(self.executor, partial(function, *args))
            try:
                return await asyncio.shield(future)
            except asyncio.CancelledError:
                # A Python thread cannot be killed safely. Finish its bounded I/O
                # before releasing ownership or closing the run.
                await asyncio.shield(future)
                raise

    def close(self):
        self.executor.shutdown(wait=True, cancel_futures=True)
