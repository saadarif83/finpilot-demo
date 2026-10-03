// One-line summary of the real MCP tools a run used, for the chat bubble.
export function toolNamesFrom(events = []) {
  return [...new Set(events.filter((e) => e.kind === "tool_call").map((e) => e.detail.tool))];
}
