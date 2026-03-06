#!/usr/bin/env python3
import os
import sys
import json
import requests

from bip_utils import (
    Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes
)

from bitcoin import SelectParams
from bitcoin.core import (
    b2lx, lx, COutPoint, CMutableTxIn, CMutableTxOut, CMutableTransaction
)
from bitcoin.core.script import (
    CScript, SignatureHash, SIGHASH_ALL
)
from bitcoin.wallet import CBitcoinSecret, P2PKHBitcoinAddress

BLOCKSTREAM_TESTNET = "https://blockstream.info/testnet/api"
DERIVATION_TEMPLATE = "m/44'/1'/0'/0/i"

def read_mnemonic(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()

def derive_walletA_keypair(mnemonic: str, index: int):
    seed = Bip39SeedGenerator(mnemonic).Generate()
    ctx = Bip44.FromSeed(seed, Bip44Coins.BITCOIN_TESTNET)
    acct = ctx.Purpose().Coin().Account(0)
    ext = acct.Change(Bip44Changes.CHAIN_EXT)
    node = ext.AddressIndex(index)

    sender_addr = node.PublicKey().ToAddress()  # P2PKH testnet address
    wif = node.PrivateKey().ToWif()             # WIF for testnet
    return sender_addr, wif

def create_walletB_and_get_addr():
    # Create a second wallet (wallet B) mnemonic 
    from bip_utils import Bip39MnemonicGenerator, Bip39WordsNum
    mnemonic_b = Bip39MnemonicGenerator().FromWordsNumber(Bip39WordsNum.WORDS_NUM_12)
    path = os.path.join(".secrets", "walletB_mnemonic.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(str(mnemonic_b).strip() + "\n")

    # Derive wallet B first receive address
    seed = Bip39SeedGenerator(mnemonic_b).Generate()
    ctx = Bip44.FromSeed(seed, Bip44Coins.BITCOIN_TESTNET)
    acct = ctx.Purpose().Coin().Account(0)
    ext = acct.Change(Bip44Changes.CHAIN_EXT)
    recipient_addr = ext.AddressIndex(0).PublicKey().ToAddress()
    return str(mnemonic_b), recipient_addr

def fetch_utxos(address: str):
    url = f"{BLOCKSTREAM_TESTNET}/address/{address}/utxo"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.json()

def pick_utxo(utxos):
    # pick largest confirmed if possible
    if not utxos:
        return None
    confirmed = [u for u in utxos if u.get("status", {}).get("confirmed", False)]
    pool = confirmed if confirmed else utxos
    return sorted(pool, key=lambda u: u["value"], reverse=True)[0]

def estimate_fee_sats(fee_rate_sat_per_vb: int = 5, inputs: int = 1, outputs: int = 2):
    # Rough legacy P2PKH size estimate:
    # tx bytes ≈ 10 + 148*inputs + 34*outputs
    size = 10 + 148 * inputs + 34 * outputs
    return size * fee_rate_sat_per_vb

def build_and_sign_p2pkh(sender_addr: str, sender_wif: str, recipient_addr: str,
                         utxo_txid: str, utxo_vout: int, utxo_value_sats: int,
                         send_value_sats: int, fee_sats: int):
    SelectParams("testnet")

    if send_value_sats + fee_sats > utxo_value_sats:
        raise ValueError("Not enough funds in selected UTXO for amount+fee")

    change_sats = utxo_value_sats - send_value_sats - fee_sats

    # -- Create txin
    outpoint = COutPoint(lx(utxo_txid), utxo_vout)
    txin = CMutableTxIn(outpoint)

    # -- Create txouts (recipient + optional change) --
    recipient_spk = P2PKHBitcoinAddress(recipient_addr).to_scriptPubKey()
    txouts = [CMutableTxOut(send_value_sats, recipient_spk)]

    # Add change output if it's not dust
    if change_sats >= 546:  # common dust threshold for P2PKH
        change_spk = P2PKHBitcoinAddress(sender_addr).to_scriptPubKey()
        txouts.append(CMutableTxOut(change_sats, change_spk))

    # -- Create unsigned tx --
    tx = CMutableTransaction([txin], txouts)

    # -- Sign (P2PKH legacy): --
    # scriptPubKey of the UTXO being spent is derived from sender address
    seckey = CBitcoinSecret(sender_wif)
    pubkey = seckey.pub
    script_pubkey = P2PKHBitcoinAddress(sender_addr).to_scriptPubKey()

    sighash = SignatureHash(script_pubkey, tx, 0, SIGHASH_ALL)
    sig = seckey.sign(sighash) + bytes([SIGHASH_ALL])

    txin.scriptSig = CScript([sig, pubkey])

    return tx, change_sats

def broadcast_tx(tx) -> str:
    raw_hex = tx.serialize().hex()
    url = f"{BLOCKSTREAM_TESTNET}/tx"
    r = requests.post(url, data=raw_hex, timeout=30)
    r.raise_for_status()
    # returns txid as plain text
    return r.text.strip()

def write_submission(sender_addr, recipient_addr, amount_sats, fee_sats, txid):
    out_path = os.path.join("submissions", "exercise03.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"Sender public address (wallet A): {sender_addr}\n")
        f.write(f"Recipient public address (wallet B): {recipient_addr}\n")
        f.write(f"Amount sent (sats): {amount_sats}\n")
        f.write(f"Fee (sats): {fee_sats}\n")
        f.write(f"Broadcast txid: {txid}\n")
    print(f"[OK] Wrote {out_path}")

def main():
    if len(sys.argv) < 2:
            print("Usage: python implementation/exercise-3.py <ADDRESS_INDEX> [AMOUNT_SATS] [FEE_SATS]")
            print("Example: python implementation/exercise-3.py 0 2000 800")
        sys.exit(1)

    address_index = int(sys.argv[1])
    amount_sats = int(sys.argv[2]) if len(sys.argv) >= 3 else 2000

    # Fee: allow override, otherwise estimate ~5 sat/vB (safe for testnet)
    if len(sys.argv) >= 4:
        fee_sats = int(sys.argv[3])
    else:
        # we have to get 2 outputs (recipient + change)
        fee_sats = estimate_fee_sats(fee_rate_sat_per_vb=5, inputs=1, outputs=2)

    mnemonic_path = os.path.join(".secrets", "walletA_mnemonic.txt")
    if not os.path.exists(mnemonic_path):
        raise FileNotFoundError(
            "Missing .secrets walletA"
        )

    walletA_mnemonic = read_mnemonic(mnemonic_path)
    sender_addr, sender_wif = derive_walletA_keypair(walletA_mnemonic, address_index)

    _, recipient_addr = create_walletB_and_get_addr()

    # Find a spendable UTXO
    
    utxos = fetch_utxos(sender_addr)
    utxo = pick_utxo(utxos)
    if utxo is None:
        raise RuntimeError("No UTXOs found.")

    utxo_txid = utxo["txid"]
    utxo_vout = utxo["vout"]
    utxo_value = utxo["value"]

    # Build + sign + broadcast
    tx, change_sats = build_and_sign_p2pkh(
        sender_addr=sender_addr,
        sender_wif=sender_wif,
        recipient_addr=recipient_addr,
        utxo_txid=utxo_txid,
        utxo_vout=utxo_vout,
        utxo_value_sats=utxo_value,
        send_value_sats=amount_sats,
        fee_sats=fee_sats
    )

    txid = broadcast_tx(tx)

    write_submission(sender_addr, recipient_addr, amount_sats, fee_sats, txid)

    print("[INFO] Sender UTXO spent:", utxo_txid, utxo_vout, utxo_value, "sats")
    print("[INFO] Change is returned to sender:", change_sats, "sats")
    print("[INFO] Broadcast txid:", txid)
    print("[INFO] Wallet B mnemonic stored in .secrets walletB")

if __name__ == "__main__":
    main()