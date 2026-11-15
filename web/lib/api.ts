// API client. Uses the sample responses in web/fixtures until NEXT_PUBLIC_API_URL is set.
import answered from "@/fixtures/answered.json";
import noDirectData from "@/fixtures/no_direct_data.json";
import outOfScope from "@/fixtures/out_of_scope.json";
import type { AskRequest, AskResponse, ChunkInfo, CoveragePoint, Investigation, TestRow } from "./types";

export const API_URL = (process.env.NEXT_PUBLIC_API_URL || "").replace(/\/$/, "");
export const usingFixtures = API_URL === "";

function fixtureFor(question: string): AskResponse {
  if (/rocket|propellant|thruster|engine/i.test(question)) return outOfScope as unknown as AskResponse;
  if (/moon|lunar|mars|martian/i.test(question)) return noDirectData as unknown as AskResponse;
  return answered as unknown as AskResponse;
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${API_URL}${path}`);
  if (!res.ok) throw new Error(`The FlameCheck API returned ${res.status} for ${path}.`);
  return res.json();
}

export async function ask(req: AskRequest): Promise<AskResponse> {
  if (usingFixtures) {
    await new Promise((r) => setTimeout(r, 350));
    return fixtureFor(req.question);
  }
  let res: Response;
  try {
    res = await fetch(`${API_URL}/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
    });
  } catch {
    throw new Error(`Couldn't reach the FlameCheck API at ${API_URL}. Check that it is running.`);
  }
  if (!res.ok) throw new Error(`The FlameCheck API returned ${res.status}. Try the question again.`);
  return res.json();
}

export const getChunks = () => (usingFixtures ? Promise.resolve([] as ChunkInfo[]) : get<ChunkInfo[]>("/chunks"));
export const getCoverage = () => get<CoveragePoint[]>("/coverage");
export const getInvestigations = () => get<Investigation[]>("/investigations");
export const getTests = () => get<TestRow[]>("/tests");
