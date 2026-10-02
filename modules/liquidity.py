import time
from typing import List, Dict, Any
from web3 import Web3
from modules.utils import logger, sleeping
import settings

PM_ABI = [
    {"inputs": [{"name": "owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"name": "owner", "type": "address"}, {"name": "index", "type": "uint256"}], "name": "tokenOfOwnerByIndex", "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"name": "tokenId", "type": "uint256"}], "name": "positions", "outputs": [
        {"name": "nonce", "type": "uint96"},
        {"name": "operator", "type": "address"},
        {"name": "token0", "type": "address"},
        {"name": "token1", "type": "address"},
        {"name": "fee", "type": "uint24"},
        {"name": "tickLower", "type": "int24"},
        {"name": "tickUpper", "type": "int24"},
        {"name": "liquidity", "type": "uint128"},
        {"name": "feeGrowthInside0LastX128", "type": "uint256"},
        {"name": "feeGrowthInside1LastX128", "type": "uint256"},
        {"name": "tokensOwed0", "type": "uint128"},
        {"name": "tokensOwed1", "type": "uint128"}
    ], "stateMutability": "view", "type": "function"},
    {"inputs": [{"components": [
        {"name": "tokenId", "type": "uint256"},
        {"name": "liquidity", "type": "uint128"},
        {"name": "amount0Min", "type": "uint256"},
        {"name": "amount1Min", "type": "uint256"},
        {"name": "deadline", "type": "uint256"}
    ], "name": "params", "type": "tuple"}], "name": "decreaseLiquidity", "outputs": [{"name": "amount0", "type": "uint256"}, {"name": "amount1", "type": "uint256"}], "stateMutability": "payable", "type": "function"},
    {"inputs": [{"components": [
        {"name": "tokenId", "type": "uint256"},
        {"name": "recipient", "type": "address"},
        {"name": "amount0Max", "type": "uint128"},
        {"name": "amount1Max", "type": "uint128"}
    ], "name": "params", "type": "tuple"}], "name": "collect", "outputs": [{"name": "amount0", "type": "uint256"}, {"name": "amount1", "type": "uint256"}], "stateMutability": "payable", "type": "function"},
    {"inputs": [{"name": "tokenId", "type": "uint256"}], "name": "burn", "outputs": [], "stateMutability": "payable", "type": "function"}
]

KONA_FARM_ABI = [
    {"inputs": [], "name": "getFarmsLength", "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"name": "", "type": "uint256"}], "name": "farms", "outputs": [
        {"name": "lpToken", "type": "address"},
        {"name": "pointsPerBlock", "type": "uint256"},
        {"name": "totalStaked", "type": "uint256"},
        {"name": "lastRewardBlock", "type": "uint256"},
        {"name": "accPointsPerShare", "type": "uint256"},
        {"name": "active", "type": "bool"},
        {"name": "minStakeAmount", "type": "uint256"}
    ], "stateMutability": "view", "type": "function"},
    {"inputs": [{"name": "user", "type": "address"}, {"name": "farmId", "type": "uint256"}], "name": "userInfo", "outputs": [
        {"name": "amount", "type": "uint256"},
        {"name": "pointsDebt", "type": "uint256"}
    ], "stateMutability": "view", "type": "function"},
    {"inputs": [{"name": "_farmId", "type": "uint256"}, {"name": "_amount", "type": "uint256"}], "name": "unstake", "outputs": [], "stateMutability": "nonpayable", "type": "function"}
]

V2_PAIR_ABI = [
    {"inputs": [], "name": "token0", "outputs": [{"name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "token1", "outputs": [{"name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"name": "owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"name": "owner", "type": "address"}, {"name": "spender", "type": "address"}], "name": "allowance", "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}], "name": "approve", "outputs": [{"name": "", "type": "bool"}], "stateMutability": "nonpayable", "type": "function"},
]

V2_ROUTER_ABI = [
    {"inputs": [
        {"name": "tokenA", "type": "address"},
        {"name": "tokenB", "type": "address"},
        {"name": "liquidity", "type": "uint256"},
        {"name": "amountAMin", "type": "uint256"},
        {"name": "amountBMin", "type": "uint256"},
        {"name": "to", "type": "address"},
        {"name": "deadline", "type": "uint256"}
    ], "name": "removeLiquidity", "outputs": [
        {"name": "amountA", "type": "uint256"},
        {"name": "amountB", "type": "uint256"}
    ], "stateMutability": "nonpayable", "type": "function"}
]

