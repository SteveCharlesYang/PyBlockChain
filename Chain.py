# title           :Chain.py
# description     :The core function of the blockchain.
# author          :CharlesYang
# created         :20180421
# version         :0.0.5
# usage           :from Chain import BlockChain
# notes           :
# python_version  :3.6.4
# ==============================================================================
"""
Main Part of the BlockChain
"""
import hashlib
import json
from time import time
from urllib.parse import urlparse
import os
import requests


class BlockChain(object):
    # TODO:(charles@aic.ac.cn) Save temporary stored data when program is going to close.
    # TODO:(charles@aic.ac.cn) Replace directly send with route requests in the network.
    # TODO:(charles@aic.ac.cn) Creating user-friendly interface.
    """
    Main Part of the BlockChain
    Attributes:
        chain: <dict> The chain, or the list of the Blocks.
        transactions: <dict> Temporary stored transactions, awaiting to be stored into blocks.
        nodes: <set> The set of available nodes with url.
    Methods:
        new_block: Creating new blocks.
        new_transaction: Start a new transaction.
        hash: Hash function.
        last_block: Give the last position of the chain.
        proof_of_work: PoW function.
        valid_proof: Judge which proof is right.
        request_resolve: Request other nodes to sync.
        register_node: Register a node to the network.
        valid_chain: Judge if a chain is valid.
        resolve_conflicts: To judge the conflict.
        save_blocks: Save the chain data and nodes.
        load_blocks: Load the chain data and nodes.
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

    def new_transaction(self, sender, recipient, amount, message=None):
        """
        Start a new transaction.
        :param sender: <str> Sender.
        :param recipient: <str> Recipient.
        :param amount: <int> Amount in transaction.
        :param message: <str> Message transferred in the network.
        :return: <int> The value of the present block with transaction recorded.
        """
        self.transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
            'message': message,
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
        # TODO:(charles@aic.ac.cn) Add additional steps to verify.
        """
        Register a node to the network.
        :param address: <str> Url of the node.
        :return: Nothing
        """
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def request_resolve(self, node_address):
        """
        Request remote nodes to sync data.
        :param node_address: <list> The address required to sync with.
        :return: Nothing
        """
        # Send the requests to all of the nodes.
        neighbours = self.nodes
        for node in neighbours:
            # TODO:(charles@aic.ac.cn) Give returns to show the status of sending.
            try:
                requests.post(f'http://{node}/nodes/resolve', json={'nodes': node_address})
            # TODO:(charles@aic.ac.cn) Add exception handle and message of this error.
            except requests.exceptions.RequestException:
                pass

    def valid_chain(self, chain):
        """
        Judge if a chain is valid.
        :param chain: The chain input.
        :return: The result of judgement.
        """
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]

            if block['previous_hash'] != self.hash(last_block):
                return False

            if not self.valid_proof(last_block['proof'], block['proof']):
                return False

            last_block = block
            current_index += 1

        return True

    def resolve_conflicts(self, request_node=None):
        """
        To judge the conflict.
        :param request_node: <str> The node to resolve.
        :return: To judge if the chain is outdated or bad.
        """
        # Judge if the mode is total sync or single point sync.
        if request_node is None:
            neighbours = self.nodes
        else:
            neighbours = [request_node]
        new_chain = None
        # Define the minimal requirement of sync
        max_length = len(self.chain)
        # Send requests to all of the nodes in the list
        for node in neighbours:
            try:
                # TODO:(charles@aic.ac.cn) Request for part of the chain to improve performance.
                response = requests.get(f'http://{node}/chain')
                if response.status_code == 200:
                    length = response.json()['length']
                    chain = response.json()['chain']
                    # The requirement of length and validation must both be met.
                    if length > max_length and self.valid_chain(chain):
                        max_length = length
                        new_chain = chain
            # TODO:(charles@aic.ac.cn) Add exception handle and message of this error.
            except requests.exceptions.RequestException:
                pass
        # Replace the chain store locally.
        if new_chain:
            self.chain = new_chain
            return True

        return False

    def save_blocks(self, directory):
        # TODO(charles@aic.ac.cn) Error handle.
        """
        Save the chain data and nodes.
        :param directory: The directory to save the data.
        :return: Nothing
        """
        changed_block = []
        with open(directory + '/index.list', 'w') as fp:
            json.dump(len(self.chain), fp)
        for block_id in reversed(range(0, len(self.chain))):
            if not os.path.exists(directory + '/db' + str(block_id) + '.json'):
                with open(directory + '/db' + str(block_id) + '.json', 'w') as fp:
                    json.dump(self.chain[block_id], fp)
                    changed_block.append(block_id)
            else:
                continue
        with open(directory + '/nodes.json', 'w') as fp:
            json.dump(list(self.nodes), fp)
        return changed_block

    def load_blocks(self, directory):
        """
        Load the chain data and nodes.
        :param directory: The directory to load the data.
        :return: Nothing
        """
        load_chain = []
        if os.path.exists(directory + '/index.list'):
            with open(directory + '/index.list') as fp:
                load_size = json.load(fp)
            for block_id in range(0, load_size):
                with open(directory + '/db' + str(block_id) + '.json') as fp:
                    load_chain.append(json.load(fp))
            with open(directory + '/nodes.json') as fp:
                load_nodes = json.load(fp)
            self.nodes = set(load_nodes)
            self.chain = load_chain
        return len(self.chain)
