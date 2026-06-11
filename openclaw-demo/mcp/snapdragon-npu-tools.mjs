#!/usr/bin/env node

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const FOUNDRY_URL = process.env.FOUNDRY_LOCAL_URL ?? "http://127.0.0.1:5272/v1";

const server = new McpServer({
  name: "snapdragon-npu-demo-tools",
  version: "0.1.0",
});

function jsonText(value) {
  return {
    content: [
      {
        type: "text",
        text: JSON.stringify(value, null, 2),
      },
    ],
  };
}

server.registerTool(
  "get_current_time",
  {
    description: "Return the current local time for the Snapdragon NPU demo.",
    inputSchema: {
      timezone: z.string().default("Asia/Calcutta").describe("IANA timezone name"),
    },
  },
  async ({ timezone = "Asia/Calcutta" }) => {
    const now = new Date();
    return jsonText({
      timezone,
      iso_time: now.toISOString(),
      display_time: new Intl.DateTimeFormat("en-US", {
        dateStyle: "medium",
        timeStyle: "medium",
        timeZone: timezone,
      }).format(now),
    });
  },
);

server.registerTool(
  "get_npu_status",
  {
    description: "Check the local Foundry endpoint and report the Snapdragon NPU model status.",
    inputSchema: {},
  },
  async () => {
    const started = Date.now();
    const response = await fetch(`${FOUNDRY_URL}/models`);
    const elapsedMs = Date.now() - started;
    const payload = await response.json();
    const models = Array.isArray(payload.data) ? payload.data : [];
    const npuModel = models.find((model) => {
      const id = String(model.id ?? "").toLowerCase();
      return id.includes("qnn") || id.includes("npu") || id.includes("qwen2.5");
    });

    return jsonText({
      status: response.ok ? "ready" : "error",
      endpoint: FOUNDRY_URL,
      latency_ms: elapsedMs,
      model: npuModel?.id ?? models[0]?.id ?? "unknown",
      device: "Snapdragon NPU",
      acceleration: "QNNExecutionProvider",
      model_count: models.length,
    });
  },
);

server.registerTool(
  "draft_stage_note",
  {
    description: "Draft a short stage note for a Snapdragon NPU agent demo.",
    inputSchema: {
      topic: z.string().default("local AI agent demo").describe("Demo topic to mention on stage"),
    },
  },
  async ({ topic = "local AI agent demo" }) =>
    jsonText({
      note: `This ${topic} runs on the Snapdragon NPU through Foundry Local, with OpenClaw orchestrating the agent loop and local tools.`,
    }),
);

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch((error) => {
  console.error("Snapdragon NPU MCP server failed:", error);
  process.exit(1);
});
