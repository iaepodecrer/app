"""
Coin Change Problem Solver

This script demonstrates step-by-step reasoning to solve the classic coin change problem:
Given a set of coin denominations and a target amount, find the minimum number of coins
needed to make up that amount.

The script shows both the naive recursive approach and an optimized dynamic programming solution.
"""

import time
from functools import lru_cache

def coin_change_recursive(coins, amount):
    """
    Naive recursive solution to the coin change problem.
    
    Step 1: Define the base cases
    Step 2: For each possible coin, recursively find solution for remaining amount
    Step 3: Return the minimum number of coins needed
    """
    # Base case: If amount is 0, no coins needed
    if amount == 0:
        return 0
    
    # Base case: If amount is negative, solution is impossible
    if amount < 0:
        return float('inf')
    
    # Initialize minimum coins to infinity
    min_coins = float('inf')
    
    # Try each coin denomination and find the minimum
    for coin in coins:
        # Recursive call for remaining amount after using current coin
        result = coin_change_recursive(coins, amount - coin)
        
        # If a solution exists for the remaining amount
        if result != float('inf'):
            # Update minimum if using this coin gives a better solution
            # (add 1 for the current coin)
            min_coins = min(min_coins, result + 1)
    
    return min_coins

def coin_change_dp(coins, amount):
    """
    Dynamic programming solution to the coin change problem.
    
    Step 1: Create a DP table to store solutions to subproblems
    Step 2: Initialize with base cases
    Step 3: Fill the table bottom-up, using optimal solutions to smaller problems
    Step 4: Return the final result
    """
    # Initialize dp array with amount+1 (which is greater than any possible solution)
    # dp[i] represents the minimum number of coins needed to make amount i
    dp = [float('inf')] * (amount + 1)
    
    # Base case: 0 amount requires 0 coins
    dp[0] = 0
    
    # Build up solutions for each amount from 1 to target amount
    for current_amount in range(1, amount + 1):
        # For each amount, try using each coin denomination
        for coin in coins:
            # If the coin value is not greater than current amount
            if coin <= current_amount:
                # Check if using this coin gives a better solution
                # dp[current_amount - coin] represents optimal solution for remaining amount
                dp[current_amount] = min(dp[current_amount], dp[current_amount - coin] + 1)
    
    # If no solution exists, dp[amount] will still be infinity
    return dp[amount] if dp[amount] != float('inf') else -1

def test_and_compare(coins, amount):
    """
    Test both solutions and compare execution time and results.
    """
    print(f"Solving coin change problem for amount {amount} with coins {coins}")
    print("-" * 50)
    
    # Test recursive solution (only for small inputs)
    if amount <= 30:  # Limit recursive solution to avoid excessive runtime
        start_time = time.time()
        recursive_result = coin_change_recursive(coins, amount)
        recursive_time = time.time() - start_time
        
        print(f"Recursive solution:")
        print(f"  Minimum coins: {recursive_result}")
        print(f"  Execution time: {recursive_time:.6f} seconds")
    else:
        print("Recursive solution skipped (amount too large)")
    
    # Test dynamic programming solution
    start_time = time.time()
    dp_result = coin_change_dp(coins, amount)
    dp_time = time.time() - start_time
    
    print(f"Dynamic programming solution:")
    print(f"  Minimum coins: {dp_result}")
    print(f"  Execution time: {dp_time:.6f} seconds")
    
    # Explain the reasoning behind the solution
    print("\nReasoning process:")
    print("1. For amount 0, we need 0 coins (base case)")
    
    # Show a few steps of the DP table filling
    if amount <= 10:
        coins_sorted = sorted(coins)
        dp = [0] + [float('inf')] * amount
        
        for amt in range(1, amount + 1):
            for coin in coins_sorted:
                if coin <= amt:
                    dp[amt] = min(dp[amt], dp[amt - coin] + 1)
            
            coins_used = []
            temp_amt = amt
            temp_dp = dp.copy()
            
            while temp_amt > 0:
                for coin in coins_sorted:
                    if coin <= temp_amt and temp_dp[temp_amt] == temp_dp[temp_amt - coin] + 1:
                        coins_used.append(coin)
                        temp_amt -= coin
                        break
            
            print(f"2. For amount {amt}, minimum coins needed is {dp[amt]}, using: {coins_used}")

if __name__ == "__main__":
    # Example 1: Standard US coins
    test_and_compare([1, 5, 10, 25], 63)
    
    print("\n" + "=" * 50 + "\n")
    
    # Example 2: Non-standard denominations
    test_and_compare([2, 5, 7], 27)
    
    print("\n" + "=" * 50 + "\n")
    
    # Example 3: Larger amount (dynamic programming only)
    test_and_compare([1, 3, 4, 5], 1000)
```
