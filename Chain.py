"""
Main Part of the BlockChain
"""
import hashlib
import json
from time import time
from urllib.parse import urlparse


class BlockChain(object):
    """
    Main Part of the BlockChain
    Attributes:
        chain: <dict> The chain, or the list of the Blocks.
        transactions: <dict> Temporary stored transactions, awaiting to be stored into blocks.
        nodes: <set> The set of available nodes with url.
    """
    def __init__(self):
        """
        Initial setup of the BlockChain.
        """
        self.chain = []
        self.transactions = []
        self.nodes = set()
        # Creating the initial block with 100 proof hash and 1 previous hash.
        self.new_block(previous_hash=1, proof=100)

    def new_block(self, proof, previous_hash=None):
        """
        Creating new blocks.
        :param proof: <int> Proof of work.
        :param previous_hash: <str> Hash value of the previous block.
        :return: <dict> The newly created block.
        """
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }
        # Empty the temp transactions.
        self.transactions = []
        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount):
        """
        Start a new transaction.
        :param sender: <str> Sender.
        :param recipient: <str> Recipient.
        :param amount: <int> Amount in transaction.
        :return: <int> The value of the present block with transaction recorded.
        """
        self.transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })
        return self.last_block['index'] + 1

    @staticmethod
    def hash(block):
        """
        Hash function.
        :param block: <dict> The block awaiting to be hashed.
        :return: <str> The hash value of a whole block.
        """
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        """
        Give the last position of the chain.
        :return: <dict> Structure of the last block.
        """
        return self.chain[-1]

    def proof_of_work(self, last_proof):
        """
        PoW function.
        :param last_proof: <int> Last proof to generate present proof.
        :return: <int> The right proof.
        """
        proof = 0
        # Loop until a valid proof is founded.
        while self.valid_proof(last_proof, proof) is False:
            proof += 1

        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
        """
        Judge which proof is right.
        :param last_proof: <int> Last proof to join in the calculation.
        :param proof: <int> Proof guessed in the loop.
        :return: <bool> Bool type of result.
        """
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "1926"

    def register_node(self, address):
        """
        Register a node to the network.
        :param address: <str> Url of the node.
        :return: Nothing
        """
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def valid_chain(self, chain):
        # TODO(charles@aic.ac.cn) The process of the validation.
        """
        Judge if a chain is valid.
        :param chain: The chain input.
        :return: The result of judgement.
        """
        return True

    def resolve_conflicts(self):
        # TODO(charles@aic.ac.cn) The process of the consensus system.
        """
        To judge the conflict.
        :return: To judge if the chain is outdated or bad.
        """
        return False

    def save_blocks(self, directory):
        # TODO(charles@aic.ac.cn) Error handle.
        # TODO(charles@aic.ac.cn) Do not write old files.
        """
        Save the chain data and nodes.
        :param directory: The directory to save the data.
        :return: Nothing
        """
        with open(directory + '/index.list', 'w') as fp:
            json.dump(len(self.chain), fp)
        for block_id in [0, len(self.chain)-1]:
            with open(directory + '/db' + str(block_id) + '.json', 'w') as fp:
                json.dump(self.chain[block_id], fp)
        with open(directory + '/nodes.list', 'w') as fp:
            json.dump(list(self.nodes), fp)
        return len(self.chain)
