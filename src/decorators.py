# -*- coding: utf-8 -*-
"""
Created on Fri Jan  5 21:30:03 2024

@author: nouman
"""

import time


def timing_decorator(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        print('-----------------------------------------------------------------------------')
        print(f"Method: {func.__name__}")
        print(f"Start Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))}")
        result = func(*args, **kwargs)

        print('\n')
        end_time = time.time()
        print(f"End Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))}")

        runtime = end_time - start_time
        print(f"Runtime: {runtime: .2f} seconds")
        print('-----------------------------------------------------------------------------')
        return result
    return wrapper