# QRIP

## Data Format

Data starts with the identifier `(QRIP)`, followed by an IP address.

| IPv4 Example | IPv6 Example |
| --- | --- |
| `(QRIP)123.45.67.89` | `(QRIP)[0123:4567:89ab:cdef::]` |

## Usage Example

```py
from .qrip import start_QRIP

start_QRIP()
```

## Blacklist

| address | IPv4 | IPv6 |
| --- | --- | --- |
| loopback | 127.0.0.0/8 | ::1 |
| link-local | 169.254.0.0/16 | fe80::/10 |
