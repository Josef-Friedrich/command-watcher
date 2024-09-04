from pretiac import set_default_client


def pytest_configure(config) -> None:  # type: ignore
    set_default_client(
        api_endpoint_host="localhost",
        http_basic_username="user",
        http_basic_password="1234",
    )
