# QRIP

## Data Format

Data starts with the identifier `(QRIP)`, followed by an IP address.

| IPv4 Example | IPv6 Example |
| --- | --- |
| `(QRIP)123.45.67.89` | `(QRIP)[0123:4567:89ab:cdef::]` |

## Python Usage Example

`start_QRIP_daemon()` uses the *multiprocessing* module to launch a separate child process.

**On Windows**, the multiprocessing module always uses the "spawn" start method, which re-imports the main module to create the child process.

**If the code is not protected by `if __name__ == '__main__':`, it will recursively spawn new processes and eventually crash.**

```py
from qrip import start_QRIP_daemon
from fastapi import FastAPI
import uvicorn

if __name__ == '__main__':
    start_QRIP_daemon()

    app = FastAPI()

    @app.get("/")
    async def read_root():
        return {'message': 'Hello World'}

    uvicorn.run(app, host='::')
```

## Command Line Usage Example

If it’s hard to integrate with your server code, you can run it directly from the command line.

- CMD

    ```
    start "" python qrip.py && python your_server.py
    ```

- PowerShell

    ```
    start python qrip.py; python your_server.py
    ```

- Bash

    ```
    python3 qrip.py & python3 your_server.py
    ```

## Blacklist

| address | IPv4 | IPv6 |
| --- | --- | --- |
| loopback | 127.0.0.0/8 | ::1 |
| link-local | 169.254.0.0/16 | fe80::/10 |
