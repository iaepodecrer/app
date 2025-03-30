import asyncio
import concurrent.futures
import time

def blocking_io(n):
    # Simulate a blocking I/O operation
    time.sleep(1)
    return f"Result {n}"

async def run_blocking_io(n, executor):
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(executor, blocking_io, n)
    return result

async def main():
    # ...existing code...
    # Utilize ThreadPoolExecutor for concurrent execution
    with concurrent.futures.ThreadPoolExecutor() as executor:
        tasks = [run_blocking_io(i, executor) for i in range(5)]
        results = await asyncio.gather(*tasks)
        for r in results:
            print(r)
    # ...existing code...

if __name__ == "__main__":
    asyncio.run(main())
