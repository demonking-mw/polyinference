"""Bounded foreground execution for trusted Git operations and merge helpers."""

from __future__ import annotations

import asyncio
import os
import signal


async def command(argv, *, timeout, output_limit, input_data=None, env=None):
    process = await asyncio.create_subprocess_exec(
        *argv,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env,
        start_new_session=True,
    )
    output, error = bytearray(), bytearray()

    async def read(stream, buffer):
        while chunk := await stream.read(65536):
            if len(output) + len(error) + len(chunk) > output_limit:
                raise ValueError("Command output exceeds configured limit")
            buffer.extend(chunk)

    async def write():
        try:
            if input_data:
                process.stdin.write(input_data)
                await process.stdin.drain()
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            process.stdin.close()

    readers = [
        asyncio.create_task(read(process.stdout, output)),
        asyncio.create_task(read(process.stderr, error)),
        asyncio.create_task(write()),
    ]
    try:
        await asyncio.wait_for(asyncio.gather(*readers, process.wait()), timeout)
        return process.returncode, bytes(output), bytes(error)
    finally:
        # A parent exiting is not proof that descendants have exited.
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        await process.wait()
        for reader in readers:
            if not reader.done():
                reader.cancel()
        await asyncio.gather(*readers, return_exceptions=True)
