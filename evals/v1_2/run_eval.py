import asyncio

from dotenv import load_dotenv
from google.adk.evaluation.agent_evaluator import AgentEvaluator
from google.adk.evaluation.eval_config import EvalConfig
from google.adk.evaluation.eval_set import EvalSet


load_dotenv(".env")


eval_set = EvalSet.model_validate({
    "eval_set_id": "shopassist_v1_2",
    "eval_cases": [
        {
            "eval_id": "order_and_return_policy",
            "session_input": {
                "app_name": "app",
                "user_id": "test_customer",
                "state": {
                    "customer_id": "CUS-001",
                },
            },
            "conversation": [
                {
                    "invocation_id": "turn_1",
                    "user_content": {
                        "role": "user",
                        "parts": [{
                            "text": (
                                "Where is ORD-101, and what is the "
                                "ShopAssist return window?"
                            ),
                        }],
                    },
                    "intermediate_data": {
                        "tool_uses": [
                            {
                                "name": "order_agent",
                                "args": {
                                    "request": "Where is ORD-101",
                                },
                            },
                            {
                                "name": "policy_agent",
                                "args": {
                                    "request": (
                                        "What is the ShopAssist "
                                        "return window?"
                                    ),
                                },
                            },
                        ],
                    },
                    "final_response": {
                        "role": "model",
                        "parts": [{
                            "text": (
                                "ORD-101 was shipped via BlueDart "
                                "with tracking number BD-SYN-101 and "
                                "an estimated delivery date of "
                                "September 15, 2026. ShopAssist accepts "
                                "eligible unused items for return within "
                                "30 calendar days after delivery."
                            ),
                        }],
                    },
                }
            ],
        },
    ],
})


eval_config = EvalConfig.model_validate({
    "criteria": {
        "tool_trajectory_avg_score": {
            "threshold": 1.0,
            "match_type": "ANY_ORDER",
        },
        "final_response_match_v2": {
            "threshold": 0.8,
            "judge_model_options": {
                "judge_model": "gemini-2.5-flash-lite",
                "num_samples": 1,
            },
        },
    }
})


async def main():
    await AgentEvaluator.evaluate_eval_set(
        agent_module="app.agent",
        eval_set=eval_set,
        eval_config=eval_config,
        num_runs=1,
        print_detailed_results=True,
    )


asyncio.run(main())