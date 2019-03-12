from ecdsa.ecdsa import curve_secp256k1, generator_secp256k1
from electroncash.bitcoin import ser_to_point, point_to_ser
from electroncash.address import Address, Script, hash160, ScriptOutput, OpCodes
from electroncash.address import OpCodes as Op
import hashlib
import time
LOCKTIME_THRESHOLD = 500000000

def joinbytes(iterable):
    """Joins an iterable of bytes and/or integers into a single byte string"""
    return b''.join((bytes((x,)) if isinstance(x,int) else x) for x in iterable)


class LastWillContract:
    """Contract of last will, that is timelocked for inheritor unless the creator bump it
    from the hot wallet or spend from the cold wallet."""

    def __init__(self, addresses):
        time1=7
        time2=0
        self.addresses=addresses
        self.redeemscript = joinbytes([
            len(addresses[0].hash160), addresses[0].hash160,
            len(addresses[1].hash160), addresses[1].hash160,
            len(addresses[2].hash160), addresses[2].hash160,
            3, Op.OP_PICK, Op.OP_TRUE, Op.OP_EQUAL,
            Op.OP_IF,
                5, Op.OP_PICK, Op.OP_HASH160, 3, Op.OP_PICK,
                Op.OP_EQUALVERIFY, 4, Op.OP_PICK, 6, Op.OP_PICK,
                Op.OP_CHECKSIG, Op.OP_NIP, Op.OP_NIP, Op.OP_NIP, Op.OP_NIP, Op.OP_NIP, Op.OP_NIP,
                Op.OP_ELSE,
                3, Op.OP_PICK, 2, Op.OP_EQUAL,
                Op.OP_IF,
                    5, Op.OP_PICK, Op.OP_HASH160, 2, Op.OP_PICK,
                    Op.OP_EQUALVERIFY, 4, Op.OP_PICK, 6, Op.OP_PICK, Op.OP_CHECKSIG,
                    Op.OP_NIP, Op.OP_NIP, Op.OP_NIP, Op.OP_NIP, Op.OP_NIP, Op.OP_NIP,
                    Op.OP_ELSE,
                    3, Op.OP_PICK, 3, Op.OP_EQUAL,
                    Op.OP_IF,
                        3, time1, time2, 64, Op.OP_CHECKSEQUENCEVERIFY, Op.OP_DROP,
                        5, Op.OP_PICK, Op.OP_HASH160, Op.OP_OVER, Op.OP_EQUALVERIFY, 4, Op.OP_PICK,
                        Op.OP_6, Op.OP_PICK, Op.OP_CHECKSIG,
                        Op.OP_NIP, Op.OP_NIP, Op.OP_NIP, Op.OP_NIP, Op.OP_NIP, Op.OP_NIP,
                        Op.OP_ELSE,
                        Op.OP_FALSE,
                    Op.OP_ENDIF,
                Op.OP_ENDIF,
            Op.OP_ENDIF
        ])

        assert 76 < len(self.redeemscript) <= 255  # simplify push in scriptsig; note len is around 200.
        self.address = Address.from_multisig_script(self.redeemscript)


