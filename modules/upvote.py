import time
import random
import requests
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from web3 import Web3

from modules.utils import logger, sleeping
from modules.agw import AgwAccount
import settings

UPVOTE_ABI = [
    {
        "inputs": [{"name": "appId", "type": "uint256"}],
        "name": "voteForApp",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function",
    }
]

# Top 10 verified and active portal apps mapping for clear logging
KNOWN_APPS = {
    179: "Kona",
    1: "Abstract",
    225: "DEPTH Protocol",
    2: "Onchain Heroes",
    3: "Gigaverse",
    168: "COSMO (MODHAUS)",
    220: "Amigo",
    207: "Tollan Universe",
    7: "Moody Madness",
    6: "Cambria",
    16: "Duper",
}

class UpvoteManager:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(settings.ABSTRACT_RPC))
        self.contract_address = Web3.to_checksum_address(
            getattr(settings, "UPVOTE_CONTRACT_ADDRESS", "0x3B50dE27506f0a8C1f4122A1e6F470009a76ce2A")
        )
        self.contract = self.w3.eth.contract(address=self.contract_address, abi=UPVOTE_ABI)
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Origin": "https://portal.abs.xyz",
            "Referer": "https://portal.abs.xyz/",
        })

    def get_vote_streak(self, agw_address: str, proxy: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Queries the official portal API for vote streak data."""
        url = f"https://backend.portal.abs.xyz/api/user/{agw_address}/vote-streak"
        proxies = {"http": proxy, "https": proxy} if proxy else None
        try:
            resp = self.session.get(url, timeout=10, proxies=proxies)
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            logger.warning(f"[{agw_address[:8]}...] Could not fetch vote streak from API: {e}")
        return None

    def upvote_account(self, account: AgwAccount, target_app_id: Optional[int] = None) -> bool:
        """Checks status and executes upvote on-chain if not already voted today."""
        agw_addr = account.agw_address
        proxy = getattr(account, "proxy", None)

        # 1. Check current streak status from portal API
        streak_data = self.get_vote_streak(agw_addr, proxy=proxy)
        if streak_data:
            current_streak = streak_data.get("currentStreakDays", 0)
            voted_today = streak_data.get("votedToday", False)
            if voted_today:
                logger.success(
                    f"[{agw_addr[:8]}...] ⭐ Already upvoted today! Current Streak: {current_streak} day(s)."
                )
                return True
            else:
                logger.info(
                    f"[{agw_addr[:8]}...] Upvote needed today. Current Streak: {current_streak} day(s)."
                )
        else:
            logger.info(f"[{agw_addr[:8]}...] Checking on-chain upvote...")

        # 2. Pick app ID to upvote
        app_candidates = getattr(settings, "UPVOTE_APP_IDS", [179, 183, 1, 225, 2, 3])
        app_id = target_app_id if target_app_id is not None else random.choice(app_candidates)
        app_name = KNOWN_APPS.get(app_id, f"App #{app_id}")

        logger.info(f"[{agw_addr[:8]}...] Voting for '{app_name}' (ID: {app_id})...")

        try:
            calldata = self.contract.encodeABI("voteForApp", args=[app_id])
            res = account.send_transaction(to=self.contract_address, data=calldata, value=0)
            tx_hash = res.get("hash", "")
            logger.success(
                f"[{agw_addr[:8]}...] ✅ Upvote tx confirmed: {settings.EXPLORER_TX_URL}{tx_hash}"
            )

            # Wait a few seconds for indexer and check new streak
            time.sleep(3)
            new_streak_data = self.get_vote_streak(agw_addr, proxy=proxy)
            if new_streak_data:
                new_streak = new_streak_data.get("currentStreakDays", 0)
                logger.success(
                    f"[{agw_addr[:8]}...] 🎉 Upvote successfully recorded! New Streak: {new_streak} day(s)!"
                )
            return True

        except Exception as e:
            err_str = str(e)
            if "AlreadyVotedFor" in err_str or "UsedAllVotes" in err_str:
                logger.info(f"[{agw_addr[:8]}...] Already voted today according to smart contract.")
                return True
            logger.error(f"[{agw_addr[:8]}...] ❌ Error during upvote: {e}")
            return False

    def get_seconds_until_next_day(self, agw_address: str) -> int:
        """Calculates seconds until the next upvote reset window (from nextVoteBy API field)."""
        data = self.get_vote_streak(agw_address)
        if data and data.get("nextVoteBy"):
            try:
                target_iso = data["nextVoteBy"].replace("Z", "+00:00")
                target_dt = datetime.fromisoformat(target_iso)
                now_dt = datetime.now(timezone.utc)
                diff = int((target_dt - now_dt).total_seconds())
                if diff > 0:
                    # Add small random buffer (3 to 7 mins) so indexer and epoch roll over cleanly
                    buffer_sec = random.randint(180, 420)
                    return diff + buffer_sec
            except Exception as e:
                logger.warning(f"Could not parse nextVoteBy timestamp: {e}")

        # Fallback if API unavailable: 4 hours
        return 4 * 3600

    def sleep_until_next_round(self, total_seconds: int) -> None:
        """Sleeps with human-readable countdown updates until the next daily upvote round."""
        target_timestamp = time.time() + total_seconds
        target_dt = datetime.now() + timedelta(seconds=total_seconds)
        logger.info(f"⏳ Sleeping until next voting round: target time is ~{target_dt.strftime('%H:%M:%S')} (Press Ctrl+C to stop)...")

        last_logged = 0
        while time.time() < target_timestamp:
            remaining = int(target_timestamp - time.time())
            if remaining <= 0:
                break

            # Log every 30 minutes, or when under 5 minutes
            if time.time() - last_logged >= 1800 or (remaining <= 300 and time.time() - last_logged >= 60):
                hours = remaining // 3600
                minutes = (remaining % 3600) // 60
                secs = remaining % 60
                logger.info(f"⏳ Upvote round sleep countdown: {hours:02d}h {minutes:02d}m {secs:02d}s remaining...")
                last_logged = time.time()

            sleep_step = min(10, remaining)
            time.sleep(sleep_step)

        logger.info("🔔 New voting window is now open! Starting next upvote cycle...")
