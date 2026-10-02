import os
import sys
import time
import random
from typing import List, Optional, Tuple
from loguru import logger
import settings

# Configure Loguru logger
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <7}</level> | <cyan>{message}</cyan>",
    colorize=True,
)
os.makedirs("logs", exist_ok=True)
logger.add(
    "logs/abstract_bot.log",
    rotation="10 MB",
    retention="7 days",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <7} | {message}",
    encoding="utf-8",
)

import re

def sleeping(seconds_range: list, comment: Optional[str] = None) -> None:
    if not seconds_range:
        return
    if len(seconds_range) == 1 or seconds_range[0] == seconds_range[1]:
        sleep_time = seconds_range[0]
    else:
        sleep_time = random.uniform(seconds_range[0], seconds_range[1])
    msg = f" ({comment})" if comment else ""
    logger.info(f"Sleeping {sleep_time:.1f}s{msg}...")
    time.sleep(sleep_time)

from eth_account import Account

def extract_private_key(raw_line: str) -> Optional[Tuple[str, Optional[str], Optional[str], Optional[str], Optional[str]]]:
    """
    Extracts (signer_pk, account_id, agw_address, evm_pk, evm_addr) supporting:
    - label:privatekeyEVM:signer
    - label:evmAddress:signer
    - privatekeyEVM:signer
    - label:signer
    - signer
    """
    raw = raw_line.strip()
    if not raw or raw.startswith("#"):
        return None

    eth_addrs = re.findall(r"0x[a-fA-F0-9]{40}\b", raw)
    hex_keys = re.findall(r"(?:0x)?([0-9a-fA-F]{64})\b", raw)
    if not hex_keys:
        return None

    parts = [p.strip() for p in raw.split(":") if p.strip()]
    account_id = None
    if parts and len(parts[0]) <= 20 and not re.fullmatch(r"(?:0x)?[0-9a-fA-F]{64}", parts[0]) and not re.fullmatch(r"0x[a-fA-F0-9]{40}", parts[0]):
        account_id = parts[0]

    evm_pk = None
    evm_addr = None
    if len(hex_keys) >= 2:
        evm_pk = "0x" + hex_keys[0].lower()
        signer_pk = "0x" + hex_keys[1].lower()
        try:
            evm_addr = Account.from_key(evm_pk).address
        except Exception:
            pass
    else:
        signer_pk = "0x" + hex_keys[0].lower()
        if eth_addrs:
            evm_addr = eth_addrs[0]

    agw_address = None
    return signer_pk, account_id, agw_address, evm_pk, evm_addr

def load_private_keys(file_path: str = "privatekeys.txt") -> List[Tuple[str, Optional[str], Optional[str], Optional[str], Optional[str]]]:
    """Returns list of (signer_pk, account_id, agw_address, evm_pk, evm_addr)."""
    if not os.path.exists(file_path):
        return []
    keys = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            res = extract_private_key(line)
            if res:
                keys.append(res)
    return keys

def load_proxies(file_path: str = "proxies.txt") -> List[str]:
    """Loads and formats proxy strings from proxies.txt."""
    if not os.path.exists(file_path):
        return []
    proxies = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            p = line.strip()
            if not p or p.startswith("#"):
                continue
            if not (p.startswith("http://") or p.startswith("https://") or p.startswith("socks5://")):
                p = "http://" + p
            proxies.append(p)
    return proxies

def load_lines(file_path: str) -> List[str]:
    if not os.path.exists(file_path):
        return []
    with open(file_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]
    return lines

def get_recipient(index: int, default_address: str) -> str:
    if getattr(settings, "RECIPIENT_MODE", "SAME_AS_EOA") == "SAME_AS_EOA":
        return default_address
    recipients = load_lines("recipients.txt")
    if not recipients:
        logger.warning("recipients.txt is empty! Falling back to account EOA address.")
        return default_address
    if index < len(recipients):
        return recipients[index]
    else:
        logger.warning(f"Index {index} out of bounds for recipients.txt! Using last recipient.")
        return recipients[-1]