class LastWillContractManager:
    """A device that spends the Last Will in three different ways."""
    def __init__(self,tx, contract, pub, priv, mode):

        self.tx=tx
        self.mode = mode
        self.public = pub
        self.keypair = {pub[0]: (priv, True)}
        self.contract = contract
        self.dummy_scriptsig_redeem = '01' * (140 + len(self.contract.redeemscript))  # make dummy scripts of correct size for size estimation.

    # def refresh(self):
    #     prevout_hash = self.fund_txid_e.text()
    #     prevout_n = int(self.fund_txout_e.text())
    #     value = int(self.fund_value_e.text())
    #     locktime = 0
    #     estimate_fee = lambda x: (1 * x)
    #     out_addr = Address.from_string(self.redeem_address_e.text())
    #
    #     # generate the special spend
    #     inp = self.contract.makeinput(prevout_hash, prevout_n, value)
    #
    #     inputs = [inp]
    #     invalue = value
    #
    #     outputs = [(TYPE_ADDRESS, self.contract.address, 0)]
    #     tx1 = Transaction.from_io(inputs, outputs, locktime)
    #     txsize = len(tx1.serialize(True)) // 2
    #     fee = estimate_fee(txsize)
    #
    #     outputs = [(TYPE_ADDRESS, self.contract.address, invalue - fee)]
    #     tx = Transaction.from_io(inputs, outputs, locktime)
    #     self.contract.signtx(tx)
    #     self.wallet.sign_transaction(tx, self.password)
    #     self.contract.completetx(tx)
    #
    #     desc = "Refreshed Last Will"
    #     show_transaction(tx, self.main_window,
    #                      desc,
    #                      prompt_if_unsaved=True)
    #
    # def spend(self):
    #     prevout_hash = self.fund_txid_e.text()
    #     prevout_n = int(self.fund_txout_e.text())
    #     value = int(self.fund_value_e.text())
    #     locktime = 0
    #     estimate_fee = lambda x: (1 * x)
    #     out_addr = Address.from_string(self.redeem_address_e.text())
    #
    #     # generate the special spend
    #     inp = self.contract.makeinput(prevout_hash, prevout_n, value)
    #
    #     inputs = [inp]
    #     invalue = value
    #
    #     outputs = [(TYPE_ADDRESS, out_addr, 0)]
    #     tx1 = Transaction.from_io(inputs, outputs, locktime)
    #     txsize = len(tx1.serialize(True)) // 2
    #     fee = estimate_fee(txsize)
    #
    #     outputs = [(TYPE_ADDRESS, out_addr, invalue - fee)]
    #     tx = Transaction.from_io(inputs, outputs, locktime)
    #     self.contract.signtx(tx)
    #     self.wallet.sign_transaction(tx, self.password)
    #     self.contract.completetx(tx)
    #
    #     desc = "Ended Last Will Contract"
    #     show_transaction(tx, self.main_window,
    #                      desc,
    #                      prompt_if_unsaved=True)
    #
    # def inherit(self):
    #     prevout_hash = self.fund_txid_e.text()
    #     prevout_n = int(self.fund_txout_e.text())
    #     value = int(self.fund_value_e.text())
    #     locktime = 0
    #     estimate_fee = lambda x: (1 * x)
    #     out_addr = Address.from_string(self.redeem_address_e.text())
    #
    #     # generate the special spend
    #     inp = self.contract.makeinput(prevout_hash, prevout_n, value)
    #
    #     inputs = [inp]
    #     invalue = value
    #
    #     outputs = [(TYPE_ADDRESS, out_addr, 0)]
    #     tx1 = Transaction.from_io(inputs, outputs, locktime)
    #     txsize = len(tx1.serialize(True)) // 2
    #     fee = estimate_fee(txsize)
    #
    #     outputs = [(TYPE_ADDRESS, out_addr, invalue - fee)]
    #     tx = Transaction.from_io(inputs, outputs, locktime)
    #     self.contract.signtx(tx)
    #     self.wallet.sign_transaction(tx, self.password)
    #     self.contract.completetx(tx)
    #
    #     desc = "Inherited From Last Will"
    #     show_transaction(tx, self.main_window,
    #                      desc,
    #                      prompt_if_unsaved=True)
    def makeinput(self, prevout_hash, prevout_n, value):
        """
        Construct an unsigned input for adding to a transaction. scriptSig is
        set to a dummy value, for size estimation.

        (note: Transaction object will fail to broadcast until you sign and run `completetx`)
        """

        scriptSig = self.dummy_scriptsig_redeem
        pubkey = self.public
        flag=2**22       # 2^22 means the sequence is in time not in blocks
        relative_time= 21   # 7 times 512s is 1h
        seq=flag+relative_time
        txin = dict(
            prevout_hash = prevout_hash,
            prevout_n = prevout_n,
            sequence = 0,
            scriptSig = scriptSig,

            type = 'unknown',
            address = self.contract.address,
            scriptCode = self.contract.redeemscript.hex(),
            num_sig = 1,
            signatures = [None],
            x_pubkeys = pubkey,
            value = value,
            )
        return txin

    def signtx(self, tx):
        """generic tx signer for compressed pubkey"""
        tx.sign(self.keypair)

    def completetx(self, tx):
        """
        Completes transaction by creating scriptSig. You need to sign the
        transaction before using this (see `signtx`). `secret` may be bytes
        (if redeeming) or None (if refunding).

        This works on multiple utxos if needed.
        """
        pub = bytes.fromhex(self.public[0])
        for txin in tx.inputs():
            # find matching inputs
            if txin['address'] != self.contract.address:
                continue
            sig = txin['signatures'][0]
            if not sig:
                continue
            sig = bytes.fromhex(sig)
            if txin['scriptSig'] == self.dummy_scriptsig_redeem:
                script = [
                    len(pub), pub,
                    len(sig), sig,
                    len(self.contract.redeemscript), self.contract.redeemscript, # Script shorter than 75 bits
                    ]
            txin['scriptSig'] = joinbytes(script).hex()
        # need to update the raw, otherwise weird stuff happens.
        tx.raw = tx.serialize()

