require("dotenv").config();
const express = require("express");
const cors = require("cors");
const fetch = require("node-fetch");
const AbortController = require("node-fetch").AbortController || globalThis.AbortController;

const app = express();
app.use(cors());
app.use(express.json());

const ICA_ENDPOINT = process.env.ICA_ENDPOINT;
const ICA_API_KEY = process.env.ICA_API_KEY;

// ICA agent can be slow on complex prompts — allow up to 120 s per attempt.
const ICA_TIMEOUT_MS = 120_000;
// Retry once on transient gateway errors (502, 503, 504).
const RETRYABLE_STATUSES = new Set([502, 503, 504]);

async function callICA(body) {
  let lastStatus, lastBody;
  for (let attempt = 1; attempt <= 2; attempt++) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), ICA_TIMEOUT_MS);
    try {
      const response = await fetch(ICA_ENDPOINT, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${ICA_API_KEY}`,
        },
        body: JSON.stringify(body),
        signal: controller.signal,
      });
      clearTimeout(timer);
      lastStatus = response.status;

      if (response.ok) return { ok: true, response };

      lastBody = await response.text();
      console.warn(`ICA attempt ${attempt} → ${lastStatus}:`, lastBody.slice(0, 200));

      if (!RETRYABLE_STATUSES.has(lastStatus)) break; // non-retryable (e.g. 401, 400)
      if (attempt < 2) {
        console.log("Retrying after 3s…");
        await new Promise((r) => setTimeout(r, 3000));
      }
    } catch (err) {
      clearTimeout(timer);
      if (err.name === "AbortError") {
        lastStatus = 504;
        lastBody = "Request timed out after 120 s.";
        console.warn(`ICA attempt ${attempt} timed out`);
        if (attempt < 2) await new Promise((r) => setTimeout(r, 3000));
      } else {
        throw err;
      }
    }
  }
  return { ok: false, status: lastStatus, body: lastBody };
}

// Task-type to system prompt router
const TASK_PROMPTS = {
  translate: `You are a requirements translator. The user will provide software requirements in any language. 
Translate them accurately into clear, professional English. Preserve all technical details.`,

  analyze: `You are a software requirements analyst. Analyze the provided requirements and give a structured report covering:
1. Clarity and completeness
2. Ambiguities or vague statements
3. Missing information
4. Suggestions for improvement`,

  review_tests: `You are a test case reviewer. Review the provided test cases against the requirements and report:
1. Missing test scenarios
2. Redundant or duplicate tests
3. Edge cases not covered
4. Inconsistencies between requirements and test cases`,

  edge_cases: `You are a software QA expert. Identify all possible edge cases, boundary conditions, and negative scenarios 
for the provided requirements or functionality. Be thorough and systematic.`,

  validate: `You are a requirements validation expert. Check the consistency between the provided requirements and test cases.
Report: 
1. Requirements with no test coverage
2. Test cases that don't map to any requirement
3. Conflicts or contradictions`,
};

app.post("/api/agent", async (req, res) => {
  const { taskType, userInput } = req.body;

  if (!taskType || !userInput) {
    return res.status(400).json({ error: "taskType and userInput are required." });
  }

  const systemPrompt = TASK_PROMPTS[taskType];
  if (!systemPrompt) {
    return res.status(400).json({ error: `Unknown taskType: ${taskType}` });
  }

  const fullPrompt = `${systemPrompt}\n\n---\n\nUser Input:\n${userInput}`;

  try {
    const result = await callICA({ message: fullPrompt });

    if (!result.ok) {
      const status = result.status;
      // Return a clean message — avoid sending raw HTML gateway pages to the UI
      const userMessage =
        status === 504 || status === 502
          ? "The ICA agent took too long to respond (gateway timeout). Please try again or simplify your input."
          : status === 503
          ? "The ICA agent is temporarily unavailable. Please try again in a moment."
          : `ICA agent error: ${status}`;
      console.error("ICA error after retries:", status, result.body?.slice(0, 200));
      return res.status(status < 500 ? status : 502).json({ error: userMessage });
    }

    const data = await result.response.json();

    // ICA A2A response shape: { messages: [{role, content}, ...] }
    // Last assistant message is the reply; fall back to other known shapes.
    const lastAssistantMsg = Array.isArray(data?.messages)
      ? [...data.messages].reverse().find((m) => m.role === "assistant")?.content
      : undefined;

    const agentReply =
      lastAssistantMsg ||
      data?.output?.text ||
      data?.message ||
      data?.response ||
      data?.result ||
      data?.content ||
      JSON.stringify(data);

    return res.json({ reply: agentReply });
  } catch (err) {
    console.error("Server error:", err);
    return res.status(500).json({ error: "Internal server error", detail: err.message });
  }
});

app.get("/health", (_req, res) => res.json({ status: "ok" }));

const PORT = process.env.PORT || 4000;
const server = app.listen(PORT, () => console.log(`Backend running on http://localhost:${PORT}`));
// Give Express enough headroom for the 2× ICA attempts + 3 s retry gap
server.setTimeout(250_000);
