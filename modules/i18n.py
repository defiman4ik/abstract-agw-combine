# ==============================================================================
#                       INTERNATIONALIZATION (i18n) MODULE
# ==============================================================================
import settings

TRANSLATIONS = {
    "UA": {
        # Меню
        "menu_title": "Виберіть режим роботи",
        "menu_scan": "1. 📊 Сканувати акаунти (Баланси AGW, EOA, токени та ліквідність)",
        "menu_liquidity": "2. 💧 Зняти ліквідність з протоколів (Aborean, KONA, Sakura Swap)",
        "menu_swap": "3. 🔄 Обміняти всі токени в ETH (Swap to ETH + Unwrap WETH)",
        "menu_withdraw": "4. 💸 Вивести ETH на EVM-гаманці (Withdraw to EVM)",
        "menu_full": "5. ⚡ Повний цикл (Зняти ліквідність -> Обмін токенів в ETH -> Вивід ETH на EVM)",
        "menu_warmup": "6. 🔥 Прогрів акаунтів (Депозит з EVM -> Свап -> Створення LP -> Стейкінг)",
        "menu_upvote": "7. ⭐ Щоденний Upvote (Підтримка стріку на portal.abs.xyz)",
        "menu_lang": "8. 🌐 Змінити мову / Change language / Сменить язык",
        "menu_exit": "9. 🚪 Вихід",
        
        # Мовний вибір
        "select_language": "Оберіть мову інтерфейсу",
        "lang_switched": "Мову інтерфейсу змінено на Українську 🇺🇦",

        # Паузи та логування
        "pause_accounts": "пауза між акаунтами",
        "pause_scan": "пауза між скануванням акаунтів",
        "pause_upvote_day": "очікування наступного дня для Upvote",
        "work_finished": "Роботу завершено.",
        "shuffled_msg": "Порядок виконання {count} акаунтів перемішано (SHUFFLE_ACCOUNTS = True).",
        "scanning_start": "Сканування {count} акаунт(ів) у послідовному порядку...",
        "swaps_start": "Початок обміну токенів для {count} акаунт(ів)...",
        "withdraw_start": "Початок виведення ETH для {count} акаунт(ів)...",
        "liquidity_start": "Початок зняття ліквідності для {count} акаунт(ів)...",
        "full_start": "Початок ПОВНОГО ЦИКЛУ для {count} акаунт(ів)...",
        "warmup_start": "Початок ПРОГРІВУ для {count} акаунт(ів)...",
        "upvote_cycle_start": "🚀 Початок UPVOTE Циклу #{cycle} для {count} акаунт(ів)...",
        "upvote_stopped": "Режим Upvote зупинено користувачем.",
    },
    "EN": {
        # Menu
        "menu_title": "Select operation mode",
        "menu_scan": "1. 📊 Scan accounts (AGW & EOA balances, tokens, liquidity)",
        "menu_liquidity": "2. 💧 Remove liquidity from protocols (Aborean, KONA, Sakura Swap)",
        "menu_swap": "3. 🔄 Swap all tokens to ETH (Swap to ETH + Unwrap WETH)",
        "menu_withdraw": "4. 💸 Withdraw ETH to EVM wallets (Withdraw to EVM)",
        "menu_full": "5. ⚡ Full cycle (Remove liquidity -> Swap to ETH -> Withdraw to EVM)",
        "menu_warmup": "6. 🔥 Warmup accounts (EVM Deposit -> Swap -> Create LP -> Stake)",
        "menu_upvote": "7. ⭐ Daily Upvote (Keep streak on portal.abs.xyz)",
        "menu_lang": "8. 🌐 Change language / Змінити мову / Сменить язык",
        "menu_exit": "9. 🚪 Exit",

        # Language selection
        "select_language": "Select interface language",
        "lang_switched": "Interface language changed to English 🇬🇧",

        # Pauses & Logs
        "pause_accounts": "pause between accounts",
        "pause_scan": "pause between account scans",
        "pause_upvote_day": "waiting for next day for Upvote",
        "work_finished": "Work finished. Goodbye!",
        "shuffled_msg": "Execution order of {count} accounts shuffled (SHUFFLE_ACCOUNTS = True).",
        "scanning_start": "Scanning {count} account(s) in sequential order...",
        "swaps_start": "Starting token swaps for {count} account(s)...",
        "withdraw_start": "Starting ETH withdrawals for {count} account(s)...",
        "liquidity_start": "Starting liquidity removal for {count} account(s)...",
        "full_start": "Starting FULL CYCLE for {count} account(s)...",
        "warmup_start": "Starting WARMUP for {count} account(s)...",
        "upvote_cycle_start": "🚀 Starting UPVOTE Cycle #{cycle} for {count} account(s)...",
        "upvote_stopped": "Upvote mode stopped by user.",
    },
    "RU": {
        # Меню
        "menu_title": "Выберите режим работы",
        "menu_scan": "1. 📊 Сканировать аккаунты (Балансы AGW, EOA, токены и ликвидность)",
        "menu_liquidity": "2. 💧 Снять ликвидность с протоколов (Aborean, KONA, Sakura Swap)",
        "menu_swap": "3. 🔄 Обменять все токены в ETH (Swap to ETH + Unwrap WETH)",
        "menu_withdraw": "4. 💸 Вывести ETH на EVM-кошельки (Withdraw to EVM)",
        "menu_full": "5. ⚡ Полный цикл (Снять ликвидность -> Обмен токенов в ETH -> Вывод ETH на EVM)",
        "menu_warmup": "6. 🔥 Прогрев аккаунтов (Депозит с EVM -> Свап -> Создание LP -> Стейкинг)",
        "menu_upvote": "7. ⭐ Ежедневный Upvote (Поддержание стрика на portal.abs.xyz)",
        "menu_lang": "8. 🌐 Сменить язык / Change language / Змінити мову",
        "menu_exit": "9. 🚪 Выход",

        # Выбор языка
        "select_language": "Выберите язык интерфейса",
        "lang_switched": "Язык интерфейса изменен на Русский 🇷🇺",

        # Паузы и логи
        "pause_accounts": "пауза между аккаунтами",
        "pause_scan": "пауза между сканированием аккаунтов",
        "pause_upvote_day": "ожидание следующего дня для Upvote",
        "work_finished": "Работа завершена.",
        "shuffled_msg": "Порядок выполнения {count} аккаунтов перемешан (SHUFFLE_ACCOUNTS = True).",
        "scanning_start": "Сканирование {count} аккаунт(ов) в последовательном порядке...",
        "swaps_start": "Начало обмена токенов для {count} аккаунт(ов)...",
        "withdraw_start": "Начало вывода ETH для {count} аккаунт(ов)...",
        "liquidity_start": "Начало снятия ликвидности для {count} аккаунт(ов)...",
        "full_start": "Начало ПОЛНОГО ЦИКЛА для {count} аккаунт(ов)...",
        "warmup_start": "Начало ПРОГРЕВА для {count} аккаунт(ов)...",
        "upvote_cycle_start": "🚀 Начало UPVOTE Цикла #{cycle} для {count} аккаунт(ов)...",
        "upvote_stopped": "Режим Upvote остановлен пользователем.",
    },
}

def get_current_language() -> str:
    lang = getattr(settings, "LANGUAGE", "UA")
    if not isinstance(lang, str):
        return "UA"
    lang_upper = lang.strip().upper()
    return lang_upper if lang_upper in TRANSLATIONS else "UA"

def set_current_language(lang: str) -> None:
    lang_upper = lang.strip().upper()
    if lang_upper in TRANSLATIONS:
        setattr(settings, "LANGUAGE", lang_upper)

def t(key: str, **kwargs) -> str:
    """Translates a message key according to the active language setting."""
    lang = get_current_language()
    dict_for_lang = TRANSLATIONS.get(lang, TRANSLATIONS["UA"])
    text = dict_for_lang.get(key)
    if text is None:
        # Fallback to English or Ukrainian
        text = TRANSLATIONS["EN"].get(key, TRANSLATIONS["UA"].get(key, key))
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text
