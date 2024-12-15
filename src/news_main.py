"""This file is used to run all the startup scripts for the News project."""


def timing_decorator(func):
    import time
    def wrapper(*args, **kwargs):
        start_time = time.time()
        print('-----------------------------------------------------------------------------')
        print(f"{func.__name__}")
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


def main():
    import nytimes as nyt
    import news_summary as news

    news.startup()
    nyt.NYTimesArticles()

if __name__ == "__main__":
    main()