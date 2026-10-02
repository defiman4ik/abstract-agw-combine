import { createAbstractClient, getSmartAccountAddressFromInitialSigner, isAGWAccount } from "@abstract-foundation/agw-client";
import { privateKeyToAccount } from "viem/accounts";
import { createPublicClient, createWalletClient, http, encodeFunctionData, parseAbi } from "viem";
import { abstract } from "viem/chains";

const RPC_URL = process.env.ABSTRACT_RPC || "https://api.mainnet.abs.xyz";
const WETH_ADDRESS = "0x3439153eb7af838ad19d56e1571fbd09333c2809";

export const publicClient = createPublicClient({
  chain: abstract,
  transport: http(RPC_URL, { batch: true }),
});

import { createSiweMessage } from "viem/siwe";

export async function resolvePrivyAgw(account) {
  try {
    const initRes = await fetch("https://auth.privy.io/api/v1/siwe/init", {
      method: "POST",
      headers: {
        "privy-app-id": "cm04asygd041fmry9zmcyn5o5",
        "Origin": "https://abs.xyz",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ address: account.address }),
    });
    if (!initRes.ok) return null;
    const initData = await initRes.json();
    if (!initData.nonce) return null;

    const message = createSiweMessage({
      address: account.address,
      chainId: 2741,
      domain: "abs.xyz",
      nonce: initData.nonce,
      uri: "https://abs.xyz",
      version: "1",
      issuedAt: new Date(),
      statement: "By signing, you are proving you own this wallet and are logging in. This does not initiate a transaction or cost any fees.",
    });

    const signature = await account.signMessage({ message });
    const authRes = await fetch("https://auth.privy.io/api/v1/siwe/authenticate", {
      method: "POST",
      headers: {
        "privy-app-id": "cm04asygd041fmry9zmcyn5o5",
        "Origin": "https://abs.xyz",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        message,
        signature,
        chainId: "eip155:2741",
        walletClientType: "metamask",
        connectorType: "injected",
      }),
    });
    if (!authRes.ok) return null;
    const data = await authRes.json();
    const customMeta = data?.user?.custom_metadata;
    if (customMeta) {
      if (typeof customMeta === "string") {
        try {
          const parsed = JSON.parse(customMeta);
          if (parsed.walletAddress) return parsed.walletAddress;
        } catch (e) {}
      } else if (customMeta.walletAddress) {
        return customMeta.walletAddress;
      }
    }
  } catch (err) {
    // Silently fall back if network or privy is unreachable
  }
  return null;
}

export async function getAccountInfo(privateKey, explicitAgwAddress = null) {
  const signer = privateKeyToAccount(privateKey);
  let agwAddress = explicitAgwAddress;
  if (!agwAddress) {
    agwAddress = await resolvePrivyAgw(signer);
  }
  if (!agwAddress) {
    agwAddress = await getSmartAccountAddressFromInitialSigner(signer.address, publicClient);
  }
  const isAgw = await isAGWAccount(publicClient, agwAddress).catch(() => false);
  const code = await publicClient.getCode({ address: agwAddress }).catch(() => null);
  const isDeployed = Boolean(code && code !== "0x");

  return {
    signerAddress: signer.address,
    agwAddress,
    isAgw,
    isDeployed,
  };
}

export async function sendAgwTransaction(privateKey, tx, explicitAgwAddress = null) {
  const signer = privateKeyToAccount(privateKey);
  let agwAddress = explicitAgwAddress;
  if (!agwAddress) {
    agwAddress = await resolvePrivyAgw(signer);
  }
  if (!agwAddress) {
    agwAddress = await getSmartAccountAddressFromInitialSigner(signer.address, publicClient);
  }

  const client = await createAbstractClient({
    signer,
    chain: abstract,
    transport: http(RPC_URL),
    publicTransport: http(RPC_URL, { batch: true }),
    address: agwAddress,
  });

  const txParams = {
    to: tx.to,
    data: tx.data || "0x",
    value: tx.value ? BigInt(tx.value) : 0n,
  };

  const hash = await client.sendTransaction(txParams);
  const receipt = await publicClient.waitForTransactionReceipt({ hash, timeout: 60000 });

  return {
    hash,
    status: receipt.status === "success" ? 1 : 0,
    blockNumber: receipt.blockNumber.toString(),
  };
}

export async function unwrapWeth(privateKey, amountWei, explicitAgwAddress = null) {
  const data = encodeFunctionData({
    abi: parseAbi(["function withdraw(uint256 wad) external"]),
    functionName: "withdraw",
    args: [BigInt(amountWei)],
  });

  return await sendAgwTransaction(privateKey, {
    to: WETH_ADDRESS,
    data,
    value: "0",
  }, explicitAgwAddress);
}

export async function transferEth(privateKey, to, amountWei, explicitAgwAddress = null) {
  return await sendAgwTransaction(privateKey, {
    to,
    value: amountWei.toString(),
    data: "0x",
  }, explicitAgwAddress);
}

export async function transferEoaEth(privateKey, to, amountWei) {
  const account = privateKeyToAccount(privateKey);
  const walletClient = createWalletClient({
    account,
    chain: abstract,
    transport: http(RPC_URL),
  });

  const hash = await walletClient.sendTransaction({
    to,
    value: BigInt(amountWei),
  });
  const receipt = await publicClient.waitForTransactionReceipt({ hash, timeout: 60000 });

  return {
    hash,
    status: receipt.status === "success" ? 1 : 0,
    blockNumber: receipt.blockNumber.toString(),
  };
}

// CLI handler for Python subprocess execution
const args = process.argv.slice(2);
if (args.length > 0) {
  const command = args[0];

  (async () => {
    try {
      if (command === "info") {
        const payload = JSON.parse(args[1]);
        const res = await getAccountInfo(payload.privateKey, payload.agwAddress || null);
        console.log(JSON.stringify({ success: true, data: res }));
      } else if (command === "send") {
        const payload = JSON.parse(args[1]);
        const res = await sendAgwTransaction(payload.privateKey, payload.tx, payload.agwAddress || null);
        console.log(JSON.stringify({ success: true, data: res }));
      } else if (command === "unwrap_weth") {
        const payload = JSON.parse(args[1]);
        const res = await unwrapWeth(payload.privateKey, payload.amountWei, payload.agwAddress || null);
        console.log(JSON.stringify({ success: true, data: res }));
      } else if (command === "transfer_eth") {
        const payload = JSON.parse(args[1]);
        const res = await transferEth(payload.privateKey, payload.to, payload.amountWei, payload.agwAddress || null);
        console.log(JSON.stringify({ success: true, data: res }));
      } else if (command === "transfer_eoa_eth") {
        const payload = JSON.parse(args[1]);
        const res = await transferEoaEth(payload.privateKey, payload.to, payload.amountWei);
        console.log(JSON.stringify({ success: true, data: res }));
      } else {
        console.error(JSON.stringify({ success: false, error: `Unknown command: ${command}` }));
        process.exit(1);
      }
    } catch (err) {
      console.error(JSON.stringify({ success: false, error: err.message || String(err) }));
      process.exit(1);
    }
  })();
}
