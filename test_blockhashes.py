from ethereum import tester
from ethereum.utils import rlp

blocknum_code = open('./blockhashes.se').read()

s = tester.state()
contract = s.abi_contract(blocknum_code)
s.mine(100)

TX_BASE_GAS = 21000

def check_storage():
    # Load the expected blockhashes
    ground_truth = dict( (i,s.blocks[i].hex_hash()) for i in range(len(s.blocks)-1))

    # Load the current storage trie for this contract
    d = s.block.get_storage(contract.address).to_dict()
    test = dict( (int(k.encode('hex'),16), v[1:].encode('hex').zfill(64)) for k,v in d.iteritems())

    #print 'ground', ground_truth
    #print 'test', test
    assert test == ground_truth, 'Consistency check: failed'
    print 'Consistency check: OK'

# Test adding recent blocks
def test_short():
    state = s.snapshot()
    print 'Testing add_recent'
    for i in range(len(s.blocks)-1):
        contract.add_recent(i)
    print 'gas used',  s.block.gas_used - (len(s.blocks)-1) * TX_BASE_GAS
    print 'average:', s.block.gas_used / (len(s.blocks)-1.) - TX_BASE_GAS

    check_storage()
    s.revert(state)

# Test the "long" way
def test_long():
    state = s.snapshot()
    print 'Testing add_old'
    contract.add_recent(len(s.blocks)-2)
    for i in range(len(s.blocks) - 2)[::-1]:
        header = s.blocks[i].header
        contract.add_old(rlp.encode(s.blocks[i+1].header), i)
    print 'gas used',  s.block.gas_used - (len(s.blocks)-1) * TX_BASE_GAS
    print 'average:', s.block.gas_used / (len(s.blocks)-1.) - TX_BASE_GAS

    check_storage()
    s.revert(state)


def print_dict(d):
    for k,v in d.iteritems():
        print int(k.encode('hex'),16), v[1:].encode('hex')

#print_dict(s.block.get_storage(contract.address).to_dict())
#print 'block hashes'
#for i,b in enumerate(s.blocks):
#    print i, b.hex_hash()

if __name__ == '__main__':
    test_short()
    test_long()
