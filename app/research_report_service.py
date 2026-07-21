import logging
from dataclasses import dataclass
from types import SimpleNamespace

from app.application_errors import (
    ApplicationError,
    ConfigurationError,
    DataStoreError,
    ResearchRunError,
)
from app.backtest_result import BacktestResult
from app.csv_historical_data import (
    load_historical_prices_from_csv,
)
from app.execution_cost import ExecutionCostModel
from app.historical_data import HistoricalPrice
from app.monte_carlo import MonteCarloSimulator
from app.monte_carlo_summary import (
    MonteCarloSummary,
    summarize_monte_carlo_results,
)
from app.news_research_summary import (
    NewsResearchSummary,
    summarize_news_research,
)
from app.news_signal_outcome_store import (
    NewsSignalOutcomeStore,
)
from app.news_signal_store import NewsSignalStore
from app.research_charts import (
    save_drawdown_chart,
    save_equity_curve_chart,
    save_monte_carlo_histogram,
    save_rolling_returns_chart,
)
from app.research_report import (
    ResearchReport,
    save_research_report_csv,
    save_research_report_json,
)
from app.research_report_builder import (
    build_research_report,
)
from app.research_setup import (
    STRATEGY_NAME,
    ResearchCostModels,
    create_research_cost_models,
    create_research_exit_manager,
    create_research_strategy_definition,
)
from app.risk import RiskLimits
from app.run_history import RunType
from app.run_history_service import RunHistoryService
from app.rolling_walk_forward_optimizer import (
    RollingWalkForwardOptimizer,
    RollingWalkForwardResult,
)
from app.rolling_walk_forward_summary import (
    RollingWalkForwardSummary,
    summarize_rolling_results,
)
from app.strategy_comparison_runner import (
    StrategyComparisonRunner,
)
from app.walk_forward_optimizer import (
    WalkForwardOptimizer,
)


@dataclass(frozen=True)
class ResearchReportRequest:
    starting_cash: float
    max_order_value: float
    max_position_value: float
    max_portfolio_exposure: float
    target_allocation_percent: float
    historical_prices_path: str = (
        "data/research_prices.csv"
    )
    news_signals_path: str = (
        "data/news_signals.jsonl"
    )
    news_outcomes_path: str = (
        "data/news_signal_outcomes.jsonl"
    )
    json_output_path: str = (
        "data/research_report.json"
    )
    csv_output_path: str = (
        "data/research_report.csv"
    )
    equity_curve_path: str = (
        "data/equity_curve.png"
    )
    drawdown_path: str = (
        "data/drawdown.png"
    )
    monte_carlo_path: str = (
        "data/monte_carlo_histogram.png"
    )
    rolling_returns_path: str = (
        "data/rolling_returns.png"
    )
    monte_carlo_simulation_count: int = 1_000
    monte_carlo_random_seed: int = 12_345

    def __post_init__(self) -> None:
        if self.starting_cash <= 0:
            raise ConfigurationError(
                "Starting cash must be positive."
            )

        if self.target_allocation_percent <= 0:
            raise ConfigurationError(
                "Target allocation percentage "
                "must be positive."
            )

        if self.monte_carlo_simulation_count <= 0:
            raise ConfigurationError(
                "Monte Carlo simulation count "
                "must be positive."
            )

        for name, value in (
            (
                "Historical prices path",
                self.historical_prices_path,
            ),
            (
                "News signals path",
                self.news_signals_path,
            ),
            (
                "News outcomes path",
                self.news_outcomes_path,
            ),
            (
                "JSON output path",
                self.json_output_path,
            ),
            (
                "CSV output path",
                self.csv_output_path,
            ),
            (
                "Equity curve path",
                self.equity_curve_path,
            ),
            (
                "Drawdown path",
                self.drawdown_path,
            ),
            (
                "Monte Carlo path",
                self.monte_carlo_path,
            ),
            (
                "Rolling returns path",
                self.rolling_returns_path,
            ),
        ):
            if not value.strip():
                raise ConfigurationError(
                    f"{name} is required."
                )


@dataclass(frozen=True)
class ResearchReportArtifacts:
    json_path: str
    csv_path: str
    equity_curve_path: str
    drawdown_path: str
    monte_carlo_path: str
    rolling_returns_path: str


