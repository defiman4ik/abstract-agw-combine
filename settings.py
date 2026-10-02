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
#                      WARMUP & ACTIVITY SETTINGS (ПРОГРІВ АКАУНТІВ)
# ==============================================================================
# Режим прогріву:
# "RANDOM" -> Для кожного акаунта випадково обирається один зі сценаріїв:
#             1) Свап туди й назад (ETH -> Токен -> ETH)
#             2) Свап + Створення LP (ETH -> Токен + створення пари Kona LP)
#             3) Свап + Створення LP + Стейкінг у фарм (Kona Farm)
# "CUSTOM" -> Виконується чітко за налаштуваннями нижче (DO_SWAP, SWAP_BACK, CREATE_LP, STAKE_FARM)
WARMUP_MODE = "CUSTOM"

# Параметри для ручного режиму (працюють при WARMUP_MODE = "CUSTOM"):
DO_SWAP = True           # Робити свап ETH -> Токен (True / False)
SWAP_BACK = True         # Свапати токен назад в ETH (прогрів суто свапом) (True / False)
CREATE_LP = True         # Створити LP пару на Kona V2 (True / False)
STAKE_FARM = True       # Закинути отримані LP токени у фарм Kona Farm (True / False)

# Мінімальний необхідний баланс ETH на AGW для запуску (якщо менше — робиться депозит з EVM):
MIN_REQUIRED_AGW_ETH = 0.01

# Діапазон депозиту ETH з EVM на AGW (якщо на AGW не вистачає):
DEPOSIT_ETH_RANGE = [0.01, 0.013]

# Токени для прогріву (можна вказувати символи "USDC", "gtBTC" або напряму адреси контрактів):
WARMUP_TOKENS = ["USDC", "gtBTC"]

# Відсоток від доступного ETH для свапу / формування пари [мін, макс]:
WARMUP_SWAP_PERCENT = [25, 40]

# ==============================================================================
#                      UPVOTE SETTINGS (ГОЛОСУВАННЯ ЗА ДОДАТКИ)
# ==============================================================================
# Смарт-контракт голосування порталу portal.abs.xyz на Abstract Mainnet
UPVOTE_CONTRACT_ADDRESS = "0x3B50dE27506f0a8C1f4122A1e6F470009a76ce2A"

# Топ-10 перевірених та активних додатків для голосування (випадковий вибір):
# 179: Kona (DEX & Yield)
# 1:   Abstract (Офіційний хаб екосистеми)
# 225: DEPTH Protocol (Vaults & DeFi)
# 2:   Onchain Heroes (RPG Game)
# 3:   Gigaverse (Gaming Ecosystem)
# 168: COSMO / MODHAUS (Social & Media)
# 220: Amigo (SocialFi & Chat)
# 207: Tollan Universe (Action RPG)
# 7:   Moody Madness (Gaming & AI)
# 6:   Cambria (MMO Game)
UPVOTE_APP_IDS = [179, 1, 225, 2, 3, 168, 220, 207, 7, 6]

# Безперервний щоденний цикл голосування (True / False):
# Якщо True — після завершення кола акаунтів бот автоматично чекає наступного дня і повторює цикл.
# Зупинити роботу можна комбінацією клавіш Ctrl+C у будь-який момент.
UPVOTE_LOOP = True


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
