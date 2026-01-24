"""Eversolar PMU protocol implementation."""
import re
import socket
import struct
from datetime import datetime, timezone

try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None


SYNC = b"\xAA\x55"


def crc16_xmodem(data: bytes) -> int:
    """Calculate CRC-16/XMODEM: poly=0x1021, init=0x0000."""
    crc = 0x0000
    for b in data:
        crc ^= (b << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc


def recv_exact(sock: socket.socket, n: int, timeout_s: float = 5.0) -> bytes:
    """Receive exactly n bytes from socket."""
    sock.settimeout(timeout_s)
    out = bytearray()
    while len(out) < n:
        chunk = sock.recv(n - len(out))
        if not chunk:
            raise RuntimeError(
                f"Socket closed while reading {n} bytes (got {len(out)})"
            )
        out.extend(chunk)
    return bytes(out)


def recv_frame(sock: socket.socket, timeout_s: float = 5.0) -> bytes:
    """Receive a frame: AA 55 cmd 00 len payload."""
    hdr = recv_exact(sock, 5, timeout_s=timeout_s)
    if hdr[:2] != SYNC:
        raise RuntimeError(f"Bad sync in response header: {hdr.hex()}")
    payload_len = hdr[4]
    payload = recv_exact(sock, payload_len, timeout_s=timeout_s) if payload_len else b""
    return hdr + payload


def build_req(cmd: int, payload: bytes) -> bytes:
    """Build a request frame."""
    if len(payload) > 255:
        raise ValueError("Payload too large")
    hdr = SYNC + bytes([cmd, 0x00, len(payload)])
    c = crc16_xmodem(hdr + payload)
    crc_be = struct.pack(">H", c)  # MSB first
    return hdr + payload + crc_be


def tz_field_84(win_tz_name: str) -> bytes:
    """Encode timezone field for init payload."""
    b = win_tz_name.encode("utf-16-le", errors="ignore")
    if len(b) > 84:
        b = b[:84]
    return b + b"\x00" * (84 - len(b))


def build_init_payload(now_local: datetime) -> bytes:
    """Build init payload with local time."""
    tz = "E. Australia Standard Time"
    tz_dst = "E. Australia Daylight Time"
    prefix = b"\xA8\xFD\xFF\xFF"
    wday = (now_local.weekday() + 1) % 7  # 0=Sun..6=Sat
    time_struct = struct.pack(
        "<8H",
        now_local.year,
        now_local.month,
        wday,
        now_local.day,
        now_local.hour,
        now_local.minute,
        now_local.second,
        0x0346,
    )
    payload = prefix + tz_field_84(tz) + tz_field_84(tz_dst) + time_struct
    if len(payload) != 188:
        raise RuntimeError(f"Init payload length unexpected: {len(payload)} (expected 188)")
    return payload


def parse_inverter_id(resp12: bytes) -> str:
    """Extract inverter ID from 0x12 response."""
    payload = resp12[5:]
    m = re.search(rb"[A-Z0-9]{16}", payload)
    if not m:
        raise RuntimeError("Could not find inverter ID in 0x12 response")
    return m.group(0).decode("ascii", errors="ignore")


def parse_code_list_from_resp12(resp12: bytes) -> list:
    """Extract data codes from 0x12 response."""
    payload = resp12[5:]
    m = re.search(rb"[A-Z0-9]{16}", payload)
    if not m:
        raise RuntimeError("Could not locate inverter ID in 0x12 response")
    i = m.end()

    tail = payload[i:]
    codes: list = []
    pos = 0
    while pos < len(tail):
        b = tail[pos]
        if b == 0x00:
            # count zero-run
            zr = 1
            while (pos + zr) < len(tail) and tail[pos + zr] == 0x00:
                zr += 1
            # if this looks like padding (>=4 zeros) and we already have real codes, stop
            if zr >= 4 and len(codes) >= 2:
                break
            # otherwise, 0x00 is a legitimate code; keep it and continue
            codes.append(0x00)
            pos += 1
            continue
        codes.append(b)
        pos += 1

    if not codes:
        raise RuntimeError("No codes parsed from 0x12 response")
    return codes


def decode_normal_info_from_resp14(resp14: bytes, codes: list) -> dict:
    """Decode data values from 0x14 response."""
    payload = resp14[5:]
    start = 0x08
    need = start + len(codes) * 2
    if len(payload) < need:
        raise RuntimeError(f"0x14 payload too short: {len(payload)} < {need}")

    vals = {}
    for idx, code in enumerate(codes):
        off = start + idx * 2
        v = payload[off] + (payload[off + 1] << 8)  # uint16 LE
        vals[code] = v
    return vals


class EversolarPMU:
    """Eversolar PMU protocol implementation."""

    def __init__(self, host: str, port: int, timeout: float = 5.0):
        """Initialize PMU connection parameters."""
        self.host = host
        self.port = port
        self.timeout = timeout
        self._inverter_id = None
        self._codes = None

    @staticmethod
    def test_connection(host: str, port: int, timeout: float = 5.0) -> bool:
        """Test if PMU is reachable by attempting init handshake."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout)
            s.connect((host, port))

            # Send init command
            now_local = datetime.now(timezone.utc)
            s.sendall(build_req(0x01, build_init_payload(now_local)))
            recv_frame(s, timeout_s=timeout)

            s.close()
            return True
        except Exception:
            return False

    def connect_and_poll(self, set_time: bool = False, tz_name: str = "Australia/Brisbane") -> dict:
        """Connect, initialize, and poll data from PMU."""
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(self.timeout)

        try:
            s.connect((self.host, self.port))

            # 1) INIT (0x01) -> (0x02)
            if ZoneInfo:
                now_local = datetime.now(ZoneInfo(tz_name))
            else:
                now_local = datetime.now()

            s.sendall(build_req(0x01, build_init_payload(now_local)))
            recv_frame(s, timeout_s=self.timeout)

            # 2) 0x11 0x00 -> 0x12 (contains inverter id + code list)
            s.sendall(build_req(0x11, b"\x00"))
            resp12_long = recv_frame(s, timeout_s=self.timeout)
            inverter_id = parse_inverter_id(resp12_long)
            codes = parse_code_list_from_resp12(resp12_long)

            # Store for later use
            self._inverter_id = inverter_id
            self._codes = codes

            # 3) keepalive 0x73 -> 0x74
            s.sendall(build_req(0x73, b""))
            recv_frame(s, timeout_s=self.timeout)

            # 4) 0x11 0x01 -> 0x12 short (compatibility)
            s.sendall(build_req(0x11, b"\x01"))
            recv_frame(s, timeout_s=self.timeout)

            # 5) keepalive again
            s.sendall(build_req(0x73, b""))
            recv_frame(s, timeout_s=self.timeout)

            # 6) 0x13 inverter_id -> 0x14 values
            s.sendall(build_req(0x13, inverter_id.encode("ascii")))
            resp14 = recv_frame(s, timeout_s=self.timeout)

            # Parse PMU time
            pmu_epoch = None
            pmu_time_utc = None
            time_delta = None

            try:
                payload14 = resp14[5:]
                pmu_epoch = int.from_bytes(payload14[2:6], "little")
                pmu_dt_utc = datetime.fromtimestamp(pmu_epoch, tz=timezone.utc)
                pmu_time_utc = pmu_dt_utc.isoformat()

                host_dt_utc = datetime.now(timezone.utc)
                time_delta = int((pmu_dt_utc - host_dt_utc).total_seconds())
            except Exception:
                pmu_epoch = None
                pmu_time_utc = None
                time_delta = None

            # Decode values
            vals = decode_normal_info_from_resp14(resp14, codes)

            # Parse and scale values
            power_w = vals.get(0x44)
            vac_v = (vals.get(0x42) / 10.0) if (0x42 in vals) else None
            fac_hz = (vals.get(0x43) / 100.0) if (0x43 in vals) else None
            e_today_kwh = (vals.get(0x0D) / 100.0) if (0x0D in vals) else None
            mode = vals.get(0x4C)

            # PV-side telemetry
            pv_v = None
            for code in (0x01, 0x02, 0x40):
                if code in vals:
                    raw = vals.get(code)
                    if raw not in (None, 0, 0xFFFF):
                        pv_v = raw / 10.0
                        break

            pv_a = None
            for code in (0x41, 0x04, 0x05, 0x46):
                if code in vals:
                    raw = vals.get(code)
                    if raw not in (None, 0, 0xFFFF) and raw <= 2000:
                        pv_a = raw / 10.0
                        break

            if pv_a is None and pv_v and power_w is not None and pv_v > 0:
                pv_a = round(power_w / pv_v, 3)

            pv_w_est = round(pv_v * pv_a, 1) if (pv_v is not None and pv_a is not None) else None

            # Total energy
            e_total_kwh = None
            if (0x47 in vals) and (0x48 in vals):
                e_total_kwh = round((vals[0x47] / 10.0) + (vals[0x48] * 6553.6), 1)

            # Total operation hours
            h_total_hours = None
            if (0x49 in vals) and (0x4A in vals):
                h_total_hours = vals[0x49] + (vals[0x4A] * 65536)

            # Error flags (32-bit: low 16 bits in 0x4D, high 16 bits in 0x4E)
            error_flags = None
            if (0x4D in vals) and (0x4E in vals):
                error_flags = vals[0x4D] + (vals[0x4E] << 16)

            return {
                "inverter_id": inverter_id,
                "power_w": power_w,
                "vac_v": vac_v,
                "fac_hz": fac_hz,
                "e_today_kwh": e_today_kwh,
                "e_total_kwh": e_total_kwh,
                "h_total_hours": h_total_hours,
                "mode": mode,
                "pv_v": pv_v,
                "pv_a": pv_a,
                "pv_w_est": pv_w_est,
                "error_flags": error_flags,
                "pmu_time_utc": pmu_time_utc,
                "time_delta": time_delta,
                "pmu_epoch": pmu_epoch,
                "raw_u16": {f"0x{k:02x}": v for k, v in vals.items()},
            }
        finally:
            s.close()

    def sync_time(self, tz_name: str = "Australia/Brisbane") -> bool:
        """Sync PMU time to host time."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(self.timeout)
            s.connect((self.host, self.port))

            # Send init with current time
            if ZoneInfo:
                now_local = datetime.now(ZoneInfo(tz_name))
            else:
                now_local = datetime.now()

            s.sendall(build_req(0x01, build_init_payload(now_local)))
            recv_frame(s, timeout_s=self.timeout)

            s.close()
            return True
        except Exception:
            return False