@dataclass(frozen=True)
class ResearchReportResult:
    report: ResearchReport
    news_summary: NewsResearchSummary
    gross_backtest_result: BacktestResult
    net_backtest_result: BacktestResult
    gross_monte_carlo_simulations: list
    net_monte_carlo_simulations: list
    gross_monte_carlo_summary: MonteCarloSummary
    net_monte_carlo_summary: MonteCarloSummary
    walk_forward_training_result: object
    walk_forward_validation_result: object
    rolling_results: list[RollingWalkForwardResult]
    rolling_summary: RollingWalkForwardSummary
    artifacts: ResearchReportArtifacts


class ResearchReportService:
    def __init__(
        self,
        *,
        run_history_service: (
            RunHistoryService | None
        ) = None,
    ) -> None:
        self._run_history_service = (
            run_history_service
        )

    def run(
        self,
        *,
        request: ResearchReportRequest,
    ) -> ResearchReportResult:
        history_record = None

        if self._run_history_service is not None:
            history_record = (
                self._run_history_service.start_run(
                    run_type=(
                        RunType.STRATEGY_REPORT
                    ),
                    metadata={
                        "historical_prices_path": (
                            request.historical_prices_path
                        ),
                        "json_output_path": (
                            request.json_output_path
                        ),
                        "csv_output_path": (
                            request.csv_output_path
                        ),
                    },
                )
            )

        try:
            result = self._run_report(
                request=request
            )
        except Exception as error:
            if (
                history_record is not None
                and self._run_history_service
                is not None
            ):
                self._run_history_service.fail_run(
                    run_id=history_record.run_id,
                    error=error,
                )
            raise

        if (
            history_record is not None
            and self._run_history_service
            is not None
        ):
            self._run_history_service.complete_run(
                run_id=history_record.run_id,
                created_count=6,
                metadata={
                    "strategy_name": (
                        result.report.strategy_name
                    ),
                    "verdict": result.report.verdict,
                    "completed_trades": (
                        result.report.net_completed_trades
                    ),
                    "news_signal_count": (
                        result.news_summary.signal_count
                    ),
                    "news_outcome_count": (
                        result.news_summary.outcome_count
                    ),
                    "artifact_paths": {
                        "json": result.artifacts.json_path,
                        "csv": result.artifacts.csv_path,
                        "equity_curve": (
                            result.artifacts.equity_curve_path
                        ),
                        "drawdown": (
                            result.artifacts.drawdown_path
                        ),
                        "monte_carlo": (
                            result.artifacts.monte_carlo_path
                        ),
                        "rolling_returns": (
                            result.artifacts
                            .rolling_returns_path
                        ),
                    },
                },
            )

        return result

    def _run_report(
        self,
        *,
        request: ResearchReportRequest,
    ) -> ResearchReportResult:
        logging.getLogger(
            "app.execution"
        ).setLevel(logging.ERROR)

        try:
            historical_prices = (
                self._load_historical_prices(
                    request.historical_prices_path
                )
            )
        except ApplicationError:
            raise
        except Exception as error:
            raise DataStoreError(
                "Historical research prices could "
                "not be loaded."
            ) from error

        if not historical_prices:
            raise ResearchRunError(
                "No research prices were loaded."
            )

        try:
            symbols = set(
                historical_prices[0].prices
            )

            risk_limits = RiskLimits(
                max_order_value=(
                    request.max_order_value
                ),
                max_position_value=(
                    request.max_position_value
                ),
                max_portfolio_exposure=(
                    request.max_portfolio_exposure
                ),
                max_trades_per_session=10_000,
                approved_symbols=symbols,
            )

            cost_models = (
                create_research_cost_models()
            )

            gross_backtest_result = (
                self._run_backtest_case(
                    historical_prices=(
                        historical_prices
                    ),
                    starting_cash=(
                        request.starting_cash
                    ),
                    risk_limits=risk_limits,
                    target_allocation_percent=(
                        request
                        .target_allocation_percent
                    ),
                    execution_cost_model=(
                        cost_models.gross
                    ),
                )
            )

            net_backtest_result = (
                self._run_backtest_case(
                    historical_prices=(
                        historical_prices
                    ),
                    starting_cash=(
                        request.starting_cash
                    ),
                    risk_limits=risk_limits,
                    target_allocation_percent=(
                        request
                        .target_allocation_percent
                    ),
                    execution_cost_model=(
                        cost_models.net
                    ),
                )
            )

            (
                gross_monte_carlo_simulations,
                gross_monte_carlo_summary,
            ) = self._summarize_trade_profits(
                starting_equity=(
                    gross_backtest_result
                    .starting_cash
                ),
                trade_profits=(
                    gross_backtest_result
                    .completed_trade_profits
                ),
                simulation_count=(
                    request
                    .monte_carlo_simulation_count
                ),
                random_seed=(
                    request
                    .monte_carlo_random_seed
                ),
            )

            (
                net_monte_carlo_simulations,
                net_monte_carlo_summary,
            ) = self._summarize_trade_profits(
                starting_equity=(
                    net_backtest_result
                    .starting_cash
                ),
                trade_profits=(
                    net_backtest_result
                    .completed_trade_profits
                ),
                simulation_count=(
                    request
                    .monte_carlo_simulation_count
                ),
                random_seed=(
                    request
                    .monte_carlo_random_seed
                ),
            )

            (
                walk_forward_training_result,
                walk_forward_validation_result,
            ) = self._run_walk_forward(
                historical_prices=(
                    historical_prices
                ),
                starting_cash=(
                    request.starting_cash
                ),
                risk_limits=risk_limits,
                target_allocation_percent=(
                    request
                    .target_allocation_percent
                ),
            )

            rolling_results = self._run_rolling(
                historical_prices=(
                    historical_prices
                ),
                starting_cash=(
                    request.starting_cash
                ),
                risk_limits=risk_limits,
                target_allocation_percent=(
                    request
                    .target_allocation_percent
                ),
            )

            rolling_summary = (
                self._summarize_rolling(
                    rolling_results
                )
            )
        except ApplicationError:
            raise
        except Exception as error:
            raise ResearchRunError(
                "Strategy research calculations "
                "failed."
            ) from error

        try:
            news_summary = self._load_news_summary(
                signals_path=(
                    request.news_signals_path
                ),
                outcomes_path=(
                    request.news_outcomes_path
                ),
            )
        except ApplicationError:
            raise
        except Exception as error:
            raise DataStoreError(
                "AI news research data could not "
                "be loaded."
            ) from error

        try:
            report = build_research_report(
                strategy_name=STRATEGY_NAME,
                gross_backtest_result=(
                    gross_backtest_result
                ),
                net_backtest_result=(
                    net_backtest_result
                ),
                gross_monte_carlo_summary=(
                    gross_monte_carlo_summary
                ),
                net_monte_carlo_summary=(
                    net_monte_carlo_summary
                ),
                net_cost_model=cost_models.net,
                walk_forward_result=(
                    SimpleNamespace(
                        training_result=(
                            walk_forward_training_result
                        ),
                        validation_result=(
                            walk_forward_validation_result
                        ),
                    )
                ),
                rolling_summary=rolling_summary,
                news_summary=news_summary,
            )

            artifacts = ResearchReportArtifacts(
                json_path=(
                    request.json_output_path
                ),
                csv_path=request.csv_output_path,
                equity_curve_path=(
                    request.equity_curve_path
                ),
                drawdown_path=(
                    request.drawdown_path
                ),
                monte_carlo_path=(
                    request.monte_carlo_path
                ),
                rolling_returns_path=(
                    request.rolling_returns_path
                ),
            )

            self._save_report(
                report=report,
                artifacts=artifacts,
            )

            self._save_charts(
                net_backtest_result=(
                    net_backtest_result
                ),
                net_monte_carlo_simulations=(
                    net_monte_carlo_simulations
                ),
                rolling_results=rolling_results,
                artifacts=artifacts,
            )
        except ApplicationError:
            raise
        except Exception as error:
            raise DataStoreError(
                "Research report artifacts could "
                "not be saved."
            ) from error

        return ResearchReportResult(
            report=report,
            news_summary=news_summary,
            gross_backtest_result=(
                gross_backtest_result
            ),
            net_backtest_result=(
                net_backtest_result
            ),
            gross_monte_carlo_simulations=(
                gross_monte_carlo_simulations
            ),
            net_monte_carlo_simulations=(
                net_monte_carlo_simulations
            ),
            gross_monte_carlo_summary=(
                gross_monte_carlo_summary
            ),
            net_monte_carlo_summary=(
                net_monte_carlo_summary
            ),
            walk_forward_training_result=(
                walk_forward_training_result
            ),
            walk_forward_validation_result=(
                walk_forward_validation_result
            ),
            rolling_results=rolling_results,
            rolling_summary=rolling_summary,
            artifacts=artifacts,
        )

    @staticmethod
    def _load_historical_prices(
        file_path: str,
    ) -> list[HistoricalPrice]:
        return load_historical_prices_from_csv(
            file_path=file_path
        )

    @staticmethod
    def _run_backtest_case(
        *,
        historical_prices: list[HistoricalPrice],
        starting_cash: float,
        risk_limits: RiskLimits,
        target_allocation_percent: float,
        execution_cost_model: ExecutionCostModel,
    ) -> BacktestResult:
        runner = StrategyComparisonRunner(
            starting_cash=starting_cash,
            risk_limits=risk_limits,
            position_exit_manager=(
                create_research_exit_manager()
            ),
            execution_cost_model=(
                execution_cost_model
            ),
        )

        _, results = runner.run(
            historical_prices=historical_prices,
            strategy_definitions=[
                create_research_strategy_definition(
                    target_allocation_percent=(
                        target_allocation_percent
                    )
                )
            ],
        )

        return results[STRATEGY_NAME]

    @staticmethod
    def _summarize_trade_profits(
        *,
        starting_equity: float,
        trade_profits: list[float],
        simulation_count: int,
        random_seed: int,
    ) -> tuple[list, MonteCarloSummary]:
        if not trade_profits:
            raise ResearchRunError(
                "The research strategy produced no "
                "completed trades."
            )

        simulations = (
            MonteCarloSimulator()
            .run_from_trade_profits(
                starting_equity=starting_equity,
                trade_profits=trade_profits,
                simulation_count=simulation_count,
                random_seed=random_seed,
            )
        )

        return (
            simulations,
            summarize_monte_carlo_results(
                simulations
            ),
        )

    @staticmethod
    def _run_walk_forward(
        *,
        historical_prices: list[HistoricalPrice],
        starting_cash: float,
        risk_limits: RiskLimits,
        target_allocation_percent: float,
    ) -> tuple[object, object]:
        optimizer = WalkForwardOptimizer(
            starting_cash=starting_cash,
            risk_limits=risk_limits,
        )

        return optimizer.run(
            historical_prices=historical_prices,
            training_fraction=0.8,
            drop_thresholds=[1.0, 2.0, 3.0],
            sma_periods=[None, 3],
            rsi_settings=[
                (None, None),
                (3, 30.0),
            ],
            cooldown_cycles=[0, 2],
            target_allocation_percent=(
                target_allocation_percent
            ),
        )

    @staticmethod
    def _run_rolling(
        *,
        historical_prices: list[HistoricalPrice],
        starting_cash: float,
        risk_limits: RiskLimits,
        target_allocation_percent: float,
    ) -> list[RollingWalkForwardResult]:
        optimizer = RollingWalkForwardOptimizer(
            starting_cash=starting_cash,
            risk_limits=risk_limits,
        )

        return optimizer.run(
            historical_prices=historical_prices,
            training_size=250,
            validation_size=50,
            step_size=50,
            drop_thresholds=[1.0, 2.0, 3.0],
            sma_periods=[None, 3],
            rsi_settings=[
                (None, None),
                (3, 30.0),
            ],
            cooldown_cycles=[0, 2],
            target_allocation_percent=(
                target_allocation_percent
            ),
        )

    @staticmethod
    def _summarize_rolling(
        results: list[RollingWalkForwardResult],
    ) -> RollingWalkForwardSummary:
        return summarize_rolling_results(
            results
        )

    @staticmethod
    def _load_news_summary(
        *,
        signals_path: str,
        outcomes_path: str,
    ) -> NewsResearchSummary:
        signals = NewsSignalStore(
            file_path=signals_path
        ).load_all()

        outcomes = NewsSignalOutcomeStore(
            file_path=outcomes_path
        ).load_all()

        return summarize_news_research(
            signals=signals,
            outcomes=outcomes,
        )

    @staticmethod
    def _save_report(
        *,
        report: ResearchReport,
        artifacts: ResearchReportArtifacts,
    ) -> None:
        save_research_report_json(
            report=report,
            output_path=artifacts.json_path,
        )
        save_research_report_csv(
            report=report,
            output_path=artifacts.csv_path,
        )

    @staticmethod
    def _save_charts(
        *,
        net_backtest_result: BacktestResult,
        net_monte_carlo_simulations: list,
        rolling_results: list[
            RollingWalkForwardResult
        ],
        artifacts: ResearchReportArtifacts,
    ) -> None:
        save_equity_curve_chart(
            equity_curve=(
                net_backtest_result.equity_curve
            ),
            output_path=(
                artifacts.equity_curve_path
            ),
        )
        save_drawdown_chart(
            equity_curve=(
                net_backtest_result.equity_curve
            ),
            output_path=artifacts.drawdown_path,
        )
        save_monte_carlo_histogram(
            simulations=(
                net_monte_carlo_simulations
            ),
            output_path=artifacts.monte_carlo_path,
        )
        save_rolling_returns_chart(
            results=rolling_results,
            output_path=(
                artifacts.rolling_returns_path
            ),
        )