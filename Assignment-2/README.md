# Assignment 2 – Bitcoin Testnet3 Wallet & Transactions

A non-custodial Bitcoin testnet3 wallet that generates BIP39/BIP44 addresses, verifies UTXOs, and creates/signs P2PKH transactions.

---

## Setup

```bash
pip install -r requirements.txt
```

---

## Exercise 1 – Generate Wallet

Creates a BIP39 mnemonic and derives 5 testnet P2PKH addresses via BIP44.

```bash
python implementation/exercise-1.py
```

**Output:** `submissions/exercise01.txt`

---

## Exercise 2 – Verify UTXO

Checks unspent outputs for a funded testnet address.

```bash
python implementation/exercise-2.py <TESTNET_ADDRESS>
```

**Output:** `submissions/exercise02.txt`

---

## Exercise 3 – Sign & Broadcast Transaction

Spends a UTXO from wallet A to wallet B and broadcasts to testnet3.

```bash
python implementation/exercise-3.py <INDEX> <AMOUNT_SATS> <FEE_SATS>
```

```bash
python implementation/exercise-3.py <INDEX> 2000 800
```

| Argument | Description |
|---|---|
| `INDEX` | Funded address index (0–4) |
| `AMOUNT_SATS` | Amount to send in satoshis |
| `FEE_SATS` | Transaction fee in satoshis |

**Output:** `submissions/exercise03.txt`

---

## Submission Structure

```
implementation/
submissions/
```

I have **not** included `.secrets/`, mnemonic files, private keys, or virtual environment folders.
