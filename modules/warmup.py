import time
import random
import requests
from typing import Dict, Any, List, Optional
from web3 import Web3

from modules.utils import logger, sleeping
from modules.agw import AgwAccount
from modules.swapper import TokenSwapper
import settings

# ERC20 minimal ABI for balance & approve
ERC20_ABI = [
    {"inputs": [{"name": "account", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}], "name": "approve", "outputs": [{"name": "", "type": "bool"}], "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [{"name": "owner", "type": "address"}, {"name": "spender", "type": "address"}], "name": "allowance", "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "stateMutability": "view", "type": "function"},
]

# V2 Pair & Router & Factory ABIs
V2_PAIR_ABI = [
    {"inputs": [], "name": "getReserves", "outputs": [{"name": "_reserve0", "type": "uint112"}, {"name": "_reserve1", "type": "uint112"}, {"name": "_blockTimestampLast", "type": "uint32"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "token0", "outputs": [{"name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "token1", "outputs": [{"name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
]

V2_FACTORY_ABI = [
    {"inputs": [{"name": "tokenA", "type": "address"}, {"name": "tokenB", "type": "address"}], "name": "getPair", "outputs": [{"name": "pair", "type": "address"}], "stateMutability": "view", "type": "function"},
]

V2_ROUTER_ABI = [
    {"inputs": [], "name": "factory", "outputs": [{"name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
    {"inputs": [
        {"name": "token", "type": "address"},
        {"name": "amountTokenDesired", "type": "uint256"},
        {"name": "amountTokenMin", "type": "uint256"},
        {"name": "amountETHMin", "type": "uint256"},
        {"name": "to", "type": "address"},
        {"name": "deadline", "type": "uint256"}
    ], "name": "addLiquidityETH", "outputs": [
        {"name": "amountToken", "type": "uint256"},
        {"name": "amountETH", "type": "uint256"},
        {"name": "liquidity", "type": "uint256"}
    ], "stateMutability": "payable", "type": "function"}
]

# Kona Farm Staking ABI
KONA_FARM_ABI = [
    {"inputs": [{"name": "farmId", "type": "uint256"}, {"name": "amount", "type": "uint256"}], "name": "stake", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [{"name": "", "type": "uint256"}], "name": "farms", "outputs": [
        {"name": "lpToken", "type": "address"},
        {"name": "allocPoint", "type": "uint256"},
        {"name": "lastRewardBlock", "type": "uint256"},
        {"name": "accPointsPerShare", "type": "uint256"},
        {"name": "isStarted", "type": "bool"},
        {"name": "minStakeAmount", "type": "uint256"},
        {"name": "isActive", "type": "bool"}
    ], "stateMutability": "view", "type": "function"}
]

# Popular Kona V2 LP pairs with their farm IDs
KONA_FARMS_INFO = {
    "USDC": {
        "farm_id": 4,
        "pair_address": "0x196Cc070Ec0cAd11fC2e7Bdec180138dF6aa4A62", # WETH-USDC
    },
    "0x84A71ccD554Cc1b02749b35d22F684CC8ec987e1": {
        "farm_id": 4,
        "pair_address": "0x196Cc070Ec0cAd11fC2e7Bdec180138dF6aa4A62",
    },
    "gtBTC": {
        "farm_id": 26,
        "pair_address": "0x1a506c4A525d66bF62Cf74B1202DD6Bf7fAE970f", # gtBTC-WETH
    },
    "0x0035b877C3aB50cFFA9eD52bA05282c7045f78dd": {
        "farm_id": 26,
        "pair_address": "0x1a506c4A525d66bF62Cf74B1202DD6Bf7fAE970f",
    },
}

WETH_ADDRESS = "0x3439153EB7AF838Ad19d56E1571FBD09333C2809"

class WarmupEngine:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(settings.ABSTRACT_RPC))
        self.swapper = TokenSwapper()
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Content-Type": "application/json",
        })

    def get_token_info(self, identifier: str) -> Optional[Dict[str, Any]]:
        """Finds token by symbol or address; fetches ERC20 data if unknown address."""
        # 1. Search in TRACKED_TOKENS
        for t in settings.TRACKED_TOKENS:
            if identifier.lower() in [t["symbol"].lower(), t["address"].lower()]:
                return dict(t)

        # 2. If it's a valid hex address, query on-chain metadata
        if Web3.is_address(identifier):
            try:
                checksum_addr = Web3.to_checksum_address(identifier)
                c = self.w3.eth.contract(address=checksum_addr, abi=ERC20_ABI)
                sym = c.functions.symbol().call()
                dec = c.functions.decimals().call()
                return {
                    "symbol": sym,
                    "name": sym,
                    "address": checksum_addr,
                    "decimals": dec,
                    "is_weth": False,
                }
            except Exception as e:
                logger.error(f"Failed to fetch on-chain metadata for token {identifier}: {e}")

        return None

    def check_and_prepare_eth(self, account: AgwAccount) -> bool:
        """Ensures AGW has sufficient ETH; if not, deposits from EOA if possible."""
        agw_addr = account.agw_address
        current_agw_bal = self.w3.eth.get_balance(agw_addr)
        min_required = getattr(settings, "MIN_REQUIRED_AGW_ETH", 0.002)
        min_required_wei = int(min_required * 1e18)

        if current_agw_bal >= min_required_wei:
            logger.info(f"[{agw_addr[:8]}...] AGW balance {current_agw_bal / 1e18:.5f} ETH is sufficient (>= {min_required} ETH).")
            return True

        # Needs deposit from EOA
        logger.info(f"[{agw_addr[:8]}...] AGW balance ({current_agw_bal / 1e18:.5f} ETH) is below required {min_required} ETH. Checking EOA...")
        if not getattr(account, "evm_private_key", None):
            logger.error(f"[{agw_addr[:8]}...] No EVM private key provided for deposit. Skipping.")
            return False

        eoa_addr = account.evm_address or account.signer_address
        eoa_bal = self.w3.eth.get_balance(eoa_addr)

        dep_range = getattr(settings, "DEPOSIT_ETH_RANGE", [0.003, 0.006])
        dep_eth = round(random.uniform(dep_range[0], dep_range[1]), 6)
        dep_wei = int(dep_eth * 1e18)
        gas_eoa_reserve = int(0.00015 * 1e18)

        if eoa_bal < dep_wei + gas_eoa_reserve:
            logger.error(
                f"[{agw_addr[:8]}...] ❌ Insufficient balance on both AGW ({current_agw_bal / 1e18:.5f} ETH) "
                f"and EOA ({eoa_bal / 1e18:.5f} ETH). Need at least {dep_eth:.5f} ETH. Skipping."
            )
            return False

        logger.info(f"[{agw_addr[:8]}...] Depositing {dep_eth:.5f} ETH from EOA ({eoa_addr[:8]}...) -> AGW...")
        try:
            res = account.transfer_eoa_eth(to=agw_addr, amount_wei=dep_wei)
            logger.success(f"[{agw_addr[:8]}...] ✅ Deposit confirmed: {settings.EXPLORER_TX_URL}{res.get('hash')}")
            sleeping(settings.SLEEP_BETWEEN_ACTIONS)
            return True
        except Exception as e:
            logger.error(f"[{agw_addr[:8]}...] ❌ Error depositing from EOA: {e}")
            return False

    def swap_eth_to_token(self, account: AgwAccount, token: Dict[str, Any], eth_wei: int) -> bool:
        """Swaps ETH to the target token via Relay aggregator."""
        symbol = token["symbol"]
        agw_addr = account.agw_address
        logger.info(f"[{agw_addr[:8]}...] Swapping {eth_wei / 1e18:.5f} ETH -> {symbol}...")

        payload = {
            "user": agw_addr,
            "originChainId": settings.CHAIN_ID,
            "destinationChainId": settings.CHAIN_ID,
            "originCurrency": "0x0000000000000000000000000000000000000000",
            "destinationCurrency": token["address"],
            "amount": str(eth_wei),
            "tradeType": "EXACT_INPUT",
        }

        try:
            resp = self.session.post("https://api.relay.link/quote", json=payload, timeout=20)
            if resp.status_code != 200:
                logger.error(f"[{agw_addr[:8]}...] Relay API error ({resp.status_code}): {resp.text[:200]}")
                return False

            quote = resp.json()
            steps = quote.get("steps", [])
            if not steps:
                logger.warning(f"[{agw_addr[:8]}...] No swap route available for ETH -> {symbol}")
                return False

            out_amount = quote.get("details", {}).get("currencyOut", {}).get("amountFormatted", "?")
            logger.info(f"[{agw_addr[:8]}...] Route found: ~{out_amount} {symbol}. Executing {len(steps)} step(s)...")

            for step in steps:
                for item in step.get("items", []):
                    tx_data = item.get("data", {})
                    to_addr = tx_data.get("to")
                    calldata = tx_data.get("data", "0x")
                    val = int(tx_data.get("value", 0))

                    if not to_addr:
                        continue

                    logger.info(f"[{agw_addr[:8]}...] Executing step: {step.get('description', step.get('id', 'action'))}...")
                    res = account.send_transaction(to=to_addr, data=calldata, value=val)
                    logger.success(f"[{agw_addr[:8]}...] ✅ Tx confirmed: {settings.EXPLORER_TX_URL}{res.get('hash')}")
                    sleeping(settings.SLEEP_BETWEEN_ACTIONS)

            logger.success(f"[{agw_addr[:8]}...] ✅ Successfully swapped ETH -> {symbol}!")
            return True

        except Exception as e:
            logger.error(f"[{agw_addr[:8]}...] ❌ Swap ETH -> {symbol} failed: {e}")
            return False

    def create_kona_lp(self, account: AgwAccount, token: Dict[str, Any]) -> bool:
        """Adds liquidity to Kona V2 pair (WETH - Token) using current token balance."""
        agw_addr = account.agw_address
        token_addr = Web3.to_checksum_address(token["address"])
        symbol = token["symbol"]
        router_addr = Web3.to_checksum_address(settings.KONA_V2_ROUTER_ADDRESS)

        token_c = self.w3.eth.contract(address=token_addr, abi=ERC20_ABI)
        token_bal = token_c.functions.balanceOf(agw_addr).call()
        if token_bal == 0:
            logger.warning(f"[{agw_addr[:8]}...] Zero {symbol} balance, cannot create LP.")
            return False

        # Get pair address: either from KONA_FARMS_INFO or dynamically from Router Factory
        farm_info = KONA_FARMS_INFO.get(symbol) or KONA_FARMS_INFO.get(token_addr)
        pair_addr = None
        if farm_info:
            pair_addr = Web3.to_checksum_address(farm_info["pair_address"])
        else:
            try:
                router_c = self.w3.eth.contract(address=router_addr, abi=V2_ROUTER_ABI)
                factory_addr = router_c.functions.factory().call()
                factory_c = self.w3.eth.contract(address=factory_addr, abi=V2_FACTORY_ABI)
                pair_addr = factory_c.functions.getPair(token_addr, Web3.to_checksum_address(WETH_ADDRESS)).call()
                if not pair_addr or pair_addr == "0x0000000000000000000000000000000000000000":
                    pair_addr = None
            except Exception as e:
                logger.error(f"[{agw_addr[:8]}...] Error looking up Kona pair for {symbol}: {e}")

        if not pair_addr:
            logger.warning(f"[{agw_addr[:8]}...] No known Kona V2 pair for {symbol}. Skipping LP creation.")
            return False

        pair_c = self.w3.eth.contract(address=pair_addr, abi=V2_PAIR_ABI)
        reserves = pair_c.functions.getReserves().call()
        t0 = pair_c.functions.token0().call()

        weth_addr = Web3.to_checksum_address(WETH_ADDRESS)
        if t0.lower() == weth_addr.lower():
            weth_res, token_res = reserves[0], reserves[1]
        else:
            weth_res, token_res = reserves[1], reserves[0]

        if token_res == 0:
            logger.error(f"[{agw_addr[:8]}...] Empty pool reserves. Skipping.")
            return False

        # Quote required ETH: (token_bal * weth_res) / token_res
        eth_needed_wei = (token_bal * weth_res) // token_res
        agw_eth_bal = self.w3.eth.get_balance(agw_addr)
        gas_safety = int(0.0003 * 1e18)

        if agw_eth_bal < eth_needed_wei + gas_safety:
            # Scale down token_bal to fit available ETH
            available_eth = max(0, agw_eth_bal - gas_safety)
            if available_eth < int(0.0003 * 1e18):
                logger.error(f"[{agw_addr[:8]}...] Insufficient ETH for LP pair. Need {eth_needed_wei / 1e18:.5f} ETH, have {agw_eth_bal / 1e18:.5f} ETH.")
                return False
            eth_needed_wei = available_eth
            token_bal = (eth_needed_wei * token_res) // weth_res

        logger.info(
            f"[{agw_addr[:8]}...] Adding Kona V2 Liquidity: {token_bal / (10**token['decimals']):.4f} {symbol} "
            f"+ {eth_needed_wei / 1e18:.5f} ETH..."
        )

        try:
            # 1. Approve token on Kona Router
            allowance = token_c.functions.allowance(agw_addr, router_addr).call()
            if allowance < token_bal:
                logger.info(f"[{agw_addr[:8]}...] Approving {symbol} on Kona Router...")
                app_data = token_c.encodeABI("approve", args=[router_addr, 2**256 - 1])
                res_app = account.send_transaction(to=token_addr, data=app_data)
                logger.success(f"[{agw_addr[:8]}...] ✅ {symbol} approved (tx: {res_app.get('hash')})")
                sleeping(settings.SLEEP_BETWEEN_ACTIONS)

            # 2. Call addLiquidityETH
            router_c = self.w3.eth.contract(address=router_addr, abi=V2_ROUTER_ABI)
            deadline = int(time.time()) + 1800
            token_min = int(token_bal * 0.95) # 5% slippage
            eth_min = int(eth_needed_wei * 0.95)

            add_data = router_c.encodeABI("addLiquidityETH", args=[
                token_addr,
                token_bal,
                token_min,
                eth_min,
                agw_addr,
                deadline
            ])

            res_add = account.send_transaction(to=router_addr, data=add_data, value=eth_needed_wei)
            logger.success(f"[{agw_addr[:8]}...] ✅ LP added successfully: {settings.EXPLORER_TX_URL}{res_add.get('hash')}")
            sleeping(settings.SLEEP_BETWEEN_ACTIONS)
            return True

        except Exception as e:
            logger.error(f"[{agw_addr[:8]}...] ❌ Error adding liquidity to Kona V2: {e}")
            return False

    def stake_in_kona_farm(self, account: AgwAccount, token: Dict[str, Any]) -> bool:
        """Stakes LP tokens into Kona Farm."""
        agw_addr = account.agw_address
        symbol = token["symbol"]
        token_addr = Web3.to_checksum_address(token["address"])
        farm_info = KONA_FARMS_INFO.get(symbol) or KONA_FARMS_INFO.get(token_addr)
        if not farm_info or "farm_id" not in farm_info:
            logger.warning(f"[{agw_addr[:8]}...] No known Kona Farm ID configured for {symbol}. Skipping farm staking.")
            return False

        farm_id = farm_info["farm_id"]
        pair_addr = Web3.to_checksum_address(farm_info["pair_address"])
        farm_addr = Web3.to_checksum_address(settings.KONA_FARM_ADDRESS)

        lp_c = self.w3.eth.contract(address=pair_addr, abi=ERC20_ABI)
        lp_bal = lp_c.functions.balanceOf(agw_addr).call()

        if lp_bal == 0:
            logger.warning(f"[{agw_addr[:8]}...] No LP tokens found to stake into Kona Farm #{farm_id}.")
            return False

        logger.info(f"[{agw_addr[:8]}...] Staking {lp_bal / 1e18:.8f} LP into Kona Farm #{farm_id}...")

        try:
            # Approve Farm contract
            allowance = lp_c.functions.allowance(agw_addr, farm_addr).call()
            if allowance < lp_bal:
                logger.info(f"[{agw_addr[:8]}...] Approving LP for Kona Farm...")
                app_data = lp_c.encodeABI("approve", args=[farm_addr, 2**256 - 1])
                res_app = account.send_transaction(to=pair_addr, data=app_data)
                logger.success(f"[{agw_addr[:8]}...] ✅ LP approved (tx: {res_app.get('hash')})")
                sleeping(settings.SLEEP_BETWEEN_ACTIONS)

            # Stake
            farm_c = self.w3.eth.contract(address=farm_addr, abi=KONA_FARM_ABI)
            stake_data = farm_c.encodeABI("stake", args=[farm_id, lp_bal])
            res_stake = account.send_transaction(to=farm_addr, data=stake_data)
            logger.success(f"[{agw_addr[:8]}...] ✅ Staked into Kona Farm #{farm_id} (tx: {settings.EXPLORER_TX_URL}{res_stake.get('hash')})")
            sleeping(settings.SLEEP_BETWEEN_ACTIONS)
            return True

        except Exception as e:
            logger.error(f"[{agw_addr[:8]}...] ❌ Error staking into Kona Farm #{farm_id}: {e}")
            return False

    def run_warmup_for_account(self, account: AgwAccount) -> bool:
        """Executes warmup strategy for an account based on settings or random selection."""
        agw_addr = account.agw_address

        # 1. Check AGW balance & prepare ETH (deposit from EOA if needed)
        if not self.check_and_prepare_eth(account):
            return False

        # Determine Scenario / Actions
        mode = getattr(settings, "WARMUP_MODE", "RANDOM").upper()
        if mode == "RANDOM":
            # Random selection:
            # 1) SWAP_ONLY: Swap ETH -> Token -> ETH (35%)
            # 2) SWAP_AND_LP: Swap ETH -> Token + Create LP (35%)
            # 3) FULL_FARM: Swap ETH -> Token + Create LP + Stake into Kona Farm (30%)
            scenario_name = random.choices(["SWAP_ONLY", "SWAP_AND_LP", "FULL_FARM"], weights=[35, 35, 30], k=1)[0]
            do_swap = True
            if scenario_name == "SWAP_ONLY":
                do_swap_back = True
                do_create_lp = False
                do_stake_farm = False
            elif scenario_name == "SWAP_AND_LP":
                do_swap_back = False
                do_create_lp = True
                do_stake_farm = False
            else: # FULL_FARM
                do_swap_back = False
                do_create_lp = True
                do_stake_farm = True
        else:
            scenario_name = "CUSTOM"
            do_swap = getattr(settings, "DO_SWAP", True)
            do_swap_back = getattr(settings, "SWAP_BACK", True)
            do_create_lp = getattr(settings, "CREATE_LP", False)
            do_stake_farm = getattr(settings, "STAKE_FARM", False)

        logger.info(
            f"[{agw_addr[:8]}...] 🎯 Scenario: {scenario_name} "
            f"(Swap: {do_swap}, SwapBack: {do_swap_back}, CreateLP: {do_create_lp}, StakeFarm: {do_stake_farm})"
        )

        # Choose token from WARMUP_TOKENS (symbols or contract addresses)
        token_identifiers = getattr(settings, "WARMUP_TOKENS", ["USDC", "gtBTC"])
        if not token_identifiers:
            logger.error(f"[{agw_addr[:8]}...] WARMUP_TOKENS list is empty in settings.")
            return False

        chosen_ident = random.choice(token_identifiers)
        chosen_token = self.get_token_info(chosen_ident)

        if not chosen_token:
            logger.error(f"[{agw_addr[:8]}...] Could not resolve token '{chosen_ident}'. Skipping.")
            return False

        chosen_symbol = chosen_token["symbol"]

        # Calculate swap amount if swap is enabled
        if do_swap:
            cur_eth = self.w3.eth.get_balance(agw_addr)
            gas_res = int(0.00035 * 1e18)
            avail_eth = max(0, cur_eth - gas_res)
            if avail_eth <= int(0.0005 * 1e18):
                logger.warning(f"[{agw_addr[:8]}...] Insufficient available ETH for swap warmup.")
                return False

            pct_range = getattr(settings, "WARMUP_SWAP_PERCENT", [25, 40])
            swap_pct = random.uniform(pct_range[0], pct_range[1]) / 100.0
            swap_wei = int(avail_eth * swap_pct)

            # Swap ETH -> Token
            success_swap = self.swap_eth_to_token(account, chosen_token, swap_wei)
            if not success_swap:
                return False

            sleeping(settings.SLEEP_BETWEEN_ACTIONS)

        # Handle Create LP / Stake Farm / Swap Back
        if do_create_lp:
            ok_lp = self.create_kona_lp(account, chosen_token)
            if ok_lp and do_stake_farm:
                sleeping(settings.SLEEP_BETWEEN_ACTIONS)
                self.stake_in_kona_farm(account, chosen_token)

        elif do_swap_back:
            token_c = self.w3.eth.contract(address=Web3.to_checksum_address(chosen_token["address"]), abi=ERC20_ABI)
            cur_tok_bal = token_c.functions.balanceOf(agw_addr).call()
            if cur_tok_bal > 0:
                token_dict = dict(chosen_token)
                token_dict["raw_balance"] = cur_tok_bal
                logger.info(f"[{agw_addr[:8]}...] Swapping {chosen_symbol} back to ETH...")
                self.swapper.swap_token_to_eth(account, token_dict)

        logger.success(f"[{agw_addr[:8]}...] 🌟 Warmup completed successfully for {scenario_name}!")
        return True
