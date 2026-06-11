from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
OPENWEBUI_DIR = REPO_ROOT / "openwebui"
DATA_DIR = OPENWEBUI_DIR / "data"
TOOL_FILE = OPENWEBUI_DIR / "tools" / "snapdragon_npu_demo.py"
PIPE_FILE = OPENWEBUI_DIR / "functions" / "snapdragon_npu_agent_pipe.py"

TOOL_ID = "snapdragon_npu_demo"
TOOL_NAME = "Snapdragon NPU Demo Tools"
PIPE_ID = "snapdragon_npu_agent_pipe"
PIPE_NAME = "Snapdragon NPU Agent Pipe"
BASE_MODEL_ID = os.environ.get("OPENWEBUI_BASE_MODEL", "qwen2.5-7b-instruct-qnn-npu")
AGENT_MODEL_ID = os.environ.get("OPENWEBUI_AGENT_MODEL", "snapdragon-npu-agent")
AGENT_MODEL_NAME = "Snapdragon NPU Agent (Native Tools)"


async def main() -> int:
    os.environ["DATA_DIR"] = str(DATA_DIR)
    os.environ.setdefault("WEBUI_AUTH", "False")
    os.environ.setdefault("WEBUI_SECRET_KEY", "local-demo-secret")

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    from open_webui.models.models import ModelForm, ModelMeta, ModelParams, Models
    from open_webui.models.tools import ToolForm, ToolMeta, Tools
    from open_webui.models.functions import FunctionForm, FunctionMeta, Functions
    from open_webui.models.users import Users
    from open_webui.utils.plugin import load_function_module_by_id, load_tool_module_by_id, replace_imports
    from open_webui.utils.tools import get_tool_specs

    users_payload = await Users.get_users(limit=1)
    users = users_payload.get("users", []) if isinstance(users_payload, dict) else users_payload
    if users:
        user_id = users[0].id
    else:
        user = await Users.insert_new_user(
            "Qualcomm Demo",
            "qualcomm-demo",
            "qualcomm-demo@local",
            "not-used",
            role="admin",
        )
        user_id = user.id

    content = replace_imports(TOOL_FILE.read_text(encoding="utf-8"))
    tool_module, frontmatter = await load_tool_module_by_id(TOOL_ID, content=content)
    specs = get_tool_specs(tool_module)

    tool_form = ToolForm(
        id=TOOL_ID,
        name=TOOL_NAME,
        content=content,
        meta=ToolMeta(
            description=(
                "Local demo tools for current time, Foundry Snapdragon NPU status, "
                "and Qualcomm DevRel stage-note drafting."
            ),
            manifest=frontmatter,
        ),
        access_grants=[{"principal_type": "user", "principal_id": "*", "permission": "read"}],
    )

    existing_tool = await Tools.get_tool_by_id(TOOL_ID)
    if existing_tool:
        await Tools.update_tool_by_id(
            TOOL_ID,
            {
                "name": tool_form.name,
                "content": tool_form.content,
                "specs": specs,
                "meta": tool_form.meta.model_dump(),
                "access_grants": tool_form.access_grants,
            },
        )
        print(f"Updated tool: {TOOL_ID}")
    else:
        await Tools.insert_new_tool(user_id, tool_form, specs)
        print(f"Created tool: {TOOL_ID}")

    model_form = ModelForm(
        id=AGENT_MODEL_ID,
        base_model_id=BASE_MODEL_ID,
        name=AGENT_MODEL_NAME,
        params=ModelParams(
            temperature=0.2,
            function_calling="default",
            system=(
                "You are a Qualcomm DevRel demo agent. Prefer using the available tools when the user asks "
                "about time, NPU/runtime status, or stage/demo notes. After tool calls, summarize clearly "
                "for a live Snapdragon NPU demo."
            ),
        ),
        meta=ModelMeta(
            description=(
                "Open WebUI agent wrapper for Foundry Local running on the Snapdragon NPU. "
                "Includes always-on demo tools."
            ),
            capabilities={
                "vision": False,
                "file_upload": False,
                "web_search": False,
                "image_generation": False,
                "code_interpreter": False,
            },
            tags=[{"name": "Qualcomm"}, {"name": "NPU"}, {"name": "Agent Demo"}],
            toolIds=[TOOL_ID],
        ),
        access_grants=[{"principal_type": "user", "principal_id": "*", "permission": "read"}],
        is_active=True,
    )

    existing_model = await Models.get_model_by_id(AGENT_MODEL_ID)
    if existing_model:
        await Models.update_model_by_id(AGENT_MODEL_ID, model_form)
        print(f"Updated model: {AGENT_MODEL_ID} -> {BASE_MODEL_ID}")
    else:
        await Models.insert_new_model(model_form, user_id)
        print(f"Created model: {AGENT_MODEL_ID} -> {BASE_MODEL_ID}")

    print(f"Tool functions: {', '.join(spec['name'] for spec in specs)}")

    pipe_content = replace_imports(PIPE_FILE.read_text(encoding="utf-8"))
    _pipe_module, pipe_type, pipe_frontmatter = await load_function_module_by_id(PIPE_ID, content=pipe_content)
    pipe_form = FunctionForm(
        id=PIPE_ID,
        name=PIPE_NAME,
        content=pipe_content,
        meta=FunctionMeta(
            description=(
                "Reliable Open WebUI pipe model that runs local agent tool steps and asks "
                "Foundry Local on the Snapdragon NPU for final wording."
            ),
            manifest=pipe_frontmatter,
        ),
    )
    existing_pipe = await Functions.get_function_by_id(PIPE_ID)
    pipe_update = {
        **pipe_form.model_dump(exclude={"id"}),
        "type": pipe_type,
        "is_active": True,
        "is_global": False,
    }
    if existing_pipe:
        await Functions.update_function_by_id(PIPE_ID, pipe_update)
        print(f"Updated pipe: {PIPE_ID}")
    else:
        await Functions.insert_new_function(user_id, pipe_type, pipe_form)
        await Functions.update_function_by_id(PIPE_ID, {"is_active": True, "is_global": False})
        print(f"Created pipe: {PIPE_ID}")

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
