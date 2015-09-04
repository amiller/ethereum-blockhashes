Blockhash contract
==================
This contract provides a reliable mapping from block number to the corresponding blockhash, even for historical blocks aged more than 256 blocks ago.

This is a workaround for a limitation of the `block.prevhash` instruction, namely that it only supports the 256 most recent blocks. This limitation affects Etherpot, among others.
See: http://aakilfernandes.github.io/blockhashes-are-only-good-for-256-blocks/

This contract stores the mapping from block number to blockhash in its local storage.
There are two ways to add blocks.

The first method, `add_recent`, simply uses the `prevhash` instruction. Hopefully, this method will be called regularly, e.g. by miners.

The second method, `add_old`, makes it possible to fill in gaps in history. It allows you to add the hash of a *parent* block, as long as the hash of the *child* is already stored. This method expects the rlp-encoded block header (typically ~476 bytes) to be passed as a string. It recomputes the hash of the header and checks that it matches the child hash in contract storage. If so, it parses out the parent hash (i.e., the first 32 bytes of the header) and stores it. With this, it's possible to fill in any amount of history and walk back.

Performance
============

- `add_recent`: 20700 gas per block
- `add_old`: 36700 gas per block

Currently, an `sstore` instruction takes `20000` gas. Although an rlp-encoded block header is 476 bytes, apparently 210 of these are zero. The cost of transaction data is different for zero or nonzero bytes; given this distribution, the data should contribute `15000` to the total. The cost of computing `sha3` itself should contribute barely anything to the total, at 120 gas for fifteen sha3 words.

According to benchmarks (see `test_blockhashes.py`), `add_recent` takes about `20700` gas and `add_old` takes about `36700`, not including the base gas cost of `21000` per transaction. This is consistent with the prediction above.

New: A Live Instance is Deployed!
=================================
Thanks to Kobi Gurk, an instance of this contract is now live:
http://etherscan.io/address/0xb278e4cb20dfbf97e78f27001f6b15288302f4d7

Pointer to the exact code of the live contract:
https://github.com/kobigurk/ethereum-blockhashes/blob/c4b5f338be68749156741cfb847af3e2ff65bab4/blockhashes.se

Given the current Ether price and default gas price limits imposed by miners, it is expensive to invoke this contract (0.2 cents per block, or $14 per day). Therefore we are running a server that pings this contract once every 256 blocks.

