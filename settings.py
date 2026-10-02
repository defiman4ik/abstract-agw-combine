# ==============================================================================
#                      ABSTRACT (AGW) COMBINE SETTINGS
# ==============================================================================

# RPC Configuration
ABSTRACT_RPC = "https://api.mainnet.abs.xyz"
CHAIN_ID = 2741
EXPLORER_TX_URL = "https://abscan.org/tx/"

# Multicall3 contract on Abstract Mainnet
MULTICALL3_ADDRESS = "0xF9cDA624FBC7e059355ce98a31693d299FACd963"

# Gas & Safety Reserve (ETH to leave on account for tx fees)
# Can be a fixed number (e.g. 0.005) or a randomized range [min, max]
GAS_RESERVE_ETH = [0.007, 0.015]

# Minimum token balance USD value to swap (avoids wasting gas on negligible dust)
MIN_SWAP_VALUE_USD = 0.05

# Slippage tolerance in percentage (e.g. 1.0 = 1%)
SLIPPAGE_PERCENT = 1.0

# Random delays in seconds [min, max]
SLEEP_BETWEEN_ACTIONS = [10, 20]            # pause between actions within single account (e.g. swap -> withdraw)
SLEEP_BETWEEN_ACCOUNTS = [600, 1800]         # pause between different accounts for transactions [min, max]
SLEEP_BETWEEN_ACCOUNTS_SCAN = [20, 30]       # fast pause between accounts in Mode 1 (balance scanner) [min, max]

# Interface language: "EN" (English - Default) | "UA" (Ukrainian) | "RU" (Russian)
LANGUAGE = "EN"

# Proxy usage toggle: True = use proxies from proxies.txt, False = direct connection
USE_PROXIES = True

# Shuffle account order for transaction modes (Scan mode always runs sequentially 1..N)
SHUFFLE_ACCOUNTS = True

# Recipient Mode for ETH withdrawal:
# "SAME_AS_EOA" -> Withdraws ETH to the account's own EVM signer address
# "FROM_FILE"   -> Reads 1-to-1 matching recipient addresses from recipients.txt
RECIPIENT_MODE = "SAME_AS_EOA"

# ==============================================================================
#               ECOSYSTEM CONFIG (TOKENS, CONTRACTS, PROTOCOLS)
# ==============================================================================
from config import (
    TRACKED_TOKENS,
    CUSTOM_POOLS,
    LIQUIDITY_PROTOCOLS,
    KONA_FARM_ADDRESS,
    KONA_V2_ROUTER_ADDRESS,
    MULTICALL3_ADDRESS,
)
