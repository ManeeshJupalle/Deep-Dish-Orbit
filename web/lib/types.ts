// Mirrors the /ask contract in ARCHITECTURE.md section 6 (and api/schemas.py).

export type Gravity = "micro" | "moon" | "mars" | "earth";
export type Status = "answered" | "no_direct_data" | "out_of_scope";
export type Outcome = "ignited" | "burned" | "extinguished" | "no_ignition" | "other";
export type TrustLevel = "high" | "medium" | "low";

export interface Conditions {
  material?: string | null;
  o2_pct?: number | null;
  pressure_kpa?: number | null;
  gravity?: Gravity | null;
  flow_cm_s?: number | null;
}

export interface AskRequest {
  question: string;
  conditions?: Conditions;
}

export interface Claim {
  text: string;
  cites: string[];
}

export interface Evidence {
  test_id: string;
  investigation: string;
  match_score: number;
  o2_pct: number | null;
  pressure_kpa: number | null;
  gravity_g: number | null;
  outcome: Outcome | null;
  source_url: string;
}

export interface AskResponse {
  status: Status;
  summary: string;
  claims: Claim[];
  evidence: Evidence[];
  bounds: { microgravity: string[]; earth: string[] };
  trust: { level: TrustLevel; reason: string };
  gaps: string[];
}

export interface ChunkInfo {
  chunk_id: string;
  source_id: string;
  title: string;
  source_url: string;
}

export interface CoveragePoint {
  test_id: string;
  o2_pct: number | null;
  pressure_kpa: number | null;
  gravity_g: number | null;
  investigation: string;
}

export interface Investigation {
  id: string;
  psi_id: string;
  title: string;
  area: string[];
  objective: string;
  hardware: string;
  fuels: string[];
  sensors: string[];
  test_count: number;
  source_url: string;
}
