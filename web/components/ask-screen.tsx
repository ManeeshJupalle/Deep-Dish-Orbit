"use client";

import { useEffect, useState } from "react";

import { AnswerCard } from "@/components/answer-card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { ask, getChunks, usingFixtures } from "@/lib/api";
import type { AskResponse, ChunkInfo, Conditions, Gravity } from "@/lib/types";

const SAMPLES = [
  "Does PMMA burn at 21% oxygen in microgravity?",
  "Is cotton safe at 34% oxygen on the Moon?",
  "Which FLEX tests used helium to put out the flame?",
  "Does cotton-fiberglass fabric burn in a spacecraft?",
];

const GRAVITY: { value: "" | Gravity; label: string }[] = [
  { value: "", label: "From the question" },
  { value: "micro", label: "Microgravity (orbit)" },
  { value: "moon", label: "Moon" },
  { value: "mars", label: "Mars" },
  { value: "earth", label: "Earth" },
];

export function AskScreen() {
  const [question, setQuestion] = useState("");
  const [material, setMaterial] = useState("");
  const [o2, setO2] = useState("");
  const [pressure, setPressure] = useState("");
  const [gravity, setGravity] = useState<"" | Gravity>("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<AskResponse | null>(null);
  const [chunks, setChunks] = useState<Map<string, ChunkInfo>>(new Map());

  useEffect(() => {
    getChunks()
      .then((list) => setChunks(new Map(list.map((c) => [c.chunk_id, c]))))
      .catch(() => {}); // chips still show the id without a link
  }, []);

  async function submit(q: string) {
    const text = q.trim();
    if (!text) {
      setError("Type a question first, or pick one of the examples.");
      return;
    }
    const conditions: Conditions = {};
    if (material.trim()) conditions.material = material.trim();
    if (o2 !== "") conditions.o2_pct = Number(o2);
    if (pressure !== "") conditions.pressure_kpa = Number(pressure);
    if (gravity) conditions.gravity = gravity;
    setLoading(true);
    setError(null);
    try {
      setData(await ask({ question: text, ...(Object.keys(conditions).length ? { conditions } : {}) }));
    } catch (e) {
      setData(null);
      setError(e instanceof Error ? e.message : "The question could not be answered. Try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-8">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          submit(question);
        }}
        className="space-y-4 rounded-lg border border-border bg-card p-4 sm:p-5"
      >
        <div className="space-y-2">
          <Label htmlFor="question" className="text-base font-semibold">
            Your question
          </Label>
          <Textarea
            id="question"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                submit(question);
              }
            }}
            placeholder="Is Nomex safe at 30% oxygen in a lunar habitat?"
            rows={2}
            className="text-base"
          />
        </div>

        <fieldset className="space-y-2">
          <legend className="text-sm text-muted-foreground">
            Conditions (optional, override what the question says)
          </legend>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <div className="space-y-1">
              <Label htmlFor="material">Material</Label>
              <Input id="material" value={material} onChange={(e) => setMaterial(e.target.value)} placeholder="cotton" />
            </div>
            <div className="space-y-1">
              <Label htmlFor="o2">Oxygen %</Label>
              <Input id="o2" type="number" min={0} max={100} step="any" value={o2} onChange={(e) => setO2(e.target.value)} placeholder="21" />
            </div>
            <div className="space-y-1">
              <Label htmlFor="pressure">Pressure kPa</Label>
              <Input id="pressure" type="number" min={0} step="any" value={pressure} onChange={(e) => setPressure(e.target.value)} placeholder="101.3" />
            </div>
            <div className="space-y-1">
              <Label htmlFor="gravity">Gravity</Label>
              <select
                id="gravity"
                value={gravity}
                onChange={(e) => setGravity(e.target.value as "" | Gravity)}
                className="h-8 w-full rounded-lg border border-input bg-transparent px-2 text-sm focus-visible:outline-2 focus-visible:outline-ring"
              >
                {GRAVITY.map((g) => (
                  <option key={g.value} value={g.value}>
                    {g.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </fieldset>

        <div className="flex flex-wrap items-center gap-3">
          <Button type="submit" size="lg" disabled={loading} className="px-5 text-base">
            {loading ? "Checking NASA data…" : "Ask"}
          </Button>
          {usingFixtures && (
            <span className="text-xs text-muted-foreground">
              Showing sample answers. Set NEXT_PUBLIC_API_URL to use the live API.
            </span>
          )}
        </div>

        <div>
          <p className="mb-1.5 text-sm text-muted-foreground">Try one of these</p>
          <ul className="flex flex-wrap gap-2">
            {SAMPLES.map((s) => (
              <li key={s}>
                <button
                  type="button"
                  onClick={() => {
                    setQuestion(s);
                    submit(s);
                  }}
                  className="rounded-full border border-border px-3 py-1 text-left text-sm hover:border-zero-g hover:text-zero-g focus-visible:outline-2 focus-visible:outline-ring"
                >
                  {s}
                </button>
              </li>
            ))}
          </ul>
        </div>
      </form>

      {error && (
        <p role="alert" className="rounded-lg border-l-4 border-destructive bg-card p-4 text-sm">
          {error}
        </p>
      )}

      {loading && (
        <div className="space-y-3" aria-label="Loading the answer">
          <Skeleton className="h-28 w-full" />
          <Skeleton className="h-6 w-2/3" />
          <Skeleton className="h-40 w-full" />
        </div>
      )}

      {!loading && data && <AnswerCard data={data} chunks={chunks} />}
    </div>
  );
}
