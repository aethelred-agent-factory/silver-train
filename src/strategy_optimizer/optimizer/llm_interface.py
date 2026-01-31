import json
import logging
import os

from openai import OpenAI


class LLMInterface:
    """
    LLM interface using the OpenAI library, compatible with DeepSeek API.
    Generates optimization proposals following the spec output schema.
    """

    def __init__(self, config):
        self.config = config
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        self.base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
        if not self.api_key:
            logging.warning("DEEPSEEK_API_KEY not found. LLMInterface will not work.")
            self.client = None
        else:
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        logging.info("Initialized LLMInterface.")

    def query_llm(self, prompt: str, context: dict) -> dict:
        """
        Sends a proposal request to the LLM.
        Returns a dict with: reasoning, params, action (UPDATE|HOLD|ROLLBACK)
        """
        if not self.client:
            logging.error("LLM client not initialized.")
            return None

        full_prompt = self._build_optimization_prompt(prompt, context)

        try:
            response = self.client.chat.completions.create(
                model="deepseek-coder",
                messages=[
                    {
                        "role": "system",
                        "content": 'You are a trading strategy optimization expert. Respond ONLY with valid JSON matching this schema: {"reasoning": "str", "params": {"param": "value"}, "action": "UPDATE|HOLD|ROLLBACK"}',
                    },
                    {"role": "user", "content": full_prompt},
                ],
                max_tokens=1000,
                temperature=0.5,
            )
            return self.parse_optimization_response(
                response.choices[0].message.content, context
            )
        except Exception as e:
            logging.error(f"Error querying LLM API: {e}")
            return None

    def _build_optimization_prompt(self, prompt: str, context: dict) -> str:
        """
        Builds the optimization prompt with current parameters, metrics, and regime info.
        """
        return f"""
You are optimizing trading strategy parameters.

OPTIMIZATION RULES:
1. Modify at most 2 parameters per iteration
2. Do NOT modify if: profit > 0% AND drawdown is decreasing vs. previous iteration
3. If 2+ regimes show improvement, return HOLD action
4. All parameter changes must respect the bounds in parameter_bounds.yaml

CURRENT STATE:
Regime: {context.get('regime_label', 'UNKNOWN')}
Regime Confidence: {context.get('regime_confidence', 0.0):.2%}
Stability State: {context.get('stability_state', 'NORMAL')}

CURRENT PARAMETERS:
{json.dumps(context.get('current_parameters', {}), indent=2)}

BACKTEST RESULTS (Global):
- Total Profit: {context.get('global_profit', 0):.2f}%
- Max Drawdown: {context.get('global_max_drawdown', 0):.2f}%
- Win Rate: {context.get('global_win_rate', 0):.2f}%
- Total Trades: {context.get('global_total_trades', 0)}
- Profit Factor: {context.get('global_profit_factor', 0):.2f}

PER-REGIME RESULTS:
{json.dumps(context.get('per_regime_metrics', {}), indent=2)}

HISTORICAL BEST PARAMETERS:
{json.dumps(context.get('best_parameters', {}), indent=2)}

TASK:
{prompt}

Return your optimization proposal in this exact JSON format:
{{
    "reasoning": "Brief explanation of your decision",
    "params": {{"parameter_name": "value", ...}},
    "action": "UPDATE" or "HOLD" or "ROLLBACK"
}}
"""

    def parse_optimization_response(self, response_content: str, context: dict) -> dict:
        """
        Parses the JSON response from the LLM and validates against constraints.
        """
        try:
            # Handle empty or whitespace-only response
            if not response_content or not response_content.strip():
                logging.error("LLM returned empty response")
                return None

            proposal = json.loads(response_content)

            # Validate schema
            if not all(k in proposal for k in ["reasoning", "params", "action"]):
                logging.error(f"Invalid proposal schema: {proposal}")
                return None

            # Validate action
            if proposal["action"] not in ["UPDATE", "HOLD", "ROLLBACK"]:
                logging.error(f"Invalid action: {proposal['action']}")
                return None

            # Apply constraint: at most 2 parameters per iteration
            if len(proposal.get("params", {})) > 2:
                logging.warning(
                    f"Proposal modifies {len(proposal['params'])} params, truncating to 2"
                )
                params_keys = list(proposal["params"].keys())[:2]
                proposal["params"] = {k: proposal["params"][k] for k in params_keys}

            # Apply constraint: don't modify if profit > 0 and drawdown decreasing
            if context.get("global_profit", 0) > 0 and context.get(
                "drawdown_decreasing", False
            ):
                logging.info(
                    "Overriding UPDATE to HOLD: profit positive and drawdown decreasing"
                )
                proposal["action"] = "HOLD"

            # Apply constraint: HOLD if 2+ regimes show improvement
            improved_regimes = context.get("improved_regimes", 0)
            if improved_regimes >= 2:
                logging.info(f"Overriding to HOLD: {improved_regimes} regimes improved")
                proposal["action"] = "HOLD"

            return proposal
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse LLM response: {e}")
            logging.debug(f"Response content: {response_content}")
            return None
