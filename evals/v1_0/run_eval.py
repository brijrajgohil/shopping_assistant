import asyncio
from google.adk.evaluation.agent_evaluator import AgentEvaluator
from google.adk.evaluation.eval_config import EvalConfig
from google.adk.evaluation.eval_set import EvalSet
from dotenv import load_dotenv
load_dotenv(".env")

eval_set = EvalSet.model_validate({
    "eval_set_id": "shopassist_example",
    "eval_cases": [
        {
            "eval_id": "existing_order",
            "session_input": {
                "app_name": "app",
                "user_id": "test_customer",
                "state": {}
            },
            "conversation": [
                {
                    "invocation_id": "turn_1",
                    "user_content": {
                        "role": "user",
                        "parts": [{"text": "Where is ORD-101?"}]
                    },
                    "intermediate_data": {
                        "tool_uses": [
                            {
                                "name": "get_order_status",
                                "args": {"order_id": "ORD-101"}
                            }
                        ]
                    },
                    "final_response": {
                        "role": "model",
                        "parts": [{
                            "text": (
                                "ORD-101 has shipped with BlueDart. Its estimated delivery date is September 15, 2026"
                            )
                        }]
                    }
                }
            ]
        }
    ]
})

# How ADK should grade the result
eval_config = EvalConfig.model_validate({
    "criteria": {
        "tool_trajectory_avg_score": 1.0,
        "final_response_match_v2": {
            "threshold": 1.0,
            "judge_model_options": {
                "judge_model": "gemini-2.5-flash-lite",
                "num_samples": 3
            }
        }
    }
})

async def main():
    await AgentEvaluator.evaluate_eval_set(
        agent_module="app.agent",
        eval_set=eval_set,
        eval_config=eval_config,
        num_runs=1,
        print_detailed_results=True
    )

asyncio.run(main())