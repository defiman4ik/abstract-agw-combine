import os
from datetime import datetime
from typing import List, Dict, Any
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

def save_scan_report_to_excel(scans: List[Dict[str, Any]]) -> str:
    """Exports scanned accounts data into a beautifully formatted Excel (.xlsx) report."""
    os.makedirs("reports", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join("reports", f"scan_report_{timestamp}.xlsx")
    last_filepath = os.path.join("reports", "last_scan_report.xlsx")

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "AGW Accounts"
    ws.views.sheetView[0].showGridLines = True

    # Palette
    HEADER_FILL = PatternFill(start_color="1F2937", end_color="1F2937", fill_type="solid") # Dark Slate
    HEADER_FONT = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
    DATA_FONT = Font(name="Segoe UI", size=10)
    TOTAL_FONT = Font(name="Segoe UI", size=10, bold=True)
    TOTAL_FILL = PatternFill(start_color="E5E7EB", end_color="E5E7EB", fill_type="solid") # Light Gray

    THIN_BORDER = Border(
        left=Side(style="thin", color="D1D5DB"),
        right=Side(style="thin", color="D1D5DB"),
        top=Side(style="thin", color="D1D5DB"),
        bottom=Side(style="thin", color="D1D5DB"),
    )

    headers = [
        "#",
        "AGW Address",
        "Signer / EOA",
        "AGW ETH",
        "EOA ETH",
        "Tokens (AGW)",
        "Liquidity (DEX)",
        "Upvote Streak",
        "Voted Today",
        "Deployed",
    ]

    # Write headers
    ws.append(headers)
    ws.row_dimensions[1].height = 26

    for col_idx in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = THIN_BORDER

    # Populate rows
    total_tokens: Dict[str, float] = {}

    for idx, scan in enumerate(scans, 1):
        acc_num = scan.get("account_id") if scan.get("account_id") else idx
        agw_addr = scan.get("agw_address", "")
        eoa_addr = scan.get("eoa_address", "")
        agw_eth = round(scan.get("agw_eth", 0.0), 6)
        eoa_eth = round(scan.get("eoa_eth", 0.0), 6)

        # Tokens list
        active_tokens = []
        for t in scan.get("agw_tokens", []):
            bal = t.get("balance", 0.0)
            if t.get("raw_balance", 0) > 0 and bal >= 0.000001:
                sym = t.get("symbol", "")
                if bal < 0.001:
                    active_tokens.append(f"{sym}: {bal:.6f}")
                else:
                    active_tokens.append(f"{sym}: {bal:.4f}")
                total_tokens[sym] = total_tokens.get(sym, 0.0) + bal
        tokens_str = "\n".join(active_tokens) if active_tokens else "-"

        # Liquidity list
        liq_list = []
        for p in scan.get("agw_liquidity", []):
            if p.get("is_farm"):
                liq_list.append(f"Kona Farm #{p['farm_id']} {p.get('pair_label', 'LP')} ({p['formatted_lp']:.8f} LP)")
            else:
                status = f"Liq: {p['liquidity']}" if p.get("liquidity", 0) > 0 else "Empty"
                liq_list.append(f"{p['protocol']} #{p['token_id']} ({status})")
        liq_str = "\n".join(liq_list) if liq_list else "-"

        streak_val = scan.get("vote_streak", 0)
        voted_today_str = "Yes" if scan.get("voted_today") else "No"
        deployed_str = "Yes" if scan.get("is_deployed", True) else "No"

        row = [
            acc_num,
            agw_addr,
            eoa_addr,
            agw_eth,
            eoa_eth,
            tokens_str,
            liq_str,
            f"{streak_val} d",
            voted_today_str,
            deployed_str,
        ]
        ws.append(row)

        curr_row = idx + 1
        num_lines = max(len(active_tokens), len(liq_list), 1)
        ws.row_dimensions[curr_row].height = max(20, num_lines * 16)

        # Styles for data row
        ws.cell(row=curr_row, column=1).alignment = Alignment(horizontal="center", vertical="center")
        ws.cell(row=curr_row, column=2).alignment = Alignment(horizontal="center", vertical="center")
        ws.cell(row=curr_row, column=3).alignment = Alignment(horizontal="center", vertical="center")
        ws.cell(row=curr_row, column=4).alignment = Alignment(horizontal="right", vertical="center")
        ws.cell(row=curr_row, column=5).alignment = Alignment(horizontal="right", vertical="center")
        ws.cell(row=curr_row, column=6).alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
        ws.cell(row=curr_row, column=7).alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
        ws.cell(row=curr_row, column=8).alignment = Alignment(horizontal="center", vertical="center")
        ws.cell(row=curr_row, column=9).alignment = Alignment(horizontal="center", vertical="center")
        ws.cell(row=curr_row, column=10).alignment = Alignment(horizontal="center", vertical="center")

        # Number formats
        ws.cell(row=curr_row, column=4).number_format = "0.000000"
        ws.cell(row=curr_row, column=5).number_format = "0.000000"

        for col_idx in range(1, len(headers) + 1):
            cell = ws.cell(row=curr_row, column=col_idx)
            cell.font = DATA_FONT
            cell.border = THIN_BORDER

    # Summary Row
    summary_row_idx = len(scans) + 2
    ws.row_dimensions[summary_row_idx].height = 24

    ws.cell(row=summary_row_idx, column=1, value="TOTAL")
    ws.cell(row=summary_row_idx, column=2, value=f"{len(scans)} accounts")
    ws.cell(row=summary_row_idx, column=3, value="")
    ws.cell(row=summary_row_idx, column=4, value=f"=SUM(D2:D{summary_row_idx - 1})")
    ws.cell(row=summary_row_idx, column=5, value=f"=SUM(E2:E{summary_row_idx - 1})")

    # Tokens summary string
    tok_summary = "\n".join([
        f"{sym}: {tot:.6f}" if tot < 0.001 else f"{sym}: {tot:.4f}"
        for sym, tot in total_tokens.items()
    ]) if total_tokens else "-"
    ws.cell(row=summary_row_idx, column=6, value=tok_summary)
    ws.cell(row=summary_row_idx, column=7, value="")
    ws.cell(row=summary_row_idx, column=8, value="")

    ws.cell(row=summary_row_idx, column=4).number_format = "0.000000"
    ws.cell(row=summary_row_idx, column=5).number_format = "0.000000"

    for col_idx in range(1, len(headers) + 1):
        cell = ws.cell(row=summary_row_idx, column=col_idx)
        cell.font = TOTAL_FONT
        cell.fill = TOTAL_FILL
        cell.border = THIN_BORDER
        if col_idx in (1, 2, 8):
            cell.alignment = Alignment(horizontal="center", vertical="center")
        elif col_idx in (4, 5):
            cell.alignment = Alignment(horizontal="right", vertical="center")
        else:
            cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)

    # Freeze header row
    ws.freeze_panes = "A2"

    # Auto-adjust column widths
    for col in ws.columns:
        col_letter = get_column_letter(col[0].column)
        if col_letter in ("B", "C"): # Full hex addresses
            ws.column_dimensions[col_letter].width = 46
        elif col_letter in ("D", "E"):
            ws.column_dimensions[col_letter].width = 16
        elif col_letter in ("F", "G"):
            ws.column_dimensions[col_letter].width = 36
        elif col_letter == "A":
            ws.column_dimensions[col_letter].width = 8
        elif col_letter == "H":
            ws.column_dimensions[col_letter].width = 12
        else:
            ws.column_dimensions[col_letter].width = 18

    wb.save(filepath)
    try:
        wb.save(last_filepath)
    except Exception:
        pass

    return filepath
