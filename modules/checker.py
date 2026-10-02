import os
import requests
from datetime import datetime
from typing import List, Dict, Any, Tuple
from web3 import Web3
from tabulate import tabulate
from modules.utils import logger
from modules.agw import AgwAccount
import settings

MULTICALL3_ABI = [
    {
        "inputs": [
            {
                "components": [
                    {"name": "target", "type": "address"},
                    {"name": "allowFailure", "type": "bool"},
                    {"name": "callData", "type": "bytes"},
                ],
                "name": "calls",
                "type": "tuple[]",
            }
        ],
        "name": "aggregate3",
        "outputs": [
            {
                "components": [
                    {"name": "success", "type": "bool"},
                    {"name": "returnData", "type": "bytes"},
                ],
                "name": "returnData",
                "type": "tuple[]",
            }
        ],
        "stateMutability": "payable",
        "type": "function",
    }
]

ERC20_BALANCE_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function",
    }
]

POSITION_MANAGER_ABI = [
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
    ], "stateMutability": "view", "type": "function"}
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
    ], "stateMutability": "view", "type": "function"}
]

KONA_PAIR_ABI = [
    {"inputs": [], "name": "token0", "outputs": [{"name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "token1", "outputs": [{"name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "stateMutability": "view", "type": "function"},
]

def get_token_symbol_from_address(addr: str) -> str:
    if not addr:
        return "?"
    addr_l = addr.lower()
    for t in settings.TRACKED_TOKENS:
        if t["address"].lower() == addr_l:
            return t["symbol"]
    return addr[:6] + "..."

class BalanceChecker:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(settings.ABSTRACT_RPC))
        self.multicall = self.w3.eth.contract(
            address=Web3.to_checksum_address(settings.MULTICALL3_ADDRESS),
            abi=MULTICALL3_ABI,
        )

    def scan_account(self, account: AgwAccount) -> Dict[str, Any]:
        """Scans ETH, ERC20 tokens and custom liquidity positions for AGW and EOA."""
        agw_addr = account.agw_address
        eoa_addr = getattr(account, "evm_address", None) or account.signer_address

        agw_eth_wei = self.w3.eth.get_balance(agw_addr)
        eoa_eth_wei = self.w3.eth.get_balance(eoa_addr)

        tracked = list(settings.TRACKED_TOKENS) + list(getattr(settings, "CUSTOM_POOLS", []))
        balance_fn = self.w3.eth.contract(abi=ERC20_BALANCE_ABI)

        # Build multicall for AGW
        calls = []
        for t in tracked:
            target = Web3.to_checksum_address(t["address"])
            calldata = balance_fn.encodeABI(fn_name="balanceOf", args=[agw_addr])
            calls.append({"target": target, "allowFailure": True, "callData": bytes.fromhex(calldata[2:])})

        # Build multicall for EOA
        for t in tracked:
            target = Web3.to_checksum_address(t["address"])
            calldata = balance_fn.encodeABI(fn_name="balanceOf", args=[eoa_addr])
            calls.append({"target": target, "allowFailure": True, "callData": bytes.fromhex(calldata[2:])})

        results = self.multicall.functions.aggregate3(calls).call()
        n = len(tracked)
        agw_results = results[:n]
        eoa_results = results[n:]

        agw_tokens = []
        for i, t in enumerate(tracked):
            success, ret = agw_results[i]
            bal_raw = int.from_bytes(ret, byteorder="big") if success and ret else 0
            decimals = t.get("decimals", 18)
            bal_float = bal_raw / (10 ** decimals)
            agw_tokens.append({
                "symbol": t.get("symbol", t.get("name", "Unknown")),
                "address": Web3.to_checksum_address(t["address"]),
                "decimals": decimals,
                "raw_balance": bal_raw,
                "balance": bal_float,
                "is_weth": t.get("is_weth", False),
            })

        eoa_tokens = []
        for i, t in enumerate(tracked):
            success, ret = eoa_results[i]
            bal_raw = int.from_bytes(ret, byteorder="big") if success and ret else 0
            decimals = t.get("decimals", 18)
            bal_float = bal_raw / (10 ** decimals)
            eoa_tokens.append({
                "symbol": t.get("symbol", t.get("name", "Unknown")),
                "address": Web3.to_checksum_address(t["address"]),
                "decimals": decimals,
                "raw_balance": bal_raw,
                "balance": bal_float,
                "is_weth": t.get("is_weth", False),
            })



        # Scan liquidity in DEX protocols (Aborean, KONA, Sakura Swap)
        # Scan liquidity in DEX protocols (Aborean, KONA CLMM, Sakura Swap)
        agw_liquidity = []
        for proto in getattr(settings, "LIQUIDITY_PROTOCOLS", []):
            try:
                pm_contract = self.w3.eth.contract(address=Web3.to_checksum_address(proto["position_manager"]), abi=POSITION_MANAGER_ABI)
                count = pm_contract.functions.balanceOf(agw_addr).call()
                if count > 0:
                    for i in range(count):
                        tid = pm_contract.functions.tokenOfOwnerByIndex(agw_addr, i).call()
                        pos = pm_contract.functions.positions(tid).call()
                        liq = pos[7]
                        agw_liquidity.append({
                            "protocol": proto["name"],
                            "token_id": tid,
                            "liquidity": liq,
                            "token0": pos[2],
                            "token1": pos[3],
                        })
            except Exception:
                pass

        # Scan Kona Farm stakes
        kona_farm_addr = getattr(settings, "KONA_FARM_ADDRESS", None)
        if kona_farm_addr:
            try:
                farm_c = self.w3.eth.contract(address=Web3.to_checksum_address(kona_farm_addr), abi=KONA_FARM_ABI)
                total_farms = farm_c.functions.getFarmsLength().call()
                calls = []
                for fid in range(total_farms):
                    cd = farm_c.encodeABI("userInfo", args=[agw_addr, fid])
                    calls.append({"target": Web3.to_checksum_address(kona_farm_addr), "allowFailure": True, "callData": bytes.fromhex(cd[2:])})

                res = self.multicall.functions.aggregate3(calls).call()
                for fid, r in enumerate(res):
                    if r[0] and len(r[1]) >= 32:
                        staked_amt = int.from_bytes(r[1][:32], "big")
                        if staked_amt > 1000:
                            f_info = farm_c.functions.farms(fid).call()
                            lp_addr = f_info[0]
                            pair_c = self.w3.eth.contract(address=Web3.to_checksum_address(lp_addr), abi=KONA_PAIR_ABI)
                            try:
                                t0 = pair_c.functions.token0().call()
                                t1 = pair_c.functions.token1().call()
                                pair_label = f"{get_token_symbol_from_address(t0)}-{get_token_symbol_from_address(t1)}"
                            except Exception:
                                t0, t1, pair_label = None, None, "LP"

                            agw_liquidity.append({
                                "protocol": "Kona Farm",
                                "farm_id": fid,
                                "lp_token": lp_addr,
                                "liquidity": staked_amt,
                                "formatted_lp": staked_amt / 1e18,
                                "pair_label": pair_label,
                                "token0": t0,
                                "token1": t1,
                                "is_farm": True,
                            })
            except Exception:
                pass

        # Scan Upvote Streak on portal.abs.xyz
        vote_streak = 0
        voted_today = False
        try:
            r = requests.get(f"https://backend.portal.abs.xyz/api/user/{agw_addr}/vote-streak", timeout=5)
            if r.status_code == 200:
                s_data = r.json()
                vote_streak = s_data.get("currentStreakDays", 0)
                voted_today = s_data.get("votedToday", False)
        except Exception:
            pass

        return {
            "account_id": getattr(account, "account_id", None),
            "agw_address": agw_addr,
            "eoa_address": eoa_addr,
            "is_deployed": account.is_deployed,
            "is_agw": account.is_agw,
            "agw_eth_wei": agw_eth_wei,
            "agw_eth": agw_eth_wei / 1e18,
            "eoa_eth_wei": eoa_eth_wei,
            "eoa_eth": eoa_eth_wei / 1e18,
            "agw_tokens": agw_tokens,
            "eoa_tokens": eoa_tokens,
            "agw_liquidity": agw_liquidity,
            "vote_streak": vote_streak,
            "voted_today": voted_today,
        }

    def print_scan_report(self, scans: List[Dict[str, Any]]) -> None:
        table_data = []
        total_agw_eth = 0.0
        total_eoa_eth = 0.0
        total_tokens: Dict[str, float] = {}

        for idx, scan in enumerate(scans, 1):
            acc_num = f"{scan['account_id']}" if scan.get("account_id") else f"{idx}"
            agw = f"{scan['agw_address'][:6]}...{scan['agw_address'][-4:]}"
            if not scan.get("is_deployed", True):
                agw += "\n(not deployed)"
            eoa = f"{scan['eoa_address'][:6]}...{scan['eoa_address'][-4:]}"
            agw_eth = f"{scan['agw_eth']:.5f}"
            eoa_eth = f"{scan['eoa_eth']:.5f}"
            total_agw_eth += scan["agw_eth"]
            total_eoa_eth += scan["eoa_eth"]

            # Filter tokens with non-zero balance on AGW
            active_tokens = []
            for t in scan["agw_tokens"]:
                bal = t["balance"]
                if t["raw_balance"] > 0 and bal >= 0.000001:
                    sym = t["symbol"]
                    if bal < 0.001:
                        active_tokens.append(f"{sym}: {bal:.6f}")
                    else:
                        active_tokens.append(f"{sym}: {bal:.4f}")
                    total_tokens[sym] = total_tokens.get(sym, 0.0) + bal

            tokens_str = "\n".join(active_tokens) if active_tokens else "-"

            # Format liquidity positions (Aborean, KONA, Sakura Swap, Kona Farm)
            liq_positions = scan.get("agw_liquidity", [])
            liq_list = []
            if liq_positions:
                for p in liq_positions:
                    if p.get("is_farm"):
                        liq_list.append(f"Kona Farm #{p['farm_id']} {p.get('pair_label', 'LP')} ({p['formatted_lp']:.8f} LP)")
                    else:
                        status = f"Liq: {p['liquidity']}" if p["liquidity"] > 0 else "Empty"
                        liq_list.append(f"{p['protocol']} #{p['token_id']} ({status})")
            liq_str = "\n".join(liq_list) if liq_list else "-"

            # Format streak string
            streak_icon = "✅" if scan.get("voted_today") else "❌"
            streak_str = f"{scan.get('vote_streak', 0)}d {streak_icon}"

            table_data.append([
                acc_num,
                agw,
                eoa,
                agw_eth,
                eoa_eth,
                tokens_str,
                liq_str,
                streak_str,
            ])

        headers = [
            "#",
            "AGW Address",
            "Signer",
            "AGW ETH",
            "EOA ETH",
            "Tokens (AGW)",
            "Liquidity (DEX)",
            "Streak",
        ]

        table_str = tabulate(table_data, headers=headers, tablefmt="grid")
        summary_lines = [
            f"Total Accounts: {len(scans)}",
            f"Total AGW ETH:  {total_agw_eth:.5f} ETH",
        ]
        if total_tokens:
            tok_summary = " | ".join([
                f"{sym}: {bal:.6f}" if bal < 0.001 else f"{sym}: {bal:.4f}"
                for sym, bal in total_tokens.items()
            ])
            summary_lines.append(f"Total Tokens:   {tok_summary}")

        print("\n" + "=" * 90)
        print("                        [SCAN REPORT] ABSTRACT (AGW) ACCOUNTS")
        print("=" * 90)
        print(table_str)
        print("-" * 90)
        for line in summary_lines:
            print(f"  {line}")
        print("=" * 90 + "\n")

        # Save copy to logs/last_scan_report.txt
        try:
            os.makedirs("logs", exist_ok=True)
            with open("logs/last_scan_report.txt", "w", encoding="utf-8") as f:
                f.write(f"SCAN REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(table_str + "\n\n")
                for line in summary_lines:
                    f.write(line + "\n")
        except Exception:
            pass

        # Export formatted Excel report (.xlsx)
        try:
            from modules.excel import save_scan_report_to_excel
            excel_path = save_scan_report_to_excel(scans)
            logger.success(f"📊 Звіт успішно експортовано в Excel: {excel_path}")
        except Exception as e:
            logger.warning(f"Не вдалося експортувати звіт в Excel: {e}")
