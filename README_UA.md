# Abstract Global Wallet (AGW) Automation Suite ⚡

[![Network](https://img.shields.io/badge/Network-Abstract%20Mainnet-blue)](https://abs.xyz/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-green.svg)](https://www.python.org/)
[![Node.js](https://img.shields.io/badge/Node.js-18%2B-brightgreen.svg)](https://nodejs.org/)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)
[![Telegram](https://img.shields.io/badge/Telegram-@defiman4ik-2CA5E0?style=flat&logo=telegram&logoColor=white)](https://t.me/defiman4ik)

[🇬🇧 English](README.md) | [🇺🇦 Українська](README_UA.md) | [🇷🇺 Русский](README_RU.md)

Повноцінний професійний комбайн для автоматизації взаємодії зі смарт-гаманцями **Abstract Global Wallet (AGW)** на базі мережі **Abstract Mainnet** ([portal.abs.xyz](https://portal.abs.xyz/)).

Розроблено спеціально для акаунтів, створених через звичайні EVM-гаманці (MetaMask / Rabby / приватні ключі) з використанням офіційного SDK `@abstract-foundation/agw-client` та стандарту **Native Account Abstraction (EIP-712)**.

---

## 🌟 Можливості та Режими роботи

```text
================================================================
         ABSTRACT GLOBAL WALLET (AGW) AUTOMATION BOT            
        Account Abstraction • Liquidity • Swapper • Bridge      
================================================================
[?] Виберіть режим роботи:
 > 1. 📊 Сканувати акаунти (Баланси AGW, EOA, токени та ліквідність)
   2. 💧 Зняти ліквідність з протоколів (Aborean, KONA, Sakura Swap)
   3. 🔄 Обміняти всі токени в ETH (Swap to ETH + Unwrap WETH)
   4. 💸 Вивести ETH на EVM-гаманці (Withdraw to EVM)
   5. ⚡ Повний цикл (Зняти ліквідність -> Обмін токенів в ETH -> Вивід ETH на EVM)
   6. 🌐 Змінити мову / Change language / Сменить язык
   7. 🚪 Вихід
```

### 1. 📊 Сканування акаунтів (Checker & Analytics)
- Детермінований розрахунок або пряме визначення адрес смарт-контрактів AGW.
- Через **Multicall3** в один виклик перевіряє:
  - Баланси нативного ETH на AGW та EOA.
  - Баланси стейкінгового `absETH`.
  - Токени екосистеми (`WETH`, `USDC`, `USDT`, `gtBTC`, `KONA`, `PEARL`, `PENGU` тощо).
  - Залочену ліквідність у DEX-пулах.
- Виводить кольорову зведену таблицю в консоль та автоматично експортує стилізований звіт у **Excel (.xlsx)** до папки `reports/`.

### 2. 💧 Зняття ліквідності (Liquidity Remover)
- Автоматично перевіряє залочені кошти в протоколах:
  - **Aborean DEX**
  - **KONA Protocol**
  - **Sakura Swap**
- Виконує claim накопичених комісій та зняття ліквідності назад на баланс AGW.

### 3. 🔄 Обмін токенів в ETH (Token Swapper)
- **WETH -> ETH**: миттєвий unwrap 1:1 через офіційний контракт WETH без комісій агрегаторів та без slippage.
- **ERC-20 -> ETH**: автоматичний вибір маршрутів через DEX-агрегатор **Relay API**, виконання approve та свапів.

### 4. 💸 Виведення ETH на EVM (Withdraw to EVM)
- Розраховує доступний баланс ETH за вирахуванням динамічного безпечного резерву газу (`GAS_RESERVE_ETH`).
- Переказ на EVM-гаманець підписанта (`SAME_AS_EOA`) або на індивідуальні адреси з `recipients.txt`.

### 5. ⚡ Повний цикл (Full Cycle)
- Автоматичний комбінований пайплайн для очищення акаунтів:
  `Зняття ліквідності -> Обмін усіх знайдених токенів в ETH -> Виведення ETH на EVM`.

### 6. 🌐 Мультимовність (i18n)
- Підтримка перемикання мови інтерфейсу в реальному часі прямо з меню або через `settings.py` (`LANGUAGE = "UA"` / `"EN"` / `"RU"`).

> 🚀 **Upcoming Feature**: Модулі розширеного прогріву (Warmup) та щоденного авто-голосування (Upvote) знаходяться на гілці `feature/warmup-upvote` і готуються до наступного релізу!

---

## 🛡️ Безпека та Anti-Sybil механізми
- **Стабільна прив'язка проксі**: кожен акаунт закріплений за своєю проксі 1-до-1, що запобігає змішуванню IP при рандомізації.
- **Роздільні затримки**:
  - `SLEEP_BETWEEN_ACCOUNTS`: тривалі затримки між транзакціями (наприклад, 10–30 хв).
  - `SLEEP_BETWEEN_ACCOUNTS_SCAN`: швидка пауза для інформаційного сканування (20–30 сек).
- **Рандомізація черги (`SHUFFLE_ACCOUNTS`)**:
  - Транзакційні режими перемішують порядок акаунтів для уникнення кластеризації.
  - Режим сканування завжди зберігає строгий порядок 1..N для зручного моніторингу.
- **Динамічний резерв газу (`GAS_RESERVE_ETH`)**: запобігає спустошенню балансів «під нуль».

---

## 📦 Встановлення та налаштування

### 1. Системні вимоги
- **Python**: версія `3.10` або вище.
- **Node.js**: версія `18.x` або вище.

### 2. Клонування та встановлення залежностей

```bash
# Клонування репозиторію
git clone https://github.com/defiman4ik/abstract-agw-combine.git
cd abstract-agw-combine

# Встановлення залежностей Node.js (обов'язково для AGW Client та Viem)
npm install

# Встановлення залежностей Python
pip install -r requirements.txt
```
> 💡 *Підказка для Windows*: Якщо PowerShell блокує виконання скриптів, запустіть `npm.cmd install`.

### 3. Конфігурація акаунтів

Створіть файл `privatekeys.txt` на основі `privatekeys.example.txt`:

```text
# Формат: ID:EVM_PRIVATE_KEY:SIGNER_PRIVATE_KEY
1:0x0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef:0xabcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789
2:0x123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef0:0xbcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789a
```
*(Також підтримується формат одного ключа `ID:PRIVATE_KEY` або просто приватний ключ).*

#### 🔑 Що таке EVM Key та Signer Key і де їх взяти?
1. **EVM Private Key (EOA)**:
   - Це приватний ключ вашого звичайного гаманця (MetaMask, Rabby тощо).
   - **Для чого потрібен**: Використовується для поповнення (депозиту ETH) з EOA на AGW у режимі прогріву (`Warmup`), а також як адреса отримувача за замовчуванням при виведенні коштів.
   - **Де взяти**: У вашому гаманці (MetaMask: *Account details -> Show private key*).

2. **AGW Signer Private Key (Підписант смарт-гаманця)**:
   - Оскільки **AGW (Abstract Global Wallet)** є смарт-контрактом (Account Abstraction EIP-712), транзакції від його імені підписуються уповноваженим ключем-підписантом (Signer).
   - **Спосіб 1 (Один ключ для обох ролей)**:
     - Якщо ваш смарт-гаманець AGW керується безпосередньо вашим EOA-ключем, ви можете вказати один і той самий ключ двічі або скористатися спрощеним форматом `1:PRIVATE_KEY`.
   - **Спосіб 2 (Експорт з portal.abs.xyz)**:
     - Відкрийте [portal.abs.xyz](https://portal.abs.xyz) та підключіть гаманець.
     - Перейдіть у профіль / налаштування гаманця (**Settings / Security**).
     - У блоці вбудованого гаманця (Privy / Embedded Wallet) виберіть опцію **"Export Private Key"** та збережіть отриманий ключ.
   - **Спосіб 3 (Через сховище браузера F12)**:
     - Натисніть `F12` на сайті `portal.abs.xyz` -> вкладка `Application` -> `Local Storage` -> `https://portal.abs.xyz`.
     - Дані авторизованого сесійного підписанта зберігаються під ключами `privy:...`.

### 4. Конфігурація проксі

Створіть файл `proxies.txt` на основі `proxies.example.txt`:

```text
http://username:password@ip:port
socks5://username:password@ip:port
```

### 5. Налаштування параметрів

Відкрийте `settings.py` та налаштуйте необхідні параметри:
- `GAS_RESERVE_ETH`: діапазон залишку ETH на газ (наприклад, `[0.007, 0.015]`).
- `SLEEP_BETWEEN_ACCOUNTS`: затримка між транзакціями акаунтів.
- `WARMUP_MODE`, `DO_SWAP`, `CREATE_LP`, `STAKE_FARM`: налаштування прогріву.
- `UPVOTE_LOOP`: безперервний щоденний цикл голосування.

---

## 🚀 Запуск

```bash
python main.py
```

У терміналі з'явиться інтерактивне меню зі списком усіх режимів. Керування здійснюється стрілками `↑` / `↓` та клавішею `Enter`.

---

## 💬 Зворотній зв'язок та пропозиції

Маєте запитання, побажання щодо нових функцій або знайшли баг? Звертайтеся:
- **Telegram**: [@defiman4ik](https://t.me/defiman4ik)

---

## 📄 Ліцензія
Цей проект розповсюджується під ліцензією [MIT](LICENSE).
Використовуйте на власний розсуд. Завжди дотримуйтесь безпеки власних приватних ключів!
