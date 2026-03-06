#!/usr/bin/env python3
import os
from bip_utils import (
    Bip39MnemonicGenerator, Bip39WordsNum, Bip39SeedGenerator,
    Bip44, Bip44Coins, Bip44Changes
)

DERIVATION_TEMPLATE = "m/44'/1'/0'/0/i"  # required by assignment (testnet)

def create_dirs():
    os.makedirs(".secrets", exist_ok=True)

def generate_wallet(words: int = 12):
    # --- Generate BIP39 mnemonic --
    if words == 12:
        mnemonic = Bip39MnemonicGenerator().FromWordsNumber(Bip39WordsNum.WORDS_NUM_12)
    elif words == 24:
        mnemonic = Bip39MnemonicGenerator().FromWordsNumber(Bip39WordsNum.WORDS_NUM_24)
    else:
        raise ValueError("words must be 12 or 24")

    # --- Derive seed from mnemonic (internally) ---
    seed_bytes = Bip39SeedGenerator(mnemonic).Generate()

    # --- BIP44 derivation for Bitcoin TESTNET ---
    bip44_ctx = Bip44.FromSeed(seed_bytes, Bip44Coins.BITCOIN_TESTNET)
    acct = bip44_ctx.Purpose().Coin().Account(0)  # m/44'/1'/0'
    ext = acct.Change(Bip44Changes.CHAIN_EXT)     # /0

    # --- Derive first 5 receive addresses: /i ---
    addrs = []
    for i in range(5):
        addr = ext.AddressIndex(i).PublicKey().ToAddress()  # P2PKH address for testnet
        addrs.append(addr)

    return str(mnemonic), addrs

def write_submission(addrs):
    out_path = os.path.join("submissions", "exercise01.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(DERIVATION_TEMPLATE + "\n")
        for a in addrs:
            f.write(a + "\n")
    print(f"[OK] Wrote {out_path}")

def store_mnemonic_locally(mnemonic: str, label: str = "walletA"):
    # --- Store locally so you can use it in exercise 3. ---
    path = os.path.join(".secrets", f"{label}_mnemonic.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(mnemonic.strip() + "\n")
    print(f"[INFO] Stored mnemonic in {path}")

def main():
    create_dirs()
    mnemonic, addrs = generate_wallet(words=12)
    write_submission(addrs)
    store_mnemonic_locally(mnemonic, label="walletA")

if __name__ == "__main__":
    main()