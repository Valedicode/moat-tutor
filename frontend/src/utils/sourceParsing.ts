import { NewsSource } from "@/types/chat";

const SOURCES_START = "[SOURCES_START]";
const SOURCES_END = "[SOURCES_END]";

export type ParsedMessageContent = {
  mainText: string;
  sources: NewsSource[];
};

export function parseMessageSources(content: string): ParsedMessageContent {
  const start = content.indexOf(SOURCES_START);
  const end = content.indexOf(SOURCES_END);

  if (start === -1 || end === -1 || end <= start) {
    return { mainText: content, sources: [] };
  }

  const mainText = content.slice(0, start).trimEnd();
  const block = content.slice(start + SOURCES_START.length, end).trim();
  const lines = block
    .split("\n")
    .map((l) => l.trim())
    .filter(Boolean);

  const sources: NewsSource[] = lines.map((line) => {
    // Format: idx|date|headline|url|similarity|passage_id
    const [, date, headline, url, similarity, passageId] = line.split("|");
    return {
      date: date ?? "",
      headline: headline ?? "",
      url: (url ?? "").replace("%7C", "|"),
      similarity: similarity ?? "",
      passageId: passageId ?? "",
    };
  });

  return { mainText, sources };
}
