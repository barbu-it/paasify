from paasify_v4.cli.main import AppMain

app = None


def run():
    "Return a Paasify App instance"

    app = AppMain()


if __name__ == "__main__":
    run()
