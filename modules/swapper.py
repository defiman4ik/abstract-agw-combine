import time
import requests
from typing import Dict, Any, List
from modules.utils import logger, sleeping
from modules.agw import AgwAccount
import settings

class TokenSwapper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Content-Type": "application/json",
        })

    def unwrap_weth(self, account: AgwAccount, amount_wei: int) -> bool:
        """Directly unwraps WETH to ETH 1:1 without DEX fees."""
        logger.info(f"[{account.agw_address[:8]}...] Unwrapping {amount_wei / 1e18:.5f} WETH to ETH...")
        try:
            res = account.unwrap_weth(amount_wei)
            tx_hash = res.get("hash")
            logger.success(f"[{account.agw_address[:8]}...] ✅ WETH unwrap confirmed: {settings.EXPLORER_TX_URL}{tx_hash}")
            return True
        except Exception as e:
            logger.error(f"[{account.agw_address[:8]}...] ❌ Failed to unwrap WETH: {e}")
            return False

    def swap_token_to_eth(self, account: AgwAccount, token: Dict[str, Any]) -> bool:
        """Swaps an ERC20 token to native ETH via Relay DEX aggregator."""
        symbol = token["symbol"]
        raw_bal = token["raw_balance"]
        decimals = token["decimals"]
        formatted_bal = raw_bal / (10 ** decimals)

        if token.get("is_weth", False):
            return self.unwrap_weth(account, raw_bal)

        logger.info(f"[{account.agw_address[:8]}...] Getting swap quote for {formatted_bal:.4f} {symbol} -> ETH...")

        payload = {
            "user": account.agw_address,
            "originChainId": settings.CHAIN_ID,
            "destinationChainId": settings.CHAIN_ID,
            "originCurrency": token["address"],
            "destinationCurrency": "0x0000000000000000000000000000000000000000",
            "amount": str(raw_bal),
            "tradeType": "EXACT_INPUT",
        }

        try:
            resp = self.session.post("https://api.relay.link/quote", json=payload, timeout=20)
            if resp.status_code != 200:
                err_text = resp.text
                if "AMOUNT_TOO_LOW" in err_text or "too small" in err_text:
                    logger.warning(f"[{account.agw_address[:8]}...] Skipping {symbol}: balance is too small for swap.")
                elif "NO_SWAP_ROUTES_FOUND" in err_text:
                    logger.warning(f"[{account.agw_address[:8]}...] Skipping {symbol}: no DEX swap route found (low liquidity).")
                else:
                    logger.error(f"[{account.agw_address[:8]}...] Relay API error ({resp.status_code}): {err_text[:200]}")
                return False

            quote = resp.json()
            steps = quote.get("steps", [])
            if not steps:
                logger.warning(f"[{account.agw_address[:8]}...] No swap route available for {symbol}")
                return False

            out_amount = quote.get("details", {}).get("currencyOut", {}).get("amountFormatted", "?")
            logger.info(f"[{account.agw_address[:8]}...] Route found: ~{out_amount} ETH. Executing {len(steps)} step(s)...")

            for step in steps:
                for item in step.get("items", []):
                    tx_data = item.get("data", {})
                    to_addr = tx_data.get("to")
                    calldata = tx_data.get("data", "0x")
                    val = int(tx_data.get("value", 0))

                    if not to_addr:
                        continue

                    logger.info(f"[{account.agw_address[:8]}...] Executing step: {step.get('description', step.get('id', 'action'))}...")
                    res = account.send_transaction(to=to_addr, data=calldata, value=val)
                    logger.success(f"[{account.agw_address[:8]}...] ✅ Tx confirmed: {settings.EXPLORER_TX_URL}{res.get('hash')}")
                    sleeping(settings.SLEEP_BETWEEN_ACTIONS)

            logger.success(f"[{account.agw_address[:8]}...] ✅ Successfully swapped {symbol} -> ETH!")
            return True

        except Exception as e:
            logger.error(f"[{account.agw_address[:8]}...] ❌ Error during swap of {symbol}: {e}")
            return False

    def swap_all_tokens(self, account: AgwAccount, tokens: List[Dict[str, Any]]) -> int:
        """Iterates over tokens with non-zero balance and swaps them to ETH."""
        swapped_count = 0
        tokens_to_swap = [
            t for t in tokens
            if t.get("raw_balance", 0) > 0 and t.get("balance", 0) >= 0.000001
        ]

        if not tokens_to_swap:
            logger.info(f"[{account.agw_address[:8]}...] No tokens to swap.")
            return 0

        for token in tokens_to_swap:
            success = self.swap_token_to_eth(account, token)
            if success:
                swapped_count += 1
            sleeping(settings.SLEEP_BETWEEN_ACTIONS)

        return swapped_count
