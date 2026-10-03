import random
import requests
from web3 import Web3
from modules.utils import logger, get_recipient, load_lines
from modules.agw import AgwAccount
import settings

def get_gas_reserve_eth() -> float:
    cfg = getattr(settings, "GAS_RESERVE_ETH", 0.00025)
    if isinstance(cfg, (list, tuple)) and len(cfg) >= 2:
        return round(random.uniform(float(cfg[0]), float(cfg[1])), 6)
    return float(cfg)

CHAIN_MAP = {
    "BASE": 8453,
    "ARBITRUM": 42161,
    "OPTIMISM": 10,
    "LINEA": 59144,
    "POLYGON": 137,
    "ETHEREUM": 1,
}

class EthWithdrawer:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(settings.ABSTRACT_RPC))

    def withdraw_agw_eth(self, account: AgwAccount, account_index: int) -> bool:
        mode = getattr(settings, "WITHDRAW_MODE", "TRANSFER").upper()
        if mode == "BRIDGE_CEX":
            return self.bridge_agw_eth_to_cex(account, account_index)
        else:
            return self.transfer_agw_eth(account, account_index)

    def transfer_agw_eth(self, account: AgwAccount, account_index: int) -> bool:
        """Transfers ETH from the AGW account to the target EVM recipient on Abstract."""
        agw_addr = account.agw_address
        current_bal = self.w3.eth.get_balance(agw_addr)
        gas_reserve = get_gas_reserve_eth()
        gas_reserve_wei = int(gas_reserve * 1e18)

        if current_bal <= gas_reserve_wei:
            logger.warning(
                f"[{agw_addr[:8]}...] Balance {current_bal / 1e18:.5f} ETH is <= gas reserve ({gas_reserve:.5f} ETH). Skipping withdrawal."
            )
            return False

        amount_to_send = current_bal - gas_reserve_wei
        target_default = getattr(account, "evm_address", None) or account.signer_address
        recipient = get_recipient(account_index, default_address=target_default)

        logger.info(
            f"[{agw_addr[:8]}...] Withdrawing {amount_to_send / 1e18:.5f} ETH -> {recipient} (leaving {gas_reserve:.5f} ETH reserve)..."
        )

        try:
            res = account.transfer_eth(to=recipient, amount_wei=amount_to_send)
            tx_hash = res.get("hash")
            logger.success(
                f"[{agw_addr[:8]}...] ✅ Withdrawal confirmed: {settings.EXPLORER_TX_URL}{tx_hash}"
            )
            return True
        except Exception as e:
            logger.error(f"[{agw_addr[:8]}...] ❌ Withdrawal failed: {e}")
            return False

    def bridge_agw_eth_to_cex(self, account: AgwAccount, account_index: int) -> bool:
        """Bridges ETH directly from AGW via Relay.link to a CEX deposit address on a random L2 chain."""
        agw_addr = account.agw_address
        current_bal = self.w3.eth.get_balance(agw_addr)
        gas_reserve = get_gas_reserve_eth()
        gas_reserve_wei = int(gas_reserve * 1e18)

        if current_bal <= gas_reserve_wei:
            logger.warning(
                f"[{agw_addr[:8]}...] Balance {current_bal / 1e18:.5f} ETH is <= gas reserve ({gas_reserve:.5f} ETH). Skipping bridge."
            )
            return False

        amount_to_send = current_bal - gas_reserve_wei

        # Retrieve CEX recipient from recipients.txt
        recipients = load_lines("recipients.txt")
        if not recipients:
            logger.error(
                f"[{agw_addr[:8]}...] ❌ recipients.txt is empty! To bridge directly to CEX, add exchange deposit addresses to recipients.txt."
            )
            return False

        if account_index < len(recipients):
            recipient_raw = recipients[account_index]
        else:
            logger.warning(
                f"[{agw_addr[:8]}...] Index {account_index} out of bounds for recipients.txt! Using last recipient."
            )
            recipient_raw = recipients[-1]

        try:
            recipient = Web3.to_checksum_address(recipient_raw)
        except Exception as e:
            logger.error(f"[{agw_addr[:8]}...] ❌ Invalid recipient address '{recipient_raw}': {e}")
            return False

        # Pick random target chain from settings
        target_chains = getattr(settings, "BRIDGE_TARGET_CHAINS", ["BASE", "ARBITRUM", "OPTIMISM"])
        if isinstance(target_chains, str):
            target_chains = [target_chains]
        chain_name = random.choice(target_chains).upper()
        dest_chain_id = CHAIN_MAP.get(chain_name, 8453)

        logger.info(
            f"[{agw_addr[:8]}...] 🌉 Requesting Relay bridge quote: {amount_to_send / 1e18:.5f} ETH -> {chain_name} (CEX: {recipient})..."
        )

        proxy = getattr(account, "proxy", None)
        proxies = {"http": proxy, "https": proxy} if proxy else None

        payload = {
            "user": agw_addr,
            "originChainId": 2741,
            "destinationChainId": dest_chain_id,
            "originCurrency": "0x0000000000000000000000000000000000000000",
            "destinationCurrency": "0x0000000000000000000000000000000000000000",
            "amount": str(amount_to_send),
            "recipient": recipient,
            "tradeType": "EXACT_INPUT"
        }

        try:
            resp = requests.post("https://api.relay.link/quote", json=payload, proxies=proxies, timeout=15)
            if resp.status_code != 200:
                raise RuntimeError(f"Relay API error ({resp.status_code}): {resp.text}")

            quote_data = resp.json()
            steps = quote_data.get("steps", [])
            if not steps:
                raise RuntimeError(f"No execution steps returned by Relay API: {quote_data}")

            step_items = steps[0].get("items", [])
            if not step_items:
                raise RuntimeError("No step items in Relay response")

            tx_info = step_items[0].get("data", {})
            tx_to = Web3.to_checksum_address(tx_info["to"])
            tx_data = tx_info.get("data", "0x")
            tx_value = int(tx_info.get("value", amount_to_send))

            # Send transaction from AGW
            res = account.send_transaction(to=tx_to, data=tx_data, value=tx_value)
            tx_hash = res.get("hash")
            logger.success(
                f"[{agw_addr[:8]}...] ✅ Bridge transaction sent! TX: {settings.EXPLORER_TX_URL}{tx_hash}"
            )
            logger.success(
                f"[{agw_addr[:8]}...] 🚀 Dispatched {amount_to_send / 1e18:.5f} ETH via Relay directly to CEX ({chain_name}) -> {recipient}!"
            )
            return True

        except Exception as e:
            logger.error(f"[{agw_addr[:8]}...] ❌ Bridge to {chain_name} failed: {e}")
            return False

    def withdraw_eoa_eth(self, account: AgwAccount, account_index: int) -> bool:
        """Transfers ETH from the EOA signer address directly to the target EVM recipient."""
        eoa_addr = account.signer_address
        current_bal = self.w3.eth.get_balance(eoa_addr)
        gas_reserve = get_gas_reserve_eth()
        gas_reserve_wei = int(gas_reserve * 1e18)

        if current_bal <= gas_reserve_wei:
            logger.warning(
                f"[{eoa_addr[:8]}...] EOA Balance {current_bal / 1e18:.5f} ETH is <= gas reserve ({gas_reserve:.5f} ETH). Skipping."
            )
            return False

        amount_to_send = current_bal - gas_reserve_wei
        recipient = get_recipient(account_index, default_address=account.signer_address)

        logger.info(
            f"[{eoa_addr[:8]}...] Withdrawing {amount_to_send / 1e18:.5f} EOA ETH -> {recipient} (leaving {gas_reserve:.5f} ETH reserve)..."
        )

        try:
            res = account.transfer_eoa_eth(to=recipient, amount_wei=amount_to_send)
            tx_hash = res.get("hash")
            logger.success(
                f"[{eoa_addr[:8]}...] ✅ EOA withdrawal confirmed: {settings.EXPLORER_TX_URL}{tx_hash}"
            )
            return True
        except Exception as e:
            logger.error(f"[{eoa_addr[:8]}...] ❌ EOA withdrawal failed: {e}")
            return False
