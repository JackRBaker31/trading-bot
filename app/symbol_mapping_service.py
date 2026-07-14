from app.broker import BrokerClient
from app.instrument_resolver import InstrumentResolver


class SymbolMappingService:
    def resolve(
        self,
        broker: BrokerClient,
        configured_symbols: list[str],
    ) -> dict[str, str]:
        resolver = InstrumentResolver(
            instruments=broker.get_instruments(),
        )

        return resolver.resolve_symbols(
            configured_symbols,
        )