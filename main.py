import sys
import random
import inquirer
from modules.utils import logger, load_lines, sleeping, load_private_keys, load_proxies
from modules.agw import AgwAccount
from modules.checker import BalanceChecker
from modules.swapper import TokenSwapper
from modules.withdrawer import EthWithdrawer
from modules.liquidity import LiquidityRemover
from modules.i18n import t, get_current_language, set_current_language
import settings

def get_execution_accounts(accounts):
    acc_list = list(accounts)
    if getattr(settings, "SHUFFLE_ACCOUNTS", False):
        random.shuffle(acc_list)
        logger.info(t("shuffled_msg", count=len(acc_list)))
    return acc_list

def check_accounts_mode(accounts):
    checker = BalanceChecker()
    scans = []
    # Для сканування завжди використовуємо послідовний порядок (1..N) без перемішування
    logger.info(f"Scanning {len(accounts)} account(s) in sequential order (SHUFFLE_ACCOUNTS = False for scan)...")
    for idx, acc in enumerate(accounts, 1):
        try:
            logger.info(f"[{idx}/{len(accounts)}] Scanning AGW: {acc.agw_address} (Signer: {acc.signer_address})...")
            scan = checker.scan_account(acc)
            scans.append(scan)
        except Exception as e:
            logger.error(f"Error scanning account {acc.signer_address}: {e}")

        if idx < len(accounts):
            sleep_scan = getattr(settings, "SLEEP_BETWEEN_ACCOUNTS_SCAN", [1, 3])
            sleeping(sleep_scan, "пауза між скануванням акаунтів")
    
    checker.print_scan_report(scans)
    return scans

def swap_tokens_mode(accounts):
    accounts = get_execution_accounts(accounts)
    checker = BalanceChecker()
    swapper = TokenSwapper()
    logger.info(f"Starting token swaps for {len(accounts)} account(s)...")

    for idx, acc in enumerate(accounts, 1):
        logger.info(f"\n[{idx}/{len(accounts)}] Account AGW: {acc.agw_address}")
        try:
            scan = checker.scan_account(acc)
            active_tokens = [t for t in scan["agw_tokens"] if t["raw_balance"] > 0 and t.get("balance", 0) >= 0.000001]
            if not active_tokens:
                logger.info(f"No tokens to swap on AGW {acc.agw_address}")
            else:
                logger.info(f"Found {len(active_tokens)} token(s) to swap.")
                swapper.swap_all_tokens(acc, active_tokens)

        except Exception as e:
            logger.error(f"Error during swap on {acc.agw_address}: {e}")

        if idx < len(accounts):
            sleeping(settings.SLEEP_BETWEEN_ACCOUNTS, "пауза між акаунтами")

    logger.success("All accounts processed for token swaps.")

def withdraw_eth_mode(accounts):
    accounts = get_execution_accounts(accounts)
    withdrawer = EthWithdrawer()
    logger.info(f"Starting ETH withdrawals for {len(accounts)} account(s)...")

    for idx, acc in enumerate(accounts, 1):
        logger.info(f"\n[{idx}/{len(accounts)}] Processing withdrawal for AGW: {acc.agw_address}")
        try:
            acc_idx = (int(acc.account_id) - 1) if (getattr(acc, "account_id", None) and str(acc.account_id).isdigit()) else (idx - 1)
            withdrawer.withdraw_agw_eth(acc, account_index=acc_idx)
        except Exception as e:
            logger.error(f"Error during withdrawal on {acc.agw_address}: {e}")

        if idx < len(accounts):
            sleeping(settings.SLEEP_BETWEEN_ACCOUNTS, "пауза між акаунтами")

    logger.success("All accounts processed for ETH withdrawals.")

def remove_liquidity_mode(accounts):
    accounts = get_execution_accounts(accounts)
    remover = LiquidityRemover()
    logger.info(f"Starting liquidity removal for {len(accounts)} account(s)...")

    for idx, acc in enumerate(accounts, 1):
        logger.info(f"\n[{idx}/{len(accounts)}] Processing liquidity removal for AGW: {acc.agw_address}")
        try:
            remover.remove_all_liquidity(acc)
        except Exception as e:
            logger.error(f"Error removing liquidity on {acc.agw_address}: {e}")

        if idx < len(accounts):
            sleeping(settings.SLEEP_BETWEEN_ACCOUNTS, "пауза між акаунтами")

    logger.success("All accounts processed for liquidity removal.")

