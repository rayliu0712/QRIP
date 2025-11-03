# QRIP

## Data Format

Data starts with the identifier `(QRIP)`, followed by an IP address.

| IPv4 Example | IPv6 Example |
| --- | --- |
| `(QRIP)123.45.67.89` | `(QRIP)[0123:4567:89ab:cdef::]` |

## Usage Example

`start_QRIP_daemon()` uses *multiprocessing* to launch a separate child process.

**On Windows**, multiprocessing always uses "spawn", which imports the main module to start the child process.

**If not protected by `if __name__ == '__main__'`, it will recursively start new processes and crash.**

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

## Blacklist

| address | IPv4 | IPv6 |
| --- | --- | --- |
| loopback | 127.0.0.0/8 | ::1 |
| link-local | 169.254.0.0/16 | fe80::/10 |
