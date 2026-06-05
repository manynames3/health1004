import { existsSync, readFileSync } from "node:fs";
import path from "node:path";
import { DocumentListResponse, TopicDetail, TopicListResponse } from "../types";

export function readStaticTopicList(endpoint = "/topics"): TopicListResponse | null {
  return readStaticJson<TopicListResponse>(["categories", `${categoryCacheName(endpoint)}.json`]);
}

export function readStaticTopicDetail(slug: string): TopicDetail | null {
  return readStaticJson<TopicDetail>(["topics", `${slug}.json`]);
}

export function readStaticDocumentList(): DocumentListResponse | null {
  return readStaticJson<DocumentListResponse>(["documents", "all.json"]);
}

function readStaticJson<T>(parts: string[]): T | null {
  for (const base of staticArchiveBases()) {
    const filePath = path.join(base, ...parts);
    if (!existsSync(filePath)) continue;
    return JSON.parse(readFileSync(filePath, "utf8")) as T;
  }
  return null;
}

function staticArchiveBases(): string[] {
  return [
    path.join(process.cwd(), "public", "static-data", "archive"),
    path.join(process.cwd(), "frontend", "public", "static-data", "archive")
  ];
}

function categoryCacheName(endpoint: string): string {
  const normalized = endpoint.replace(/^\/+|\/+$/g, "") || "topics";
  return normalized === "topics" ? "topics" : normalized;
}
