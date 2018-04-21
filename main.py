# title           :main.py
# description     :The console interface and main program of the blockchain based on flask.
# author          :CharlesYang
# created         :20180421
# version         :0.0.5
# usage           :python3 main.py
# notes           :
# python_version  :3.6.4
# ==============================================================================
"""
Web interact with the BlockChain
"""
# TODO(charles@aic.ac.cn) Save transactions timely or when close the program into files.
# TODO(charles@aic.ac.cn) Config, especially initial config, is totally a mess.
from flask import Flask, jsonify, request
from uuid import uuid4
from Chain import BlockChain
import configparser as cp
import os
import logging
from gevent import monkey
from gevent.pywsgi import WSGIServer
import time
monkey.patch_all()

# Setup config reader
config = cp.ConfigParser()
app = Flask(__name__)
# ID of the miner/user.
node_identifier = '-1'
# Initialize the main blockchain.
MainChain = BlockChain()
# Setup loggers
# TODO:(charles@aic.ac.cn) Set debug level in config file.
logger = logging.getLogger('BlockChain')
logger.setLevel(logging.DEBUG)
fileLogHandler = logging.FileHandler('blockchain.log')
logger.addHandler(fileLogHandler)


def config_init():
    """
    Initialize the config file.
    :return: None
    """
    # Create config sections and default settings.
    config.add_section('api')
    config.set('api', 'bind_ip', '0.0.0.0')
    config.set('api', 'port', '5000')
    config.add_section('identity')
    # User id, also the id for mining and transaction.
    user_uuid = str(uuid4()).replace('-', '')
    logger.info('User uuid: ' + user_uuid)
    config.set('identity', 'uuid', user_uuid)
    config.add_section('data')
    config.set('data', 'chain_dir', 'chain_data')
    config.write(open('config.ini', 'w'))
    logger.info('First run config generated.')


@app.route('/nodes', methods=['GET'])
def nodes_list():
    """
    Show the list of registered nodes.
    :return: The json type of the nodes data.
    """
    response = {
        'nodes': [node for node in MainChain.nodes],
        'length': len(MainChain.nodes),
    }
    return jsonify(response), 200


@app.route('/chain', methods=['GET'])
def full_chain():
    """
    Read the full chain data.
    :return: The json type of the chain data.
    """
    response = {
        'chain': MainChain.chain,
        'length': len(MainChain.chain),
    }
    return jsonify(response), 200


@app.route('/mine', methods=['GET'])
def mine():
    # TODO:(charles@aic.ac.cn) Erase temp transactions when a new block is created.
    """
    Main in the blockchain.
    :return: Information about the mined data.
    """
    last_block = MainChain.last_block
    last_proof = last_block['proof']
    proof = MainChain.proof_of_work(last_proof)
    # The sender of mined transaction is 0.
    MainChain.new_transaction(
        sender="0",
        recipient=node_identifier,
        amount=1,
    )

    block = MainChain.new_block(proof)

    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
        # Save automatically when a new block is generaterd
        'saved_block': MainChain.save_blocks(data_path)
    }
    MainChain.request_resolve(config.get('api', 'bind_ip') + ':' + str(config.getint('api', 'port')))
    return jsonify(response), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    # TODO:(charles@aic.ac.cn) Broadcast this transaction to the other nodes.
    """
    Start a new Transaction.
    data = {
        sender: Send of the transaction.
        recipient: Recipient of the transaction.
        amount: Amount to transfer.
    }
    :return: The result of the transaction.
    """
    values = request.get_json()
    # Verify that all necessary elements are in the request.
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400
    # Judge if the extra message is in the transaction.
    if 'message' in values:
        index = MainChain.new_transaction(values['sender'], values['recipient'], values['amount'], values['message'])
    else:
        index = MainChain.new_transaction(values['sender'], values['recipient'], values['amount'])

    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 201


@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    """
    Register a node in the network.
    data = {
        nodes:[list of the node]
    }
    :return: The result of the registration.
    """
    values = request.get_json()

    nodes = values.get('nodes')
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    for node in nodes:
        MainChain.register_node(node)

    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(MainChain.nodes),
        # When nodes are added, extra process will be performed to sync with them.
        'sync_replaced': MainChain.resolve_conflicts()
    }
    return jsonify(response), 201


@app.route('/nodes/resolve', methods=['POST'])
def consensus():
    """
    Consensus system check.
    data = {
        nodes: [list of nodes]
    }
    :return: The status of the present chain.
    """
    values = request.get_json()
    # Judge whether it's total sync or single point sync.
    if values is None:
        nodes = None
    else:
        nodes = values.get('nodes')
        if nodes is None:
            return "Error: Please supply a valid list of nodes", 400
    # time.sleep(0.5)
    replaced = MainChain.resolve_conflicts(request_node=nodes)

    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': MainChain.chain
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': MainChain.chain
        }

    return jsonify(response), 200


@app.route('/save', methods=['GET'])
# TODO:(charles@aic.ac.cn) This method should be removed when automatic saving is coded.
def save_blocks():
    """
    Save blocks into file.
    :return: Result of the saving and saved blocks.
    """
    response = {
        'message': 'Chain state saved',
        'changed_block': MainChain.save_blocks(data_path)
    }
    return jsonify(response), 200


if __name__ == '__main__':
    # Judge if config is missing.
    logger.info('Welcome to blockchain project.')
    if not os.path.exists('config.ini'):
        logging.warning('Config file not found, setup for the first run.')
        config_init()
    # Read the config file.
    config.read('config.ini')
    # Create data dir.
    data_path = config.get('data', 'chain_dir')
    if not os.path.exists(data_path):
        logger.warning('Data path not found, setup for the first run.')
        os.makedirs(data_path)
        logger.info('Will loading blocks.')
    # Load exists data from directory.
    MainChain.load_blocks(data_path)
    # Initially sync with nodes.
    MainChain.resolve_conflicts()
    # Initially save blocks.
    MainChain.save_blocks(data_path)
    # Define local api url.
    api_url = 'http://' + config.get('api', 'bind_ip') + ':' + str(config.getint('api', 'port'))
    # Read user id.
    node_identifier = config.get('identity', 'uuid')
    """
    Run the main app.
    """
    logger.info('Now the API is open in ' + api_url)
    # Flask is now replaced with concurrent and non-blocking service.
    http_server = WSGIServer((config.get('api', 'bind_ip'), config.getint('api', 'port')), app)
    http_server.serve_forever()
