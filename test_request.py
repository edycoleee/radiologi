from tmp.app1 import create_app


def run_test():
    app = create_app()
    with app.test_client() as c:
        rv = c.get('/api/satset/halo')
        print('status_code:', rv.status_code)
        try:
            print('json:', rv.get_json())
        except Exception:
            print('data:', rv.data)


if __name__ == '__main__':
    run_test()
