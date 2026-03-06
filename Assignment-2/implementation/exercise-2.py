#!/usr/bin/env python3
import os
import sys
import requests

BLOCKSTREAM_TESTNET = "https://blockstream.info/testnet/api"

def fetch_utxos(address: str):
    url = f"{BLOCKSTREAM_TESTNET}/address/{address}/utxo"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.json()

def pick_relevant_utxo(utxos):
    if not utxos:
        return None
    # choose largest by value (often the faucet payment)
    return sorted(utxos, key=lambda u: u["value"], reverse=True)[0]

def write_submission(address: str, utxo):
    out_path = os.path.join("submissions", "exercise02.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"Public address: {address}\n")
        if utxo is None:
            f.write("Funding txid: (none found)\n")
            f.write("Amount received: 0\n")
            f.write("Confirmed: false\n")
        else:
            txid = utxo["txid"]
            value = utxo["value"]
            confirmed = bool(utxo.get("status", {}).get("confirmed", False))
            f.write(f"Funding txid: {txid}\n")
            f.write(f"Amount received: {value} sats\n")
            f.write(f"Confirmed: {str(confirmed).lower()}\n")
    print(f"[OK] Wrote {out_path}")

def main():
    if len(sys.argv) != 2:
        print("Using default address: python implementation/exercise-2.py <TESTNET_P2PKH_ADDRESS>")
        sys.exit(1)

    address = sys.argv[1].strip()
    utxos = fetch_utxos(address)
    utxo = pick_relevant_utxo(utxos)
    write_submission(address, utxo)

if __name__ == "__main__":
    main()