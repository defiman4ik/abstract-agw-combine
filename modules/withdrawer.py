import random
from web3 import Web3
from modules.utils import logger, get_recipient
from modules.agw import AgwAccount
import settings

def get_gas_reserve_eth() -> float:
    cfg = getattr(settings, "GAS_RESERVE_ETH", 0.00025)
    if isinstance(cfg, (list, tuple)) and len(cfg) >= 2:
        return round(random.uniform(float(cfg[0]), float(cfg[1])), 6)
    return float(cfg)

class EthWithdrawer:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(settings.ABSTRACT_RPC))

    def withdraw_agw_eth(self, account: AgwAccount, account_index: int) -> bool:
        """Transfers ETH from the AGW account to the target EVM recipient."""
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
