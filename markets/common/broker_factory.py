def get_broker(name: str, **kwargs):
    name = name.lower()
    if name in ("paper", "paperbroker"):
        from markets.common.paper_broker import PaperBroker
        return PaperBroker(**kwargs)
    raise ValueError(f"Unknown broker: {name}")
