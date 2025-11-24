import json
import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, List, Dict, Any, Optional

from langchain_core.tools import BaseTool

from reasoning.base import BaseAgent
from reasoning.messages.llm_client import LLMClient
from reasoning.messages.openai_client import OpenAIChatClient
from reasoning.model.reasoning_result import ReasoningResult
from reasoning.tools.final_answer import FinalAnswerTool
from reasoning.tools.python_exec import PythonExecTool
from reasoning.tools.simulate_exec import SimulateTools, RunSimulationTool, RunBatchTool
from reasoning.utils.load_results import load_results
from reasoning.helpers.prompts import _default_system_prompt, _append_tool_message
from reasoning.helpers.chat_utils import prune_history
from reasoning.config.tools import _openai_tools_spec
from db.config.database import DatabaseConfig

LOG_FMT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FMT, stream=sys.stdout)
log = logging.getLogger("agent_loop")

@dataclass
class ReasoningAgent(BaseAgent):
    model_id: str
    db_config: DatabaseConfig = field(default_factory=lambda: DatabaseConfig())
    db_path: str = ""
    llm: LLMClient = field(default_factory=lambda: OpenAIChatClient(model="gpt-5-mini", temperature=1.0))
    max_steps: int = 20
    temperature: float = 1.0

    # Hooks / callbacks (override as needed)
    system_prompt_builder: Callable[[List[str]], str] = field(default=None)
    history_pruner: Callable[[List[Dict[str, Any]]], List[Dict[str, Any]]] = field(default=None)
    report_store: Callable[[str, str, str, List[str]], None] = field(default=None)  # (model_id, question, answer, images)

    # Internal tool instances (bound to model/db and df when loaded)
    _tools: Dict[str, BaseTool] = field(init=False, default_factory=dict)

    def __post_init__(self) -> None:
        # Set up database path
        self.db_path = self.db_config.database_path
        
        # Set defaults for optional callbacks
        if self.system_prompt_builder is None:
            self.system_prompt_builder = _default_system_prompt
        if self.history_pruner is None:
            self.history_pruner = prune_history
        if self.report_store is None:
            # Lazy import to avoid circulars; replace with your store_report
            from db import store_report as _store_report  # type: ignore
            self.report_store = _store_report

    # ── Public entrypoint ────────────────────────────────────────────────────
    def ask(self, question: str, stop_flag: Optional[Callable[[], bool]] = None) -> ReasoningResult:
        """Main entry point for asking questions to the reasoning agent."""
        log.info("=== Starting analysis for model_id=%s ===", self.model_id)

        # Initialize session
        df, schema = self._load_context()
        sim_code = ""  # no longer embedding code in the prompt
        self._build_tools(df)
        # No preview needed - agent will use python_exec to explore data
        history = self._initialize_conversation(question, schema, None)
        # Prime with a lightweight schema summary via python_exec to steer tool usage
        try:
            self._prime_with_schema_summary(history)
        except Exception as e:
            log.debug("Schema primer failed: %s", e)
        
        # Initialize tracking
        tracking_state = self._initialize_tracking()
        
        # Main reasoning loop
        return self._reasoning_loop(history, tracking_state, stop_flag, question)
    
    # ---------- logging helpers ----------
    def _truncate(self, text: Any, limit: int = 300) -> str:
        try:
            s = str(text)
        except Exception:
            return "<unprintable>"
        return s if len(s) <= limit else s[:limit] + " …"

    def _load_context(self) -> tuple:
        """Load data context and schema."""
        df = load_results(db_path=self.db_path, model_id=self.model_id)
        schema = list(df.columns)
        return df, schema
    
    def _load_sim_code(self) -> str:
        """Load simulation code for the current model."""
        from reasoning.helpers.sim_code_loader import load_simulation_code_safe
        return load_simulation_code_safe(self.model_id, self.db_path)
    
    def _build_tools(self, df: Any) -> None:
        """Build tools bound to this session."""
        sim = SimulateTools(db_config=self.db_config, default_model_id=self.model_id)
        self._tools = {
            "python_exec": PythonExecTool(df=df),
            "run_simulation_for_model": RunSimulationTool(sim),
            "run_batch_for_model": RunBatchTool(sim),
            "final_answer": FinalAnswerTool(),
        }
    
    def _initialize_conversation(self, question: str, schema: List[str], preview: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Initialize conversation history."""
        return [
            {"role": "system", "content": self.system_prompt_builder(schema, preview)},
            {"role": "user", "content": question},
        ]
    
    def _initialize_tracking(self) -> Dict[str, Any]:
        """Initialize tracking state for images and code."""
        return {
            "seen_imgs": {p.name for p in Path.cwd().glob("*.png")},
            "all_images": [],
            "code_map": {},
            "step_idx": 0
        }
    
    def _reasoning_loop(self, history: List[Dict[str, Any]], tracking_state: Dict[str, Any], 
                       stop_flag: Optional[Callable[[], bool]], question: str) -> ReasoningResult:
        """Main reasoning loop."""
        tools_spec = _openai_tools_spec()
        
        for _ in range(self.max_steps):
            step_num = tracking_state.get("step_idx", 0)
            log.info("[step %s] Calling LLM (history=%s messages)", step_num, len(self.history_pruner(history)))
            if stop_flag and stop_flag():
                return self._create_result(history, tracking_state, "(stopped)")

            # Get LLM response
            msg = self.llm.chat(messages=self.history_pruner(history), tools=tools_spec)
            if "tool_calls" in msg and msg["tool_calls"]:
                log.info("[step %s] LLM proposed %s tool call(s)", step_num, len(msg["tool_calls"]))
            else:
                log.info("[step %s] LLM text reply: %s", step_num, self._truncate(msg.get("content", "")))
            assistant_entry = self._create_assistant_entry(msg)
            history.append(assistant_entry)

            # Process tool calls if any
            if assistant_entry.get("tool_calls"):
                names = [tc.get("function", {}).get("name", "?") for tc in assistant_entry["tool_calls"]]
                log.info("[step %s] Processing tool calls: %s", step_num, names)
                final_result = self._process_tool_calls(
                    history, assistant_entry["tool_calls"], tracking_state, question
                )
                if final_result:  # final_answer was called
                    log.info("[step %s] Final answer produced, exiting loop", step_num)
                    return final_result
                continue

            # Nudge if no tool call
            log.info("[step %s] No tool call; nudging model to use a tool", step_num)
            self._nudge_for_tool_call(history)

        # Loop exhausted
        log.error("Agent loop exhausted without an answer")
        fallback_msg = (
            "I couldn't finalize an answer within the step limit. "
            "Please allow me to use a tool. I can: \n"
            "- run_simulation_for_model to run new simulations,\n"
            "- run_batch_for_model for parameter sweeps, or\n"
            "- python_exec to analyze the dataframe.\n"
            "Re-ask your question or request a specific tool call."
        )
        return self._create_result(history, tracking_state, fallback_msg)
    
    def _create_assistant_entry(self, msg: Dict[str, Any]) -> Dict[str, Any]:
        """Create assistant entry from LLM message."""
        assistant_entry = {"role": "assistant", "content": msg.get("content", "")}
        if "tool_calls" in msg:
            assistant_entry["tool_calls"] = msg["tool_calls"]
        return assistant_entry
    
    def _process_tool_calls(self, history: List[Dict[str, Any]], tool_calls: List[Dict[str, Any]], 
                           tracking_state: Dict[str, Any], question: str) -> Optional[ReasoningResult]:
        """Process all tool calls in the assistant message."""
        for tc in tool_calls:
            call_id = tc["id"]
            fname = tc["function"]["name"]
            raw_args = tc["function"]["arguments"] or "{}"
            log.info("[tool %s] name=%s args=%s", call_id, fname, self._truncate(raw_args))

            # Parse arguments
            args = self._parse_tool_args(history, call_id, raw_args)
            if args is None:
                log.warning("[tool %s] Malformed arguments", call_id)
                continue

            # Handle code tracking for python_exec
            if fname == "python_exec":
                if not self._track_python_code(history, call_id, args, tracking_state):
                    log.warning("[tool %s] Skipping python_exec due to missing/empty code", call_id)
                    continue

            # Execute tool
            result = self._execute_tool(history, call_id, fname, args)
            if result is None:
                log.warning("[tool %s] No result returned", call_id)
                continue

            # Track images
            self._track_images(result, tracking_state)
            if isinstance(result, dict) and not result.get("ok", True):
                log.info("[tool %s] Completed with error: %s", call_id, self._truncate(result.get("stderr", "")))
            else:
                log.info("[tool %s] Completed successfully", call_id)

            # Handle final answer specially
            if fname == "final_answer":
                return self._handle_final_answer(history, call_id, result, tracking_state, question)

            # Append tool result and continue
            self._append_tool_message(history, call_id, result)

        return None  # Continue loop
    
    def _parse_tool_args(self, history: List[Dict[str, Any]], call_id: str, raw_args: str) -> Optional[Dict[str, Any]]:
        """Parse tool arguments from JSON string."""
        try:
            return json.loads(raw_args)
        except json.JSONDecodeError:
            self._append_tool_message(history, call_id, {"ok": False, "stderr": "Malformed tool arguments"})
            return None
    
    def _track_python_code(self, history: List[Dict[str, Any]], call_id: str, 
                          args: Dict[str, Any], tracking_state: Dict[str, Any]) -> bool:
        """Track Python code for python_exec calls."""
        code = args.get("code", "")
        if not isinstance(code, str) or not code.strip():
            self._append_tool_message(history, call_id, {"ok": False, "stderr": "No code provided"})
            return False
        
        tracking_state["code_map"][tracking_state["step_idx"]] = code
        tracking_state["step_idx"] += 1
        return True
    
    def _execute_tool(self, history: List[Dict[str, Any]], call_id: str, 
                     fname: str, args: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Execute a tool and return its result."""
        tool = self._tools.get(fname)
        if not tool:
            self._append_tool_message(history, call_id, {"ok": False, "stderr": f"Unknown tool '{fname}'"})
            return None

        try:
            log.info("[tool %s] Executing %s", call_id, fname)
            # Try calling with args dict first (for tools like python_exec)
            try:
                return tool._run(args)  # type: ignore[arg-type]
            except TypeError:
                # If that fails, try with keyword arguments (for tools like final_answer)
                return tool._run(**args)  # type: ignore[arg-type]
        except TypeError as e:
            result = {"ok": False, "stderr": f"Bad arguments: {e}"}
        except Exception as e:
            result = {"ok": False, "stderr": f"{type(e).__name__}: {e}"}
        
        return result

    def _prime_with_schema_summary(self, history: List[Dict[str, Any]]) -> None:
        """Run a small python_exec to summarize df structure and first rows."""
        primer_code = (
            "import pandas as pd\n"
            "info = {\n"
            "  'columns': list(df.columns),\n"
            "  'n_rows': int(len(df)),\n"
            "  'preview': df.head(3).to_dict(orient='list')\n"
            "}\n"
            "print(info)\n"
        )
        args = {"code": primer_code}
        call_id = "prime_python_exec_0"
        result = self._execute_tool(history, call_id, "python_exec", args)
        if result is not None:
            self._append_tool_message(history, call_id, result)
            log.info("[primer] Schema summary executed (ok=%s)", getattr(result, "get", lambda *_: False)("ok", True))
    
    def _track_images(self, result: Any, tracking_state: Dict[str, Any]) -> None:
        """Track new images from tool results."""
        if not isinstance(result, dict):
            return
            
        for img in result.get("images", []):
            if img not in tracking_state["seen_imgs"]:
                tracking_state["seen_imgs"].add(img)
                tracking_state["all_images"].append(img)
    
    def _handle_final_answer(self, history: List[Dict[str, Any]], call_id: str, 
                           result: Dict[str, Any], tracking_state: Dict[str, Any], 
                           question: str) -> ReasoningResult:
        """Handle final_answer tool call."""
        log.info("[final_answer %s] Raw result type=%s, keys=%s", call_id, type(result), list(result.keys()) if isinstance(result, dict) else "N/A")
        
        fa = result if isinstance(result, dict) else {}
        
        # Extract answer text - handle both string and dict cases
        if isinstance(fa, dict) and "answer" in fa:
            answer_text = fa["answer"]
            # If answer_text is still a dict, extract the string from it
            if isinstance(answer_text, dict):
                answer_text = answer_text.get("answer", str(answer_text))
            log.info("[final_answer %s] Extracted answer from dict: type=%s, len=%s", call_id, type(answer_text), len(str(answer_text)))
        elif isinstance(fa, str):
            answer_text = fa
            log.info("[final_answer %s] Using fa as string: len=%s", call_id, len(answer_text))
        else:
            answer_text = str(fa)
            log.info("[final_answer %s] Converted fa to string: len=%s", call_id, len(answer_text))
            
        merged_images = list({*tracking_state["all_images"], *fa.get("images", [])})
        log.info("[final_answer %s] len(answer)=%s images=%s", call_id, len(answer_text), len(merged_images))
        
        # Persist report
        try:
            log.info("[final_answer %s] About to store: answer_text type=%s, value=%s", call_id, type(answer_text), self._truncate(str(answer_text)))
            self.report_store(self.model_id, question, answer_text, merged_images)
        except Exception as e:
            log.warning("store_report failed: %s", e)

        # Echo tool message and return
        self._append_tool_message(history, call_id, fa)
        
        # Debug: log what we're returning
        log.info("[final_answer %s] Returning ReasoningResult with answer type=%s, len=%s", call_id, type(answer_text), len(str(answer_text)))
        
        return ReasoningResult(
            history=history, 
            code_map=tracking_state["code_map"], 
            answer=answer_text, 
            images=merged_images
        )
    
    def _nudge_for_tool_call(self, history: List[Dict[str, Any]]) -> None:
        """Nudge the model to use a tool call."""
        history.append({
            "role": "user",
            "content": (
                "Use a tool call now. Available tools: python_exec, run_simulation_for_model, "
                "run_batch_for_model, final_answer. If you're ready to answer, use final_answer "
                "with structured format: final_answer(answer='specific parameter values/ranges', "
                "values=[numerical_values], images=['plots']). Respond with a single tool call."
            ),
        })
    
    def _create_result(self, history: List[Dict[str, Any]], tracking_state: Dict[str, Any], 
                      answer: str) -> ReasoningResult:
        """Create a ReasoningResult from current state."""
        return ReasoningResult(
            history=history,
            code_map=tracking_state["code_map"],
            answer=answer,
            images=tracking_state["all_images"]
        )
    
    def _append_tool_message(self, history: List[Dict[str, Any]], call_id: str, payload: Any) -> None:
        """Helper method to append tool messages to history."""
        _append_tool_message(history, call_id, payload)
