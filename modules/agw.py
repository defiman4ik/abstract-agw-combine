import json
import subprocess
import os
from typing import Dict, Any, Optional
from web3 import Web3
from modules.utils import logger, extract_private_key
import settings

class AgwAccount:
    def __init__(
        self,
        private_key: str,
        account_id: Optional[str] = None,
        agw_address: Optional[str] = None,
        proxy: Optional[str] = None,
        evm_private_key: Optional[str] = None,
        evm_address: Optional[str] = None,
    ):
        res = extract_private_key(private_key)
        if res:
            pk, parsed_id, parsed_agw, parsed_evm_pk, parsed_evm_addr = res
            self.private_key = pk
            self.account_id = account_id or parsed_id
            self.explicit_agw = agw_address or parsed_agw
            self.evm_private_key = evm_private_key or parsed_evm_pk
            self.evm_address = evm_address or parsed_evm_addr
        else:
            if not private_key.startswith("0x"):
                private_key = "0x" + private_key
            self.private_key = private_key
            self.account_id = account_id
            self.explicit_agw = agw_address
            self.evm_private_key = evm_private_key
            self.evm_address = evm_address

        self.proxy = proxy
        payload = json.dumps({
            "privateKey": self.private_key,
            "agwAddress": self.explicit_agw
        })
        info = self._call_executor("info", payload)
        self.signer_address = Web3.to_checksum_address(info["signerAddress"])
        self.agw_address = Web3.to_checksum_address(info["agwAddress"])
        self.is_agw = info.get("isAgw", False)
        self.is_deployed = info.get("isDeployed", False)

        if self.evm_address:
            self.evm_address = Web3.to_checksum_address(self.evm_address)

    def _call_executor(self, command: str, *args) -> Dict[str, Any]:
        script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "agw_executor.mjs")
        cmd = ["node", script_path, command] + list(args)
        
        env = os.environ.copy()
        env["ABSTRACT_RPC"] = getattr(settings, "ABSTRACT_RPC", "https://api.mainnet.abs.xyz")
        if self.proxy:
            env["HTTP_PROXY"] = self.proxy
            env["HTTPS_PROXY"] = self.proxy
        
        proc = subprocess.run(cmd, capture_output=True, text=True, env=env)
        
        if proc.returncode != 0:
            err_msg = proc.stderr.strip() or proc.stdout.strip()
            try:
                err_json = json.loads(err_msg)
                raise RuntimeError(err_json.get("error", err_msg))
            except Exception:
                raise RuntimeError(f"AGW Executor error (code {proc.returncode}): {err_msg}")

        try:
            res_json = json.loads(proc.stdout.strip())
            if not res_json.get("success"):
                raise RuntimeError(res_json.get("error", "Unknown executor failure"))
            return res_json.get("data", {})
        except json.JSONDecodeError:
            raise RuntimeError(f"Failed to parse AGW executor output: {proc.stdout}")

    def send_transaction(self, to: str, data: str = "0x", value: int = 0) -> Dict[str, Any]:
        payload = json.dumps({
            "privateKey": self.private_key,
            "agwAddress": self.agw_address,
            "tx": {
                "to": to,
                "data": data,
                "value": str(value)
            }
        })
        return self._call_executor("send", payload)

    def unwrap_weth(self, amount_wei: int) -> Dict[str, Any]:
        payload = json.dumps({
            "privateKey": self.private_key,
            "agwAddress": self.agw_address,
            "amountWei": str(amount_wei)
        })
        return self._call_executor("unwrap_weth", payload)

    def transfer_eth(self, to: str, amount_wei: int) -> Dict[str, Any]:
        payload = json.dumps({
            "privateKey": self.private_key,
            "agwAddress": self.agw_address,
            "to": to,
            "amountWei": str(amount_wei)
        })
        return self._call_executor("transfer_eth", payload)

    def transfer_eoa_eth(self, to: str, amount_wei: int) -> Dict[str, Any]:
        pk = self.evm_private_key or self.private_key
        payload = json.dumps({
            "privateKey": pk,
            "to": to,
            "amountWei": str(amount_wei)
        })
        return self._call_executor("transfer_eoa_eth", payload)
