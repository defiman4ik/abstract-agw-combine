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
        Account Abstraction • Liquidity • Swapper • Bridge      
================================================================
[?] Select operation mode:
 > 1. 📊 Scan accounts (AGW & EOA balances, tokens, liquidity)
   2. 💧 Remove liquidity from protocols (Aborean, KONA, Sakura Swap)
   3. 🔄 Swap all tokens to ETH (Swap to ETH + Unwrap WETH)
   4. 💸 Withdraw ETH to EVM wallets (Withdraw to EVM)
   5. ⚡ Full cycle (Remove liquidity -> Swap to ETH -> Withdraw to EVM)
   6. 🌐 Change language / Змінити мову / Сменить язык
   7. 🚪 Exit
```

### 1. 📊 Scan Accounts (Checker & Analytics)
- Deterministic calculation and resolution of AGW smart account addresses.
- Single-request inspection via **Multicall3**:
  - Native ETH balances on both AGW and EOA signer accounts.
  - Staked `absETH` balances.
  - Ecosystem tokens (`WETH`, `USDC`, `USDT`, `gtBTC`, `KONA`, `PEARL`, `PENGU`, etc.).
  - Locked liquidity positions across supported DEX pools.
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

### 6. 🌐 Multi-Language Support (i18n)
- Switch language on the fly right inside the interactive menu or via `settings.py` (`LANGUAGE = "EN"` / `"UA"` / `"RU"`).

> 🚀 **Upcoming Feature**: Advanced Warmup Engine and Daily Upvote Streak Keeper are currently in development on the `feature/warmup-upvote` branch and scheduled for the next release!

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
git clone https://github.com/defitools-lab/abstract-agw-combine.git
cd abstract-agw-combine

# Install Node.js dependencies (Required for AGW Client & Viem)
npm install

# Install Python dependencies
pip install -r requirements.txt
```
> 💡 *Note for Windows users*: If PowerShell blocks npm script execution, use `npm.cmd install`.

### 3. Account Configuration

Create `privatekeys.txt` based on `privatekeys.example.txt`:

```text
# Format: ID:EVM_PRIVATE_KEY:SIGNER_PRIVATE_KEY
1:0x0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef:0xabcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789
2:0x123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef0:0xbcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789a
```
*(Single key format `ID:PRIVATE_KEY` or plain private keys are also supported).*

#### 🔑 What are EVM Key and Signer Key, and where to get them?
1. **EVM Private Key (EOA)**:
   - The standard private key of your master EVM wallet (MetaMask, Rabby, etc.).
   - **Purpose**: Used for funding your smart account (EVM -> AGW deposit in `Warmup` mode) and as the default recipient address for withdrawals.
   - **Where to get**: Inside your wallet app (MetaMask: *Account details -> Show private key*).

2. **AGW Signer Private Key (Smart Account Signer)**:
   - Because **AGW (Abstract Global Wallet)** is a smart contract account (Account Abstraction EIP-712), transactions on its behalf are authorized by a designated signer key.
   - **Option 1 (Single key for both roles)**:
     - If your AGW account is authorized directly with your EOA key, you can provide the same key twice or use the simplified format `1:PRIVATE_KEY`.
   - **Option 2 (Export from portal.abs.xyz)**:
     - Log in to [portal.abs.xyz](https://portal.abs.xyz) with your wallet.
     - Go to your account / wallet settings (**Settings / Security**).
     - In the embedded wallet section (Privy / Embedded Wallet), select **"Export Private Key"** and save the key securely.
   - **Option 3 (Via browser storage F12)**:
     - Open Developer Tools (`F12`) on `portal.abs.xyz` -> navigate to `Application` -> `Local Storage` -> `https://portal.abs.xyz`.
     - Authorized session and signer data are stored under keys labeled `privy:...`.

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