class LiquidityRemover:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(settings.ABSTRACT_RPC))
        self.protocols = getattr(settings, "LIQUIDITY_PROTOCOLS", [])

    def get_positions(self, agw_address: str) -> List[Dict[str, Any]]:
        """Returns all open CLMM LP positions across supported protocols for an AGW account."""
        positions = []
        agw_addr = Web3.to_checksum_address(agw_address)
        for proto in self.protocols:
            try:
                pm = self.w3.eth.contract(address=Web3.to_checksum_address(proto["position_manager"]), abi=PM_ABI)
                count = pm.functions.balanceOf(agw_addr).call()
                for i in range(count):
                    token_id = pm.functions.tokenOfOwnerByIndex(agw_addr, i).call()
                    pos = pm.functions.positions(token_id).call()
                    positions.append({
                        "protocol": proto["name"],
                        "pm_address": proto["position_manager"],
                        "token_id": token_id,
                        "token0": pos[2],
                        "token1": pos[3],
                        "fee": pos[4],
                        "liquidity": pos[7],
                        "tokens_owed0": pos[10],
                        "tokens_owed1": pos[11],
                    })
            except Exception as e:
                logger.error(f"Error querying positions for {proto['name']} on {agw_address}: {e}")
        return positions

    def unstake_and_remove_kona_farms(self, account) -> bool:
        """Checks for staked LP tokens in Kona Farm, unstakes them, and removes liquidity from the V2 pool."""
        farm_addr = getattr(settings, "KONA_FARM_ADDRESS", None)
        router_addr = getattr(settings, "KONA_V2_ROUTER_ADDRESS", None)
        if not farm_addr or not router_addr:
            return True

        agw_addr = account.agw_address
        farm_contract = self.w3.eth.contract(address=Web3.to_checksum_address(farm_addr), abi=KONA_FARM_ABI)
        try:
            total_farms = farm_contract.functions.getFarmsLength().call()
        except Exception as e:
            logger.error(f"[{agw_addr}] Error getting Kona farms count: {e}")
            return True

        all_ok = True
        for fid in range(total_farms):
            try:
                uinfo = farm_contract.functions.userInfo(agw_addr, fid).call()
                staked_amt = uinfo[0]
                if staked_amt <= 1000:
                    continue

                f_info = farm_contract.functions.farms(fid).call()
                lp_addr = Web3.to_checksum_address(f_info[0])

                logger.info(f"[{agw_addr}] Found stake in Kona Farm #{fid}: {staked_amt / 1e18:.8f} LP.")

                # 1. Unstake from Farm
                # Official Kona frontend unstakes (amount - 1) to satisfy 'Remaining must be gt min' contract constraint
                unstake_amt = staked_amt - 1 if staked_amt > 1 else staked_amt
                logger.info(f"[{agw_addr}] Unstaking {unstake_amt / 1e18:.8f} LP from Kona Farm #{fid}...")
                unstake_data = farm_contract.encodeABI("unstake", args=[fid, unstake_amt])
                res = account.send_transaction(to=farm_addr, data=unstake_data)
                logger.success(f"[{agw_addr}] Successfully unstaked from Kona Farm #{fid} (tx: {res.get('hash')})")
                sleeping(settings.SLEEP_BETWEEN_ACTIONS)

                # 2. Check LP balance and remove liquidity
                lp_contract = self.w3.eth.contract(address=lp_addr, abi=V2_PAIR_ABI)
                # Wait briefly for balance to update if needed
                lp_bal = lp_contract.functions.balanceOf(agw_addr).call()
                if lp_bal == 0:
                    time.sleep(2)
                    lp_bal = lp_contract.functions.balanceOf(agw_addr).call()

                if lp_bal > 0:
                    logger.info(f"[{agw_addr}] Removing liquidity for {lp_bal / 1e18:.8f} LP tokens...")

                    # Approve Router if allowance is not enough
                    allowance = lp_contract.functions.allowance(agw_addr, Web3.to_checksum_address(router_addr)).call()
                    if allowance < lp_bal:
                        logger.info(f"[{agw_addr}] Approving LP tokens for Kona Router...")
                        approve_data = lp_contract.encodeABI("approve", args=[Web3.to_checksum_address(router_addr), 2**256 - 1])
                        res_app = account.send_transaction(to=lp_addr, data=approve_data)
                        logger.success(f"[{agw_addr}] LP tokens approved (tx: {res_app.get('hash')})")
                        sleeping(settings.SLEEP_BETWEEN_ACTIONS)

                    # Remove liquidity from V2 pool
                    t0 = lp_contract.functions.token0().call()
                    t1 = lp_contract.functions.token1().call()
                    router_c = self.w3.eth.contract(address=Web3.to_checksum_address(router_addr), abi=V2_ROUTER_ABI)
                    deadline = int(time.time()) + 1800
                    rem_data = router_c.encodeABI("removeLiquidity", args=[
                        Web3.to_checksum_address(t0),
                        Web3.to_checksum_address(t1),
                        lp_bal,
                        0,
                        0,
                        agw_addr,
                        deadline
                    ])
                    res_rem = account.send_transaction(to=router_addr, data=rem_data)
                    logger.success(f"[{agw_addr}] Liquidity successfully removed from Kona V2 pool (tx: {res_rem.get('hash')})")
                    sleeping(settings.SLEEP_BETWEEN_ACTIONS)

            except Exception as e:
                logger.error(f"[{agw_addr}] Error unstaking/removing Kona Farm #{fid}: {e}")
                all_ok = False

        return all_ok

    def remove_all_liquidity(self, account) -> bool:
        """Removes liquidity and collects all tokens/fees from all DEX protocols & farms for the account."""
        # 1. Unstake and remove liquidity from Kona Farms
        self.unstake_and_remove_kona_farms(account)

        # 2. Process CLMM/V3 positions across Aborean, KONA, Sakura Swap
        positions = self.get_positions(account.agw_address)
        if not positions:
            logger.info(f"[{account.agw_address}] No CLMM NFT positions found.")
            return True

        # Filter only active positions that actually have liquidity or uncollected tokens/fees
        active_positions = [
            p for p in positions
            if p.get("liquidity", 0) > 0 or p.get("tokens_owed0", 0) > 0 or p.get("tokens_owed1", 0) > 0
        ]

        if not active_positions:
            logger.info(f"[{account.agw_address}] All {len(positions)} CLMM position(s) are already empty. Skipping.")
            return True

        logger.info(f"[{account.agw_address}] Found {len(active_positions)} active CLMM LP position(s) to process.")
        all_ok = True

        for p in active_positions:
            proto_name = p["protocol"]
            token_id = p["token_id"]
            pm_addr = Web3.to_checksum_address(p["pm_address"])
            pm = self.w3.eth.contract(address=pm_addr, abi=PM_ABI)
            liq = p["liquidity"]

            try:
                # Decrease liquidity if > 0
                if liq > 0:
                    logger.info(f"[{account.agw_address}] Decreasing liquidity for {proto_name} #{token_id} (amount: {liq})...")
                    deadline = int(time.time()) + 1800
                    dec_data = pm.encodeABI("decreaseLiquidity", args=[(token_id, liq, 0, 0, deadline)])
                    res = account.send_transaction(to=pm_addr, data=dec_data)
                    logger.success(f"[{account.agw_address}] Liquidity decreased (tx: {res.get('hash')})")
                    sleeping(settings.SLEEP_BETWEEN_ACTIONS)

                # Collect all tokens and fees to AGW account
                tokens_owed0 = p.get("tokens_owed0", 0)
                tokens_owed1 = p.get("tokens_owed1", 0)
                if liq > 0 or tokens_owed0 > 0 or tokens_owed1 > 0:
                    logger.info(f"[{account.agw_address}] Collecting tokens & fees from {proto_name} #{token_id}...")
                    max_uint128 = 2**128 - 1
                    collect_data = pm.encodeABI("collect", args=[(token_id, account.agw_address, max_uint128, max_uint128)])
                    res = account.send_transaction(to=pm_addr, data=collect_data)
                    logger.success(f"[{account.agw_address}] Collected tokens from {proto_name} #{token_id} (tx: {res.get('hash')})")
                    sleeping(settings.SLEEP_BETWEEN_ACTIONS)

            except Exception as e:
                logger.error(f"[{account.agw_address}] Error removing liquidity on {proto_name} #{token_id}: {e}")
                all_ok = False

        return all_ok
