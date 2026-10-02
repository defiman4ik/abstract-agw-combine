# ==============================================================================
#                      ABSTRACT (AGW) MANAGER SETTINGS
# ==============================================================================

# RPC Configuration
ABSTRACT_RPC = "https://api.mainnet.abs.xyz"
CHAIN_ID = 2741
EXPLORER_TX_URL = "https://abscan.org/tx/"

# Multicall3 contract on Abstract Mainnet
MULTICALL3_ADDRESS = "0xF9cDA624FBC7e059355ce98a31693d299FACd963"

# Gas & Safety Reserve (ETH to leave on account for tx fees)
# Можна вказати фіксоване число (наприклад, 0.00025) або діапазон для рандомізації [мін, макс]
GAS_RESERVE_ETH = [0.007, 0.015]

# Minimum token balance USD value to swap (avoids wasting gas on negligible dust)
MIN_SWAP_VALUE_USD = 0.05

# Slippage tolerance in percentage (e.g. 1.0 = 1%)
SLIPPAGE_PERCENT = 1.0

# Рандомні паузи в секундах [min, max]
SLEEP_BETWEEN_ACTIONS = [10, 20]            # пауза між діями всередині акаунта (наприклад, між свапом і виведенням)
SLEEP_BETWEEN_ACCOUNTS = [600, 1800]         # рандомна пауза між акаунтами для транзакцій (свапи, прогрів, upvote) [мін, макс]
SLEEP_BETWEEN_ACCOUNTS_SCAN = [20, 30]         # окрема швидка пауза між акаунтами для режиму 1 (сканування та звіт) [мін, макс]

# Interface language / Мова інтерфейсу / Язык интерфейса: "UA" | "EN" | "RU"
LANGUAGE = "UA"

# Shuffle account order
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
