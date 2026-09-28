import asyncio

from dotenv import load_dotenv
from google.adk.evaluation.agent_evaluator import AgentEvaluator
from google.adk.evaluation.eval_config import EvalConfig
from google.adk.evaluation.eval_set import EvalSet

load_dotenv(".env")


eval_set = EvalSet.model_validate({
    "eval_set_id": "shopassist_v1_1",
    "eval_cases": [
        {
            "eval_id": "duplicate_refund",
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
                                "Refund ORD-102 because the "
                                "keyboard is faulty."
                            ),
                        }],
                    },
                    "intermediate_data": {
                        "tool_uses": [
                            {
                                "name": "request_refund",
                                "args": {
                                    "order_id": "ORD-102",
                                    "reason": (
                                        "The keyboard is faulty."
                                    ),
                                },
                            }
                        ],
                    },
                    "final_response": {
                        "role": "model",
                        "parts": [{
                            "text": (
                                "This order already has a refund "
                                "request, so another request cannot "
                                "be created."
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
        "tool_trajectory_avg_score": 1.0,
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