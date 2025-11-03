# QRIP

## Data Example

| IPv4 | IPv6 |
| --- | --- |
| `(QRIP)123.45.67.89` | `(QRIP)[0123:4567:89ab:cdef::]` |

data always starts with identifier `(QRIP)`

## Blacklist

| address | IPv4 | IPv6 |
| --- | --- | --- |
| loopback | 127.0.0.0/8 | ::1 |
| link-local | 169.254.0.0/16 | fe80::/10 |