def full_cycle_mode(accounts):
    accounts = get_execution_accounts(accounts)
    checker = BalanceChecker()
    remover = LiquidityRemover()
    swapper = TokenSwapper()
    withdrawer = EthWithdrawer()
    logger.info(f"Starting FULL CYCLE (Liquidity -> Swap -> Withdraw) for {len(accounts)} account(s)...")

    for idx, acc in enumerate(accounts, 1):
        logger.info(f"\n{'=' * 60}")
        logger.info(f"[{idx}/{len(accounts)}] FULL CYCLE for AGW: {acc.agw_address}")
        logger.info(f"{'=' * 60}")

        try:
            # 1. Remove liquidity and collect all tokens/fees from DEX protocols
            logger.info("Step 1/3: Checking and removing liquidity...")
            remover.remove_all_liquidity(acc)
            sleeping(settings.SLEEP_BETWEEN_ACTIONS)

            # 2. Scan balances and swap all tokens to ETH
            logger.info("Step 2/3: Scanning tokens and swapping to ETH...")
            scan = checker.scan_account(acc)
            active_tokens = [t for t in scan["agw_tokens"] if t["raw_balance"] > 0 and t.get("balance", 0) >= 0.000001]
            
            if active_tokens:
                logger.info(f"Swapping {len(active_tokens)} token(s) to ETH...")
                swapper.swap_all_tokens(acc, active_tokens)
                sleeping(settings.SLEEP_BETWEEN_ACTIONS)
            else:
                logger.info("No tokens to swap.")

            # 3. Withdraw ETH to EVM
            logger.info("Step 3/3: Withdrawing ETH...")
            acc_idx = (int(acc.account_id) - 1) if (getattr(acc, "account_id", None) and str(acc.account_id).isdigit()) else (idx - 1)
            withdrawer.withdraw_agw_eth(acc, account_index=acc_idx)

        except Exception as e:
            logger.error(f"Error during full cycle on {acc.agw_address}: {e}")

        if idx < len(accounts):
            sleeping(settings.SLEEP_BETWEEN_ACCOUNTS, "пауза між акаунтами")

    logger.success("Full cycle completed for all accounts.")

def change_language_mode():
    lang_questions = [
        inquirer.List(
            "lang",
            message=t("select_language"),
            choices=[
                ("🇺🇦 Українська (UA)", "UA"),
                ("🇬🇧 English (EN)", "EN"),
                ("🇷🇺 Русский (RU)", "RU"),
            ],
            default=get_current_language(),
        )
    ]
    ans = inquirer.prompt(lang_questions)
    if ans and "lang" in ans:
        set_current_language(ans["lang"])
        logger.success(t("lang_switched"))

def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    print("""
    ================================================================
                     ABSTRACT (AGW) WALLET MANAGER                  
            Account Abstraction • Token Swapper • Withdrawer        
    ================================================================
    """)

    key_tuples = load_private_keys("privatekeys.txt")
    if not key_tuples:
        logger.error("privatekeys.txt has no valid private keys! Please add private keys to privatekeys.txt and run again.")
        sys.exit(1)

    proxies = load_proxies("proxies.txt") if getattr(settings, "USE_PROXIES", True) else []
    proxy_info = f" and {len(proxies)} proxy(ies)" if proxies else " (running without proxies)"
    logger.info(f"Loaded {len(key_tuples)} private key(s){proxy_info}.")

    logger.info("Initializing AGW accounts...")
    accounts = []
    for idx, item in enumerate(key_tuples):
        if len(item) == 5:
            pk, acc_id, agw_addr, evm_pk, evm_addr = item
        else:
            pk, acc_id, agw_addr = item[:3]
            evm_pk, evm_addr = None, None
        proxy = proxies[idx % len(proxies)] if proxies else None
        try:
            acc = AgwAccount(
                pk,
                account_id=acc_id,
                agw_address=agw_addr,
                proxy=proxy,
                evm_private_key=evm_pk,
                evm_address=evm_addr,
            )
            accounts.append(acc)
        except Exception as e:
            acc_label = f"ID {acc_id}" if acc_id else f"...{pk[-6:]}"
            logger.error(f"Failed to initialize account for {acc_label}: {e}")

    if not accounts:
        logger.error("No valid accounts initialized!")
        sys.exit(1)

    logger.success(f"Initialized {len(accounts)} AGW account(s) successfully.")

    while True:
        questions = [
            inquirer.List(
                "mode",
                message=t("menu_title"),
                choices=[
                    (t("menu_scan"), "scan"),
                    (t("menu_liquidity"), "liquidity"),
                    (t("menu_swap"), "swap"),
                    (t("menu_withdraw"), "withdraw"),
                    (t("menu_full"), "full"),
                    (t("menu_lang"), "lang"),
                    (t("menu_exit"), "exit"),
                ],
            )
        ]

        answers = inquirer.prompt(questions)
        if not answers or answers["mode"] == "exit":
            logger.info(t("work_finished"))
            break

        mode = answers["mode"]
        if mode == "scan":
            check_accounts_mode(accounts)
        elif mode == "liquidity":
            remove_liquidity_mode(accounts)
        elif mode == "swap":
            swap_tokens_mode(accounts)
        elif mode == "withdraw":
            withdraw_eth_mode(accounts)
        elif mode == "full":
            full_cycle_mode(accounts)
        elif mode == "lang":
            change_language_mode()

        print("\n")

if __name__ == "__main__":
    main()
