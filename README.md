# Abstract Global Wallet (AGW) Automation Suite ⚡

[![Network](https://img.shields.io/badge/Network-Abstract%20Mainnet-blue)](https://abs.xyz/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-green.svg)](https://www.python.org/)
[![Node.js](https://img.shields.io/badge/Node.js-18%2B-brightgreen.svg)](https://nodejs.org/)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

[🇬🇧 English](README.md) | [🇺🇦 Українська](README_UA.md) | [🇷🇺 Русский](README_RU.md)

A comprehensive, all-in-one automation tool for **Abstract Global Wallet (AGW)** smart contract accounts on **Abstract Mainnet** ([portal.abs.xyz](https://portal.abs.xyz/)).

Designed specifically for accounts created via standard EVM wallets (MetaMask / Rabby / Private Keys) utilizing the official `@abstract-foundation/agw-client` SDK and **Native Account Abstraction (EIP-712)** standard.

---

## 🌟 Features & Operation Modes

```text
================================================================
         ABSTRACT GLOBAL WALLET (AGW) AUTOMATION BOT            
        Account Abstraction • Warmup • Swapper • Upvote        
================================================================
[?] Select operation mode:
 > 1. 📊 Scan accounts (AGW & EOA balances, tokens, liquidity)
   2. 💧 Remove liquidity from protocols (Aborean, KONA, Sakura Swap)
   3. 🔄 Swap all tokens to ETH (Swap to ETH + Unwrap WETH)
   4. 💸 Withdraw ETH to EVM wallets (Withdraw to EVM)
   5. ⚡ Full cycle (Remove liquidity -> Swap to ETH -> Withdraw to EVM)
   6. 🔥 Warmup accounts (EVM Deposit -> Swap -> Create LP -> Stake)
   7. ⭐ Daily Upvote (Keep streak on portal.abs.xyz)
   8. 🌐 Change language / Змінити мову / Сменить язык
   9. 🚪 Exit
```

### 1. 📊 Scan Accounts (Checker & Analytics)
- Deterministic calculation and resolution of AGW smart account addresses.
- Single-request inspection via **Multicall3**:
  - Native ETH balances on both AGW and EOA signer accounts.
  - Staked `absETH` balances.
  - Ecosystem tokens (`WETH`, `USDC`, `USDT`, `gtBTC`, `KONA`, `PEARL`, `PENGU`, etc.).
  - Locked liquidity positions across supported DEX pools.
  - Daily voting status & current **Upvote Streak** from [portal.abs.xyz](https://portal.abs.xyz/rewards).
- Beautiful colored summary table printed directly to console and exported to styled **Excel (.xlsx)** reports in `reports/`.

### 2. 💧 Remove Liquidity (Liquidity Remover)
- Automatically scans and claims locked positions from:
  - **Aborean DEX**
  - **KONA Protocol**
  - **Sakura Swap**
- Collects trading fees and safely returns all liquidity to the AGW balance.

### 3. 🔄 Swap All Tokens to ETH (Token Swapper)
- **WETH -> ETH**: Instant 1:1 unwrapping via the native WETH contract without DEX routing fees or slippage.
- **ERC-20 -> ETH**: Optimal liquidity routing via **Relay API**, handling approvals and atomic swaps.

### 4. 💸 Withdraw ETH to EVM Wallets (Withdraw to EVM)
- Computes liquid ETH balance while reserving a configurable safety gas buffer (`GAS_RESERVE_ETH`).
- Transfers funds to the signer's own EVM address (`SAME_AS_EOA`) or dedicated recipient addresses from `recipients.txt` (`FROM_FILE`).

### 5. ⚡ Full Clean Cycle (Full Cycle)
- Automated multi-step cleanup pipeline per account:
  `Remove Liquidity -> Swap all tokens to ETH -> Withdraw remaining ETH to EVM`.

### 6. 🔥 Warmup Accounts (Warmup Engine)
- Flexible modular activity engine:
  - Automatic top-up deposit from EVM to AGW if balance is below threshold (< 0.01 ETH).
  - Swap ETH to selected target token (`USDC`, `gtBTC`, etc.).
  - Add liquidity to **Kona V2 LP** pool with auto-calculated ratios and approvals.
  - Stake LP tokens into **Kona Farm** for yield and reward points.
  - Modes: `CUSTOM` (preset steps) or `RANDOM` (randomized activity patterns for Sybil resistance).

### 7. ⭐ Daily Upvote (Daily Vote & Streak Keeper)
- Direct on-chain interaction with official contract `0x3B50dE27506f0a8C1f4122A1e6F470009a76ce2A` via `voteForApp(uint256 appId) payable`.
- Queries backend API to check eligibility and vote streak, skipping accounts that already voted today.
- Votes for random verified top-10 ecosystem apps (`UPVOTE_APP_IDS`).
- **Autonomous Continuous Daily Loop (`UPVOTE_LOOP = True`)**: automatically calculates remaining seconds until next epoch/day, sleeps, and resumes voting automatically.

### 8. 🌐 Multi-Language Support (i18n)
- Switch language on the fly right inside the interactive menu or via `settings.py` (`LANGUAGE = "EN"` / `"UA"` / `"RU"`).

---

## 🛡️ Anti-Sybil & Safety Features
- **1-to-1 Static Proxy Binding**: each account is permanently bound to a designated proxy from `proxies.txt` to prevent IP cross-contamination during shuffling.
- **Dedicated Delay Profiles**:
  - `SLEEP_BETWEEN_ACCOUNTS`: long random delays between transactions (e.g. 10–30 min).
  - `SLEEP_BETWEEN_ACCOUNTS_SCAN`: fast pauses for balance checks (20–30 sec).
- **Execution Order Control (`SHUFFLE_ACCOUNTS`)**:
  - Transaction modes randomize execution order to avoid clustering.
  - Scan mode strictly preserves sequential order (1..N) for consistent reporting.
- **Dynamic Gas Reserves (`GAS_RESERVE_ETH`)**: randomized reserves prevent accounts from being completely drained.

---

## 📦 Installation & Setup

### 1. Requirements
- **Python**: version `3.10` or higher.
- **Node.js**: version `18.x` or higher.

### 2. Clone & Install Dependencies

```bash
# Clone repository
git clone https://github.com/your-username/abstract-agw-bot.git
cd abstract-agw-bot

# Install Node.js dependencies
npm install

# Install Python dependencies
pip install -r requirements.txt
```

### 3. Account Configuration

Create `privatekeys.txt` based on `privatekeys.example.txt`:

```text
# Format: ID:EVM_PRIVATE_KEY:SIGNER_PRIVATE_KEY
1:0x0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef:0xabcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789
2:0x123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef0:0xbcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789a
```
*(Single key format `ID:PRIVATE_KEY` or plain private keys are also supported).*

### 4. Proxy Configuration

Create `proxies.txt` based on `proxies.example.txt`:

```text
http://username:password@ip:port
socks5://username:password@ip:port
```

### 5. Settings Configuration

Open `settings.py` and configure parameters to your preference:
- `LANGUAGE`: default interface language (`"EN"`, `"UA"`, or `"RU"`).
- `GAS_RESERVE_ETH`: gas reserve range (e.g. `[0.007, 0.015]`).
- `SLEEP_BETWEEN_ACCOUNTS`: pause range between account transactions.
- `WARMUP_MODE`, `DO_SWAP`, `CREATE_LP`, `STAKE_FARM`: warmup strategy.
- `UPVOTE_LOOP`: continuous daily voting loop.

---

## 🚀 Usage

```bash
python main.py
```

An interactive menu will guide you through all available modes using keyboard arrow keys `↑` / `↓` and `Enter`.

---

## 📄 License
Distributed under the [MIT](LICENSE) License. Use at your own discretion. Always keep your private keys secure!
